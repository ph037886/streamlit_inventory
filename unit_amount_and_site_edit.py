import streamlit as st
import sqlite_control

st.header('編輯排裝資料與櫃位資料')

keyword = st.selectbox(
    '輸入醫令碼或英文商品名：',
    sqlite_control.auto_complete_diacode_and_engname(),
    key='keyword',
    accept_new_options=False,
    index=0
)

need_inventory=sqlite_control.get_need_inventory_from_keyword(keyword)


if need_inventory.empty==True:
    result_container=st.container()
    result_container.write('不在這次盤點品項中。')
else:
    result_container=st.container()
    #叫出基本資料
    main_info=need_inventory.iloc[0]
    result_container.write(main_info['DA_EGNAME'])
    diacode=main_info['DA_DIACODE']
    
    #櫃位編輯
    df_site=sqlite_control.get_realworld_site(diacode)
    st.data_editor(df_site, 
                   num_rows="dynamic", 
                   use_container_width=True, 
                   key=f'df_site_{diacode}',)
    
    #排裝編輯