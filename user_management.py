import streamlit as st

from login import require_role, logout_button
import sqlite_control

current_user = require_role(["admin"])
logout_button()

st.header("使用者管理")

roles = sqlite_control.get_auth_roles()
role_name_by_id = {role["id"]: role["role_name"] for role in roles}
role_code_by_id = {role["id"]: role["role_code"] for role in roles}

tab_add, tab_manage, tab_roles = st.tabs(["新增使用者", "使用者與權限", "角色管理"])

with tab_add:
    with st.form("create_user", clear_on_submit=True):
        col1, col2 = st.columns(2)
        username = col1.text_input("帳號")
        display_name = col2.text_input("姓名")
        email = col1.text_input("Email")
        password = col2.text_input("初始密碼", type="password")
        confirm_password = col1.text_input("確認密碼", type="password")
        selected_role_ids = [
            role["id"]
            for role in roles
            if col2.checkbox(
                f"{role['role_name']} ({role['role_code']})",
                key=f"new_role_{role['id']}",
            )
        ]

        if st.form_submit_button("新增使用者", type="primary"):
            if password != confirm_password:
                st.error("兩次密碼不一致")
            elif len(password) < 8:
                st.error("密碼至少需要 8 個字元")
            else:
                success, message = sqlite_control.create_auth_user(
                    username,
                    display_name,
                    email,
                    password,
                    selected_role_ids,
                )
                if success:
                    st.session_state.pop("_authenticator", None)
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

with tab_manage:
    users = sqlite_control.get_auth_users()
    if not users:
        st.info("目前沒有使用者")
    else:
        table_rows = [
            {
                "帳號": user["username"],
                "姓名": user["display_name"] or "",
                "Email": user["email"] or "",
                "狀態": "啟用" if user["is_active"] else "停用",
                "角色": ", ".join(user["roles"] or []),
            }
            for user in users
        ]
        st.dataframe(table_rows, width="stretch", hide_index=True)

        user_options = {
            f"{user['username']} ({'啟用' if user['is_active'] else '停用'})": user
            for user in users
        }
        selected_label = st.selectbox("選擇使用者", list(user_options))
        selected_user = user_options[selected_label]

        is_own_account = selected_user["id"] == current_user["id"]

        col_status, col_reset = st.columns(2)
        with col_status:
            st.subheader("帳號狀態")
            status_label = "啟用" if selected_user["is_active"] else "停用"
            if is_own_account:
                st.button(status_label, disabled=True, key="status_self")
                st.caption("不可停用目前登入中的管理員帳號")
            elif st.button(
                "停用帳號" if selected_user["is_active"] else "啟用帳號",
                key=f"toggle_{selected_user['id']}",
            ):
                success, message = sqlite_control.set_auth_user_active(
                    selected_user["id"],
                    not selected_user["is_active"],
                )
                if success:
                    st.session_state.pop("_authenticator", None)
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        with col_reset:
            st.subheader("重設密碼")
            with st.form("reset_password"):
                new_password = st.text_input("新密碼", type="password")
                confirm_new_password = st.text_input("確認新密碼", type="password")
                if st.form_submit_button("重設密碼"):
                    if new_password != confirm_new_password:
                        st.error("兩次密碼不一致")
                    else:
                        success, message = sqlite_control.reset_auth_user_password(
                            selected_user["id"],
                            new_password,
                        )
                        if success:
                            st.session_state.pop("_authenticator", None)
                            st.success(message)
                        else:
                            st.error(message)

        st.subheader("使用者權限")
        selected_role_ids = st.multiselect(
            "角色",
            options=[role["id"] for role in roles],
            default=[
                role["id"]
                for role in roles
                if role["role_code"] in selected_user["roles"]
            ],
            format_func=lambda role_id: (
                f"{role_name_by_id[role_id]} "
                f"({role_code_by_id[role_id]})"
            ),
            key=f"roles_{selected_user['id']}",
        )
        if st.button("儲存權限", type="primary", key="save_roles"):
            success, message = sqlite_control.set_auth_user_roles(
                selected_user["id"],
                selected_role_ids,
            )
            if success:
                st.session_state.pop("_authenticator", None)
                st.success(message)
                st.rerun()
            else:
                st.error(message)

with tab_roles:
    st.dataframe(
        [
            {
                "角色代碼": role["role_code"],
                "角色名稱": role["role_name"],
            }
            for role in roles
        ],
        width="stretch",
        hide_index=True,
    )

    with st.form("create_role", clear_on_submit=True):
        role_code = st.text_input("角色代碼", help="例如：inventory、primary_edit")
        role_name = st.text_input("角色名稱", help="例如：盤點人員")
        if st.form_submit_button("新增角色"):
            success, message = sqlite_control.create_auth_role(role_code, role_name)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
