from login import require_login, require_role, logout_button

user = require_login()
user = require_role(["admin", "primary_edit"])
logout_button()

import streamlit as st
import pandas as pd
import chardet
import sqlite_control

st.title("上傳資料")

upload_option_dict={
    "從 HIS 匯入": "from_his",
    "櫃位資料匯入": "realworld_site",
    "排裝資料匯入": "unit_amount",}


upload_option = st.selectbox("選擇匯入項目", options=list(upload_option_dict.keys()))

retain_old_data = st.toggle("保留舊資料", value=False, key="retain_old_data")

if retain_old_data:
    st.write("保留舊資料，匯入資料不可與現有資料重複。")
    
uploaded_file = st.file_uploader(
    "Upload data", accept_multiple_files=False, type="csv"
)
if uploaded_file is not None:
    #先做編碼檢測，避免Big5錯誤
    raw_data = uploaded_file.read()
    encoding_type = chardet.detect(raw_data)["encoding"]

    # 將檔案指標重設回開頭（避免後續讀取不到資料）
    uploaded_file.seek(0)

    df = pd.read_csv(uploaded_file, encoding=encoding_type)
    st.write(df)
    if st.button("確認匯入"):
        is_success, message = sqlite_control.upload_from_his_or_inventory(df, "from_his", retain_old_data)
        if is_success:
            st.success(message)
        else:
            st.error(message)
        