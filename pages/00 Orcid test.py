import streamlit as st
from requests.auth import HTTPBasicAuth
import requests


if not st.user.is_logged_in:
    st.header("Log in:")
    if st.button("Log in with ORCID"):
        st.login("orcid")
    if st.button("Log in with GOOGLE"):
        st.login("google")
    st.stop()
else:
    if st.button("Log out"):
        st.logout()

st.write(f"Hello, {st.user.name}!")

st.write("Query params:", st.experimental_get_query_params())
st.write("User:", getattr(st.user, "is_logged_in", None))
st.write("Secrets auth section:", st.secrets.get("auth"))

st.json(st.user)

st.write("session station:", st.session_state)


# ------ Sidebar
if st.user.is_logged_in:
    st.sidebar.success("You are logged in with ORCID")
else:
    st.sidebar.error('You are not loged in to ORCID')


