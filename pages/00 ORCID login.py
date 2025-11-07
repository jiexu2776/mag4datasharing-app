import streamlit as st
import urllib.parse
import requests
from requests.auth import HTTPBasicAuth

CLIENT_ID = st.secrets.get("Orcid_ID", "")
CLIENT_SECRET = st.secrets.get("Orcid_Secret", "")
REDIRECT_URI = "https://mag4datasharing-app.streamlit.app/ORCID_login"

def exchange_code_for_token(code: str):
    r = requests.post(
        "https://orcid.org/oauth/token",
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI},
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        timeout=20
    )
    return r.json().get("access_token") if r.status_code == 200 else None

def get_userinfo(access_token: str):
    r = requests.get(
        "https://orcid.org/oauth/userinfo",
        headers={"Authorization": f"Bearer {access_token}", "Accept":"application/json"},
        timeout=20
    )
    return r.json() if r.status_code == 200 else None

# Session init
for k, v in {"is_authenticated": False, "orcid_token": None, "userinfo": None}.items():
    st.session_state.setdefault(k, v)

st.title("ORCID Authentication")

# Handle return from ORCID
params = getattr(st, "query_params", {}) or st.experimental_get_query_params()
code = params.get("code")
if isinstance(code, list):
    code = code[0]
if code and not st.session_state.is_authenticated:
    with st.spinner("Completing sign-in…"):
        token = exchange_code_for_token(code)
        if token:
            st.session_state.orcid_token = token
            st.session_state.userinfo = get_userinfo(token)
            st.session_state.is_authenticated = True
            st.success("✅ Logged in with ORCID.")
        else:
            st.error("❌ Token exchange failed (check client ID/secret and redirect URI).")

if not st.session_state.is_authenticated:
    q = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid /authenticate",
        "redirect_uri": REDIRECT_URI,
    }
    authorization_url = "https://orcid.org/oauth/authorize?" + urllib.parse.urlencode(q)
    st.link_button("🔑 Login with ORCID", authorization_url)  # ← simplest and most reliable
else:
    st.sidebar.success("Logged in")
    u = st.session_state.userinfo or {}
    st.write(f"**Name:** {u.get('name','—')}  \n**ORCID iD:** {u.get('sub','—')}")
