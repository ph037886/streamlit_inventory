import streamlit as st
import sqlite_control

st.header('盤點結果')

df_record=sqlite_control.get_need_inventory_record()

st.subheader('盤點概要')
st.write(f'已盤點櫃位數：{len(df_record.dropna(subset=['總量']))} ({(len(df_record.dropna(subset=['總量']))/len(df_record)):.1%})')
st.write(f'需盤點櫃位數：{len(df_record)}')

st.dataframe(df_record)
