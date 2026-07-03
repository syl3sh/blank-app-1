import streamlit as st
import pandas as pd
import io
import re
import pickle
from PIL import Image
import requests
import time
import subprocess
import datetime
import wakeonlan
import pytz
from pathlib import Path
import streamlit_authenticator as stauth


sgt = pytz.timezone("Asia/Singapore")

config = {
    "credentials": {
        "usernames": {
            "admin": {
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
    authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)
    
