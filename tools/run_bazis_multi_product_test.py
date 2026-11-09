# -*- coding: utf-8 -*-
import os
import time
import json
import ctypes
import subprocess

ROAMING_BAZIS = r"C:\Users\VladimirWorkPC\AppData\Roaming\Bazis"
DOCS_BAZIS = r"C:\Users\VladimirWorkPC\Documents\Bazis"
BAZIS_EXE = r"C:\Program Files (x86)\BazisSoft\Bazis\Bazis.exe"
REPORT_PATH = r"C:\Users\VladimirWorkPC\Downloads\cutriteV9071\bazis_live_test_report.json"

JS_AUTOTEST = r"""// Автоматический прогон 5 различных мебельных изделий внутри движка БАЗИС-Мебельщик 2021
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

    if (th >= 2 && th <= 5) {
        if (n.indexOf("дно") >= 0 && n.indexOf("ящ") >= 0) return "Дно ящика";
        return "Стенка задняя";
    }
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
    if (n.indexOf("планк") >= 0) return rawName;
    if (n.indexOf("цокол") >= 0) return "Планка цокольная";
    if (n.indexOf("фасад") >= 0) return rawName;
    if (n.indexOf("двер") >= 0) return "Фасад";

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

function assignGostCiphers(code, productName, defaultUnit, orderNum) {
    Article.Name = productName;
    Article.Code = code;
    Article.ShortSign = code;
    Article.OrderName = orderNum;
    Article.OrderCode = orderNum;
    try {
        ArrangePositions(FurnPositionMode.All, Model);
    } catch (e) {}

    var groupMap = {};
    var nextIndex = 1;
    Model.forEachPanel(function(p) {
        if (!p) return;
        StartEditing(p);
        var gostName = normalizeGostName(p.Name, p);
        p.Name = gostName;
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
}

function buildKitchenBaseCabinet(samplesDir) {
    NewModel();
    var furnDir = "C:\\Users\\VladimirWorkPC\\Documents\\Bazis\\Scripts\\Форум\\Шкаф кухонный нижний\\";
    var W = 800, D = 560, H = 820, Hleg = 100, Th = 16;

    function addEdge(panel, elemIdx, isThick) {
        var b = panel.Butts.Add();
        b.ElemIndex = elemIdx;
        if (isThick) {
            b.Material = "Кромка ПВХ бук 2/19\r34";
            b.Sign = "Бук2/19";
            b.Thickness = 2.0;
            b.Width = 19;
        } else {
            b.Material = "Кромка ПВХ бук 0,4/19\r38";
            b.Sign = "Бук0,4/19";
            b.Thickness = 0.4;
            b.Width = 19;
        }
    }

    ActiveMaterial.Make("ДСП бук 16\r57", 16);

    var dno = AddHorizPanel(0, 0, W, D, Hleg);
    dno.Name = "Дно нижнее";
    addEdge(dno, 0, false);
    addEdge(dno, 1, false);
    addEdge(dno, 2, true);
    addEdge(dno, 3, false);
    dno.Build();

    var bokL = AddVertPanel(0, Hleg + Th, D, H, 0);
    bokL.Name = "Боковина левая";
    addEdge(bokL, 0, false);
    addEdge(bokL, 1, true);
    addEdge(bokL, 2, false);
    bokL.Build();

    var bokR = AddVertPanel(0, Hleg + Th, D, H, W - Th);
    bokR.Name = "Боковина правая";
    addEdge(bokR, 0, false);
    addEdge(bokR, 1, true);
    addEdge(bokR, 2, false);
    bokR.Build();

    var plPer = AddHorizPanel(Th, D - 100, W - Th, D, H - Th);
    plPer.Name = "Планка стяжная передняя";
    addEdge(plPer, 0, false);
    addEdge(plPer, 2, true);
    plPer.Build();

    var plZad = AddHorizPanel(Th, 0, W - Th, 100, H - Th);
    plZad.Name = "Планка стяжная задняя";
    addEdge(plZad, 0, false);
    addEdge(plZad, 2, false);
    plZad.Build();

    var polka1 = AddHorizPanel(Th + 1, 20, W - Th - 1, D - 20, Hleg + Th + 220);
    polka1.Name = "Полка съёмная";
    addEdge(polka1, 0, false);
    addEdge(polka1, 1, false);
    addEdge(polka1, 2, true);
    addEdge(polka1, 3, false);
    polka1.Build();

    var polka2 = AddHorizPanel(Th + 1, 20, W - Th - 1, D - 20, Hleg + Th + 450);
    polka2.Name = "Полка съёмная";
    addEdge(polka2, 0, false);
    addEdge(polka2, 1, false);
    addEdge(polka2, 2, true);
    addEdge(polka2, 3, false);
    polka2.Build();

    var cokol = AddFrontPanel(0, 0, W, Hleg, D - 40);
    cokol.Name = "Планка цокольная";
    addEdge(cokol, 0, false);
    addEdge(cokol, 1, false);
    addEdge(cokol, 2, false);
    addEdge(cokol, 3, false);
    cokol.Build();

    var fasL = AddFrontPanel(2, Hleg + 2, W / 2 - 2, H - 2, D);
    fasL.Name = "Фасад левый";
    for (var k = 0; k < 4; k++) addEdge(fasL, k, true);
    fasL.Build();

    var fasR = AddFrontPanel(W / 2 + 2, Hleg + 2, W - 2, H - 2, D);
    fasR.Name = "Фасад правый";
    for (var k2 = 0; k2 < 4; k2++) addEdge(fasR, k2, true);
    fasR.Build();

    ActiveMaterial.Make("ДВП ламинированная клен\r56", 3);
    var zadSt = AddFrontPanel(2, Hleg + 2, W - 2, H - 2, -3);
    zadSt.Name = "Стенка задняя";
    zadSt.Build();

    // Устанавливаем фурнитуру из штатной библиотеки Крепёж (евровинты, опоры, полкодержатели, ручки)
    var krepDir = "C:\\Users\\VladimirWorkPC\\Documents\\Bazis\\Scripts\\Крепёж\\";
    var evrovint = OpenFurniture(krepDir + "Евровинт.f3d");
    if (evrovint) {
        evrovint.Mount(bokL, dno, Th / 2, Hleg, 80);
        evrovint.Mount(bokL, dno, Th / 2, Hleg, D - 80);
        evrovint.Mount(bokR, dno, W - Th / 2, Hleg, 80);
        evrovint.Mount(bokR, dno, W - Th / 2, Hleg, D - 80);
        evrovint.Mount(plPer, bokL, Th / 2, H - Th, D - 50);
        evrovint.Mount(plPer, bokR, W - Th / 2, H - Th, D - 50);
        evrovint.Mount(plZad, bokL, Th / 2, H - Th, 50);
        evrovint.Mount(plZad, bokR, W - Th / 2, H - Th, 50);
    }
    var opora = OpenFurniture(krepDir + "Опора.f3d");
    if (opora) {
        opora.Mount1(dno, 60, Hleg, 60, 0);
        opora.Mount1(dno, W - 60, Hleg, 60, 0);
        opora.Mount1(dno, 60, Hleg, D - 60, 0);
        opora.Mount1(dno, W - 60, Hleg, D - 60, 0);
    }
    var ruchka = OpenFurniture(krepDir + "Ручка.f3d");
    if (ruchka) {
        ruchka.Mount1(fasL, W / 2 - 40, H - 120, D + Th, 0);
        ruchka.Mount1(fasR, W / 2 + 40, H - 120, D + Th, 0);
    }

    Action.Commit();
    assignGostCiphers("МК.741124.001", "Шкаф кухонный нижний", "00", "3333");
    var path = samplesDir + "Шкаф_кухонный_нижний_ГОСТ.b3d";
    SaveModel(path);
    return path;
}

function snapshotModel() {
    var snap = {
        orderName: Article.OrderName,
        productName: Article.Name,
        productCode: Article.Code,
        shortSign: Article.ShortSign,
        panelCount: 0,
        buttCount: 0,
        cutCount: 0,
        fastenerCount: 0,
        panels: []
    };

    function countNonPanels(list) {
        for (var i = 0; i < list.Count; i++) {
            var obj = list.Objects[i];
            if (!obj) continue;
            if (obj.List && obj.AsList) {
                countNonPanels(obj.AsList);
            } else if (!obj.AsPanel) {
                snap.fastenerCount++;
            }
        }
    }
    countNonPanels(Model);

    Model.forEachPanel(function(p) {
        if (!p) return;
        snap.panelCount++;
        var butts = [];
        if (p.Butts && p.Butts.Count > 0) {
            for (var b = 0; b < p.Butts.Count; b++) {
                var bt = p.Butts[b];
                butts.push({
                    elem: bt.ElemIndex,
                    sign: bt.Sign,
                    thick: Math.round(bt.Thickness * 10) / 10,
                    mat: ExtractMatName(bt.Material),
                    code: ExtractMatCode(bt.Material)
                });
                snap.buttCount++;
            }
        }
        var cuts = (p.Cuts && p.Cuts.Count) ? p.Cuts.Count : 0;
        snap.cutCount += cuts;
        snap.panels.push({
            name: p.Name,
            artPos: p.ArtPos,
            designation: p.Designation,
            matName: ExtractMatName(p.MaterialName),
            matCode: ExtractMatCode(p.MaterialName),
            w: Math.round(p.ContourWidth * 10) / 10,
            h: Math.round(p.ContourHeight * 10) / 10,
            th: Math.round(p.Thickness * 10) / 10,
            cuts: cuts,
            butts: butts
        });
    });
    return snap;
}

function switchDecorAndOrder(orderNum, productCode, decor, hdfMat) {
    Article.OrderName = orderNum;
    Article.OrderCode = orderNum;
    Article.Code = productCode;
    Article.ShortSign = productCode;
    Model.forEachPanel(function(panel) {
        if (!panel) return;
        StartEditing(panel);
        var th = Math.round(panel.Thickness);
        if (th >= 15 && th <= 18) {
            panel.MaterialName = decor.boardMat;
        } else if (th >= 2 && th <= 5 && hdfMat !== "") {
            panel.MaterialName = hdfMat;
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
            }
        }
        if (panel.ArtPos && productCode) {
            panel.Designation = productCode + "." + panel.ArtPos;
        }
        panel.Build();
    });
    Action.Commit();
}

function compareInvariants(before, after, expectedOrder, expectedMatName, expectedEdge2Sign, expectedEdge04Sign) {
    var errors = [];
    if (after.orderName !== expectedOrder) {
        errors.push("OrderName mismatch: " + after.orderName + " != " + expectedOrder);
    }
    if (before.panelCount !== after.panelCount) {
        errors.push("PanelCount mismatch: " + before.panelCount + " != " + after.panelCount);
    }
    if (before.buttCount !== after.buttCount) {
        errors.push("ButtCount mismatch: " + before.buttCount + " != " + after.buttCount);
    }
    if (before.cutCount !== after.cutCount) {
        errors.push("CutCount mismatch: " + before.cutCount + " != " + after.cutCount);
    }
    if (before.fastenerCount !== after.fastenerCount) {
        errors.push("FastenerCount mismatch: " + before.fastenerCount + " != " + after.fastenerCount);
    }
    for (var i = 0; i < before.panels.length; i++) {
        var p0 = before.panels[i];
        var p1 = after.panels[i];
        if (!p1) break;
        if (p0.name !== p1.name) errors.push("Panel[" + i + "] Name changed: " + p0.name + " -> " + p1.name);
        if (p0.artPos !== p1.artPos) errors.push("Panel[" + i + "] ArtPos changed: " + p0.artPos + " -> " + p1.artPos);
        if (p0.designation !== p1.designation) errors.push("Panel[" + i + "] Designation changed: " + p0.designation + " -> " + p1.designation);
        if (p0.w !== p1.w || p0.h !== p1.h || p0.th !== p1.th) {
            errors.push("Panel[" + i + "] Size changed: " + p0.w + "x" + p0.h + "x" + p0.th + " -> " + p1.w + "x" + p1.h + "x" + p1.th);
        }
        if (p1.th === 16 && p1.matName !== expectedMatName) {
            errors.push("Panel[" + i + "] MatName not updated: " + p1.matName + " != " + expectedMatName);
        }
        if (p0.butts.length !== p1.butts.length) {
            errors.push("Panel[" + i + "] Butt count changed");
        } else {
            for (var b = 0; b < p0.butts.length; b++) {
                var b0 = p0.butts[b];
                var b1 = p1.butts[b];
                if (b0.elem !== b1.elem) errors.push("Panel[" + i + "] Butt elem changed: " + b0.elem + " -> " + b1.elem);
                if (b0.thick !== b1.thick) errors.push("Panel[" + i + "] Butt thickness changed: " + b0.thick + " -> " + b1.thick);
                var expSign = (b1.thick >= 1.2) ? expectedEdge2Sign : expectedEdge04Sign;
                if (b1.sign !== expSign) errors.push("Panel[" + i + "] Butt sign mismatch: " + b1.sign + " != " + expSign);
            }
        }
    }
    return {
        passed: errors.length === 0,
        errorCount: errors.length,
        errors: errors
    };
}

var report = {
    timestamp: (new Date()).toISOString(),
    engine: "Bazis.exe 2021 (LibKernel3D.dll + ESTools.dll)",
    productsTested: 0,
    allPassed: true,
    results: []
};

try {
    var samplesDir = "C:\\Users\\VladimirWorkPC\\Documents\\Bazis\\Модели\\Samples\\";

    // --- ИЗДЕЛИЕ 1: Секретер (без блоков) ---
    LoadModel(samplesDir + "Секретер.b3d");
    var before1 = snapshotModel();
    switchDecorAndOrder("4050", "МК.741121.001", {
        boardMat: "ЛДСП 16мм Дуб Сонома\rLDSP-16-SONOMA",
        edge2Mat: "Кромка ПВХ Дуб Сонома 2/19\rPVC-20x19-SONOMA",
        edge2Sign: "Сон2/19",
        edge04Mat: "Кромка ПВХ Дуб Сонома 0,4/19\rPVC-04x19-SONOMA",
        edge04Sign: "Сон0,4/19"
    }, "ДВП ламинированная белая\r52");
    var out1 = samplesDir + "Тест_1_Секретер_Заказ4050_ДубСонома.b3d";
    SaveModel(out1);
    LoadModel(out1);
    var after1 = snapshotModel();
    var check1 = compareInvariants(before1, after1, "4050", "ЛДСП 16мм Дуб Сонома", "Сон2/19", "Сон0,4/19");
    report.results.push({
        product: "1. Секретер (МК.741121.001, без блоков)",
        sourceFile: samplesDir + "Секретер.b3d",
        savedFile: out1,
        before: before1,
        after: after1,
        verification: check1
    });
    if (!check1.passed) report.allPassed = false;
    report.productsTested++;

    // --- ИЗДЕЛИЕ 2: Секретер в блоках (7 вложенных блоков) ---
    LoadModel(samplesDir + "Секретер в блоках.b3d");
    var before2 = snapshotModel();
    switchDecorAndOrder("4051", "МК.741121.002", {
        boardMat: "ЛДСП 16мм Кашемир серый\rLDSP-16-CASHMERE",
        edge2Mat: "Кромка ПВХ Кашемир 2/19\rPVC-20x19-CASHMERE",
        edge2Sign: "Каш2/19",
        edge04Mat: "Кромка ПВХ Кашемир 0,4/19\rPVC-04x19-CASHMERE",
        edge04Sign: "Каш0,4/19"
    }, "ДВП ламинированная клен\r56");
    var out2 = samplesDir + "Тест_2_СекретерВБлоках_Заказ4051_Кашемир.b3d";
    SaveModel(out2);
    LoadModel(out2);
    var after2 = snapshotModel();
    var check2 = compareInvariants(before2, after2, "4051", "ЛДСП 16мм Кашемир серый", "Каш2/19", "Каш0,4/19");
    report.results.push({
        product: "2. Секретер в блоках (МК.741121.002, 7 уровней блоков)",
        sourceFile: samplesDir + "Секретер в блоках.b3d",
        savedFile: out2,
        before: before2,
        after: after2,
        verification: check2
    });
    if (!check2.passed) report.allPassed = false;
    report.productsTested++;

    // --- ИЗДЕЛИЕ 3: Шкаф с антресолью и консолями (45 деталей, радиусные полки, 2 сборочных блока) ---
    LoadModel(samplesDir + "Шкаф в блоках.b3d");
    var before3 = snapshotModel();
    switchDecorAndOrder("4052", "МК.741122.001", {
        boardMat: "ЛДСП 16мм Венге Цаво\rLDSP-16-WENGE",
        edge2Mat: "Кромка ПВХ Венге Цаво 2/19\rPVC-20x19-WENGE",
        edge2Sign: "Вен2/19",
        edge04Mat: "Кромка ПВХ Венге Цаво 0,4/19\rPVC-04x19-WENGE",
        edge04Sign: "Вен0,4/19"
    }, "ДВП ламинированная клен\r56");
    var out3 = samplesDir + "Тест_3_ШкафВБлоках_Заказ4052_Венге.b3d";
    SaveModel(out3);
    LoadModel(out3);
    var after3 = snapshotModel();
    var check3 = compareInvariants(before3, after3, "4052", "ЛДСП 16мм Венге Цаво", "Вен2/19", "Вен0,4/19");
    report.results.push({
        product: "3. Шкаф с антресолью и консолями (МК.741122.001, 45 деталей, 16 радиусных)",
        sourceFile: samplesDir + "Шкаф в блоках.b3d",
        savedFile: out3,
        before: before3,
        after: after3,
        verification: check3
    });
    if (!check3.passed) report.allPassed = false;
    report.productsTested++;

    // --- ИЗДЕЛИЕ 4: Тумба с дверью и полкой (BZ85, паз под ДВП, эксцентрики, шканты, петли, ручка) ---
    LoadModel(samplesDir + "Тумба.b3d");
    assignGostCiphers("МК.741123.001", "Тумба с дверью и полкой", "00", "3333");
    var tumbaGostPath = samplesDir + "Тумба_ГОСТ.b3d";
    SaveModel(tumbaGostPath);
    LoadModel(tumbaGostPath);
    var before4 = snapshotModel();
    switchDecorAndOrder("4053", "МК.741123.001", {
        boardMat: "ЛДСП 16мм Антрацит\rLDSP-16-ANTHRACITE",
        edge2Mat: "Кромка ПВХ Антрацит 2/19\rPVC-20x19-ANTHRACITE",
        edge2Sign: "Ант2/19",
        edge04Mat: "Кромка ПВХ Антрацит 0,4/19\rPVC-04x19-ANTHRACITE",
        edge04Sign: "Ант0,4/19"
    }, "ДВП ламинированная белая\r52");
    var out4 = samplesDir + "Тест_4_Тумба_Заказ4053_Антрацит.b3d";
    SaveModel(out4);
    LoadModel(out4);
    var after4 = snapshotModel();
    var check4 = compareInvariants(before4, after4, "4053", "ЛДСП 16мм Антрацит", "Ант2/19", "Ант0,4/19");
    report.results.push({
        product: "4. Тумба с дверью и полкой (МК.741123.001, паз ДВП + эксцентрики + петли)",
        sourceFile: tumbaGostPath,
        savedFile: out4,
        before: before4,
        after: after4,
        verification: check4
    });
    if (!check4.passed) report.allPassed = false;
    report.productsTested++;

    // --- ИЗДЕЛИЕ 5: Шкаф кухонный нижний (МК.741124.001, опоры + евровинты + ручки + 2 полки) ---
    var kitchenGostPath = buildKitchenBaseCabinet(samplesDir);
    LoadModel(kitchenGostPath);
    var before5 = snapshotModel();
    switchDecorAndOrder("4054", "МК.741124.001", {
        boardMat: "ЛДСП 16мм Дуб Галифакс\rLDSP-16-HALIFAX",
        edge2Mat: "Кромка ПВХ Дуб Галифакс 2/19\rPVC-20x19-HALIFAX",
        edge2Sign: "Гал2/19",
        edge04Mat: "Кромка ПВХ Дуб Галифакс 0,4/19\rPVC-04x19-HALIFAX",
        edge04Sign: "Гал0,4/19"
    }, "ДВП ламинированная клен\r56");
    var out5 = samplesDir + "Тест_5_ШкафКухонный_Заказ4054_Галифакс.b3d";
    SaveModel(out5);
    LoadModel(out5);
    var after5 = snapshotModel();
    var check5 = compareInvariants(before5, after5, "4054", "ЛДСП 16мм Дуб Галифакс", "Гал2/19", "Гал0,4/19");
    report.results.push({
        product: "5. Шкаф кухонный нижний (МК.741124.001, евровинты + опоры + ручки)",
        sourceFile: kitchenGostPath,
        savedFile: out5,
        before: before5,
        after: after5,
        verification: check5
    });
    if (!check5.passed) report.allPassed = false;
    report.productsTested++;

} catch (err) {
    report.allPassed = false;
    report.fatalError = err.toString();
}

system.writeTextFile("C:\\Users\\VladimirWorkPC\\Downloads\\cutriteV9071\\bazis_live_test_report.json", JSON.stringify(report, null, 2));
Action.Finish();
"""


def run_test():
    if os.path.exists(REPORT_PATH):
        os.remove(REPORT_PATH)

    scripts_dir = os.path.join(DOCS_BAZIS, "Scripts")
    autotest_js_path = os.path.join(scripts_dir, "_autotest_multi_products.js")
    with open(autotest_js_path, "w", encoding="cp1251") as f:
        f.write(JS_AUTOTEST)

    settings_path = os.path.join(ROAMING_BAZIS, "Settings.xml")
    with open(settings_path, "r", encoding="utf-8") as f:
        orig_settings = f.read()

    injected_settings = orig_settings.replace(
        "</Scripts>",
        f"      <Script>\n        <Path>{autotest_js_path}</Path>\n        <Key>120</Key>\n      </Script>\n    </Scripts>",
    )
    with open(settings_path, "w", encoding="utf-8") as f:
        f.write(injected_settings)

    subprocess.run(["taskkill", "/F", "/IM", "Bazis.exe"], capture_output=True)
    time.sleep(1.0)

    sample_model = os.path.join(DOCS_BAZIS, "Модели", "Samples", "Секретер.b3d")
    subprocess.Popen([BAZIS_EXE, sample_model])

    user32 = ctypes.windll.user32
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    VK_F9 = 0x78

    try:
        hwnd = 0
        for _ in range(30):
            time.sleep(0.3)
            hwnd = user32.FindWindowW("TFormMain", None)
            if hwnd and user32.IsWindowVisible(hwnd):
                break
        time.sleep(1.5)
        print(f"Bazis TFormMain HWND: {hex(hwnd)}")
        if hwnd:
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            user32.PostMessageW(hwnd, WM_KEYDOWN, VK_F9, 0)
            user32.PostMessageW(hwnd, WM_KEYUP, VK_F9, 0)

        for _ in range(30):
            if os.path.exists(REPORT_PATH) and os.path.getsize(REPORT_PATH) > 100:
                break
            time.sleep(0.5)
    finally:
        subprocess.run(["taskkill", "/F", "/IM", "Bazis.exe"], capture_output=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            f.write(orig_settings)
        if os.path.exists(autotest_js_path):
            os.remove(autotest_js_path)

    if not os.path.exists(REPORT_PATH):
        raise RuntimeError("bazis_live_test_report.json was not created!")

    with open(REPORT_PATH, "rb") as fb:
        raw_b = fb.read()
    data = json.loads(raw_b.decode("cp1251"))
    with open(REPORT_PATH, "w", encoding="utf-8") as fw:
        json.dump(data, fw, ensure_ascii=False, indent=2)

    print(f"=== ОТЧЁТ АВТОТЕСТА BAZIS.EXE (Проверено изделий: {data['productsTested']}, allPassed={data['allPassed']}) ===")
    if "fatalError" in data:
        print("FATAL ERROR:", data["fatalError"])
    for r in data["results"]:
        v = r["verification"]
        b = r["before"]
        a = r["after"]
        print(
            f"  * {r['product']}:\n"
            f"      До:    Заказ={b['orderName']}, Шифр={b['productCode']}, Панелей={b['panelCount']}, Кромок={b['buttCount']}, Пазов={b['cutCount']}, Крепежа={b['fastenerCount']}\n"
            f"      После: Заказ={a['orderName']}, Шифр={a['productCode']}, Панелей={a['panelCount']}, Кромок={a['buttCount']}, Пазов={a['cutCount']}, Крепежа={a['fastenerCount']}\n"
            f"      Проверка инвариантности: PASSED={v['passed']} (ошибок: {v['errorCount']})"
        )
        if v["errors"]:
            for err in v["errors"][:10]:
                print(f"        - {err}")


if __name__ == "__main__":
    run_test()
