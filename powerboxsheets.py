import streamlit as st
import numpy as np
import pandas as pd
df = pd.read_excel('data/ATE_Tracking_Record_10726.xlsx')

edited_df = st.data_editor(df, num_rows = "dynamic")

if st.button("Save Changes"):
  edited_df.to_excel("data/ATE_Tracking_Record_10726.xlsx", index = False)
  st.dataframe(edited_df.fillna(""))
  st.success("Saved")
