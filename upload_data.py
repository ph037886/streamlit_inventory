import streamlit as st
import pandas as pd
import chardet

st.title("上傳盤點清單")

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
        # 將資料寫入 SQLite 資料庫
        import sqlite3
        conn = sqlite3.connect("inventory.db")
        try:
            if retain_old_data:
                # 保留舊資料，直接將新資料附加到現有資料後面
                df.to_sql("from_his", conn, if_exists="append", index=False)
            else:
                # 不保留舊資料，先刪除現有資料，再將新資料寫入
                df.to_sql("from_his", conn, if_exists="replace", index=False)
            conn.close()
            st.success("資料已上傳成功！")
        except Exception as e:
            st.error(f"資料上傳失敗：{e}")
        