from login import require_login, require_role, logout_button

user = require_login()
user = require_role(["admin", "primary_edit"])
logout_button()

import streamlit as st
import sqlite_control

st.header('盤點結果')

event_list = sqlite_control.get_all_inventory_event()['IE_NAME'].tolist()
selected_event = st.selectbox('請選擇盤點事件：', event_list, index=0)

df_record=sqlite_control.get_need_inventory_record(selected_event)


with st.expander('篩選盤點結果', expanded=True):
    
    only_none_amount = st.toggle('只顯示總量為空的項目')
    #讓篩選器左右排列比較不影響版面
    filter_col1, filter_col2 = st.columns([1, 1])

    real_site_options = (
        df_record['真實櫃位']
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    selected_real_sites = filter_col1.multiselect(
        '真實櫃位',
        options=real_site_options,
    )

    worktop_options = (
        df_record['檯面']
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    selected_worktops = filter_col2.multiselect(
        '檯面',
        options=worktop_options,
    )

filtered_df_record = df_record.copy()

if only_none_amount:
    filtered_df_record = filtered_df_record[
        filtered_df_record['總量'].isna()
    ]

if selected_real_sites:
    filtered_df_record = filtered_df_record[
        filtered_df_record['真實櫃位'].isin(selected_real_sites)
    ]

if selected_worktops:
    filtered_df_record = filtered_df_record[
        filtered_df_record['檯面'].isin(selected_worktops)
    ]

st.subheader('盤點概要')
completed_count = len(filtered_df_record.dropna(subset=['總量']))
filtered_count = len(filtered_df_record)
completed_percentage = (
    completed_count / filtered_count
    if filtered_count > 0
    else 0
)
#st.write(f'已盤點櫃位數：{completed_count} 'f'({completed_percentage:.1%})')
#st.write(f'需盤點櫃位數：{filtered_count}')

st.metric(label="總盤點狀況", value=f'{completed_count}/{filtered_count}', delta=f'{completed_percentage:.1%}', delta_color="blue", delta_arrow="off", border=True)

st.dataframe(filtered_df_record)
