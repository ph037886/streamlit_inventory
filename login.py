import streamlit as st
import streamlit_authenticator as stauth

from sqlite_control import get_credentials, get_active_user


def create_authenticator():
    if "_authenticator" not in st.session_state:
        credentials = get_credentials()

        st.session_state["_authenticator"] = stauth.Authenticate(
            credentials,
            cookie_name=st.secrets["login"]["cookie_name"],
            cookie_key=st.secrets["login"]["cookie_key"],
            cookie_expiry_days=st.secrets["login"]["cookie_expiry_days"],
            auto_hash=False,
        )

    return st.session_state["_authenticator"]

def get_authenticator():
    if "_authenticator" not in st.session_state:
        st.session_state["_authenticator"] = (
            create_authenticator()
        )

    return st.session_state["_authenticator"]

def require_login():
    authenticator = create_authenticator()

    if st.session_state.get("authentication_status") is not True:
        st.title("系統登入")

        authenticator.login(
            location="main",
            max_login_attempts=5,
            fields={
                "Form name": "使用者登入",
                "Username": "使用者帳號",
                "Password": "登入密碼",
                "Login": "登入系統",
            },
        )

    status = st.session_state.get("authentication_status")

    if status is False:
        st.error("帳號或密碼錯誤")
        st.stop()

    if status is not True:
        st.stop()

    username = st.session_state.get("username")
    user = get_active_user(username)
    

    if user is None or user["is_active"] is not True:
        st.error("帳號不存在或已停用")
        st.stop()

    st.session_state["roles"] = user["roles"]

    return user


def require_role(allowed_roles):
    user = require_login()

    if not set(user["roles"]).intersection(allowed_roles):
        st.error("你沒有使用此頁面的權限")
        st.stop()

    return user


def logout_button():
    if st.session_state.get("authentication_status") is not True:
        return

    authenticator = create_authenticator()

    authenticator.logout(
        button_name="登出系統",
        location="sidebar",
    )