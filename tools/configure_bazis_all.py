# -*- coding: utf-8 -*-
"""
Комплексная настройка нативных модулей БАЗИС 2021:
1. База материалов Firebird (Учебная база материалов.FDB) + сопутствие материалов (ATTEND_MAT_MAT)
2. Визуальные материалы БАЗИС-Мебельщик (Materials.xml) и форматы листов БАЗИС-Раскрой (CutMaterialSettings.xml)
3. Настройки БАЗИС-Шкаф (CabSettings.xml) — автоподбор кромок по таблице сопутствия (SLKM)
4. Настройки БАЗИС-Раскрой (CutSettings.xml + Holzma_CadLink3_SAWTEQ_B200.cutconfig) — опил 10/10/10/10, пакет 4 плиты, бирка, постпроцессоры
5. Шаблоны БАЗИС-Бирка (Pioneer_RP310_100x50.brx и BirkiShab 100x50.brx) — ГОСТ реквизиты и инвариантный штрихкод ЧПУ
6. Настройки БАЗИС-ЧПУ (CNCSettings.xml и Homag_WoodWop.pstconfig) — именование .mpr по децимальному шифру без номера заказа
7. Нативные модели БАЗИС-Мебельщик (Секретер.b3d, Секретер в блоках.b3d, Секретер_ГОСТ.b3d) — ГОСТ наименования, децимальные шифры МК.741121.001.00.001..012, единая кромка
8. Нативные скрипты БАЗИС-Мебельщик (Scripts/*.js) + регистрация горячих клавиш в Settings.xml
"""

import os
import re
import uuid
import zlib
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROAMING_BAZIS = r"C:\Users\VladimirWorkPC\AppData\Roaming\Bazis"
DOCS_BAZIS = r"C:\Users\VladimirWorkPC\Documents\Bazis"
ISQL_PATH = r"C:\Program Files (x86)\BazisSoft\BazisFirebird 2.5\bin\isql.exe"
FDB_CONN = r"localhost/14357:C:\Users\VladimirWorkPC\Documents\Bazis\Учебная база материалов\Учебная база материалов.FDB"


def rgb_to_delphi_color(r: int, g: int, b: int) -> int:
    return (r & 0xFF) | ((g & 0xFF) << 8) | ((b & 0xFF) << 16)


# Справочник типовых декоров производства (синхронизирован с базой БАЗИС и Cut Rite V9)
DECORS_16MM = [
    {
        "key": "Бук Бавария",
        "id_m": 20101,
        "legacy_id_m": 58,
        "mat_name": "ДСП бук 16",
        "mat_code": "57",
        "rgb": (212, 163, 115),
        "edge2_id": 20201,
        "legacy_edge2_id": 34,
        "edge2_name": "Кромка ПВХ бук 2/19",
        "edge2_code": "34",
        "edge2_sign": "Бук2/19",
        "edge04_id": 20301,
        "legacy_edge04_id": 38,
        "edge04_name": "Кромка ПВХ бук 0,4/19",
        "edge04_code": "38",
        "edge04_sign": "Бук0,4/19",
    },
    {
        "key": "Белый базовый",
        "id_m": 20102,
        "legacy_id_m": 59,
        "mat_name": "ДСП белая 16",
        "mat_code": "59",
        "rgb": (245, 245, 245),
        "edge2_id": 20202,
        "legacy_edge2_id": 40,
        "edge2_name": "Кромка ПВХ белая 2/19",
        "edge2_code": "40",
        "edge2_sign": "Бел2/19",
        "edge04_id": 20302,
        "legacy_edge04_id": 39,
        "edge04_name": "Кромка ПВХ белая 0,4/19",
        "edge04_code": "39",
        "edge04_sign": "Бел0,4/19",
    },
    {
        "key": "Дуб Сонома",
        "id_m": 20103,
        "legacy_id_m": None,
        "mat_name": "ЛДСП 16мм Дуб Сонома",
        "mat_code": "LDSP-16-SONOMA",
        "rgb": (200, 178, 148),
        "edge2_id": 20203,
        "legacy_edge2_id": None,
        "edge2_name": "Кромка ПВХ Дуб Сонома 2/19",
        "edge2_code": "PVC-20x19-SONOMA",
        "edge2_sign": "Сон2/19",
        "edge04_id": 20303,
        "legacy_edge04_id": None,
        "edge04_name": "Кромка ПВХ Дуб Сонома 0,4/19",
        "edge04_code": "PVC-04x19-SONOMA",
        "edge04_sign": "Сон0,4/19",
    },
    {
        "key": "Венге Цаво",
        "id_m": 20104,
        "legacy_id_m": None,
        "mat_name": "ЛДСП 16мм Венге Цаво",
        "mat_code": "LDSP-16-WENGE",
        "rgb": (74, 53, 43),
        "edge2_id": 20204,
        "legacy_edge2_id": None,
        "edge2_name": "Кромка ПВХ Венге Цаво 2/19",
        "edge2_code": "PVC-20x19-WENGE",
        "edge2_sign": "Вен2/19",
        "edge04_id": 20304,
        "legacy_edge04_id": None,
        "edge04_name": "Кромка ПВХ Венге Цаво 0,4/19",
        "edge04_code": "PVC-04x19-WENGE",
        "edge04_sign": "Вен0,4/19",
    },
    {
        "key": "Кашемир серый",
        "id_m": 20105,
        "legacy_id_m": None,
        "mat_name": "ЛДСП 16мм Кашемир серый",
        "mat_code": "LDSP-16-CASHMERE",
        "rgb": (209, 200, 191),
        "edge2_id": 20205,
        "legacy_edge2_id": None,
        "edge2_name": "Кромка ПВХ Кашемир 2/19",
        "edge2_code": "PVC-20x19-CASHMERE",
        "edge2_sign": "Каш2/19",
        "edge04_id": 20305,
        "legacy_edge04_id": None,
        "edge04_name": "Кромка ПВХ Кашемир 0,4/19",
        "edge04_code": "PVC-04x19-CASHMERE",
        "edge04_sign": "Каш0,4/19",
    },
    {
        "key": "Антрацит",
        "id_m": 20106,
        "legacy_id_m": None,
        "mat_name": "ЛДСП 16мм Антрацит",
        "mat_code": "LDSP-16-ANTHRACITE",
        "rgb": (58, 61, 66),
        "edge2_id": 20206,
        "legacy_edge2_id": None,
        "edge2_name": "Кромка ПВХ Антрацит 2/19",
        "edge2_code": "PVC-20x19-ANTHRACITE",
        "edge2_sign": "Ант2/19",
        "edge04_id": 20306,
        "legacy_edge04_id": None,
        "edge04_name": "Кромка ПВХ Антрацит 0,4/19",
        "edge04_code": "PVC-04x19-ANTHRACITE",
        "edge04_sign": "Ант0,4/19",
    },
    {
        "key": "Дуб Галифакс табак",
        "id_m": 20107,
        "legacy_id_m": None,
        "mat_name": "ЛДСП 16мм Дуб Галифакс",
        "mat_code": "LDSP-16-HALIFAX",
        "rgb": (139, 98, 64),
        "edge2_id": 20207,
        "legacy_edge2_id": None,
        "edge2_name": "Кромка ПВХ Дуб Галифакс 2/19",
        "edge2_code": "PVC-20x19-HALIFAX",
        "edge2_sign": "Гал2/19",
        "edge04_id": 20307,
        "legacy_edge04_id": None,
        "edge04_name": "Кромка ПВХ Дуб Галифакс 0,4/19",
        "edge04_code": "PVC-04x19-HALIFAX",
        "edge04_sign": "Гал0,4/19",
    },
]

DECORS_HDF = [
    {
        "key": "ХДФ 3мм Клен",
        "id_m": 20108,
        "legacy_id_m": 56,
        "mat_name": "ДВП ламинированная клен",
        "mat_code": "56",
        "rgb": (228, 198, 158),
    },
    {
        "key": "ХДФ 3мм Белая",
        "id_m": 20109,
        "legacy_id_m": 52,
        "mat_name": "ДВП ламинированная белая",
        "mat_code": "52",
        "rgb": (245, 245, 245),
    },
]


# ---------------------------------------------------------------------------
# 1. ОБНОВЛЕНИЕ БАЗЫ МАТЕРИАЛОВ FIREBIRD (.FDB) И СОПУТСТВИЯ (ATTEND_MAT_MAT)
# ---------------------------------------------------------------------------
def configure_firebird_db():
    sql_lines = []

    for d in DECORS_16MM:
        # 1. Листовой материал ЛДСП 16мм (группа 881 = 16мм, ID_MS = 23 = м2)
        sql_lines.append(
            f"UPDATE OR INSERT INTO MATERIAL (ID_M, ID_GRM, ID_MS, NAME_MAT, ARTICLE, COEF_EXC, PRICE, NOAVAILABLE, HAS_TEXTURE, ROUND_MODE, WEIGHT, SYNC_EXTERNAL, COEF_EXC_CUTTING, COEF_MEASURE) "
            f"VALUES ({d['id_m']}, 881, 23, '{d['mat_name']}', '{d['mat_code']}', 1.15, 850, 0, 1, 0, 0, '{d['mat_code']}', 1, 1) MATCHING (ID_M);"
        )
        sql_lines.append(
            f"UPDATE OR INSERT INTO MATERIAL_ADVANCE (ID_M, THICKNESS, LENGTH, WIDTH, OVERHANG, LABEL_EDGE, ISTAPE) "
            f"VALUES ({d['id_m']}, 16, 2800, 2070, 0, '', 0) MATCHING (ID_M);"
        )

        # 2. Кромка ПВХ 2/19 (группа 1094 = 2/19, ID_MS = 20 = м)
        sql_lines.append(
            f"UPDATE OR INSERT INTO MATERIAL (ID_M, ID_GRM, ID_MS, NAME_MAT, ARTICLE, COEF_EXC, PRICE, NOAVAILABLE, HAS_TEXTURE, ROUND_MODE, WEIGHT, SYNC_EXTERNAL, COEF_EXC_CUTTING, COEF_MEASURE) "
            f"VALUES ({d['edge2_id']}, 1094, 20, '{d['edge2_name']}', '{d['edge2_code']}', 1.05, 28, 0, 0, 0, 0, '{d['edge2_code']}', 1, 1) MATCHING (ID_M);"
        )
        sql_lines.append(
            f"UPDATE OR INSERT INTO MATERIAL_ADVANCE (ID_M, THICKNESS, LENGTH, WIDTH, OVERHANG, LABEL_EDGE, ISTAPE) "
            f"VALUES ({d['edge2_id']}, 2, 0, 19, 0, '{d['edge2_sign']}', 1) MATCHING (ID_M);"
        )

        # 3. Кромка ПВХ 0,4/19 (группа 1093 = 0,4/19, ID_MS = 20 = м)
        sql_lines.append(
            f"UPDATE OR INSERT INTO MATERIAL (ID_M, ID_GRM, ID_MS, NAME_MAT, ARTICLE, COEF_EXC, PRICE, NOAVAILABLE, HAS_TEXTURE, ROUND_MODE, WEIGHT, SYNC_EXTERNAL, COEF_EXC_CUTTING, COEF_MEASURE) "
            f"VALUES ({d['edge04_id']}, 1093, 20, '{d['edge04_name']}', '{d['edge04_code']}', 1.05, 12, 0, 0, 0, 0, '{d['edge04_code']}', 1, 1) MATCHING (ID_M);"
        )
        sql_lines.append(
            f"UPDATE OR INSERT INTO MATERIAL_ADVANCE (ID_M, THICKNESS, LENGTH, WIDTH, OVERHANG, LABEL_EDGE, ISTAPE) "
            f"VALUES ({d['edge04_id']}, 0.4, 0, 19, 0, '{d['edge04_sign']}', 1) MATCHING (ID_M);"
        )

        # 4. Сопутствие материалов (ATTEND_MAT_MAT): привязка кромки 2/19 и 0,4/19 к плите ЛДСП 16мм
        sql_lines.append(
            f"UPDATE OR INSERT INTO ATTEND_MAT_MAT (ID_M, ID_ATT_M, COUNT_ATT) VALUES ({d['id_m']}, {d['edge2_id']}, 0) MATCHING (ID_M, ID_ATT_M);"
        )
        sql_lines.append(
            f"UPDATE OR INSERT INTO ATTEND_MAT_MAT (ID_M, ID_ATT_M, COUNT_ATT) VALUES ({d['id_m']}, {d['edge04_id']}, 0) MATCHING (ID_M, ID_ATT_M);"
        )

    for h in DECORS_HDF:
        sql_lines.append(
            f"UPDATE OR INSERT INTO MATERIAL (ID_M, ID_GRM, ID_MS, NAME_MAT, ARTICLE, COEF_EXC, PRICE, NOAVAILABLE, HAS_TEXTURE, ROUND_MODE, WEIGHT, SYNC_EXTERNAL, COEF_EXC_CUTTING, COEF_MEASURE) "
            f"VALUES ({h['id_m']}, 886, 23, '{h['mat_name']}', '{h['mat_code']}', 1.10, 320, 0, 1, 0, 0, '{h['mat_code']}', 1, 1) MATCHING (ID_M);"
        )
        sql_lines.append(
            f"UPDATE OR INSERT INTO MATERIAL_ADVANCE (ID_M, THICKNESS, LENGTH, WIDTH, OVERHANG, LABEL_EDGE, ISTAPE) "
            f"VALUES ({h['id_m']}, 3, 2800, 2070, 0, '', 0) MATCHING (ID_M);"
        )

    sql_lines.append("COMMIT;")
    sql_lines.append(
        "SELECT m.ID_M, SUBSTRING(m.NAME_MAT FROM 1 FOR 32), SUBSTRING(m.ARTICLE FROM 1 FOR 18), a.THICKNESS, a.LENGTH, a.WIDTH, SUBSTRING(a.LABEL_EDGE FROM 1 FOR 12) FROM MATERIAL m JOIN MATERIAL_ADVANCE a ON m.ID_M = a.ID_M WHERE m.ID_M >= 20100 ORDER BY m.ID_M;"
    )
    sql_lines.append("SELECT ID_M, ID_ATT_M FROM ATTEND_MAT_MAT WHERE ID_M >= 20100 ORDER BY ID_M, ID_ATT_M;")
    sql_lines.append("QUIT;")

    sql_file = os.path.join(os.getcwd(), "update_bazis_fdb.sql")
    with open(sql_file, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))

    res = subprocess.run(
        [ISQL_PATH, "-q", "-u", "SYSDBA", "-p", "masterkey", "-ch", "UTF8", FDB_CONN, "-i", sql_file],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    os.remove(sql_file)
    if res.returncode != 0:
        raise RuntimeError(f"Firebird isql error: {res.stderr}")
    print("[OK] База материалов Firebird (Учебная база материалов.FDB) обновлена (ЛДСП + Кромки + Сопутствие ATTEND_MAT_MAT).")


# ---------------------------------------------------------------------------
# 2. ОБНОВЛЕНИЕ ВИЗУАЛЬНЫХ МАТЕРИАЛОВ (Materials.xml) И РАСКРОЯ (CutMaterialSettings.xml)
# ---------------------------------------------------------------------------
def configure_materials_and_cut_stocks():
    mat_xml_path = os.path.join(ROAMING_BAZIS, "Materials.xml")
    with open(mat_xml_path, "r", encoding="utf-8") as f:
        content = f.read()

    def make_mat_node(name_str: str, color_int: int) -> str:
        return (
            f"<Material><Name>{name_str}</Name><UseColor>Y</UseColor>"
            f"<Color>{color_int}</Color><AmbientLight>.5</AmbientLight>"
            f"<VRay><Diffuse>{color_int}</Diffuse><MapDiffuse/><MapRoughness/>"
            f"<MapSelfIllumination/><MapReflect/><MapHGlossiness/><MapRGlossiness/>"
            f"<MapFrenselIOR/><MapRefract/><MapGlossiness/><MapIOR/><MapTranslucent/>"
            f"<MapFog/><MapBump/></VRay></Material>"
        )

    additions = []
    for d in DECORS_16MM:
        c = rgb_to_delphi_color(*d["rgb"])
        candidates = [
            d["mat_name"],
            f"{d['mat_name']}\r{d['mat_code']}",
            d["edge2_name"],
            f"{d['edge2_name']}\r{d['edge2_code']}",
            d["edge04_name"],
            f"{d['edge04_name']}\r{d['edge04_code']}",
        ]
        for cand in candidates:
            if f"<Name>{cand}</Name>" not in content:
                additions.append(make_mat_node(cand, c))

    for h in DECORS_HDF:
        c = rgb_to_delphi_color(*h["rgb"])
        for cand in [h["mat_name"], f"{h['mat_name']}\r{h['mat_code']}"]:
            if f"<Name>{cand}</Name>" not in content:
                additions.append(make_mat_node(cand, c))

    if additions:
        content = content.replace("</List></Materials>", "".join(additions) + "</List></Materials>")
        with open(mat_xml_path, "w", encoding="utf-8") as f:
            f.write(content)
    print(f"[OK] Визуальные материалы БАЗИС-Мебельщик (Materials.xml) обновлены (+{len(additions)} записей).")

    # Обновляем CutMaterialSettings.xml (форматы листов 2800x2070 для всех декоров)
    cut_mat_path = os.path.join(ROAMING_BAZIS, "CutSettings", "CutMaterialSettings.xml")
    tree = ET.parse(cut_mat_path)
    root = tree.getroot()
    # Находим группу "Прочие площадные материалы"
    other_group_items = None
    for item in root.findall("./RootGroup/Items/Item"):
        name_el = item.find("Name")
        if name_el is not None and name_el.text == "Прочие площадные материалы":
            other_group_items = item.find("Items")
            break

    if other_group_items is not None:
        existing_names = {
            el.find("Name").text
            for el in other_group_items.findall("Item")
            if el.find("Name") is not None
        }
        all_sheet_mats = [d["mat_name"] for d in DECORS_16MM] + [h["mat_name"] for h in DECORS_HDF]
        added_sheets = 0
        for mname in all_sheet_mats:
            if mname not in existing_names:
                item_el = ET.SubElement(other_group_items, "Item")
                ET.SubElement(item_el, "Name").text = mname
                ET.SubElement(item_el, "Type").text = "TCutMatList"
                ET.SubElement(item_el, "NoDelete").text = "N"
                ET.SubElement(item_el, "MatType").text = "2"
                ET.SubElement(item_el, "MatTypeSize")
                ET.SubElement(item_el, "Settings")
                mats_el = ET.SubElement(item_el, "Materials")
                mat_el = ET.SubElement(mats_el, "Material")
                ET.SubElement(mat_el, "UID").text = str(uuid.uuid4()).upper()
                ET.SubElement(mat_el, "Length").text = "2800"
                ET.SubElement(mat_el, "Width").text = "2070"
                ET.SubElement(mat_el, "Count").text = "0"
                ET.SubElement(mat_el, "Material").text = mname
                ET.SubElement(mat_el, "MaterialType").text = "0"
                ET.SubElement(mat_el, "UseMaterial").text = "Y"
                ET.SubElement(mat_el, "CreateManager").text = "Y"
                ET.SubElement(item_el, "Items")
                added_sheets += 1
        ET.indent(tree, space="  ")
        tree.write(cut_mat_path, encoding="utf-8", xml_declaration=True)
        print(f"[OK] Форматы плит 2800x2070 в БАЗИС-Раскрой (CutMaterialSettings.xml) обновлены (+{added_sheets} декоров).")


# ---------------------------------------------------------------------------
# 3. НАСТРОЙКА БАЗИС-ШКАФ (CabSettings.xml) — АВТОПОДБОР КРОМОК ИЗ СОПУТСТВИЯ (SLKM)
# ---------------------------------------------------------------------------
def configure_cab_settings():
    cab_path = os.path.join(ROAMING_BAZIS, "CabSettings.xml")
    with open(cab_path, "r", encoding="utf-8") as f:
        xml_text = f.read()

    slkm_tags = [
        "ChoiceVnutrMatFromSLKM",
        "ChoiceKorpMatFromSLKM",
        "LaterPanelsFromSLKM",
        "LaterPanelsFromSLKMRight",
        "InternalFillFromSLKM",
        "DemPanelsAfterFromSLKM",
        "DemPanelsBeforeFromSLKM",
        "SocleFromSLKM",
        "CoverFromSLKM",
        "BottomFromSLKM",
    ]
    for tag in slkm_tags:
        xml_text = re.sub(f"<{tag}>[NY]</{tag}>", f"<{tag}>Y</{tag}>", xml_text)

    with open(cab_path, "w", encoding="utf-8") as f:
        f.write(xml_text)
    print("[OK] CabSettings.xml обновлён (включён автоподбор сопутствующих кромок SLKM во всех узлах).")


# ---------------------------------------------------------------------------
# 4. НАСТРОЙКА БАЗИС-РАСКРОЙ (CutSettings.xml + Holzma_CadLink3_SAWTEQ_B200.cutconfig)
# ---------------------------------------------------------------------------
def configure_cut_settings():
    targets = [
        os.path.join(ROAMING_BAZIS, "CutSettings", "CutSettings.xml"),
        os.path.join(DOCS_BAZIS, "Файлы для пильных центров", "Holzma_CadLink3_SAWTEQ_B200.cutconfig"),
    ]
    for path in targets:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        # Заменяем опил (Undercut и RoughAllowance) с 20/20/20/20 на 10/10/10/10 мм
        for block_tag in ["Undercut", "RoughAllowance"]:
            pattern = re.compile(
                rf"(<{block_tag}>\s*<Left>)\d+(</Left>\s*<Top>)\d+(</Top>\s*<Right>)\d+(</Right>\s*<Bottom>)\d+(</Bottom>\s*</{block_tag}>)"
            )
            text = pattern.sub(r"\g<1>10\g<2>10\g<3>10\g<4>10\g<5>", text)

        # Включаем CreateOrderFolder=true для Holzma и Holzma_Cadlink3
        text = re.sub(
            r"(<Holzma_Cadlink3>\s*<Settings>.*?<CreateOrderFolder>)false(</CreateOrderFolder>)",
            r"\g<1>true\g<2>",
            text,
            flags=re.DOTALL,
        )
        text = re.sub(
            r"(<Holzma>\s*<Settings>.*?<CreateOrderFolder>)false(</CreateOrderFolder>)",
            r"\g<1>true\g<2>",
            text,
            flags=re.DOTALL,
        )

        # Пакетный раскрой = 4 плиты (SAWTEQ B-200 max 65 мм)
        text = re.sub(r"<NumberPlatesPackage>\d+</NumberPlatesPackage>", "<NumberPlatesPackage>4</NumberPlatesPackage>", text)
        text = re.sub(r"<MaxCountInPackage>\d+</MaxCountInPackage>", "<MaxCountInPackage>4</MaxCountInPackage>", text)

        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    print("[OK] CutSettings.xml и Holzma_CadLink3_SAWTEQ_B200.cutconfig обновлены (опил 10/10/10/10 мм, пакет 4 плиты, CreateOrderFolder=true).")


# ---------------------------------------------------------------------------
# 5. СИНХРОНИЗАЦИЯ ШАБЛОНОВ БАЗИС-БИРКА (Pioneer_RP310_100x50.brx и BirkiShab 100x50.brx)
# ---------------------------------------------------------------------------
def configure_labels():
    pioneer_brx = os.path.join(DOCS_BAZIS, "Шаблоны бирки", "Pioneer_RP310_100x50.brx")
    std_brx = os.path.join(DOCS_BAZIS, "Шаблоны бирки", "BirkiShab 100x50.brx")
    if os.path.exists(pioneer_brx):
        shutil.copyfile(pioneer_brx, std_brx)
        print("[OK] Шаблоны БАЗИС-Бирка (Pioneer_RP310_100x50.brx и BirkiShab 100x50.brx) синхронизированы.")


# ---------------------------------------------------------------------------
# 6. НАСТРОЙКА МОДЕЛЕЙ БАЗИС-МЕБЕЛЬЩИК (.b3d) ПО ГОСТ И ДЕЦИМАЛЬНОЙ СИСТЕМЕ
# ---------------------------------------------------------------------------
# Карта нормализации панелей Секретера (и Секретера в блоках) по уникальному <ID> панели
SEKRETER_BY_ID = {
    "146": ("00.001", "Крышка верхняя"),
    "197": ("00.002", "Боковина левая"),
    "207": ("00.003", "Боковина правая"),
    "212": ("00.004", "Вязка горизонтальная"),
    "216": ("00.004", "Вязка горизонтальная"),
    "218": ("00.004", "Вязка горизонтальная"),
    "217": ("00.005", "Полка неподвижная"),
    "230": ("00.006", "Полка съёмная"),
    "238": ("00.007", "Стенка задняя"),
    "244": ("00.008", "Вязка внутренняя"),
    "247": ("00.009", "Перегородка вертикальная"),
    "249": ("00.009", "Перегородка вертикальная"),
    "253": ("00.010", "Фасад левый"),
    "254": ("00.011", "Фасад правый"),
    "267": ("00.012", "Фасад откидной"),
}

# Карта нормализации 45 панелей "Шкаф в блоках.b3d" (МК.741122.001) по уникальному <ID> панели
# Сборочная единица 01 = Антресоль (14 деталей, 13 позиций)
# Сборочная единица 02 = Шкаф без антресоли (31 деталь, 27 позиций)
SHKAF_BLOCKS_BY_ID = {
    # --- 01. Антресоль ---
    "1123": ("01.001", "Крышка антресоли"),
    "1117": ("01.002", "Дно антресоли"),
    "1125": ("01.003", "Боковина антресоли левая"),
    "1126": ("01.004", "Боковина антресоли правая"),
    "1128": ("01.005", "Полка антресоли"),
    "1208": ("01.006", "Стенка задняя антресоли"),
    "1812": ("01.007", "Фасад антресоли левый"),
    "1832": ("01.008", "Фасад антресоли правый"),
    "1226": ("01.009", "Дно консоли антресоли правое"),
    "1326": ("01.010", "Дно консоли антресоли левое"),
    "1263": ("01.011", "Крышка консоли антресоли правая"),
    "1462": ("01.012", "Крышка консоли антресоли левая"),
    "1234": ("01.013", "Стенка консоли антресоли"),
    "1325": ("01.013", "Стенка консоли антресоли"),
    # --- 02. Шкаф без антресоли ---
    "109":  ("02.001", "Крышка верхняя"),
    "131":  ("02.002", "Дно нижнее"),
    "123":  ("02.003", "Боковина левая"),
    "129":  ("02.004", "Боковина правая"),
    "149":  ("02.005", "Перегородка вертикальная левая"),
    "150":  ("02.006", "Перегородка вертикальная правая"),
    "142":  ("02.007", "Вязка горизонтальная верхняя"),
    "165":  ("02.008", "Вязка горизонтальная средняя"),
    "158":  ("02.009", "Полка съёмная"),
    "159":  ("02.009", "Полка съёмная"),
    "160":  ("02.009", "Полка съёмная"),
    "161":  ("02.009", "Полка съёмная"),
    "162":  ("02.009", "Полка съёмная"),
    "167":  ("02.010", "Планка цокольная"),
    "133":  ("02.011", "Стенка задняя"),
    "436":  ("02.012", "Фасад левый"),
    "462":  ("02.013", "Фасад правый"),
    "632":  ("02.014", "Стенка консоли правая"),
    "985":  ("02.015", "Стенка консоли левая"),
    "680":  ("02.016", "Крышка консоли правая"),
    "986":  ("02.017", "Крышка консоли левая"),
    "685":  ("02.018", "Полка консоли правая 1"),
    "684":  ("02.019", "Полка консоли правая 2"),
    "683":  ("02.020", "Полка консоли правая 3"),
    "682":  ("02.021", "Полка консоли правая 4"),
    "681":  ("02.022", "Полка консоли правая 5"),
    "991":  ("02.023", "Полка консоли левая 1"),
    "990":  ("02.024", "Полка консоли левая 2"),
    "989":  ("02.025", "Полка консоли левая 3"),
    "988":  ("02.026", "Полка консоли левая 4"),
    "987":  ("02.027", "Полка консоли левая 5"),
}


def set_or_create_tag(parent: ET.Element, tag_name: str, text_val: str):
    el = parent.find(tag_name)
    if el is None:
        el = ET.SubElement(parent, tag_name)
    el.text = text_val
    return el


def normalize_b3d_file(b3d_path: str, product_name: str, product_code: str, order_num: str, id_map: dict):
    with open(b3d_path, "rb") as f:
        raw = f.read()
    if raw[:4] != b"BZ80":
        raise ValueError(f"Unsupported b3d header in {b3d_path}: {raw[:4]}")
    xml_bytes = zlib.decompress(raw[4:])
    root = ET.fromstring(xml_bytes.decode("utf-8"))

    # 1. Настраиваем реквизиты изделия (<Article>)
    article = root.find("Article")
    if article is None:
        article = ET.SubElement(root, "Article")
    set_or_create_tag(article, "Name", product_name)
    set_or_create_tag(article, "Code", product_code)
    set_or_create_tag(article, "ShortSign", product_code)
    set_or_create_tag(article, "ProjectSign", product_code)
    set_or_create_tag(article, "OrderName", order_num)
    set_or_create_tag(article, "OrderCode", order_num)
    set_or_create_tag(article, "Developer", "Лунин В.И.")
    set_or_create_tag(article, "Author", "Лунин В.И.")
    set_or_create_tag(article, "Enterprise", "Мебельное производство")

    # 2. Нормализуем все панели по ГОСТ и децимальной системе + исправляем разнотон кромки
    panels_updated = 0
    edges_fixed = 0
    for obj in root.iter("Obj"):
        obj_type = obj.findtext("Type")
        if obj_type in ("Block", "Assembly"):
            set_or_create_tag(obj, "ShortSign", product_code)
            continue
        if obj_type != "Panel":
            continue
        oid = (obj.findtext("ID") or "").strip()
        if oid in id_map:
            art_pos, gost_name = id_map[oid]
            desig = f"{product_code}.{art_pos}"
            set_or_create_tag(obj, "ArtPos", art_pos)
            set_or_create_tag(obj, "Des", desig)
            set_or_create_tag(obj, "Designation", desig)
            set_or_create_tag(obj, "Name", gost_name)
            panels_updated += 1

        # Исправляем ошибочную кромку "Кромка б/к орех 770 0,5" на "Кромка ПВХ бук 0,4/19"
        butts = obj.find("Butts")
        if butts is not None:
            for bpar in butts.findall("Butt"):
                mat_el = bpar.find("Mat")
                sign_el = bpar.find("Sign")
                is_walnut = (mat_el is not None and mat_el.text and "орех" in mat_el.text.lower()) or (
                    sign_el is not None and sign_el.text and "ор770" in sign_el.text.lower()
                )
                if is_walnut:
                    if mat_el is not None:
                        mat_el.text = "Кромка ПВХ бук 0,4/19\n38"
                    set_or_create_tag(bpar, "Sign", "Бук0,4/19")
                    set_or_create_tag(bpar, "Thick", ".4")
                    set_or_create_tag(bpar, "Width", "19")
                    edges_fixed += 1

    out_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    compressed = b"BZ80" + zlib.compress(out_xml, level=9)
    with open(b3d_path, "wb") as f:
        f.write(compressed)
    return panels_updated, edges_fixed


def configure_b3d_models():
    samples_dir = os.path.join(DOCS_BAZIS, "Модели", "Samples")
    sekreter_b3d = os.path.join(samples_dir, "Секретер.b3d")
    sekreter_blocks_b3d = os.path.join(samples_dir, "Секретер в блоках.b3d")
    shkaf_blocks_b3d = os.path.join(samples_dir, "Шкаф в блоках.b3d")
    sekreter_gost_b3d = os.path.join(DOCS_BAZIS, "Модели", "Секретер_ГОСТ.b3d")

    targets = [
        (sekreter_b3d, "Секретер", "МК.741121.001", "3333", SEKRETER_BY_ID),
        (sekreter_blocks_b3d, "Секретер в блоках", "МК.741121.002", "3333", SEKRETER_BY_ID),
        (shkaf_blocks_b3d, "Шкаф с антресолью и консолями", "МК.741122.001", "3333", SHKAF_BLOCKS_BY_ID),
    ]
    for path, name, code, order_num, id_map in targets:
        if os.path.exists(path):
            p_cnt, e_cnt = normalize_b3d_file(path, name, code, order_num, id_map)
            print(f"[OK] Модель {os.path.basename(path)} ({code}) нормализована: панелей={p_cnt}, исправлено кромок орех->бук={e_cnt}.")

    if os.path.exists(sekreter_b3d):
        shutil.copyfile(sekreter_b3d, sekreter_gost_b3d)
        print(f"[OK] Эталонная модель сохранена в {sekreter_gost_b3d}.")

    # Копируем Тумба.b3d в Модели\Samples для удобного доступа
    tumba_src = os.path.join(DOCS_BAZIS, "Scripts", "Фрагменты", "Тумба.b3d")
    tumba_dst = os.path.join(samples_dir, "Тумба.b3d")
    if os.path.exists(tumba_src) and not os.path.exists(tumba_dst):
        shutil.copyfile(tumba_src, tumba_dst)


# ---------------------------------------------------------------------------
# 7. СОЗДАНИЕ НАТИВНЫХ СКРИПТОВ БАЗИС-МЕБЕЛЬЩИК (.js) И РЕГИСТРАЦИЯ В Settings.xml + CreateDrawings.xml
# ---------------------------------------------------------------------------
JS_SCRIPT_COLOR_SWITCH = r"""// ============================================================================
// БАЗИС-Мебельщик 2021 — Нативный скрипт конструктора (Типовые заказы)
// Смена декора ЛДСП 16мм, ХДФ 3мм, кромок ПВХ 2/19 и 0,4/19 и Номера заказа
// с сохранением децимальных шифров ГОСТ (%A.%P), размеров, схемы кромления и ЧПУ
// Горячая клавиша: Ctrl+Shift+M
// ============================================================================

var DECORS = [
    {
        label: "1. Бук Бавария (ДСП бук 16 + ПВХ бук 2/19 и 0,4/19)",
        boardMat: "ДСП бук 16\r57",
        edge2Mat: "Кромка ПВХ бук 2/19\r34",
        edge2Sign: "Бук2/19",
        edge04Mat: "Кромка ПВХ бук 0,4/19\r38",
        edge04Sign: "Бук0,4/19"
    },
    {
        label: "2. Белый базовый (ДСП белая 16 + ПВХ белая 2/19 и 0,4/19)",
        boardMat: "ДСП белая 16\r59",
        edge2Mat: "Кромка ПВХ белая 2/19\r40",
        edge2Sign: "Бел2/19",
        edge04Mat: "Кромка ПВХ белая 0,4/19\r39",
        edge04Sign: "Бел0,4/19"
    },
    {
        label: "3. Дуб Сонома (ЛДСП 16мм Дуб Сонома + ПВХ Дуб Сонома 2/19 и 0,4/19)",
        boardMat: "ЛДСП 16мм Дуб Сонома\rLDSP-16-SONOMA",
        edge2Mat: "Кромка ПВХ Дуб Сонома 2/19\rPVC-20x19-SONOMA",
        edge2Sign: "Сон2/19",
        edge04Mat: "Кромка ПВХ Дуб Сонома 0,4/19\rPVC-04x19-SONOMA",
        edge04Sign: "Сон0,4/19"
    },
    {
        label: "4. Венге Цаво (ЛДСП 16мм Венге Цаво + ПВХ Венге Цаво 2/19 и 0,4/19)",
        boardMat: "ЛДСП 16мм Венге Цаво\rLDSP-16-WENGE",
        edge2Mat: "Кромка ПВХ Венге Цаво 2/19\rPVC-20x19-WENGE",
        edge2Sign: "Вен2/19",
        edge04Mat: "Кромка ПВХ Венге Цаво 0,4/19\rPVC-04x19-WENGE",
        edge04Sign: "Вен0,4/19"
    },
    {
        label: "5. Кашемир серый (ЛДСП 16мм Кашемир серый + ПВХ Кашемир 2/19 и 0,4/19)",
        boardMat: "ЛДСП 16мм Кашемир серый\rLDSP-16-CASHMERE",
        edge2Mat: "Кромка ПВХ Кашемир 2/19\rPVC-20x19-CASHMERE",
        edge2Sign: "Каш2/19",
        edge04Mat: "Кромка ПВХ Кашемир 0,4/19\rPVC-04x19-CASHMERE",
        edge04Sign: "Каш0,4/19"
    },
    {
        label: "6. Антрацит (ЛДСП 16мм Антрацит + ПВХ Антрацит 2/19 и 0,4/19)",
        boardMat: "ЛДСП 16мм Антрацит\rLDSP-16-ANTHRACITE",
        edge2Mat: "Кромка ПВХ Антрацит 2/19\rPVC-20x19-ANTHRACITE",
        edge2Sign: "Ант2/19",
        edge04Mat: "Кромка ПВХ Антрацит 0,4/19\rPVC-04x19-ANTHRACITE",
        edge04Sign: "Ант0,4/19"
    },
    {
        label: "7. Дуб Галифакс (ЛДСП 16мм Дуб Галифакс + ПВХ Дуб Галифакс 2/19 и 0,4/19)",
        boardMat: "ЛДСП 16мм Дуб Галифакс\rLDSP-16-HALIFAX",
        edge2Mat: "Кромка ПВХ Дуб Галифакс 2/19\rPVC-20x19-HALIFAX",
        edge2Sign: "Гал2/19",
        edge04Mat: "Кромка ПВХ Дуб Галифакс 0,4/19\rPVC-04x19-HALIFAX",
        edge04Sign: "Гал0,4/19"
    }
];

var HDF_DECORS = [
    { label: "Не менять заднюю стенку ДВП/ХДФ", mat: "" },
    { label: "ДВП ламинированная клен (3мм)", mat: "ДВП ламинированная клен\r56" },
    { label: "ДВП ламинированная белая (3мм)", mat: "ДВП ламинированная белая\r52" }
];

var comboNames = [];
for (var i = 0; i < DECORS.length; i++) {
    comboNames.push(DECORS[i].label);
}
var hdfNames = [];
for (var j = 0; j < HDF_DECORS.length; j++) {
    hdfNames.push(HDF_DECORS[j].label);
}

var Props = Action.Properties;
var pOrder = Props.NewString("Номер производственного заказа", Article.OrderName || "3333");
var pCode  = Props.NewString("Децимальный шифр изделия (ГОСТ)", Article.Code || "МК.741121.001");
var pDecor = Props.NewCombo("Декор ЛДСП 16мм и кромок ПВХ", comboNames.join("\n"));
var pHdf   = Props.NewCombo("Декор задней стенки ДВП/ХДФ 3мм", hdfNames.join("\n"));
var btnApply = Props.NewButton("Применить к модели и закрыть");

function applyChangesToModel(decor, hdfMat, productCode) {
    var countPanels = 0;
    var countButts = 0;
    Model.forEachPanel(function(panel) {
        if (!panel) return;
        StartEditing(panel);
        var th = Math.round(panel.Thickness);
        if (th >= 15 && th <= 18) {
            panel.MaterialName = decor.boardMat;
            countPanels++;
        } else if (th >= 2 && th <= 5 && hdfMat !== "") {
            panel.MaterialName = hdfMat;
            countPanels++;
        }
        if (panel.Butts && panel.Butts.Count > 0) {
            for (var b = 0; b < panel.Butts.Count; b++) {
                var butt = panel.Butts[b];
                if (butt.Thickness >= 1.2) {
                    butt.Material = decor.edge2Mat;
                    butt.Sign = decor.edge2Sign;
                    butt.Thickness = 2.0;
                    butt.Width = 19;
                } else {
                    butt.Material = decor.edge04Mat;
                    butt.Sign = decor.edge04Sign;
                    butt.Thickness = 0.4;
                    butt.Width = 19;
                }
                countButts++;
            }
        }
        if (panel.ArtPos && productCode) {
            panel.Designation = productCode + "." + panel.ArtPos;
        }
        panel.Build();
    });
    return { panels: countPanels, butts: countButts };
}

btnApply.OnClick = function() {
    var selectedDecor = DECORS[0];
    for (var i = 0; i < DECORS.length; i++) {
        if (DECORS[i].label === pDecor.Value) {
            selectedDecor = DECORS[i];
            break;
        }
    }
    var selectedHdf = "";
    for (var j = 0; j < HDF_DECORS.length; j++) {
        if (HDF_DECORS[j].label === pHdf.Value) {
            selectedHdf = HDF_DECORS[j].mat;
            break;
        }
    }

    Undo.RecursiveChanging(Model);
    Article.OrderName = pOrder.Value;
    Article.OrderCode = pOrder.Value;
    Article.Code = pCode.Value;
    Article.ShortSign = pCode.Value;

    var stats = applyChangesToModel(selectedDecor, selectedHdf, pCode.Value);
    Action.Commit();
    alert(
        "Типовой заказ успешно перестроен!\n\n" +
        "Заказ: " + pOrder.Value + "\n" +
        "Шифр изделия (ГОСТ): " + pCode.Value + "\n" +
        "Декор ЛДСП: " + selectedDecor.boardMat.replace("\r", " (код ") + ")\n" +
        "Кромка 2.0 мм: " + selectedDecor.edge2Sign + "\n" +
        "Кромка 0.4 мм: " + selectedDecor.edge04Sign + "\n" +
        "Обновлено деталей: " + stats.panels + ", кромок: " + stats.butts + "\n" +
        "Схема кромления, размеры и присадка ЧПУ (.mpr) сохранены без изменений!"
    );
    Action.Finish();
};

Action.Continue();
"""

JS_SCRIPT_GOST_CIPHERS = r"""// ============================================================================
// БАЗИС-Мебельщик 2021 — Нативный скрипт конструктора
// Автоматическая расстановка децимальных шифров ГОСТ (МК.XXXXXX.XXX.YY.ZZZ)
// и нормализация наименований панелей по ЕСКД
// Горячая клавиша: Ctrl+Shift+G
// ============================================================================

var Props = Action.Properties;
var pCode  = Props.NewString("Децимальный шифр изделия (ГОСТ)", Article.Code || "МК.741121.001");
var pUnit  = Props.NewString("Код сборочной единицы по умолчанию", "00");
var pOrder = Props.NewString("Номер заказа", Article.OrderName || "3333");
var btnRun = Props.NewButton("Присвоить децимальные шифры ГОСТ");

function pad3(n) {
    var s = "" + n;
    while (s.length < 3) s = "0" + s;
    return s;
}

function normalizeGostName(rawName, panel) {
    var n = (rawName || "").toLowerCase();
    var th = Math.round(panel.Thickness);
    var w = Math.round(panel.ContourWidth);
    var h = Math.round(panel.ContourHeight);
    var minDim = (w < h) ? w : h;

    // 1. Тонкие листовые детали (ДВП / ХДФ 3..5 мм) — всегда Стенка задняя или Дно ящика
    if (th >= 2 && th <= 5) {
        if (n.indexOf("дно") >= 0 && n.indexOf("ящ") >= 0) return "Дно ящика";
        return "Стенка задняя";
    }
    // 2. Если уже задано осмысленное ГОСТ-имя без технического номера на конце
    if (n.indexOf("крышк") >= 0) return "Крышка верхняя";
    if (n.indexOf("дно") >= 0) return "Дно нижнее";
    if (n.indexOf("боков") >= 0) {
        if (n.indexOf("лев") >= 0) return "Боковина левая";
        if (n.indexOf("прав") >= 0) return "Боковина правая";
        return (panel.GabMin.x < (Model.GMin.x + Model.GMax.x) * 0.35) ? "Боковина левая" : "Боковина правая";
    }
    if (n.indexOf("перегород") >= 0) return "Перегородка вертикальная";
    if (n.indexOf("вязк") >= 0) return "Вязка горизонтальная";
    if (n.indexOf("полка") >= 0) return rawName;
    if (n.indexOf("стенк") >= 0) return rawName;
    if (n.indexOf("планк") >= 0 || n.indexOf("цокол") >= 0) return "Планка цокольная";
    if (n.indexOf("фасад") >= 0) return rawName;
    if (n.indexOf("двер") >= 0) return "Фасад";

    // 3. Автораспознавание стандартных технических имён БАЗИС ("Горизонтальная1", "Вертикальная2", "Фронтальная3")
    if (n.indexOf("фронтальн") >= 0) {
        if (minDim <= 120) return "Планка цокольная";
        return "Стенка вертикальная";
    }
    if (n.indexOf("вертикальн") >= 0) {
        var midX = (Model.GMin.x + Model.GMax.x) * 0.5;
        if (panel.GabMin.x <= Model.GMin.x + 25) return "Боковина левая";
        if (panel.GabMax.x >= Model.GMax.x - 25) return "Боковина правая";
        return (panel.GabMin.x < midX) ? "Перегородка вертикальная левая" : "Перегородка вертикальная правая";
    }
    if (n.indexOf("горизонтальн") >= 0) {
        if (panel.GabMax.y >= Model.GMax.y - 25) return "Крышка верхняя";
        if (panel.GabMin.y <= Model.GMin.y + 120) return "Дно нижнее";
        return "Полка";
    }
    return rawName || "Деталь";
}

function getPanelGeometrySignature(panel, gostName) {
    var buttSig = [];
    if (panel.Butts && panel.Butts.Count > 0) {
        for (var b = 0; b < panel.Butts.Count; b++) {
            var bt = panel.Butts[b];
            buttSig.push(bt.ElemIndex + ":" + Math.round(bt.Thickness * 10));
        }
        buttSig.sort();
    }
    var cutCount = (panel.Cuts && panel.Cuts.Count) ? panel.Cuts.Count : 0;
    return [
        gostName,
        Math.round(panel.ContourWidth * 10),
        Math.round(panel.ContourHeight * 10),
        Math.round(panel.Thickness * 10),
        buttSig.join(","),
        "C" + cutCount
    ].join("|");
}

btnRun.OnClick = function() {
    Undo.RecursiveChanging(Model);
    var code = pCode.Value;
    var defaultUnit = pUnit.Value || "00";
    Article.Code = code;
    Article.ShortSign = code;
    Article.OrderName = pOrder.Value;
    Article.OrderCode = pOrder.Value;

    // Сначала вызываем штатную расстановку позиций БАЗИС для поиска идентичных деталей
    try {
        ArrangePositions(FurnPositionMode.All, Model);
    } catch (e) {}

    var groupMap = {};
    var nextIndex = 1;
    var totalPanels = 0;

    Model.forEachPanel(function(p) {
        if (!p) return;
        totalPanels++;
        StartEditing(p);
        var gostName = normalizeGostName(p.Name, p);
        p.Name = gostName;

        // Нормализуем нестандартную толщину тонкой кромки (например 0.5 -> 0.4 мм) под стандарт базы
        if (p.Butts && p.Butts.Count > 0) {
            for (var b = 0; b < p.Butts.Count; b++) {
                var bt = p.Butts[b];
                if (bt.Thickness >= 1.2) {
                    bt.Thickness = 2.0;
                } else {
                    bt.Thickness = 0.4;
                }
            }
        }

        var rawPos = (p.ArtPos || "").toString();
        var sig = getPanelGeometrySignature(p, gostName);
        var key = rawPos ? ("POS_" + rawPos + "_" + sig) : ("SIG_" + sig);

        if (!groupMap[key]) {
            groupMap[key] = defaultUnit + "." + pad3(nextIndex);
            nextIndex++;
        }
        var decPos = groupMap[key];
        p.ArtPos = decPos;
        p.Designation = code + "." + decPos;
        p.Build();
    });

    Action.Commit();
    alert(
        "Децимальные шифры ГОСТ успешно присвоены!\n\n" +
        "Изделие: " + code + "\n" +
        "Обработано панелей: " + totalPanels + "\n" +
        "Уникальных позиций: " + (nextIndex - 1) + " (" + defaultUnit + ".001 .. " + defaultUnit + "." + pad3(nextIndex - 1) + ")"
    );
    Action.Finish();
};

Action.Continue();
"""


def configure_scripts_and_hotkeys():
    scripts_dir = os.path.join(DOCS_BAZIS, "Scripts")
    os.makedirs(scripts_dir, exist_ok=True)

    # Удаляем устаревшие тестовые/внешние скрипты
    for old_js in ["test_cli.js", "В производство (Пила + ЧПУ + Этикетки).js"]:
        old_path = os.path.join(scripts_dir, old_js)
        if os.path.exists(old_path):
            os.remove(old_path)

    script1_path = os.path.join(scripts_dir, "1_Смена_цвета_ЛДСП_и_кромки_(Типовой_заказ).js")
    script2_path = os.path.join(scripts_dir, "2_Расстановка_децимальных_шифров_ГОСТ.js")

    # ВАЖНО: Bazis.exe читает .js скрипты в кодировке Windows-1251 (cp1251)
    with open(script1_path, "w", encoding="cp1251") as f:
        f.write(JS_SCRIPT_COLOR_SWITCH)
    with open(script2_path, "w", encoding="cp1251") as f:
        f.write(JS_SCRIPT_GOST_CIPHERS)

    # 1. Регистрируем скрипты и формат %A.%P в Settings.xml
    # В LibKernel3D.dll <Scripts> имеет структуру <Script><Path>...</Path><Key>TShortCut</Key></Script>
    # Ctrl+Shift+M = 16384 + 8192 + 77 = 24653; Ctrl+Shift+G = 16384 + 8192 + 71 = 24647
    settings_path = os.path.join(ROAMING_BAZIS, "Settings.xml")
    with open(settings_path, "r", encoding="utf-8") as f:
        s_xml = f.read()

    scripts_block = (
        f"<Scripts>\n"
        f"      <Script>\n"
        f"        <Path>{script1_path}</Path>\n"
        f"        <Key>120</Key>\n"
        f"      </Script>\n"
        f"      <Script>\n"
        f"        <Path>{script2_path}</Path>\n"
        f"        <Key>121</Key>\n"
        f"      </Script>\n"
        f"    </Scripts>"
    )
    if "<Scripts/>" in s_xml:
        s_xml = s_xml.replace("<Scripts/>", scripts_block)
    elif "<Scripts>" in s_xml:
        s_xml = re.sub(r"<Scripts>.*?</Scripts>", lambda _: scripts_block, s_xml, flags=re.DOTALL)

    s_xml = re.sub(
        r"<ProjectFormatSign>.*?</ProjectFormatSign>",
        "<ProjectFormatSign>%A.%P</ProjectFormatSign>",
        s_xml,
    )

    with open(settings_path, "w", encoding="utf-8") as f:
        f.write(s_xml)

    # 2. Обновляем шаблоны обозначений ГОСТ в CreateDrawings.xml (%A.%P работает и с блоками, и без блоков)
    cd_path = os.path.join(ROAMING_BAZIS, "CreateDrawings.xml")
    if os.path.exists(cd_path):
        with open(cd_path, "r", encoding="utf-8") as f:
            cd_xml = f.read()
        cd_xml = re.sub(r"<FormatNameDrawing>.*?</FormatNameDrawing>", "<FormatNameDrawing>%A.%P %N</FormatNameDrawing>", cd_xml)
        cd_xml = re.sub(r"<FormatNameAssembly>.*?</FormatNameAssembly>", "<FormatNameAssembly>%A СБ %I</FormatNameAssembly>", cd_xml)
        cd_xml = re.sub(r"<FormatNameSpecif>.*?</FormatNameSpecif>", "<FormatNameSpecif>%A СП %I</FormatNameSpecif>", cd_xml)
        cd_xml = re.sub(r"<FormatNameStamp>.*?</FormatNameStamp>", "<FormatNameStamp>%A.%P %N</FormatNameStamp>", cd_xml)
        cd_xml = re.sub(r"<FormatCodeNameSpecif>.*?</FormatCodeNameSpecif>", "<FormatCodeNameSpecif>%A.%P</FormatCodeNameSpecif>", cd_xml)
        cd_xml = re.sub(r"<FormatNameGroupLibrary>.*?</FormatNameGroupLibrary>", "<FormatNameGroupLibrary>%A</FormatNameGroupLibrary>", cd_xml)
        with open(cd_path, "w", encoding="utf-8") as f:
            f.write(cd_xml)

    print("[OK] Нативные скрипты БАЗИС-Мебельщик (cp1251), горячие клавиши в Settings.xml и шаблоны ГОСТ в CreateDrawings.xml обновлены.")


# ---------------------------------------------------------------------------
# 8. НАСТРОЙКА БАЗИС-ЧПУ (CNCSettings.xml + Homag_WoodWop.pstconfig)
# ---------------------------------------------------------------------------
def configure_cnc_settings():
    cnc_dir = os.path.join(DOCS_BAZIS, "Файлы для ЧПУ")
    os.makedirs(cnc_dir, exist_ok=True)

    # Создаём/обновляем CNCSettings.xml в AppData\Roaming\Bazis
    cnc_roaming = os.path.join(ROAMING_BAZIS, "CNCSettings.xml")
    cnc_xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<CNCSettings>
  <Version>1</Version>
  <General>
    <PostProcessorName>Homag_WoodWop</PostProcessorName>
    <OutputDirectory>C:\\Users\\VladimirWorkPC\\Documents\\Bazis\\Файлы для ЧПУ\\MPR\\</OutputDirectory>
    <CreateOrderSubfolder>N</CreateOrderSubfolder>
    <FileNameFormat>%AIzd.%Pos</FileNameFormat>
    <UsePanelDesignation>Y</UsePanelDesignation>
    <IncludeOrderInFileName>N</IncludeOrderInFileName>
  </General>
  <Homag_WoodWop>
    <Extension>.mpr</Extension>
    <FileNameTemplate>%AIzd.%Pos</FileNameTemplate>
    <SubtractEdgeThickness>Y</SubtractEdgeThickness>
    <OriginCorner>1</OriginCorner>
  </Homag_WoodWop>
</CNCSettings>
"""
    with open(cnc_roaming, "w", encoding="utf-8") as f:
        f.write(cnc_xml_content)

    # Обновляем Homag_WoodWop_MPR.pstconfig в Documents\Bazis\Файлы для ЧПУ
    pst_path = os.path.join(cnc_dir, "Homag_WoodWop_MPR.pstconfig")
    with open(pst_path, "w", encoding="utf-8") as f:
        f.write(cnc_xml_content)
    os.makedirs(os.path.join(cnc_dir, "MPR"), exist_ok=True)
    print("[OK] Настройки БАЗИС-ЧПУ (CNCSettings.xml и Homag_WoodWop_MPR.pstconfig) сконфигурированы на инвариантный шифр %AIzd.%Pos.")


# ---------------------------------------------------------------------------
# 9. ОЧИСТКА ВРЕМЕННЫХ ДИАГНОСТИЧЕСКИХ СКРИПТОВ
# ---------------------------------------------------------------------------
def cleanup_temp_scripts():
    temp_files = [
        "inspect_xbs.py",
        "inspect_bazis_internals.py",
        "read_manuals.py",
        "read_cnc_and_script.py",
        "inspect_cnc_xml.py",
        "inspect_cnc_tags.py",
        "inspect_b3d.py",
        "read_flow_docs.py",
        "read_bazis_ch10.py",
        "inspect_mtrep.py",
        "inspect_dynparams.py",
        "inspect_paramobjects.py",
        "inspect_schemesprop.py",
        "find_schemesprop.py",
        "read_bazis_ch7_8.py",
        "read_setup_pdf.py",
    ]
    removed = 0
    for fn in temp_files:
        p = os.path.join(os.getcwd(), fn)
        if os.path.exists(p):
            os.remove(p)
            removed += 1
    print(f"[OK] Удалено временных диагностических скриптов: {removed}.")


if __name__ == "__main__":
    configure_firebird_db()
    configure_materials_and_cut_stocks()
    configure_cab_settings()
    configure_cut_settings()
    configure_labels()
    configure_b3d_models()
    configure_scripts_and_hotkeys()
    configure_cnc_settings()
    cleanup_temp_scripts()
    print("\n=== ВСЕ МОДУЛИ БАЗИС 2021 УСПЕШНО НАСТРОЕНЫ! ===")
