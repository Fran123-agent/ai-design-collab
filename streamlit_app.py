import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import json

# Garment templates
TEMPLATES = {
    "Hoodie": "hoodie_template.png",
    "T-Shirt": "tshirt_template.png",
    "Crewneck": "crewneck_template.png"
}

def load_template(garment):
    return Image.open(TEMPLATES[garment]).convert("RGBA")

@st.cache_data(show_spinner=True)
def generate_image(prompt):
    try:
        api_url = "https://stablediffusionapi.com/api/v4/dreambooth"
        headers = {
            "Content-Type": "application/json"
        }
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
            "guidance_scale": 7.5,
            "multi_lingual": "no",
            "panorama": "no",
            "self_attention": "no",
            "upscale": "no",
            "embeddings": None,
            "lora": None,
            "webhook": None,
            "track_id": None
        }

        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        # 🪵 Debug output
        st.write("API response:", result)

        if "output" in result and isinstance(result["output"], list):
            image_url = result["output"][0]
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            return Image.open(BytesIO(image_response.content)).convert("RGBA")
        else:
            raise Exception(f"Invalid response structure from the API: {result}")

    except Exception as e:
        st.error(f"Image generation error: {e}")
        raise

def create_mockup(template_img, design_img):
    design_img = design_img.resize((368, 300))
    mockup = template_img.copy()
    mockup.paste(design_img, (200, 300), design_img)
    return mockup

# Streamlit UI
st.title("🎨 AI Design Collab Assistant")
st.write("Drop your idea and we’ll mock it up on your favorite garment.")

garment = st.selectbox("Choose your base garment:", list(TEMPLATES.keys()))
prompt = st.text_area("Describe your design idea:", placeholder="e.g. A graffiti-style phoenix with neon accents")

uploaded_img = st.file_uploader("(Optional) Upload an inspiration image", type=["png", "jpg", "jpeg"])
generate_btn = st.button("Generate Design")

if generate_btn and prompt.strip():
    with st.spinner("Cooking up your design..."):
        try:
            ai_image = generate_image(prompt.strip())
            template = load_template(garment)
            mockup = create_mockup(template, ai_image)
            st.image(mockup, caption="Here’s your mockup!", use_column_width=True)

            with st.expander("Submit your design"):
                name = st.text_input("Your name or IG handle")
                if st.button("Submit Idea"):
                    st.success("Submitted! We'll review and maybe feature it.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
else:
    st.info("Enter a prompt and hit Generate to get started.")
