import os
import streamlit as st
import base64
from openai import OpenAI
from PIL import Image, ImageOps
import numpy as np
from streamlit_drawable_canvas import st_canvas
from gtts import gTTS
import io

# ---- Configuración de página ----
st.set_page_config(page_title='🎨 Tablero Inteligente', layout="centered")
st.markdown("""
    <style>
        .stApp {background: linear-gradient(120deg, #faf3dd, #c8d5b9);}
        h1, h2, h3, h4 {color: #4a4e69;}
    </style>
""", unsafe_allow_html=True)

st.title('🧠 Tablero Inteligente')
st.write("Dibuja algo en el panel y deja que la IA lo interprete...")

# ---- Barra lateral ----
with st.sidebar:
    st.subheader("⚙️ Configuración")
    stroke_width = st.slider('Ancho de línea', 1, 30, 5)
    stroke_color = st.color_picker("Color del trazo", "#000000")
    idioma = st.selectbox("Idioma de análisis", ["Español", "Inglés", "Francés"])
    ke = st.text_input('🔑 Ingresa tu clave de API', type="password")
    limpiar = st.button("🧹 Limpiar tablero")

# ---- Inicialización ----
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False

# ---- Crear el tablero ----
canvas_result = st_canvas(
    fill_color="rgba(255,165,0,0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color="#ffffff",
    height=300,
    width=400,
    drawing_mode="freedraw",
    key="canvas",
)

if limpiar:
    st.session_state.analysis_done = False
    st.experimental_rerun()

# ---- Función para codificar imagen ----
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode("utf-8")

# ---- Cliente OpenAI ----
if ke:
    client = OpenAI(api_key=ke)
else:
    st.warning("Por favor, ingresa tu API key para continuar.")
    st.stop()

# ---- Análisis ----
if st.button("🔍 Analizar imagen") and canvas_result.image_data is not None:
    with st.spinner("Analizando el boceto..."):
        img = Image.fromarray(np.array(canvas_result.image_data).astype('uint8')).convert('RGBA')
        img.save("boceto.png")

        base64_img = encode_image_to_base64("boceto.png")
        prompt = f"Describe brevemente el dibujo en {idioma.lower()}."

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                    ],
                }],
                max_tokens=300
            )
            full_response = response.choices[0].message.content
            st.image("boceto.png", caption="🖼️ Tu dibujo")
            st.success("✨ Descripción generada:")
            st.write(full_response)
            st.session_state.analysis_done = True
            st.session_state.full_response = full_response

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

# ---- Generar historia ----
if st.session_state.analysis_done:
    st.divider()
    if st.button("📚 Crear historia infantil"):
        with st.spinner("Imaginando historia..."):
            story_prompt = (
                f"Basándote en esta descripción: '{st.session_state.full_response}', "
                f"crea una historia infantil corta, dulce y creativa en {idioma.lower()}."
            )
            story = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": story_prompt}],
                max_tokens=400
            )
            texto = story.choices[0].message.content
            st.balloons()
            st.markdown("### 🧚 Tu historia:")
            st.write(texto)

            # Opción para escuchar
            if st.button("🔊 Escuchar historia"):
                tts = gTTS(texto, lang="es" if idioma == "Español" else "en")
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                st.audio(audio_fp.getvalue(), format="audio/mp3")
