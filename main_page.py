import streamlit as st

st.set_page_config(page_title='藥局盤點系統', layout='wide')

pages = [
	st.Page('inventory_page.py', title='盤點'),
	st.Page('need_inventory_record.py', title='盤點結果'),
	st.Page('unit_amount_and_site_edit.py', title='櫃位及排裝設定'),
	st.Page('user_management.py', title='使用者管理'),
 	#st.Page('upload_from_his.py', title='上傳品項表'),
	st.Page('upload_need_inventory.py', title='上傳盤點清單'),
	#st.Page('upload_site.py', title='上傳櫃位清單'),
	#st.Page('upload_unit.py', title='上傳排裝資料'),
]

selected_page = st.navigation(pages, position='sidebar')
selected_page.run()
