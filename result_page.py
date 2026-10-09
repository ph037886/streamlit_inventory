import streamlit as st
import sqlite_control

st.header('盤點結果')

df_record=sqlite_control.get_all_inventory_record()

diacode_filter=st.multiselect('品項篩選', 
               sqlite_control.auto_complete_diacode_and_engname(),
               accept_new_options=False,)

if diacode_filter:
    df_record=df_record[(df_record['醫令碼'].isin(diacode_filter)) | (df_record['商品名'].isin(diacode_filter))]

st.dataframe(df_record)

if len(df_record)<5:
    st.write('盤點概述 (少於5筆才顯示)：')
    item_list=df_record['醫令碼'].drop_duplicates().tolist()
    for i in item_list:
        item_record=df_record[df_record['醫令碼']==i]
        sum_volume=item_record['各排裝總量'].sum()
        st.write(f'{i}，總量：{sum_volume}')