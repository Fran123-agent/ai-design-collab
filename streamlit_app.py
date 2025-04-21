
import streamlit as st
from PIL import Image
import requests
from io import BytesIO
import openai
import os

# Set your OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")

# Garment templates
TEMPLATES = {
    "Hoodie": "hoodie_template.png",
    "T-Shirt": "tshirt_template.png",
    "Crewneck": "crewneck_template.png"
}

# Load templates
def load_template(garment):
    return Image.open(TEMPLATES[garment]).convert("RGBA")

# Generate image from prompt using DALL-E
@st.cache_data(show_spinner=True)
def generate_image(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="512x512"
    )
    image_url = response['data'][0]['url']
    image_response = requests.get(image_url)
    return Image.open(BytesIO(image_response.content)).convert("RGBA")

# Overlay design on garment template
def create_mockup(template_img, design_img):
    design_img = design_img.resize((368, 300))
    mockup = template_img.copy()
    mockup.paste(design_img, (200, 300), design_img)
    return mockup

# Streamlit App
st.title("🎨 AI Design Collab Assistant")
st.write("Drop your idea and we’ll mock it up on your favorite garment.")

# User inputs
garment = st.selectbox("Choose your base garment:", list(TEMPLATES.keys()))
prompt = st.text_area("Describe your design idea:", placeholder="e.g. A graffiti-style phoenix with neon accents")

uploaded_img = st.file_uploader("(Optional) Upload an inspiration image", type=["png", "jpg", "jpeg"])

generate_btn = st.button("Generate Design")

if generate_btn and prompt:
    with st.spinner("Cooking up your design..."):
        try:
            ai_image = generate_image(prompt)
            template = load_template(garment)
            mockup = create_mockup(template, ai_image)

            st.image(mockup, caption="Here’s your mockup!", use_column_width=True)

            with st.expander("Submit your design"):
                name = st.text_input("Your name or IG handle")
                if st.button("Submit Idea"):
                    st.success("Submitted! We'll review and maybe feature it.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
else:
    st.info("Enter a prompt and hit Generate to get started.")
