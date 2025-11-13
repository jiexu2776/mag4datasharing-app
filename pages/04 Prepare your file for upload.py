import streamlit as st

st.title('How to prepare your dataset before upload')

st.write('Needs to be a csv file')

if st.user.is_logged_in:
    st.sidebar.success("You are logged in with ORCID")
else:
    st.sidebar.error('You are not loged in to ORCID')
if st.sidebar.button("Log out"):
    st.logout()

if st.sidebar.button("Log out"):
    st.logout()

