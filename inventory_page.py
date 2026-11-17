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
    if site==None:
        result_container.error('請選擇櫃位。')
        return
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




#以下開始streamlit網頁介面

st.header('盤點頁面')

diacode_and_engname_lsit=sqlite_control.auto_complete_diacode_and_engname()



#url參數：醫令碼
if 'diacode' in st.query_params and st.query_params['diacode'] is not None:
    if st.query_params['diacode'].upper() in diacode_and_engname_lsit:
        keyword_index=diacode_and_engname_lsit.index(st.query_params['diacode'].upper())
    else:
        keyword_index=0
else:
    keyword_index=0
    
keyword = st.selectbox(
    '輸入醫令碼或英文商品名：',
    diacode_and_engname_lsit,
    key='keyword_selectbox',
    on_change=reset_inventory_amounts,
    accept_new_options=False,
    index=keyword_index,
)

user_id='test'

need_inventory=sqlite_control.get_need_inventory_from_keyword(keyword)

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
    if df_site.empty==True:
        result_container.write('此醫令碼尚未設定櫃位，請先至「盤點設定」頁面設定櫃位，或先使用HIS櫃位。')
        site_list=need_inventory['DA_SITE'].tolist()
    else:
        site_list=df_site['RS_SITE'].tolist()
    
    #url參數：櫃位
    if 'site' in st.query_params and st.query_params['site'] is not None:
        if st.query_params['site'] in site_list:
            site_index=site_list.index(st.query_params['site'])
            default_site=site_list[site_index]
        else:
            default_site=site_list[0]
    else:
        default_site=site_list[0]
    
    if len(site_list) == 1:
        site = result_container.pills('請選擇櫃位：', site_list, default=default_site)
    else:
        site=result_container.pills(
            '請選擇櫃位：', site_list, default=default_site)
    
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
