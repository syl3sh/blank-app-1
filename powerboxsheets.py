import streamlit as st
import numpy as np
import pandas as pd
df = pd.read_excel('data/ATE_Tracking_Record_10726.xlsx')
st.write(df)
df = df.fillna("") 
df = df.dropna(axis=0, how="all")
df = df.dropna(axis=1, how="all")
df = df.dropna(axis=3, how="all")
