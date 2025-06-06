import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import json
import datetime
import time

# FIREBASE CONFIG
PROJECT_ID = "ai-design-collab"
FIREBASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/designs"

TEMPLATES = {
    "Hoodie": "hoodie_template.png",
    "T-Shirt": "tshirt_template.png",
    "Crewneck": "crewneck_template.png"
}

if "voted_ids" not in st.session_state:
    st.session_state.voted_ids = set()

st.set_page_config(page_title="AI Design Collab — North East", layout="centered")

# Custom styling: layout + tab colors
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: black; }
    h3, .stMarkdown, label { color: black !important; }
    #MainMenu, footer, header { visibility: hidden; }
    [data-baseweb="tab-list"] {
        background-color: #ffffff;
        border-bottom: 1px solid #ccc;
    }
    [data-baseweb="tab"] {
        color: black;
        background-color: #f2f2f2;
        border-radius: 6px 6px 0 0;
        margin-right: 8px;
        padding: 0.5em 1em;
        font-weight: 500;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background-color: #000000 !important;
        color: white !important;
    }
    [data-baseweb="tab"]:hover {
        background-color: #cc0000;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Branding header
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,300;400&display=swap" rel="stylesheet">
<div style="display: flex; align-items: center; justify-content: center; gap: 1.5em; margin-top: 1em;">
    <img src="https://i.imgur.com/Mj0JSG5.png" width="60" style="margin-bottom: 0;">
    <div style='font-family: "Source Serif 4", serif; text-align: left;'>
        <div style='font-size: 36px; font-weight: 400; text-transform: uppercase; letter-spacing: 1px;'>North East Streetwear</div>
        <div style='font-size: 20px; font-weight: 300; text-align: center;'>North of the Noise</div>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

def load_template(garment):
    return Image.open(TEMPLATES[garment]).convert("RGBA")

@st.cache_data(show_spinner=True)
def generate_image(prompt):
    api_url = "https://stablediffusionapi.com/api/v4/dreambooth"
    headers = { "Content-Type": "application/json" }
    payload = {
        "key": "ltKAsEti5CsV8MFeemRMW4WufMsMqsvScIud2xWnWGPsvA8bQXE4sDSzOurI",
        "model_id": "realistic-vision-v51",
        "prompt": prompt,
        "width": "512",
        "height": "512",
        "samples": "1",
        "num_inference_steps": "30",
        "safety_checker": "no",
        "enhance_prompt": "yes",
        "guidance_scale": 7.5
    }
    response = requests.post(api_url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    result = response.json()
    image_url = result["output"][0]
    image_response = requests.get(image_url)
    image_response.raise_for_status()
    return image_url, Image.open(BytesIO(image_response.content)).convert("RGBA")

def create_mockup(template_img, design_img):
    design_img = design_img.resize((368, 300))
    mockup = template_img.copy()
    mockup.paste(design_img, (200, 300), design_img)
    return mockup

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
    response.raise_for_status()

def update_vote(document_name, current_votes):
    patch_url = f"{FIREBASE_URL}/{document_name}?updateMask.fieldPaths=votes"
    payload = { "fields": { "votes": {"integerValue": str(current_votes + 1)} } }
    requests.patch(patch_url, json=payload)

def get_gallery():
    try:
        response = requests.get(FIREBASE_URL)
        response.raise_for_status()
        data = response.json()
        return sorted(data.get("documents", []), key=lambda d: d["fields"]["timestamp"]["timestampValue"], reverse=True)
    except Exception as e:
        st.error(f"Could not load gallery: {e}")
        return []

tab1, tab2 = st.tabs(["🎨 Create a Design", "🖼 Community Gallery"])

with tab1:
    st.subheader("Upload or Generate Your Design")
    upload_image = st.file_uploader("Upload a PNG or JPG image", type=["png", "jpg", "jpeg"])
    prompt = st.text_area("Describe your design (optional)")
    name = st.text_input("Your name or IG handle")
    garment = st.selectbox("Choose your base garment (if generated):", list(TEMPLATES.keys()))
    submit_btn = st.button("Submit to Gallery")

    if submit_btn and name.strip() and (upload_image or prompt.strip()):
        with st.spinner("Submitting your design..."):
            try:
                if upload_image:
                    img = Image.open(upload_image).convert("RGBA")
                    image_url = "https://via.placeholder.com/512x512.png?text=Uploaded+Image"
                else:
                    image_url, img = generate_image(prompt.strip())
                    template = load_template(garment)
                    img = create_mockup(template, img)

                st.image(img, caption="Design preview", use_container_width=True)
                submit_to_firestore(name.strip(), prompt.strip(), image_url)
                st.success("✅ Design submitted to the gallery!")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

with tab2:
    docs = get_gallery()
    for doc in docs:
        doc_name = doc["name"].split("/")[-1]
        fields = doc.get("fields", {})
        name = fields.get("name", {}).get("stringValue", "Anonymous")
        prompt = fields.get("prompt", {}).get("stringValue", "")
        image_url = fields.get("image_url", {}).get("stringValue", "")
        votes = int(fields.get("votes", {}).get("integerValue", "0"))

        if image_url:
            st.image(image_url, width=384)
        else:
            st.warning("⚠️ This submission has no image attached.")
            st.json(fields)

        st.caption(f"**{name}** – _{prompt}_")
        vote_key = f"vote-{doc_name}"
        has_voted = doc_name in st.session_state.voted_ids

        if has_voted:
            st.button(f"✅ Voted ({votes})", key=vote_key, disabled=True)
        else:
            if st.button(f"👍 Vote ({votes})", key=vote_key):
                try:
                    update_vote(doc_name, votes)
                    st.session_state.voted_ids.add(doc_name)
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.warning(f"Vote registered, but rerun was blocked: {e}")

        st.markdown("---")
