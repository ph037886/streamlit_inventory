INSERT INTO FROM_HIS ('DA_DIACODE', 'DA_EGNAME', 'DA_CHNAME', 'DA_CNAME', 'DA_SITE') VALUES 
    --口服
    ('OCRES', 'CRESTOR 10MG TAB', 'rosuvastatin calcium 10mg', '冠脂妥膜衣錠 10毫克', '1A4'),
    ('OXAN2', 'XANAX 0.25 MG TAB (管4)', 'alprazolam 0.25mg', '贊安諾錠 0.25毫克', '1Q6'),
    --外用
    ('ENEOM', 'NEOMYCIN 軟膏 28GM OINT.', 'neomycin sulfate 5% 28gm', '新黴素軟膏', '1E1'),
    ('EONSD', 'O.N.S.D. OPH 10ML SOL', 'neostigmine oph. soln 0.01% 10ml', '硫酸甲酯新斯狄明點眼液', '1J4'),
    --針劑
    ('IBROS', 'BROSYM 500MG/500MG INJ (抗3)', 'cefoperazone 500mg+sulbactam 500mg', '博益欣注射劑 500/500毫克', '甲2'),
    ('ISMOF', '★ SMOFKABIVEN 1448ML INFUSION', 'glucose +sodium acetate+kcl+cacl+soybean oil+fish-oil...', '斯莫克必恩周邊靜脈輸注液', '點滴'),
    ('IDIPE', '(舊) DIPHENHYDRAMINE 30MG INJ', 'diphenhydramine 30mg/ml 1ml', '鹽酸二苯胺明注射液', '甲8');

INSERT INTO REALWORLD_SITE ('RS_DIACODE', 'RS_SITE', 'RS_WORKTOP') VALUES
    --口服
    ('OCRES', '1A4-調1', '調1'),
    ('OCRES', '1A4-調2', '調2'),
    ('OCRES', '庫存', '庫存'),
    ('OXAN2', '1Q6', '門診共用台'),
    ('OXAN2', '管櫃庫存', '管櫃庫存'),
    --外用
    ('ENEOM', '1E1-調1', '調1'),
    ('ENEOM', '1E1-調2', '調2'),
    ('ENEOM', '庫存', '庫存'),
    ('EONSD', '1J4-調1', '調1'),
    ('EONSD', '1J4-調2', '調2'),
    ('EONSD', '庫存', '庫存'),
    --針劑
    ('IBROS', '甲2', '住院針劑'),
    ('IBROS', '庫存', '庫存'),
    ('ISMOF', '點滴', '住院點滴'),
    ('IDIPE', '甲8', '住院針劑'),
    ('IDIPE', '庫存', '庫存'),
    ('IDIPE', '門診針劑', '門診中間台');


INSERT INTO UNIT_AMOUNT ('UA_DIACODE', 'UA_UNIT', 'UA_AMOUNT') VALUES
    ('OCRES', '排', '14'),
    ('OCRES', '盒', '28'),
    ('OXAN2', '排', '10'),
    ('IBROS', '盒', '10'),
    ('ISMOF', '箱', '4');

INSERT INTO ('', '') VALUES
    (),

INSERT INTO ('', '') VALUES
    (),