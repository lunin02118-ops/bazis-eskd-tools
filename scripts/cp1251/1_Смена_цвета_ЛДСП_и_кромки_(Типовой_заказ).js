// ============================================================================
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
