import psycopg
from psycopg.rows import dict_row
import streamlit as st
import pandas as pd
import numpy as np
import bcrypt

def postgres_link():
    return psycopg.connect(
        st.secrets["DATABASE_URL"]
    )
    
def read_query(sql, params=None):
    with postgres_link() as conn:
        df = pd.read_sql_query(
            sql,
            conn,
            params=params,
        )

    df.columns = [str(column).upper() for column in df.columns]
    return df

def get_his_info_use_diacode(diacode: str): #取得藥品基本資料
    """用醫令碼取得藥品基本資料
    Args:
        diacode (str): 醫令碼
    Returns:
        pandas.DataFrame: 藥品基本資料
    """
    
    sql="""
    SELECT DA_DIACODE
    , DA_EGNAME
    , DA_CHNAME
    , DA_CNAME
    , DA_SITE
    FROM FROM_HIS
    WHERE UPPER(DA_DIACODE)=UPPER(%s)
    """
    df=read_query(sql, params=(diacode,))
    return df

def get_his_info_use_engname(engname: str): #取得藥品基本資料
    """用商品名取得藥品基本資料
    Args:
        engname (str): 英文商品名
    Returns:
        pandas.DataFrame: 藥品基本資料
    """
    sql="""
    SELECT DA_DIACODE
    , DA_EGNAME
    , DA_CHNAME
    , DA_CNAME
    , DA_SITE
    FROM FROM_HIS
    WHERE UPPER(DA_EGNAME)=UPPER(%s)
    """
    
    df=read_query(sql, params=(engname,))
    return df

def get_realworld_site(diacode):
    """用醫令碼取得真實櫃位資料
    Args:
        diacode (str): 醫令碼
    Returns:
        pandas.DataFrame: 真實櫃位資料
    """
    sql="""
        SELECT *
        FROM REALWORLD_SITE
        WHERE UPPER(RS_DIACODE)=UPPER(%s)
        """
    
    df=read_query(sql, params=(diacode,))
    return df
    
def get_unit_amount(diacode):
    sql="""
        SELECT *
        FROM UNIT_AMOUNT
        WHERE UPPER(UA_DIACODE)=UPPER(%s)
        """
    df=read_query(sql, params=(diacode,))
    return df

def save_realworld_site_and_unit_amount(
    diacode,
    df_site,
    df_unit_amount,
):
    site_columns = ["RS_DIACODE", "RS_SITE", "RS_WORKTOP"]
    unit_columns = ["UA_DIACODE", "UA_UNIT", "UA_AMOUNT"]

    site_rows = df_site[site_columns].dropna(how="all").copy()
    unit_rows = df_unit_amount[unit_columns].dropna(how="all").copy()

    site_rows = site_rows.dropna(
        subset=["RS_SITE", "RS_WORKTOP"]
    )
    unit_rows = unit_rows.dropna(
        subset=["UA_UNIT", "UA_AMOUNT"]
    )

    try:
        unit_rows["UA_AMOUNT"] = unit_rows["UA_AMOUNT"].astype(int)
    except (TypeError, ValueError) as error:
        raise ValueError("排裝數量必須是整數。") from error

    if (unit_rows["UA_AMOUNT"] <= 0).any():
        raise ValueError("排裝數量必須大於 0。")

    site_values = [
        (diacode, row["RS_SITE"], row["RS_WORKTOP"])
        for _, row in site_rows.iterrows()
    ]

    unit_values = [
        (diacode, row["UA_UNIT"], row["UA_AMOUNT"])
        for _, row in unit_rows.iterrows()
    ]

    with postgres_link() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM REALWORLD_SITE
                WHERE RS_DIACODE = %s
                """,
                (diacode,),
            )

            cursor.execute(
                """
                DELETE FROM UNIT_AMOUNT
                WHERE UA_DIACODE = %s
                """,
                (diacode,),
            )

            cursor.executemany(
                """
                INSERT INTO REALWORLD_SITE
                    (RS_DIACODE, RS_SITE, RS_WORKTOP)
                VALUES (%s, %s, %s)
                """,
                site_values,
            )

            cursor.executemany(
                """
                INSERT INTO UNIT_AMOUNT
                    (UA_DIACODE, UA_UNIT, UA_AMOUNT)
                VALUES (%s, %s, %s)
                """,
                unit_values,
            )

def get_all_worktop():
    """取得所有檯面資料
    Returns:
        pandas.DataFrame: 檯面資料
    """
    sql="""
        SELECT DISTINCT RS_WORKTOP
        FROM REALWORLD_SITE
        WHERE RS_WORKTOP IS NOT NULL
        ORDER BY RS_WORKTOP
        """
    df=read_query(sql)
    return df

def get_all_inventory_record():
    sql="""
        SELECT *
        FROM SUM_WITH_UNIT
        """
    df=read_query(sql)
    return df

def get_all_diacode_and_engname():
    sql="""
        SELECT DA_DIACODE, DA_EGNAME
        FROM FROM_HIS
        """
    
    df=read_query(sql)
    return df

def auto_complete_diacode_and_engname():
    df=get_all_diacode_and_engname()
    diacode_list=df['DA_DIACODE'].tolist()
    engname_list=df['DA_EGNAME'].tolist()
    return diacode_list+engname_list

def get_need_inventory_from_keyword(keyword):
    need_inventory=get_his_info_use_diacode(keyword)
    if need_inventory.empty==False:
        return need_inventory
    else:
        need_inventory=get_his_info_use_engname(keyword)
        return need_inventory
    
def get_need_inventory_diacode_and_engname(inventory_event_no: int | None = None):
    sql="""
        SELECT DA_DIACODE, DA_EGNAME
        FROM NEED_INVENTORY
        LEFT JOIN FROM_HIS 
            ON NEED_INVENTORY.NI_DIACODE=FROM_HIS.DA_DIACODE
        WHERE NEED_INVENTORY.NI_EVENT = %s
        """
    
    df=read_query(sql, params=(inventory_event_no,))
    return df

def auto_complete_diacode_and_engname_for_need_inventory(inventory_event_no: int | None = None):
    df=get_need_inventory_diacode_and_engname(inventory_event_no)
    print(df)
    diacode_list=df['DA_DIACODE'].tolist()
    engname_list=df['DA_EGNAME'].tolist()
    return diacode_list+engname_list
    
def upload_from_his_or_inventory(df, table_name, retain_old_data):
    allowed_tables = {
        "from_his": {
            "columns": (
                "DA_DIACODE",
                "DA_EGNAME",
                "DA_CHNAME",
                "DA_CNAME",
                "DA_SITE",
            ),
            "conflict_columns": ("DA_DIACODE",),
            "update_columns": (
                "DA_EGNAME",
                "DA_CHNAME",
                "DA_CNAME",
                "DA_SITE",
            ),
        },
        "need_inventory": {
            "columns": (
                "NI_DIACODE",
                "NI_EVENT",
            ),
            "conflict_columns": (
                "NI_EVENT",
                "NI_DIACODE",
            ),
            "update_columns": (),  # 重複資料不需要更新欄位
        },
        "realworld_site": {
            "columns": (
                "RS_DIACODE",
                "RS_SITE",
                "RS_WORKTOP",
            ),
            "conflict_columns": (
                "RS_DIACODE",
                "RS_SITE",
            ),
            "update_columns": (
                "RS_WORKTOP",
            ),
        },
        "unit_amount": {
            "columns": (
                "UA_DIACODE",
                "UA_UNIT",
                "UA_AMOUNT",
            ),
            "conflict_columns": (
                "UA_DIACODE",
                "UA_UNIT",
            ),
            "update_columns": (
                "UA_AMOUNT",
            ),
        },
    }

    if table_name not in allowed_tables:
        return False, "不支援的匯入資料表。"

    table_config = allowed_tables[table_name]
    columns = table_config["columns"]
    conflict_columns = table_config["conflict_columns"]
    update_columns = table_config["update_columns"]

    missing_columns = [
        column for column in columns
        if column not in df.columns
    ]
    if missing_columns:
        return False, f"CSV 缺少欄位：{missing_columns}"
    values = [
        tuple(
            None if pd.isna(row[column]) else row[column]
            for column in columns
        )
        for _, row in df.iterrows()
    ]
    try:
        conflict_target = ", ".join(conflict_columns)

        if update_columns:
            update_clause = ", ".join(
                f"{column} = EXCLUDED.{column}"
                for column in update_columns
            )
            on_conflict_sql = (
                f"ON CONFLICT ({conflict_target}) "
                f"DO UPDATE SET {update_clause}"
            )
        else:
            on_conflict_sql = (
                f"ON CONFLICT ({conflict_target}) DO NOTHING"
            )

        column_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        with postgres_link() as conn:
            with conn.cursor() as cursor:
                if not retain_old_data:
                    cursor.execute(f"DELETE FROM {table_name}")
                cursor.executemany(
                    f"""
                    INSERT INTO {table_name} ({column_names})
                    VALUES ({placeholders})
                    {on_conflict_sql}
                    """,
                    values,
                )

        return True, "資料已上傳成功！"

    except Exception as error:
        return False, f"資料上傳失敗：{error}"
    
def get_need_inventory_record(event_name: str | None = None) -> pd.DataFrame:
    sql="""
          /*查詢本次盤點品項_依醫令碼區分*/
        SELECT NEED_INVENTORY.NI_DIACODE "醫令碼"
        , FROM_HIS.DA_EGNAME "商品名"
        , SUM(INVENTORY_RECORD.IR_RECORD * COALESCE(UNIT_AMOUNT.UA_AMOUNT, 1)) AS "總量"
        , REALWORLD_SITE.RS_SITE AS "真實櫃位"
        , REALWORLD_SITE.RS_WORKTOP AS "檯面"
        , INVENTORY_EVENT.IE_NAME AS "盤點事件"
        
        FROM NEED_INVENTORY
        RIGHT JOIN INVENTORY_EVENT 
            ON INVENTORY_EVENT.IE_NO=NEED_INVENTORY.NI_EVENT
        LEFT JOIN FROM_HIS 
        ON FROM_HIS.DA_DIACODE=NEED_INVENTORY.NI_DIACODE
        LEFT JOIN REALWORLD_SITE
            ON REALWORLD_SITE.RS_DIACODE = NEED_INVENTORY.NI_DIACODE
        LEFT JOIN INVENTORY_RECORD
            ON INVENTORY_RECORD.IR_DIACODE = NEED_INVENTORY.NI_DIACODE
        AND (
            INVENTORY_RECORD.IR_SITE = REALWORLD_SITE.RS_SITE
            OR REALWORLD_SITE.RS_SITE IS NULL
        )
        AND INVENTORY_RECORD.IR_EVENT_NO = NEED_INVENTORY.NI_EVENT
        AND INVENTORY_RECORD.IR_DC = FALSE
        LEFT JOIN UNIT_AMOUNT 
            ON (UNIT_AMOUNT.UA_DIACODE=INVENTORY_RECORD.IR_DIACODE 
            AND UNIT_AMOUNT.UA_UNIT=INVENTORY_RECORD.IR_UNIT)
        
        WHERE INVENTORY_EVENT.IE_NAME = %s
            
        GROUP BY NEED_INVENTORY.NI_DIACODE
        , FROM_HIS.DA_EGNAME
        , REALWORLD_SITE.RS_SITE
        , REALWORLD_SITE.RS_WORKTOP 
        , INVENTORY_EVENT.IE_NAME 
        
        ORDER BY NEED_INVENTORY.NI_DIACODE, REALWORLD_SITE.RS_SITE"""
    df=read_query(sql, params=(event_name,))
    return df

def get_all_inventory_event():
    sql="""
        SELECT *
        FROM INVENTORY_EVENT
        ORDER BY IE_START DESC
        """
    df=read_query(sql)
    return df

def add_new_event(event_name, event_date):
    sql="""
        INSERT INTO INVENTORY_EVENT (IE_NAME, IE_START)
        VALUES (%s, %s)
        """
    try:
        with postgres_link() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (event_name, event_date))
        return True, "新增盤點事件成功！"
    except Exception as error: 
        return False, f"新增盤點事件失敗：{error}"

def get_inventory_event_by_name(event_name): 
    """用盤點事件名稱查詢盤點事件資料
    Args:
        event_name (str): 盤點事件名稱
    Returns:
        pandas.DataFrame: 盤點事件資料"""
    sql="""
        SELECT *
        FROM INVENTORY_EVENT
        WHERE IE_NAME = %s
        ORDER BY IE_START DESC
        """
    df=read_query(sql, params=(event_name,))
    return df

def find_existing_inventory_record(diacode, site, inventory_event_no):
    sql="""
        SELECT IR_ID
        , IR_DIACODE
        , IR_SITE
        , IR_UNIT
        , IR_RECORD
        , IR_USER
        , IR_TIME
        , IR_EVENT_NO
        , IR_DC
        , IR_DC_TIME
        FROM INVENTORY_RECORD
        WHERE IR_DIACODE = %s
        AND IR_SITE = %s
        AND IR_EVENT_NO = %s
        AND IR_DC = FALSE
        ORDER BY IR_TIME DESC, IR_ID DESC
        """
    df=read_query(sql, params=(diacode, site, inventory_event_no))
    return df


def save_inventory_amounts(diacode, site, result_list, user_id, inventory_event_no,):
    submitted_amounts = {
        unit: int(amount)
        for amount, unit in result_list
    }

    with postgres_link() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT IR_ID
                , IR_UNIT
                , IR_RECORD
                FROM INVENTORY_RECORD
                WHERE IR_DIACODE = %s
                  AND IR_SITE = %s
                  AND IR_EVENT_NO = %s
                  AND IR_DC = FALSE
                ORDER BY IR_TIME DESC, IR_ID DESC
                FOR UPDATE
                """,
                (diacode, site, inventory_event_no),
            )
            existing_rows = cursor.fetchall()

            existing_amounts = {}
            existing_ids = []
            for record_id, unit, amount in existing_rows:
                existing_ids.append(record_id)
                if unit not in existing_amounts:
                    existing_amounts[unit] = amount

            all_units = set(existing_amounts) | set(submitted_amounts)
            is_unchanged = all(
                existing_amounts.get(unit, 0)
                == submitted_amounts.get(unit, 0)
                for unit in all_units
            )
            if is_unchanged:
                return "unchanged"

            if existing_ids:
                cursor.execute(
                    """
                    UPDATE INVENTORY_RECORD
                    SET IR_DC = TRUE,
                        IR_DC_TIME = CURRENT_TIMESTAMP
                    WHERE IR_ID = ANY(%s)
                    """,
                    (existing_ids,),
                )

            insert_values = [
                (
                    user_id,
                    diacode,
                    site,
                    unit,
                    amount,
                    inventory_event_no,
                )
                for unit, amount in submitted_amounts.items()
                if amount > 0
            ]
            if insert_values:
                cursor.executemany(
                    """
                    INSERT INTO INVENTORY_RECORD
                        (IR_USER, IR_DIACODE, IR_SITE, IR_UNIT,
                         IR_RECORD, IR_EVENT_NO)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    insert_values,
                )

    return "saved"

def get_credentials():
    """取得啟用帳號及其角色，轉換為 authenticator 格式。"""

    sql = """
        SELECT
            auth_users.username,
            auth_users.display_name,
            auth_users.email,
            auth_users.password_hash,
            ARRAY_REMOVE(
                ARRAY_AGG(auth_roles.role_code),
                NULL
            ) AS roles
        FROM auth_users
        LEFT JOIN auth_user_roles
            ON auth_users.id = auth_user_roles.user_id
        LEFT JOIN auth_roles
            ON auth_user_roles.role_id = auth_roles.id
        WHERE auth_users.is_active = TRUE
        GROUP BY auth_users.id
    """

    with postgres_link() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql)
            users = cur.fetchall()

    credentials = {"usernames": {}}

    for user in users:
        credentials["usernames"][user["username"].lower()] = {
            "name": user["display_name"] or user["username"],
            "email": user["email"] or "",
            "password": user["password_hash"],
            "roles": user["roles"] or [],
        }

    return {"usernames": credentials["usernames"]}


from psycopg.rows import dict_row

def get_active_user(username):
    sql = """
        SELECT
            u.id,
            u.username,
            u.display_name,
            u.email,
            u.is_active,
            COALESCE(
                ARRAY_REMOVE(ARRAY_AGG(r.role_code), NULL),
                ARRAY[]::varchar[]
            ) AS roles
        FROM auth_users AS u
        LEFT JOIN auth_user_roles AS ur
            ON u.id = ur.user_id
        LEFT JOIN auth_roles AS r
            ON ur.role_id = r.id
        WHERE LOWER(TRIM(u.username)) = LOWER(TRIM(%s))
          AND u.is_active = TRUE
        GROUP BY
            u.id,
            u.username,
            u.display_name,
            u.email,
            u.is_active
    """

    with postgres_link() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (username,))
            user = cur.fetchone()

    return user


def get_auth_roles():
    sql = """
        SELECT id, role_code, role_name
        FROM auth_roles
        ORDER BY role_name, role_code
    """

    with postgres_link() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql)
            return cur.fetchall()


def get_auth_users():
    sql = """
        SELECT
            auth_users.id,
            auth_users.username,
            auth_users.display_name,
            auth_users.email,
            auth_users.is_active,
            auth_users.created_at,
            auth_users.updated_at,
            COALESCE(
                ARRAY_REMOVE(ARRAY_AGG(auth_user_roles.role_id), NULL),
                ARRAY[]::varchar[]
            ) AS roles
        FROM auth_users
        LEFT JOIN auth_user_roles
            ON auth_users.id = auth_user_roles.user_id
        LEFT JOIN auth_roles
            ON auth_user_roles.role_id = auth_roles.id
        GROUP BY
            auth_users.id,
            auth_users.username,
            auth_users.display_name,
            auth_users.email,
            auth_users.is_active,
            auth_users.created_at,
            auth_users.updated_at
        ORDER BY auth_users.is_active DESC, auth_users.username
    """

    with postgres_link() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql)
            return cur.fetchall()


def create_auth_user(username, display_name, email, password, role_ids):
    username = username.strip()
    display_name = display_name.strip()
    email = email.strip()

    if not username or not display_name:
        return False, "帳號及姓名不可空白"
    if len(password) < 8:
        return False, "密碼至少需要 8 個字元"

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")

    try:
        with postgres_link() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO auth_users
                        (username, display_name, email, password_hash, is_active)
                    VALUES (%s, %s, NULLIF(%s, ''), %s, TRUE)
                    RETURNING id
                    """,
                    (username, display_name, email, password_hash),
                )
                user_id = cur.fetchone()[0]

                cur.executemany(
                    """
                    INSERT INTO auth_user_roles (user_id, role_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    [(user_id, role_id) for role_id in role_ids],
                )
        return True, "使用者新增成功"
    except psycopg.errors.UniqueViolation as error:
        if "username" in str(error):
            return False, "此帳號已存在"
        if "email" in str(error):
            return False, "此 Email 已被使用"
        return False, "帳號或 Email 已存在"
    except Exception as error:
        return False, f"使用者新增失敗：{error}"


def set_auth_user_active(user_id, is_active):
    try:
        with postgres_link() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE auth_users
                    SET is_active = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (is_active, user_id),
                )
        return True, "使用者狀態已更新"
    except Exception as error:
        return False, f"更新使用者狀態失敗：{error}"


def set_auth_user_roles(user_id, role_ids):
    try:
        with postgres_link() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM auth_user_roles WHERE user_id = %s",
                    (user_id,),
                )
                cur.executemany(
                    """
                    INSERT INTO auth_user_roles (user_id, role_id)
                    VALUES (%s, %s)
                    """,
                    [(user_id, role_id) for role_id in role_ids],
                )
        return True, "使用者權限已更新"
    except Exception as error:
        return False, f"更新使用者權限失敗：{error}"


def reset_auth_user_password(user_id, password):
    if len(password) < 8:
        return False, "密碼至少需要 8 個字元"

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    ).decode("utf-8")

    try:
        with postgres_link() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE auth_users
                    SET password_hash = %s,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (password_hash, user_id),
                )
        return True, "密碼已重設"
    except Exception as error:
        return False, f"重設密碼失敗：{error}"


def create_auth_role(role_code, role_name):
    role_code = role_code.strip().lower()
    role_name = role_name.strip()
    if not role_code or not role_name:
        return False, "角色代碼及角色名稱不可空白"

    try:
        with postgres_link() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO auth_roles (role_code, role_name)
                    VALUES (%s, %s)
                    """,
                    (role_code, role_name),
                )
        return True, "角色新增成功"
    except psycopg.errors.UniqueViolation:
        return False, "角色代碼已存在"
    except Exception as error:
        return False, f"角色新增失敗：{error}"
    
def change_inventory_event_end_time(event_name: str, end_time: str) -> tuple[bool, str]:
    """更改盤點事件結束時間
    Args:
        event_name (str): 盤點事件名稱
        end_time (str): 結束時間
    Returns:
        tuple[bool, str]: (是否成功, 訊息)
    """
    try:
        with postgres_link() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE INVENTORY_EVENT
                    SET IE_END = %s
                    WHERE IE_NAME = %s
                    """,
                    (end_time, event_name),
                )
        return True, "盤點事件已結束"
    except Exception as error:
        return False, f"結束盤點事件失敗：{error}"