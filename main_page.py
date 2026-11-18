import streamlit as st

st.set_page_config(page_title='藥局盤點系統', layout='wide')

pages = [
	st.Page('inventory_page.py', title='盤點'),
	st.Page('result_page.py', title='盤點結果'),
	st.Page('unit_amount_and_site_edit.py', title='櫃位及排裝設定'),
	#st.Page('upload_data.py', title='上傳盤點清單'),
]

selected_page = st.navigation(pages, position='sidebar')
selected_page.run()