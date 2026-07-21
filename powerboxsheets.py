import streamlit as st
import numpy as np
import pandas as pd
df = pd.read_excel('data/ATE_Tracking_Record_10726.xlsx')
st.dataframe(df.fillna(""))
edited_df = st.data_editor(df, num_rows = "dynamic")
if st.button("Save changes"):
    edited_df.to_excel("data/mydata.xlsx", index=False)
    st.success("Saved!")
if st.buttons("Save Changes"):
  edited_df.to_excel("data/ATE_Tracking_Record_10726.xlsx", index = False)
  st.success("Saved")
