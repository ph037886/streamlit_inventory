import streamlit as st
import sqlite_control

st.header('盤點結果')

df_record=sqlite_control.get_need_inventory_record()

st.dataframe(df_record)
