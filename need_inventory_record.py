from login import require_login, require_role, logout_button

user = require_login()
user = require_role(["admin", "primary_edit"])
logout_button()

import streamlit as st
import sqlite_control
import pandas as pd

@st.dialog(title="關閉盤點事件")
def close_inventory_event(event_name):
    def close_event(event_name):
        is_success, message = sqlite_control.change_inventory_event_end_time(event_name, pd.Timestamp.now())
        if is_success:
            return f"盤點事件 '{event_name}' 已關閉。"
        else:
            return f"關閉盤點事件 '{event_name}' 失敗：{message}"
    st.write(f"確定要關閉盤點事件： '{event_name}' 嗎？")
    if st.button("確認"):
        result = close_event(event_name)
        st.write(result)
    if st.button("取消"):
        st.rerun()
st.header('盤點結果')

inventory_event= sqlite_control.get_all_inventory_event()
event_list = inventory_event['IE_NAME'].tolist()
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

summary_title, close_event= st.columns([1, 1])

summary_title.subheader('盤點概要')

event_end_time = inventory_event.loc[inventory_event['IE_NAME'] == selected_event, 'IE_END'].values[0]
if pd.isna(event_end_time):
    close_event.button('關閉盤點事件', on_click=close_inventory_event, args=(selected_event,))
else:
    event_end_time = pd.to_datetime(event_end_time).strftime('%Y-%m-%d %H:%M:%S')
    close_event.write(f"盤點事件已於 {event_end_time} 關閉。")

st.write('顯示總盤點狀況')
completed_count = len(df_record.dropna(subset=['總量']))
filtered_count = len(df_record)
completed_percentage = (
    completed_count / filtered_count
    if filtered_count > 0
    else 0
)
#st.write(f'已盤點櫃位數：{completed_count} 'f'({completed_percentage:.1%})')
#st.write(f'需盤點櫃位數：{filtered_count}')

st.metric(label="總盤點狀況", value=f'{completed_count}/{filtered_count}', delta=f'{completed_percentage:.1%}', delta_color="blue", delta_arrow="off", border=True, width='content')
worktop_list=df_record['檯面'].dropna().drop_duplicates().sort_values().tolist()
cols = st.columns(len(worktop_list))
i=0
for worktop in worktop_list:
    worktop_df = df_record[df_record['檯面'] == worktop]
    worktop_completed_count = len(worktop_df.dropna(subset=['總量']))
    worktop_filtered_count = len(worktop_df)
    worktop_completed_percentage = (
        worktop_completed_count / worktop_filtered_count
        if worktop_filtered_count > 0
        else 0
    )
    if worktop_completed_percentage == 1:
        percentage_color = "green"
    else:
        percentage_color = "blue"
    with cols[i]:
        st.metric(label=f"{worktop}盤點狀況", value=f'{worktop_completed_count}/{worktop_filtered_count}', delta=f'{worktop_completed_percentage:.1%}', delta_color=percentage_color, delta_arrow="off", border=True)
    i += 1
    if i >=5:
        i = 0


st.dataframe(filtered_df_record)
