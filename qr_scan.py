先關掉相機功能
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
