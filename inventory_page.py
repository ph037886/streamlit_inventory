import streamlit as st
import sqlite_control
import time
import pandas as pd
import cv2
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import threading

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
        result_container.error('請選擇櫃位。')
        return
    
    conn = sqlite_control.postgres_link()
    cursor = conn.cursor()
    for input_amount, unit in result_list:
        if input_amount > 0:
            cursor.execute(
                "INSERT INTO INVENTORY_RECORD (IR_USER, IR_DIACODE, IR_SITE, IR_UNIT, IR_RECORD, IR_EVENT_NO) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, diacode, site, unit, input_amount, inventory_event_no)
            )
    
            conn.commit()
            conn.close()
            with st.spinner("Wait for it...", show_time=True):
                time.sleep(1)
            sum_amount = count_sum_amount(result_list, df_unit_amount)
            temporary_message = st.empty()
            temporary_message.write(f'排裝後總量：{sum_amount}')
            time.sleep(3)
            temporary_message.empty()
        else:
            temporary_message = st.empty()
            temporary_message.error(f'盤點數目為0不紀錄')
            time.sleep(3)
            temporary_message.empty()



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

#QR code相機掃描後，會將醫令碼帶入keyword欄位，並自動帶入櫃位欄位，若櫃位有多個，則預設選擇第一個櫃位。
if "camera_started" not in st.session_state:
    st.session_state.camera_started = False

if "qr_scan_result" not in st.session_state:
    st.session_state.qr_scan_result = ""

if "qr_scan_applied" not in st.session_state:
    st.session_state.qr_scan_applied = False

if "_qr_live_state" not in st.session_state:
    st.session_state._qr_live_state = {
        "decoded_text": None,
        "frame_count": 0,
        "lock": threading.Lock(),
    }


def close_camera():
    st.session_state.camera_started = False
    with st.session_state._qr_live_state["lock"]:
        st.session_state._qr_live_state["decoded_text"] = None
        st.session_state._qr_live_state["frame_count"] = 0


def apply_qr_result(decoded_text):
    qr_result_split = decoded_text.split('id=')
    if len(qr_result_split) == 2:
        diacode = qr_result_split[1].strip()
        st.session_state.qr_scan_result = decoded_text
        st.session_state.qr_scan_applied = True
        st.session_state['keyword_selectbox'] = diacode
        close_camera()
    else:
        st.session_state.qr_scan_result = ""
        st.session_state.qr_scan_applied = False
        close_camera()
        st.error("QR code格式錯誤，請重新掃描。")


if not st.session_state.camera_started:
    if st.button("啟動相機，掃瞄藥盒QR code"):
        st.session_state.qr_scan_applied = False
        with st.session_state._qr_live_state["lock"]:
            st.session_state._qr_live_state["decoded_text"] = None
            st.session_state._qr_live_state["frame_count"] = 0
        st.session_state.camera_started = True
        st.rerun()
else:
    st.button(
        "關閉相機",
        on_click=close_camera,
    )

if st.session_state.camera_started:
    qr_live_state = st.session_state._qr_live_state

    def qr_video_frame_callback(frame):
        with qr_live_state["lock"]:
            if qr_live_state["decoded_text"] is not None:
                return frame
            qr_live_state["frame_count"] += 1
            if qr_live_state["frame_count"] % 5 != 0:
                return frame

        image = frame.to_ndarray(format="bgr24")
        detector = cv2.QRCodeDetector()
        decoded_text, points, _ = detector.detectAndDecode(image)

        if decoded_text:
            with qr_live_state["lock"]:
                if qr_live_state["decoded_text"] is None:
                    qr_live_state["decoded_text"] = decoded_text

        return frame

    webrtc_streamer(
        key="inventory_qr_live",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration={
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        },
        media_stream_constraints={
            "video": {"facingMode": "environment"},
            "audio": False,
        },
        video_frame_callback=qr_video_frame_callback,
        async_processing=True,
    )


@st.fragment(run_every=1.0)
def poll_live_qr_result():
    if not st.session_state.camera_started:
        return

    with st.session_state._qr_live_state["lock"]:
        decoded_text = st.session_state._qr_live_state["decoded_text"]

    if decoded_text:
        apply_qr_result(decoded_text)
        st.rerun()


poll_live_qr_result()

if st.session_state.qr_scan_applied:
    st.success("掃描成功，已套用醫令碼及進入盤點品項。")

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

    with result_container.form(key=f"inventory_form_{diacode}", clear_on_submit=False):
        if len(site_list) == 1:
            site = st.pills('請選擇櫃位：', site_list, default=default_site)
        else:
            site=st.pills(
                '請選擇櫃位：', site_list, default=default_site)
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

        st.form_submit_button(
            '送出',
            on_click=record_inventory_amounts,
            args=(
                diacode,
                site,
                result_list,
                df_unit_amount,
                user_id,
                inventory_event_no,
            ),
        )

record_container=st.container()
