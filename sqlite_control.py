import psycopg
import streamlit as st
import pandas as pd

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

def get_his_info_use_diacode(diacode): #取得藥品基本資料
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

def get_his_info_use_engname(engname): #取得藥品基本資料
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
    
def get_need_inventory_diacode_and_engname():
    sql="""
        SELECT DA_DIACODE, DA_EGNAME
        FROM NEED_INVENTORY
        LEFT JOIN FROM_HIS ON NEED_INVENTORY.NI_DIACODE=FROM_HIS.DA_DIACODE
        """
    
    df=read_query(sql)
    return df

def auto_complete_diacode_and_engname_for_need_inventory():
    df=get_need_inventory_diacode_and_engname()
    diacode_list=df['DA_DIACODE'].tolist()
    engname_list=df['DA_EGNAME'].tolist()
    return diacode_list+engname_list
    
def upload_from_his_or_inventory(df, table_name, retain_old_data):
    allowed_tables = {
        "from_his": (
            "DA_DIACODE",
            "DA_EGNAME",
            "DA_CHNAME",
            "DA_CNAME",
            "DA_SITE",
        ),
        "need_inventory": (
            "NI_DIACODE",
            "NI_EVENT",
        )
    }

    if table_name not in allowed_tables:
        return False, "不支援的匯入資料表。"

    columns = allowed_tables[table_name]

    missing_columns = [
        column for column in columns
        if column not in df.columns
    ]
    if missing_columns:
        return False, f"CSV 缺少欄位：{missing_columns}"

    try:
        values = [
            tuple(row[column] for column in columns)
            for _, row in df.iterrows()
        ]

        column_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        with postgres_link() as conn:
            with conn.cursor() as cursor:
                if not retain_old_data:
                    cursor.execute(
                        f"DELETE FROM {table_name}"
                    )

                cursor.executemany(
                    f"""
                    INSERT INTO {table_name} ({column_names})
                    VALUES ({placeholders})
                    ON CONFLICT (DA_DIACODE) DO UPDATE SET
                        DA_EGNAME = EXCLUDED.DA_EGNAME,
                        DA_CHNAME = EXCLUDED.DA_CHNAME,
                        DA_CNAME = EXCLUDED.DA_CNAME,
                        DA_SITE = EXCLUDED.DA_SITE
                    """,
                    values,
                )

        return True, "資料已上傳成功！"

    except Exception as error:
        return False, f"資料上傳失敗：{error}"
    
def get_need_inventory_record():
    sql="""
          /*查詢本次盤點品項_依醫令碼區分*/
        SELECT NEED_INVENTORY.NI_DIACODE "醫令碼"
        , FROM_HIS.DA_EGNAME "商品名"
        , SUM(INVENTORY_RECORD.IR_RECORD * COALESCE(UNIT_AMOUNT.UA_AMOUNT, 1)) AS "排裝後總量"
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
        LEFT JOIN UNIT_AMOUNT 
            ON (UNIT_AMOUNT.UA_DIACODE=INVENTORY_RECORD.IR_DIACODE 
            AND UNIT_AMOUNT.UA_UNIT=INVENTORY_RECORD.IR_UNIT)
            
        GROUP BY NEED_INVENTORY.NI_DIACODE
        , FROM_HIS.DA_EGNAME
        , REALWORLD_SITE.RS_SITE
        , REALWORLD_SITE.RS_WORKTOP 
        , INVENTORY_EVENT.IE_NAME 
        
        ORDER BY NEED_INVENTORY.NI_DIACODE, REALWORLD_SITE.RS_SITE"""
    df=read_query(sql)
    return df

def get_all_inventory_event():
    sql="""
        SELECT *
        FROM INVENTORY_EVENT
        """
    df=read_query(sql)
    return df