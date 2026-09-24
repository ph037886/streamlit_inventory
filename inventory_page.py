import streamlit as st
import sqlite_control

keyword=st.text_input('輸入關鍵字：')

result_container=st.container()

need_inventory=sqlite_control.get_his_info(keyword)

if need_inventory.empty==True:
    result_container.write('不在這次盤點品項中。')
else:
    #result_container.dataframe(need_inventory)
    main_info=need_inventory.iloc[0]
    result_container.write(main_info['DA_EGNAME'])
    result_container.write(main_info['DA_CHNAME'])
    result_container.write(main_info['DA_CNAME'])