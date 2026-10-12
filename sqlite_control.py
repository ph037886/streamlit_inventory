import sqlite3
import pandas as pd

def sqlite_link():
    conn = sqlite3.connect('inventory.db')
    return conn

def get_his_info_use_diacode(diacode): #取得藥品基本資料
    sql="""
    SELECT DA_DIACODE
    , DA_EGNAME
    , DA_CHNAME
    , DA_CNAME
    FROM FROM_HIS
    WHERE DA_DIACODE=upper('&diacode')
    """
    
    sql=sql.replace('&diacode', diacode)
    
    df= pd.read_sql(sql, sqlite_link())
    return df

def get_his_info_use_engname(engname): #取得藥品基本資料
    sql="""
    SELECT DA_DIACODE
    , DA_EGNAME
    , DA_CHNAME
    , DA_CNAME
    FROM FROM_HIS
    WHERE DA_EGNAME=upper('&engname')
    """
    
    sql=sql.replace('&engname', engname)
    
    df= pd.read_sql(sql, sqlite_link())
    return df

def get_realworld_site(diacode):
    sql="""
        SELECT *
        FROM REALWORLD_SITE
        WHERE RS_DIACODE=upper('&diacode')
        """
        
    sql=sql.replace('&diacode', diacode)
    
    df= pd.read_sql(sql, sqlite_link())
    return df
    
def get_unit_amount(diacode):
    sql="""
        SELECT *
        FROM UNIT_AMOUNT
        WHERE UA_DIACODE=upper('&diacode')
        """
            
    sql=sql.replace('&diacode', diacode)
    
    df= pd.read_sql(sql, sqlite_link())
    return df

def save_realworld_site_and_unit_amount(diacode, df_site, df_unit_amount):
    site_columns = ['RS_DIACODE', 'RS_SITE', 'RS_WORKTOP']
    unit_columns = ['UA_DIACODE', 'UA_UNIT', 'UA_AMOUNT']
    site_rows = df_site[site_columns].dropna(how='all').copy()
    unit_rows = df_unit_amount[unit_columns].dropna(how='all').copy()

    site_rows = site_rows.dropna(subset=['RS_SITE', 'RS_WORKTOP'])
    unit_rows = unit_rows.dropna(subset=['UA_UNIT', 'UA_AMOUNT'])
    try:
        unit_rows['UA_AMOUNT'] = unit_rows['UA_AMOUNT'].astype(int)
    except (TypeError, ValueError) as error:
        raise ValueError('排裝數量必須是整數。') from error

    if (unit_rows['UA_AMOUNT'] <= 0).any():
        raise ValueError('排裝數量必須大於 0。')

    conn = sqlite_link()
    try:
        conn.execute('BEGIN')
        conn.execute('DELETE FROM REALWORLD_SITE WHERE RS_DIACODE = ?', (diacode,))
        conn.execute('DELETE FROM UNIT_AMOUNT WHERE UA_DIACODE = ?', (diacode,))
        conn.executemany(
            'INSERT INTO REALWORLD_SITE (RS_DIACODE, RS_SITE, RS_WORKTOP) VALUES (?, ?, ?)',
            [(diacode, row['RS_SITE'], row['RS_WORKTOP']) for _, row in site_rows.iterrows()]
        )
        conn.executemany(
            'INSERT INTO UNIT_AMOUNT (UA_DIACODE, UA_UNIT, UA_AMOUNT) VALUES (?, ?, ?)',
            [(diacode, row['UA_UNIT'], row['UA_AMOUNT']) for _, row in unit_rows.iterrows()]
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_all_inventory_record():
    sql="""
        SELECT *
        FROM SUM_WITH_UNIT
        """
    
    df= pd.read_sql(sql, sqlite_link())
    return df

def get_all_diacode_and_engname():
    sql="""
        SELECT DA_DIACODE, DA_EGNAME
        FROM FROM_HIS
        """
    
    df= pd.read_sql(sql, sqlite_link())
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
