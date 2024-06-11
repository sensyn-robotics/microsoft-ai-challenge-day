import streamlit as st

st.title("Yo-Ko-So: Sensyn Guide")
prompt = st.chat_input("Please enter your question")

# init message
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt:
    # add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        responce = "こんにちは"
        st.markdown(responce)

    # add assistant message
    st.session_state.messages.append(
        {"role": "assistant", "content": responce})
