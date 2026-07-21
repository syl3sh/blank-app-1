import streamlit as st
import numpy as np
import pandas as pd
df = pd.read_excel('ATE_Tracking_Record_10726.xlsx')
st.write(df.head())
time.sleep(30)
st.rerun()

