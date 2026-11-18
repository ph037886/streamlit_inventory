import psycopg
import streamlit as st
import pandas as pd

def postgres_link():
    return psycopg.connect(
        st.secrets["DATABASE_URL"]
    )

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
    with postgres_link() as conn:
        df= pd.read_sql_query(sql, conn, params=(diacode,))
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
    
    with postgres_link() as conn:
        df= pd.read_sql_query(sql, conn, params=(engname,))
    return df

def get_realworld_site(diacode):
    sql="""
        SELECT *
        FROM REALWORLD_SITE
        WHERE UPPER(RS_DIACODE)=UPPER(%s)
        """
    
    with postgres_link() as conn:
        df= pd.read_sql_query(sql, conn, params=(diacode,))
    return df
    
def get_unit_amount(diacode):
    sql="""
        SELECT *
        FROM UNIT_AMOUNT
        WHERE UPPER(UA_DIACODE)=UPPER(%s)
        """
    with postgres_link() as conn:
        df= pd.read_sql_query(sql, conn, params=(diacode,))
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
    with postgres_link() as conn:
        df= pd.read_sql_query(sql, conn)
    return df

def get_all_diacode_and_engname():
    sql="""
        SELECT DA_DIACODE, DA_EGNAME
        FROM FROM_HIS
        """
    
    with postgres_link() as conn:
        df= pd.read_sql_query(sql, conn)
    return df

def auto_complete_diacode_and_engname():
    df=get_all_diacode_and_engname()
    diacode_list=df['da_diacode'].tolist()
    engname_list=df['da_egname'].tolist()
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
    
    with postgres_link() as conn:
        df= pd.read_sql_query(sql, conn)
    return df

def auto_complete_diacode_and_engname_for_need_inventory():
    df=get_need_inventory_diacode_and_engname()
    diacode_list=df['da_diacode'].tolist()
    engname_list=df['da_egname'].tolist()
    return diacode_list+engname_list
