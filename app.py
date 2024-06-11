import streamlit as st

st.title("Yo-Ko-So: Sensyn Guide")
prompt = st.chat_input("Please enter your question")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        responce = "こんにちは"
        st.markdown(responce)
