import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import json
import datetime

# FIREBASE CONFIG
PROJECT_ID = "ai-design-collab"
FIREBASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/designs"

# Template images for garments
TEMPLATES = {
    "Hoodie": "hoodie_template.png",
    "T-Shirt": "tshirt_template.png",
    "Crewneck": "crewneck_template.png"
}

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
    payload = {
        "fields": {
            "votes": {"integerValue": str(current_votes + 1)}
        }
    }
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

# Streamlit UI
tab1, tab2 = st.tabs(["🎨 Create a Design", "🖼 Community Gallery"])

with tab1:
    st.title("🎨 AI Design Collab Assistant")
    garment = st.selectbox("Choose your base garment:", list(TEMPLATES.keys()))
    prompt = st.text_area("Describe your design idea:", placeholder="e.g. A graffiti-style phoenix with neon accents")
    name = st.text_input("Your name or IG handle")
    generate_btn = st.button("Generate & Submit")

    if generate_btn and prompt.strip() and name.strip():
        with st.spinner("Generating your design..."):
            try:
                image_url, ai_image = generate_image(prompt.strip())
                template = load_template(garment)
                mockup = create_mockup(template, ai_image)
                st.image(mockup, caption="Here’s your mockup!", use_column_width=True)

                submit_to_firestore(name.strip(), prompt.strip(), image_url)
                st.success("✅ Design submitted to the gallery!")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

with tab2:
    st.title("🖼 Community Gallery")
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
        vote_btn = st.button(f"👍 Vote ({votes})", key=f"vote-{doc_name}")
        if vote_btn:
            update_vote(doc_name, votes)
            st.experimental_rerun()
        st.markdown("---")
