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

# --- UI TEST: NO FORM ---
st.title("🚧 Submit Without Form (Direct Button)")

name = st.text_input("Your name or IG handle")
if st.button("🔁 Submit Design to Firestore"):
    st.write("🧠 Button clicked — sending to Firestore...")
    try:
        submit_to_firestore(
            name,
            "Hardcoded test prompt from no-form debug",
            "https://via.placeholder.com/512x512.png?text=Test"
        )
        st.success("✅ Submitted successfully!")
    except Exception as e:
        st.error(f"❌ Submission failed: {e}")
