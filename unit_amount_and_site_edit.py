import streamlit as st
import sqlite_control
import datetime

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
    result_container.write('櫃位編輯')
    df_site=sqlite_control.get_realworld_site(diacode)
    df_site=df_site[['RS_SITE','RS_WORKTOP']]
    df_site=df_site.rename(columns={'RS_SITE':'櫃位','RS_WORKTOP':'工作區域'})
    edited_site = result_container.data_editor(df_site,
                   num_rows="dynamic", 
                   width='stretch', 
                   key=f'df_site_{diacode}',)
    
    #排裝編輯
    result_container.write('排裝編輯')
    df_unit_amount=sqlite_control.get_unit_amount(diacode)
    df_unit_amount=df_unit_amount[['UA_UNIT','UA_AMOUNT']]
    df_unit_amount=df_unit_amount.rename(columns={'UA_UNIT':'單位','UA_AMOUNT':'排裝數量'})
    edited_unit_amount = result_container.data_editor(df_unit_amount,
                   num_rows="dynamic", 
                   width='stretch', 
                   key=f'df_unit_amount_{diacode}',)

    save_button, saved_at_container = result_container.columns([1, 3])
    if save_button.button('存檔', key=f'save_{diacode}'):
        try:
            edited_site = edited_site.rename(columns={'櫃位':'RS_SITE','工作區域':'RS_WORKTOP'})
            edited_site['RS_DIACODE'] = diacode
            edited_unit_amount = edited_unit_amount.rename(columns={'單位':'UA_UNIT','排裝數量':'UA_AMOUNT'})
            edited_unit_amount['UA_DIACODE'] = diacode
            sqlite_control.save_realworld_site_and_unit_amount(
                diacode, edited_site, edited_unit_amount
            )
            st.session_state[f'saved_at_{diacode}'] = datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'
            )
            result_container.success('存檔成功')
        except ValueError as error:
            result_container.error(str(error))

    saved_at = st.session_state.get(f'saved_at_{diacode}')
    if saved_at:
        saved_at_container.write(f'最後存檔時間：{saved_at}')
    