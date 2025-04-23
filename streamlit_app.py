import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import json
import datetime
import uuid
import firebase_admin
from firebase_admin import credentials, firestore

# ----------------------------
# 🔥 Firebase Setup
# ----------------------------

if "firebase_initialized" not in st.session_state:
    firebase_config = {
        "type": "service_account",
        "project_id": "ai-design-collab",
        "private_key_id": "dummy",
        "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEv...\\n-----END PRIVATE KEY-----\\n",
        "client_email": "dummy@ai-design-collab.iam.gserviceaccount.com",
        "client_id": "dummy",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/dummy@ai-design-collab.iam.gserviceaccount.com"
    }

    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred, {'projectId': firebase_config["project_id"]})
    st.session_state.firebase_initialized = True

db = firestore.client()

# ----------------------------
# 🧵 Mockup Templates
# ----------------------------

TEMPLATES = {
    "Hoodie": "hoodie_template.png",
    "T-Shirt": "tshirt_template.png",
    "Crewneck": "crewneck_template.png"
}

def load_template(garment):
    return Image.open(TEMPLATES[garment]).convert("RGBA")

# ----------------------------
# 🎨 AI Image Generation
# ----------------------------

@st.cache_data(show_spinner=True)
def generate_image(prompt):
    try:
        api_url = "https://stablediffusionapi.com/api/v4/dreambooth"
        headers = { "Content-Type": "application/json" }
        payload = {
            "key": "ltKAsEti5CsV8MFeemRMW4WufMsMqsvScIud2xWnWGPsvA8bQXE4sDSzOurI",
            "model_id": "realistic-vision-v51",
            "prompt": prompt,
            "negative_prompt": "",
            "width": "512",
            "height": "512",
            "samples": "1",
            "num_inference_steps": "30",
            "safety_checker": "no",
            "enhance_prompt": "yes",
            "seed": None,
            "guidance_scale": 7.5
        }

        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        if "output" in result and isinstance(result["output"], list):
            image_url = result["output"][0]
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            return image_url, Image.open(BytesIO(image_response.content)).convert("RGBA")
        else:
            raise Exception(f"Invalid response structure from API: {result}")

    except Exception as e:
        st.error(f"Image generation error: {e}")
        raise

# ----------------------------
# 🧩 Overlay Design on Template
# ----------------------------

def create_mockup(template_img, design_img):
    design_img = design_img.resize((368, 300))
    mockup = template_img.copy()
    mockup.paste(design_img, (200, 300), design_img)
    return mockup

# ----------------------------
# 🚀 Streamlit App UI
# ----------------------------

tab1, tab2 = st.tabs(["🎨 Create a Design", "🖼 Community Gallery"])

# --- Tab 1: Design Generator
with tab1:
    st.title("🎨 AI Design Collab Assistant")

    garment = st.selectbox("Choose your base garment:", list(TEMPLATES.keys()))
    prompt = st.text_area("Describe your design idea:", placeholder="e.g. A graffiti-style phoenix with neon accents")
    generate_btn = st.button("Generate Design")

    if generate_btn and prompt.strip():
        with st.spinner("Generating your design..."):
            try:
                image_url, ai_image = generate_image(prompt.strip())
                template = load_template(garment)
                mockup = create_mockup(template, ai_image)
                st.image(mockup, caption="Here’s your mockup!", use_column_width=True)

                with st.form("Submit design"):
                    name = st.text_input("Your name or IG handle")
                    if st.form_submit_button("Submit to Gallery"):
                        doc_id = str(uuid.uuid4())
                        db.collection("designs").document(doc_id).set({
                            "name": name,
                            "prompt": prompt.strip(),
                            "image_url": image_url,
                            "votes": 0,
                            "timestamp": datetime.datetime.utcnow().isoformat()
                        })
                        st.success("✅ Design submitted to the gallery!")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# --- Tab 2: Community Gallery
with tab2:
    st.title("🖼 Community Gallery")

    docs = db.collection("designs").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    for doc in docs:
        design = doc.to_dict()
        st.image(design["image_url"], width=384)
        st.caption(f"**{design.get('name', 'Anonymous')}** – _{design.get('prompt', '')}_")
        vote_col1, vote_col2 = st.columns([1, 4])
        with vote_col1:
            if st.button(f"👍 {design.get('votes', 0)}", key=f"vote-{doc.id}"):
                db.collection("designs").document(doc.id).update({
                    "votes": firestore.Increment(1)
                })
        st.markdown("---")
