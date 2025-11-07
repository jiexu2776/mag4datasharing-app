import streamlit as st
from requests.auth import HTTPBasicAuth
import requests
import urllib.parse  # <-- you were missing this import

# -------------------- Config
CLIENT_ID = st.secrets["Orcid_ID"]
CLIENT_SECRET = st.secrets["Orcid_Secret"]

# IMPORTANT: This must EXACTLY match one of the Redirect URIs registered in your ORCID app
# If you've registered /ORCID_login there, use that. If you've registered /Browse_Datasets, keep it.
REDIRECT_URI = "https://mag4datasharing-app.streamlit.app/ORCID_login"

# -------------------- Helpers
def get_orcid_token(code: str):
    resp = requests.post(
        "https://orcid.org/oauth/token",
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI},
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        timeout=20,
    )
    return resp.json().get("access_token") if resp.status_code == 200 else None

def get_orcid_user_info(access_token: str):
    resp = requests.get(
        "https://orcid.org/oauth/userinfo",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=20,
    )
    if resp.status_code == 200:
        return resp.json()
    else:
        return None  # avoid st.error inside helpers

# -------------------- Session init (do NOT reset every run)
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "orcid_token" not in st.session_state:
    st.session_state.orcid_token = None
if "orcid_user_info" not in st.session_state:
    st.session_state.orcid_user_info = None

# -------------------- UI
st.title("ORCID Authentication")
st.info("Click the button to sign in with ORCID. You’ll be redirected to ORCID and back here automatically.")

# 1) If redirected back with ?code=..., complete login immediately
params = st.query_params
code = params.get("code")
if isinstance(code, list):
    code = code[0]

if code and not st.session_state.is_authenticated:
    with st.spinner("Completing ORCID sign-in..."):
        token = get_orcid_token(code)
        if token:
            st.session_state.orcid_token = token
            st.session_state.orcid_user_info = get_orcid_user_info(token)
            st.session_state.is_authenticated = True
            st.success("✅ Logged in with ORCID.")
        else:
            st.error("❌ ORCID token exchange failed. Check client ID/secret and redirect URI.")

# 2) Show login button (single-click → top-level redirect)
if not st.session_state.is_authenticated:
    auth_params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid /authenticate",
        "redirect_uri": REDIRECT_URI,
    }
    authorization_url = "https://orcid.org/oauth/authorize?" + urllib.parse.urlencode(auth_params)

    if st.button("🔑 Login with ORCID"):
        # Force top-level navigation (avoids iframe “refused to connect”)
        st.markdown(
            f"""
            <script>
            if (window.top) {{
                window.top.location.href = "{authorization_url}";
            }} else {{
                window.location.href = "{authorization_url}";
            }}
            </script>
            """,
            unsafe_allow_html=True,
        )

# 3) Sidebar status
if st.session_state.is_authenticated:
    st.sidebar.success("✅ You are logged in with ORCID")
    if st.session_state.orcid_user_info:
        u = st.session_state.orcid_user_info
        st.write(
            f"**Name:** {u.get('name','—')}  \n"
            f"**ORCID iD:** {u.get('sub','—')}"
        )
else:
    st.sidebar.warning("🔒 You are not logged in to ORCID")
