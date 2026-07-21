import streamlit as st
import numpy as np
import pandas as pd
from io import BytesIO
df = pd.read_excel('data/ATE_Tracking_Record_10726.xlsx')

edited_df = st.data_editor(df, num_rows = "dynamic")

if st.button("Save Changes on Dashboard"):
  edited_df.to_excel("data/ATE_Tracking_Record_10726.xlsx", index = False)
  st.success("Saved")

def convert_df_to_excel(df):
  output = BytesIO()
  with pd.ExcelWriter(output, engine = "openpyxl") as writer:
    df.to_excel(writer, index = False, sheet_name = "sheet1")
    return output.getvalue()

excel_data = convert_df_to_excel(edited_df)

st.download_button(
    label="Save copy as Excel",
    data=excel_data,
    file_name="ATE Tracking Record 10726_edited.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
  
  
  
