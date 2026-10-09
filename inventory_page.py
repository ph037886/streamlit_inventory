import streamlit as st
import sqlite_control
import time

def print_result(something):
    print(something)

def reset_inventory_amounts(): #在keyword重新輸入時，歸零數量欄位
    for key in st.session_state:
        if key.startswith('input_amount_'):
            st.session_state[key] = 0

def count_sum_amount(result_list, df_unit_amount):
    sum_amount = 0
    for input_amount, unit in result_list:
        if unit=='散裝':
            sum_amount+=input_amount
        else:
            unit_amount=df_unit_amount[df_unit_amount['UA_UNIT']==unit]['UA_AMOUNT'].values[0]
            sum_amount+=input_amount*unit_amount
    return sum_amount

def record_inventory_amounts(diacode, site, result_list, user_id):
    conn = sqlite_control.sqlite_link()
    cursor = conn.cursor()
    
    for input_amount, unit in result_list:
        if input_amount > 0:
            cursor.execute(
                "INSERT INTO INVENTORY_RECORD (IR_USER, IR_DIACODE, IR_SITE, IR_UNIT, IR_RECORD) VALUES (?, ?, ?, ?, ?)",
                (user_id, diacode, site, unit, input_amount)
            )
    
    conn.commit()
    conn.close()
    with st.spinner("Wait for it...", show_time=True):
        time.sleep(2)

def get_need_inventory_from_keyword(keyword):
    need_inventory=sqlite_control.get_his_info_use_diacode(keyword)
    if need_inventory.empty==False:
        return need_inventory
    else:
        need_inventory=sqlite_control.get_his_info_use_engname(keyword)
        return need_inventory


#以下開始streamlit網頁介面


st.header('盤點頁面')

keyword = st.selectbox(
    '輸入醫令碼或英文商品名：',
    sqlite_control.auto_complete_diacode_and_engname(),
    key='keyword',
    on_change=reset_inventory_amounts,
    accept_new_options=False,
)

user_id='test'

need_inventory=get_need_inventory_from_keyword(keyword)

if need_inventory.empty==True:
    result_container=st.container()
    result_container.write('不在這次盤點品項中。')
else:
    result_container=st.container()
    #叫出基本資料
    main_info=need_inventory.iloc[0]
    result_container.write(main_info['DA_EGNAME'])
    result_container.write(main_info['DA_CHNAME'])
    result_container.write(main_info['DA_CNAME'])
    diacode=main_info['DA_DIACODE']
    
    #叫出櫃位
    df_site=sqlite_control.get_realworld_site(diacode)
    site_list=df_site['RS_SITE'].tolist()
    site=result_container.pills(
        '請選擇櫃位：', site_list)
    
    #叫出排裝設定
    df_unit_amount=sqlite_control.get_unit_amount(diacode)
    unit_list=df_unit_amount['UA_UNIT'].tolist()
    result_list=[]
    i=-1
    while i<len(unit_list):
        if i==-1:
            unit='散裝'
        else:
            unit=unit_list[i]
        i+=1
        input_amount = result_container.number_input(
            f'請輸入{unit}數量：',
            min_value=0,
            step=1,
            key=f'input_amount_{diacode}_{unit}', #增加key，讓前面的reset_inventory_amounts()可以歸零
        )
        result_list.append((input_amount, unit))
    sum_amount = count_sum_amount(result_list, df_unit_amount)
    result_container.subheader(f'總量：{sum_amount}')
    result_container.button('送出', on_click=record_inventory_amounts, args=(diacode, site, result_list, user_id,))
    
record_container=st.container()
