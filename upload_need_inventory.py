from login import require_login, require_role, logout_button

user = require_login()
user = require_role(["admin", "primary_edit"])
logout_button()

import streamlit as st
import pandas as pd
import chardet
import sqlite_control

def mapping_not_in_from_his(df):
    # 取得 HIS 資料庫中的品項編號清單
    his_item_numbers = sqlite_control.get_his_item_numbers()

    # 找出 df 中不在 HIS 資料庫中的品項編號
    not_in_his = df[~df['NI_ITEM'].isin(his_item_numbers)]

    return not_in_his

st.title("上傳本次盤點品項表")

inventory_event_name=st.text_input("請輸入本次盤點事件名稱", value="", key="inventory_event_name", help="建議輸入日期+事件，如2026/11/11盤點")

inventory_event_datetime=st.date_input("請選擇本次盤點事件日期", value=None, key="inventory_event_datetime")
    
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
        if not inventory_event_name:
            st.error("請輸入本次盤點事件名稱")
        if not inventory_event_datetime:
            st.error("請選擇本次盤點事件日期")
        if inventory_event_name and inventory_event_datetime:
            is_success, message = sqlite_control.add_new_event(inventory_event_name, inventory_event_datetime)
            if is_success:
                st.success(message)
                event_no = sqlite_control.get_inventory_event_by_name(inventory_event_name)["IE_NO"].values[0]
                df["NI_EVENT"] = event_no
                is_success, message = sqlite_control.upload_from_his_or_inventory(df, "need_inventory", True)
                if is_success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.error(message)

        