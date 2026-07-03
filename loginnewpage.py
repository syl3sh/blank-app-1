import streamlit as st
import requests
import time
import datetime
import pytz
from pathlib import Path
import streamlit_authenticator as stauth


sgt = pytz.timezone("Asia/Singapore")

config = {
    "credentials": {
        "usernames": {
            "admin": {
                "email": st.secrets["credentials"]["usernames"]["admin"]["email"],
                "first_name": st.secrets["credentials"]["usernames"]["admin"]["first_name"],
                "last_name": st.secrets["credentials"]["usernames"]["admin"]["last_name"],
                "username": st.secrets["credentials"]["usernames"]["admin"]["username"],
                "password": st.secrets["credentials"]["usernames"]["admin"]["password"],
                "logged_in": False,
                "failed_login_attempts": 0
            }
        }
    },
    "cookie": {
        "name": st.secrets["cookie"]["name"],
        "key": st.secrets["cookie"]["key"],
        "expiry_days": st.secrets["cookie"]["expiry_days"]
    }
}
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)
st.session_state['authenticator'] = authenticator

authenticator.login()

if st.session_state.get('authentication_status') is False:
    st.error("Username/Password is incorrect")
elif st.session_state.get('authentication_status') is None:
    st.warning("Please enter username and password")
elif st.session_state.get('authentication_status'):
    st.success('Welcome')
    if st.button("Go to Dashboard", use_container_width=True):
        st.switch_page("pages/streamlit_app1.py")
    
    
