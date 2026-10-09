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
