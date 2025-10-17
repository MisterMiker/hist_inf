import os
import streamlit as st
import base64
from openai import OpenAI
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas

# ---- Configuración de página ----
st.set_page_config(page_title='🎨 Tablero Inteligente', layout="centered")
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(120deg, #fefae0, #e9edc9);
            color: #3a3a3a;
        }
        h1, h2, h3, h4 {
            color: #283618;
        }
        .stButton>button {
            background-color: #606c38;
            color: white;
            border-radius: 10px;
            border: none;
        }
        .stButton>button:hover {
            background-color: #283618;
        }
    </style>
""", unsafe_allow_html=True)

st.title('🧠 Tablero Inteligente')
st.write("Dibuja un boceto en el panel y deja que la IA lo interprete.")

# ---- Inicialización de session_state ----
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'full_response' not in st.session_state:
    st.session_state.full_response = ""
if 'base64_image' not in st.session_state:
    st.session_state.base64_image = ""
if 'image_history' not in st.session_state:
    st.session_state.image_history = []  # Guardar imágenes analizadas

# ---- Barra lateral ----
with st.sidebar:
    st.subheader("⚙️ Opciones del Tablero")
    stroke_width = st.slider('Ancho del trazo', 1, 30, 5)
    stroke_color = st.color_picker("Color del trazo", "#000000")
    ke = st.text_input('🔑 Ingresa tu Clave API', type="password")
    limpiar = st.button("🧹 Limpiar tablero")

# ---- Crear el tablero ----
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color="#ffffff",
    height=300,
    width=400,
    drawing_mode="freedraw",
    key="canvas",
)

# Limpiar tablero
if limpiar:
    st.session_state.analysis_done = False
    st.experimental_rerun()

# ---- Función para codificar imagen ----
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# ---- Inicializar cliente ----
if not ke:
    st.warning("Por favor ingresa tu API key para continuar.")
    st.stop()

client = OpenAI(api_key=ke)

# ---- Botón de análisis ----
if st.button("🔍 Analizar dibujo") and canvas_result.image_data is not None:
    with st.spinner("Analizando boceto..."):
        img = Image.fromarray(np.array(canvas_result.image_data).astype('uint8')).convert('RGBA')
        img.save("boceto.png")

        base64_img = encode_image_to_base64("boceto.png")

        prompt_text = "Describe brevemente el contenido de este dibujo en español."

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                    ],
                }],
                max_tokens=300
            )

            full_response = response.choices[0].message.content
            st.session_state.full_response = full_response
            st.session_state.analysis_done = True
            st.session_state.image_history.append(("boceto.png", full_response))  # Guardar imagen y descripción

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

# ---- Mostrar resultado del análisis ----
if st.session_state.analysis_done:
    st.divider()
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("boceto.png", caption="🖼️ Tu dibujo analizado")
    with col2:
        st.markdown("### ✨ Descripción generada:")
        st.write(st.session_state.full_response)

# ---- Mostrar historial de imágenes ----
if st.session_state.image_history:
    st.divider()
    st.subheader("🕒 Historial de dibujos analizados")
    for i, (img_path, desc) in enumerate(reversed(st.session_state.image_history[-3:]), 1):
        with st.expander(f"🖌️ Análisis {len(st.session_state.image_history) - i + 1}"):
            st.image(img_path, caption=f"Dibujo {len(st.session_state.image_history) - i + 1}")
            st.write(desc)
