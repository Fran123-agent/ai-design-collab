import streamlit as st
import requests
import json
import datetime

# FIREBASE CONFIG
PROJECT_ID = "ai-design-collab"
FIREBASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/designs"

def submit_to_firestore(name, prompt, image_url):
    payload = {
        "fields": {
            "name": {"stringValue": name},
            "prompt": {"stringValue": prompt},
            "image_url": {"stringValue": image_url},
            "votes": {"integerValue": "0"},
            "timestamp": {"timestampValue": datetime.datetime.utcnow().isoformat() + "Z"}
        }
    }
    response = requests.post(FIREBASE_URL, json=payload)
    st.write("📬 Firebase response:", response.status_code, response.text)
    response.raise_for_status()

# --- UI TEST ONLY ---
st.title("🧪 Firebase Submit Debug Test")

st.markdown("This is a test-only version to verify form submission and Firestore write.")

# Static mock design
mock_prompt = "Test design for debugging"
mock_image_url = "https://via.placeholder.com/512x512.png?text=Design+Test"

with st.form("Test Submit Form"):
    name = st.text_input("Your name or IG handle")
    submitted = st.form_submit_button("Submit Design to Firestore")
    if submitted:
        st.write("🧠 Form submitted — calling Firestore...")
        try:
            submit_to_firestore(name, mock_prompt, mock_image_url)
            st.success("✅ Submitted successfully!")
        except Exception as e:
            st.error(f"❌ Submission failed: {e}")
