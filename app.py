import streamlit as st
from backend import ChatBot
import numpy as np
from PIL import Image
import base64


def to_base64(uploaded_file):
    file_buffer = uploaded_file.read()
    b64 = base64.b64encode(file_buffer).decode()
    return f"data:image/png;base64,{b64}"


st.title("Yo-Co-So: Sensyn Guide")
prompt = st.chat_input(
    "Please enter your question. You can also upload an image from the side bar.")

# prepare bot
bot = ChatBot()

# init message
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


with st.sidebar:
    st.title("Upload Your Images")
    st.session_state.image = st.file_uploader(
        label=" ")
    print(f"{st.session_state.image}")
    if st.session_state.image is not None:
        image_url_contents = to_base64(st.session_state.image)

        # display image
        st.image(image_url_contents, use_column_width=True)


if prompt:
    # add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        responce = bot.respond(prompt, image_url_contents)
        st.markdown(responce)

    # add assistant message
    st.session_state.messages.append(
        {"role": "assistant", "content": responce})
