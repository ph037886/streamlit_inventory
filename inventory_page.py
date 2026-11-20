import streamlit as st
import sqlite_control
import pandas as pd

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

def record_inventory_amounts(diacode, site, result_list, df_unit_amount, user_id, inventory_event_no):
    if site==None:
        st.error('請選擇櫃位。')
        return

    if all(input_amount == 0 for input_amount, _ in result_list):
        st.error('盤點數目為0不紀錄')
        return

    save_result = sqlite_control.save_inventory_amounts(
        diacode,
        site,
        result_list,
        user_id,
        inventory_event_no,
    )
    if save_result == "unchanged":
        st.info('盤點資料相同，不需變更。')
        return

    sum_amount = count_sum_amount(result_list, df_unit_amount)
    st.success(f'盤點資料已儲存，排裝後總量：{sum_amount}')



#以下開始streamlit網頁介面

st.header('盤點頁面')

#顯示盤點事件，並留下尚未停止，且開始日期大於今天的事件，讓使用者選擇，預設選擇第一個事件
inventory_event_df=sqlite_control.get_all_inventory_event()
#統一時區
inventory_event_df["IE_START"] = pd.to_datetime(
    inventory_event_df["IE_START"],
    utc=True,
)

now = pd.Timestamp.now(tz="UTC")

inventory_event_df = inventory_event_df[
    inventory_event_df["IE_END"].isna()
    & (inventory_event_df["IE_START"] <= now)
]
inventory_event_list=inventory_event_df['IE_NAME'].tolist()
if len(inventory_event_list)==1:
    disabled_type=True
else:
    disabled_type=False
inventory_event_name=st.selectbox('請選擇盤點事件：', inventory_event_list, index=0, disabled=disabled_type)
inventory_event_no = sqlite_control.get_inventory_event_by_name(inventory_event_name)["IE_NO"].values[0]
diacode_and_engname_lsit=sqlite_control.auto_complete_diacode_and_engname_for_need_inventory(inventory_event_no)

#相機功能先關掉，要還原得時候放這裡

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
if keyword_index==0 and need_inventory.empty==True:
    pass
elif need_inventory.empty==True:
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

    #叫出排裝設定
    df_unit_amount=sqlite_control.get_unit_amount(diacode)
    unit_list=df_unit_amount['UA_UNIT'].tolist()

    site = result_container.pills(
        '請選擇櫃位：',
        site_list,
        default=default_site,
    )

    existing_records = sqlite_control.find_existing_inventory_record(
        diacode,
        site,
        inventory_event_no,
    )
    prefill_key = f'{inventory_event_no}:{diacode}:{site}'
    if st.session_state.get('inventory_prefill_key') != prefill_key:
        existing_amounts = (
            existing_records
            .drop_duplicates('IR_UNIT')
            .set_index('IR_UNIT')['IR_RECORD']
            .to_dict()
        )
        st.session_state['inventory_prefill_key'] = prefill_key
        for unit in ['散裝'] + unit_list:
            st.session_state[f'input_amount_{diacode}_{unit}'] = int(
                existing_amounts.get(unit, 0)
            )

    if not existing_records.empty:
        st.error('已有盤點資料')

    with result_container.form(key=f"inventory_form_{diacode}", clear_on_submit=False):
        result_list = []
        i = -1

        while i < len(unit_list):
            if i == -1:
                unit = '散裝'
            else:
                unit = unit_list[i]

            i += 1

            input_amount = st.number_input(
                f'請輸入{unit}數量：',
                min_value=0,
                step=1,
                key=f'input_amount_{diacode}_{unit}',
            )
            result_list.append((input_amount, unit))

        submitted = st.form_submit_button('送出')

    if submitted:
        record_inventory_amounts(
            diacode,
            site,
            result_list,
            df_unit_amount,
            user_id,
            inventory_event_no,
        )

record_container=st.container()
