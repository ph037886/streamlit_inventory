CREATE TABLE FROM_HIS ( /*從HIS匯入的資料，理論上是這次盤點的品項表*/
    DA_DIACODE CHAR(8) NOT NULL, /*醫令碼*/
    DA_EGNAME TEXT NOT NULL, /*商品名*/
    DA_CHNAME TEXT NOT NULL, /*學名*/
    DA_CNAME TEXT, /*中文名*/
    DA_SITE CHAR(5) /*櫃位*/
    );

CREATE TABLE REALWORLD_SITE ( /*真實櫃位*/
    RS_DIACODE CHAR(8) NOT NULL, /*醫令碼，和真實櫃位連結*/
    RS_SITE CHAR(10) NOT NULL, /*真實櫃位，可對應HIS內同櫃位，實際不同檯面，如：1A2-調1*/
    RS_WORKTOP CHAR(10) NOT NULL /*分類，對應檯面，後續可計算檯面完成度，如：調1、住院針劑、小藥盒-呂睿騰*/
    );

CREATE TABLE UNIT_AMOUNT ( /*單位數量*/
    UA_DIACODE CHAR(8) NOT NULL, /*醫令碼*/
    UA_UNIT CHAR(5) NOT NULL, /*單位，如：排、盒、包*/
    UA_AMOUNT INTEGER NOT NULL /*單位數量，正整數，如：14、28*/
    );

CREATE TABLE INVENTORY_RECORD ( /*盤點紀錄*/
    IR_DIACODE CHAR(8) NOT NULL, /*醫令碼*/
    IR_SITE CHAR(10) NOT NULL, /*真實櫃位，可對應HIS內同櫃位，實際不同檯面，如：1A2-調1*/
    IR_UNIT CHAR(5) NOT NULL, /*單位，如：排、盒、包*/
    IR_RECORD INTEGER, /*盤點量，從前端輸入進來的量*/
    IR_USER CHAR(10) NOT NULL, /*盤點人，紀錄HIS帳號*/
    IR_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP /*紀錄時間*/
    
    /*
    備註：
    這邊是紀錄盤點資料從前端進來的資料，不做計算
    計算再用view去計算數目
    */
    );

