import streamlit as st
import requests


BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI-Smart city", layout="wide")
st.title("AI SMART CITY")

# --- 1. Upload Section ---
st.header("Upload Image")
uploaded_file = st.file_uploader("Choose a file", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    if st.button("Upload to Server"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        try:
            response = requests.post(f"{BASE_URL}/uploadfile/", files=files)
            if response.status_code == 200:
                st.session_state["uploaded_filename"] = uploaded_file.name
                st.session_state["uploaded_image"] = uploaded_file.getvalue()
                st.success(f"File '{uploaded_file.name}' saved successfully.")
            else:
                st.error(f"Upload failed with status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the Backend. Is it running?")

st.divider()

# --- 2. Description Section ---
st.header("Enter User Description")
description_input = st.text_area("Enter your description:", placeholder="What is in this image?")

address_input = st.text_input("Enter the address",placeholder="Adreess of the complaint area")
if st.button("Upload Description"):

    # --- Validation ---
    if not description_input.strip():
        st.warning("Please enter a description")

    elif not address_input.strip():
        st.warning("Please enter an address")

    elif "uploaded_filename" not in st.session_state:
        st.warning("Please upload an image first")

    else:

        payload = {
            "text": description_input,
            "address": address_input,
            "filename": st.session_state["uploaded_filename"]
        }

        try:
            response = requests.post(
                f"{BASE_URL}/imageDescription",
                json=payload
            )

            if response.status_code == 200:
                data = response.json()

                st.session_state["confirmed_description"] = data.get("description")
                st.session_state["confirmed_address"] = data.get("address")

                st.success("Description uploaded successfully.")

            else:
                st.error(f"Failed to upload description. Status: {response.status_code}")

        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the Backend.")

st.divider()


# --- 3. Result Display ---
if "uploaded_image" in st.session_state and "confirmed_description" in st.session_state:
    st.header("Result")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(st.session_state["uploaded_image"], width=400)
        st.markdown(
                f"""
                <div style='
                    background-color: #1a3a5c;
                    border: 1px solid #2e6da4;
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin-top: 10px;
                    text-align: center;
                    font-size: 16px;
                    color: #d0e8ff;
                '>
                    <b>Description:</b> {st.session_state["confirmed_description"]}<br>
                    <b>Address:</b> {st.session_state.get("confirmed_address", "N/A")}
                </div>
                """,
    unsafe_allow_html=True
)
