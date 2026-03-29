import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI-Smart City", layout="wide")


st.markdown("""
<style>
    /* Auth card */
    .auth-card {
        background: linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%);
        border: 1px solid #2e6da4;
        border-radius: 12px;
        padding: 32px 36px;
        max-width: 420px;
        margin: 60px auto 0 auto;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    .auth-title {
        color: #d0e8ff;
        font-size: 26px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 4px;
        letter-spacing: 1px;
    }
    .auth-subtitle {
        color: #7aafd4;
        font-size: 13px;
        text-align: center;
        margin-bottom: 24px;
    }
    /* Tab-style toggle */
    .tab-row {
        display: flex;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #2e6da4;
        margin-bottom: 24px;
    }
    /* Logged-in badge */
    .user-badge {
        background: #1a3a5c;
        border: 1px solid #2e6da4;
        border-radius: 20px;
        padding: 4px 14px;
        color: #d0e8ff;
        font-size: 13px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "token" not in st.session_state:
    st.session_state["token"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "Login"   

def auth_page():
    st.markdown("<h1 style='text-align:center;color:#d0e8ff;letter-spacing:2px;margin-top:20px;'>🏙️ AI SMART CITY</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#7aafd4;margin-bottom:0;'>Intelligent Urban Complaint Management</p>", unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.6, 1])
    with mid:
\        col_l, col_r = st.columns(2)
        with col_l:
            if st.button("🔑  Login", use_container_width=True,
                         type="primary" if st.session_state["auth_mode"] == "Login" else "secondary"):
                st.session_state["auth_mode"] = "Login"
                st.rerun()
        with col_r:
            if st.button("✏️  Sign Up", use_container_width=True,
                         type="primary" if st.session_state["auth_mode"] == "Sign Up" else "secondary"):
                st.session_state["auth_mode"] = "Sign Up"
                st.rerun()

        st.markdown("---")

        if st.session_state["auth_mode"] == "Login":
            st.markdown("<div class='auth-title'>Welcome Back</div>", unsafe_allow_html=True)
            st.markdown("<div class='auth-subtitle'>Sign in to continue</div>", unsafe_allow_html=True)

            username = st.text_input("Username", key="login_user", placeholder="Enter username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter password")

            if st.button("Login →", use_container_width=True, type="primary"):
                if not username.strip() or not password.strip():
                    st.warning("Please fill in both fields.")
                else:
                    try:
                        resp = requests.post(
                            f"{BASE_URL}/login",
                            data={"username": username, "password": password},
                            headers={"Content-Type": "application/x-www-form-urlencoded"}
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state["logged_in"] = True
                            st.session_state["token"] = data["access_token"]
                            st.session_state["username"] = username
                            st.success(f"Welcome back, **{username}**! 🎉")
                            st.rerun()
                        else:
                            detail = resp.json().get("detail", "Login failed.")
                            st.error(f"❌ {detail}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to the backend. Is it running?")

        else:
            st.markdown("<div class='auth-title'>Create Account</div>", unsafe_allow_html=True)
            st.markdown("<div class='auth-subtitle'>Join AI Smart City today</div>", unsafe_allow_html=True)

            new_user = st.text_input("Choose a Username", key="signup_user", placeholder="Enter username")
            new_pass = st.text_input("Choose a Password", type="password", key="signup_pass", placeholder="Min 6 characters")
            confirm_pass = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Re-enter password")

            if st.button("Create Account →", use_container_width=True, type="primary"):
                if not new_user.strip() or not new_pass.strip():
                    st.warning("Please fill in all fields.")
                elif len(new_pass) < 6:
                    st.warning("Password must be at least 6 characters.")
                elif new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                else:
                    try:
                        resp = requests.post(
                            f"{BASE_URL}/signup",
                            data={"username": new_user, "password": new_pass},
                            headers={"Content-Type": "application/x-www-form-urlencoded"}
                        )
                        if resp.status_code == 200:
                            st.success("Account created! Please log in.")
                            st.session_state["auth_mode"] = "Login"
                            st.rerun()
                        else:
                            detail = resp.json().get("detail", "Sign up failed.")
                            st.error(f"❌ {detail}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to the backend. Is it running?")

def main_app():
    col_title, col_user = st.columns([5, 1])
    with col_title:
        st.title("🏙️ AI SMART CITY")
    with col_user:
        st.markdown(f"<div class='user-badge'>👤 {st.session_state['username']}</div>", unsafe_allow_html=True)
        if st.button("Logout", type="secondary"):
            for key in ["logged_in", "token", "username",
                        "uploaded_filename", "uploaded_image",
                        "confirmed_description", "confirmed_address"]:
                st.session_state.pop(key, None)
            st.rerun()

    st.header("Upload Image")
    uploaded_file = st.file_uploader("Choose a file", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        if st.button("Upload to Server"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                response = requests.post(f"{BASE_URL}/uploadfile/", files=files, headers=headers)
                if response.status_code == 200:
                    st.session_state["uploaded_filename"] = uploaded_file.name
                    st.session_state["uploaded_image"] = uploaded_file.getvalue()
                    st.success(f"File '{uploaded_file.name}' saved successfully.")
                else:
                    st.error(f"Upload failed with status: {response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the Backend. Is it running?")

    st.divider()

    st.header("Enter User Description")
    description_input = st.text_area("Enter your description:", placeholder="What is in this image?")
    address_input = st.text_input("Enter the address", placeholder="Address of the complaint area")

    if st.button("Upload Description"):
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
                headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                response = requests.post(f"{BASE_URL}/imageDescription", json=payload, headers=headers)
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

    
def admin_panel():
    st.title("🏙️ AI Smart City - Admin Panel")
    st.subheader(f"Welcome, {st.session_state['username']} (Administrator)")

    if st.button("Logout", type="secondary"):
        st.session_state.clear()
        st.rerun()

    st.divider()

    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    try:
        resp = requests.get(f"{BASE_URL}/admin/complaints", headers=headers)
        if resp.status_code == 200:
            complaints = resp.json()
            if not complaints:
                st.info("No complaints have been filed yet.")
            else:
                for c in complaints:
                    with st.expander(f"📌 {c['username']} - {c['address']}"):
                        st.write(f"**Description:** {c['text']}")
                        st.image(f"{BASE_URL}/view/{c['filename']}", caption="Attached Evidence", width=300)
                        st.write(f"**Current Severity:** {c['severity']}")
        else:
            st.error("Access denied. Are you sure you're an admin?")
    except Exception as e:
        st.error("Failed to connect to the backend server.")    
        
if st.session_state["logged_in"]:
    if st.session_state["username"] in ["BHAVY", "SMARTYY"]:
        admin_panel()
    else:
        main_app()
else:
    auth_page()        
