import streamlit as st
import cv2
import numpy as np
import pandas as pd
import datetime
import os
from streamlit_javascript import st_javascript

# --- Updated User credentials ---
USERS = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    '11283': {'password': '11283', 'role': 'user'},
    '11202': {'password': '11202', 'role': 'user'}
}

ATTENDANCE_FILE = 'attendance.csv'

# Initialize attendance file
def init_attendance_file():
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=['Name', 'Date', 'Time', 'Latitude', 'Longitude', 'ImageFile'])
        df.to_csv(ATTENDANCE_FILE, index=False)

# Webcam single frame capture
def capture_image():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("Webcam not detected.")
        return None

    ret, frame = cap.read()
    cap.release()

    if not ret:
        st.error("Failed to capture image.")
        return None

    return frame

# Face detection in image
def detect_face_and_save(frame):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    if len(faces) == 0:
        return None, None

    for (x, y, w, h) in faces:
        face_img = frame[y:y+h, x:x+w]
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        image_path = f"face_{timestamp}.jpg"
        cv2.imwrite(image_path, face_img)
        return face_img, image_path

    return None, None

# Fixed get_location with unique key and retry button
def get_location():
    key = "get_location_component"
    coords = st_javascript(
        "navigator.geolocation.getCurrentPosition((pos) => pos.coords)",
        key=key
    )
    if coords and isinstance(coords, dict) and "latitude" in coords:
        return coords["latitude"], coords["longitude"]
    else:
        st.warning("Please allow location access and press the button below to retry.")
        if st.button("Retry Location"):
            st.experimental_rerun()
    return None

# Login
def login():
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login_btn = st.sidebar.button("Login")

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.session_state['role'] = ''

    if login_btn:
        user = USERS.get(username)
        if user and user['password'] == password:
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.session_state['role'] = user['role']
            st.success(f"Logged in as {username}")
        else:
            st.error("Invalid credentials")

    return st.session_state['logged_in'], st.session_state['role'], st.session_state['username']

# Logout
def logout():
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.session_state['role'] = ''
        st.experimental_rerun()

# Main app
def main():
    st.set_page_config(page_title="Attendance System", layout="centered")
    st.title("Attendance System")

    init_attendance_file()

    logged_in, role, username = login()
    if logged_in:
        logout()
        menu = ["Check In"]
        if role == "admin":
            menu.append("Admin View")

        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Check In":
            if st.button("Capture Face"):
                frame = capture_image()
                if frame is not None:
                    face_img, image_path = detect_face_and_save(frame)
                    if face_img is not None:
                        st.image(face_img, caption="Face Captured", channels="BGR")

                        location = get_location()
                        if not location:
                            st.warning("Could not retrieve location. Please allow access and try again.")
                            return
                        lat, lon = location

                        now = datetime.datetime.now()
                        df = pd.read_csv(ATTENDANCE_FILE)
                        df = df.append({
                            'Name': username,
                            'Date': now.strftime('%Y-%m-%d'),
                            'Time': now.strftime('%H:%M:%S'),
                            'Latitude': lat,
                            'Longitude': lon,
                            'ImageFile': image_path
                        }, ignore_index=True)
                        df.to_csv(ATTENDANCE_FILE, index=False)
                        st.success("Attendance Recorded.")
                    else:
                        st.error("No face detected. Try again.")
                else:
                    st.error("Failed to capture from webcam.")

        elif choice == "Admin View" and role == "admin":
            st.header("Attendance Records")
            df = pd.read_csv(ATTENDANCE_FILE)
            st.dataframe(df)
            st.download_button("Download CSV", df.to_csv(index=False), "attendance.csv")
    else:
        st.info("Please log in to use the system.")

if __name__ == "__main__":
    main()
