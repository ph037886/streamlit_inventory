import sqlite3
import pandas as pd

def sqlite_link():
    conn = sqlite3.connect('inventory.db')
    return conn

def get_his_info(diacode): #取得藥品基本資料
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
        FROM INVENTORY_RECORD
        """
    
    df= pd.read_sql(sql, sqlite_link())
    return df