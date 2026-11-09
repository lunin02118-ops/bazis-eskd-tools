// ============================================================================
// БАЗИС-Мебельщик 2021 — Нативный скрипт конструктора (Горячая клавиша: F10)
// Автоматическое заполнение децимальных номеров деталей по шаблону ГОСТ/ЕСКД
// на основе шифра изделия (%A), кода сборочной единицы (%U) и позиции (%P)
// ============================================================================

var iniPath = "C:\\Users\\VladimirWorkPC\\Documents\\Bazis\\Scripts\\cipher_template.ini";

function loadIniConfig() {
    var cfg = {
        template: "%A.%U.%P",
        defaultUnit: "00",
        digitsMode: 0,
        nameMode: 0,
        lastCode: "889.00.000",
        lastOrder: "4050"
    };
    try {
        var fso = new ActiveXObject("Scripting.FileSystemObject");
        if (fso.FileExists(iniPath)) {
            var ts = fso.OpenTextFile(iniPath, 1, false);
            while (!ts.AtEndOfStream) {
                var line = ts.ReadLine();
                var eq = line.indexOf("=");
                if (eq > 0) {
                    var k = line.substring(0, eq).replace(/^\s+|\s+$/g, "");
                    var v = line.substring(eq + 1).replace(/^\s+|\s+$/g, "");
                    if (k === "Template" && v) cfg.template = v;
                    if (k === "DefaultUnit" && v) cfg.defaultUnit = v;
                    if (k === "DigitsMode") cfg.digitsMode = parseInt(v, 10) || 0;
                    if (k === "NameMode") cfg.nameMode = parseInt(v, 10) || 0;
                    if (k === "LastCode" && v) cfg.lastCode = v;
                    if (k === "LastOrder" && v) cfg.lastOrder = v;
                }
            }
            ts.Close();
        }
    } catch (e) {}
    return cfg;
}

function saveIniConfig(cfg) {
    try {
        var fso = new ActiveXObject("Scripting.FileSystemObject");
        var ts = fso.CreateTextFile(iniPath, true);
        ts.WriteLine("Template=" + cfg.template);
        ts.WriteLine("DefaultUnit=" + cfg.defaultUnit);
        ts.WriteLine("DigitsMode=" + cfg.digitsMode);
        ts.WriteLine("NameMode=" + cfg.nameMode);
        ts.WriteLine("LastCode=" + cfg.lastCode);
        ts.WriteLine("LastOrder=" + cfg.lastOrder);
        ts.Close();
    } catch (e) {}
}

function detectModelCipher(fallbackCode) {
    var c = (Article.Code || "").replace(/^\s+|\s+$/g, "");
    if (!c) c = (Article.ShortSign || "").replace(/^\s+|\s+$/g, "");
    if (!c) {
        try {
            for (var i = 0; i < Model.Count; i++) {
                var obj = Model.Objects[i];
                if (obj && obj.Designation) {
                    var d = ("" + obj.Designation).replace(/^\s+|\s+$/g, "");
                    if (d.length >= 2) { c = d; break; }
                }
            }
        } catch (e) {}
    }
    return c || fallbackCode || "889.00.000";
}

function extractBaseProductCode(rawCode) {
    var c = (rawCode || "").replace(/^\s+|\s+$/g, "");
    // Если шифр изделия записан с суффиксом сборочного чертежа (.00.000 или .000),
    // выделяем базовый шифр изделия (%A), чтобы не задваивать .00.000.00.001
    c = c.replace(/\.00\.000$/, "").replace(/\.000$/, "");
    return c || "889";
}

function padNum(n, digits) {
    var s = "" + n;
    while (s.length < digits) s = "0" + s;
    return s;
}

var cfg = loadIniConfig();
var detectedCipher = detectModelCipher(cfg.lastCode);

var Props = Action.Properties;
var pCode     = Props.NewString("Шифр изделия (%A)", detectedCipher);
var pTemplate = Props.NewString("Шаблон децимального шифра детали", cfg.template);
var pUnit     = Props.NewString("Код сборочной единицы по умолчанию (%U)", cfg.defaultUnit);
var pDigits   = Props.NewCombo("Разрядность номера детали (%P)", "3 знака (001, 002...)\n2 знака (01, 02...)");
pDigits.ItemIndex = cfg.digitsMode;
var pNameMode = Props.NewCombo(
    "Наименования деталей (%N)",
    "Сохранять мои названия (заменять только Горизонтальная/Вертикальная)\n" +
    "Не менять наименования деталей (только заполнить шифры по шаблону)\n" +
    "Переименовать все детали по шаблону ГОСТ"
);
pNameMode.ItemIndex = cfg.nameMode;
var pOrder    = Props.NewString("Номер заказа", Article.OrderName || cfg.lastOrder);
var btnRun    = Props.NewButton("Заполнить децимальные шифры по шаблону");

function isGenericBazisPanelName(name) {
    var n = (name || "").replace(/^\s+|\s+$/g, "").toLowerCase();
    if (!n) return true;
    if (/^(горизонтальная|вертикальная|фронтальная|панель|фальшпанель|деталь|погонаж)\s*\d*$/.test(n)) {
        return true;
    }
    return false;
}

function stripTrailingAutoDigits(name) {
    var s = (name || "").replace(/^\s+|\s+$/g, "");
    // Убираем техническую цифру БАЗИС в конце стандартных слов ("Боковина левая1" -> "Боковина левая", "Полка2" -> "Полка")
    return s.replace(/^([А-Яа-яЁё\s\-]+?)\d+$/, "$1").replace(/\s+$/, "");
}

function resolveGostPanelName(rawName, panel, modeIndex) {
    var cleanRaw = (rawName || "").replace(/^\s+|\s+$/g, "");
    // Режим 1: вообще не трогать наименования деталей
    if (modeIndex === 1) {
        return cleanRaw || "Деталь";
    }
    // Режим 0 (по умолчанию): сохранять названия конструктора, заменяя только технические "Горизонтальная1/Вертикальная2"
    if (modeIndex === 0 && !isGenericBazisPanelName(cleanRaw)) {
        return stripTrailingAutoDigits(cleanRaw);
    }

    var n = cleanRaw.toLowerCase();
    var th = Math.round(panel.Thickness);
    var w = Math.round(panel.ContourWidth);
    var h = Math.round(panel.ContourHeight);
    var minDim = (w < h) ? w : h;

    // 1. Тонкие листовые детали (ДВП / ХДФ 3..5 мм)
    if (th >= 2 && th <= 5) {
        if (n.indexOf("дно") >= 0 && n.indexOf("ящ") >= 0) return "Дно ящика";
        return "Стенка задняя";
    }
    // 2. Распознавание по ключевым словам
    if (n.indexOf("крышк") >= 0) return "Крышка верхняя";
    if (n.indexOf("столешн") >= 0) return "Столешница";
    if (n.indexOf("дно") >= 0) return (n.indexOf("ящ") >= 0) ? "Дно ящика" : "Дно нижнее";
    if (n.indexOf("боков") >= 0) {
        if (n.indexOf("лев") >= 0) return "Боковина левая";
        if (n.indexOf("прав") >= 0) return "Боковина правая";
        return (panel.GabMin.x < (Model.GMin.x + Model.GMax.x) * 0.35) ? "Боковина левая" : "Боковина правая";
    }
    if (n.indexOf("перегород") >= 0) return "Перегородка вертикальная";
    if (n.indexOf("вязк") >= 0) return "Вязка горизонтальная";
    if (n.indexOf("полка") >= 0) return stripTrailingAutoDigits(cleanRaw);
    if (n.indexOf("стенк") >= 0) return stripTrailingAutoDigits(cleanRaw);
    if (n.indexOf("царг") >= 0) return stripTrailingAutoDigits(cleanRaw);
    if (n.indexOf("планк") >= 0 || n.indexOf("цокол") >= 0) return "Планка цокольная";
    if (n.indexOf("фасад") >= 0 || n.indexOf("двер") >= 0) return stripTrailingAutoDigits(cleanRaw) || "Фасад";

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
    return stripTrailingAutoDigits(cleanRaw) || "Деталь";
}

function getPanelGeometrySignature(panel, partName) {
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
        partName,
        Math.round(panel.ContourWidth * 10),
        Math.round(panel.ContourHeight * 10),
        Math.round(panel.Thickness * 10),
        buttSig.join(","),
        "C" + cutCount
    ].join("|");
}

function detectPanelUnitCode(panel, rawPos, defaultUnit) {
    // Если штатная иерархическая расстановка позиций вернула "01.002" (деталь внутри Сборочной единицы 01)
    if (rawPos && rawPos.indexOf(".") > 0) {
        var parts = rawPos.split(".");
        var u = parseInt(parts[0], 10);
        if (!isNaN(u) && u > 0) {
            return padNum(u, 2);
        }
    }
    return defaultUnit;
}

function formatByTemplate(tpl, baseCode, unitCode, posNumStr, partName) {
    var s = tpl || "%A.%U.%P";
    s = s.replace(/%A/g, baseCode);
    s = s.replace(/%U/g, unitCode);
    s = s.replace(/%P/g, posNumStr);
    s = s.replace(/%N/g, partName || "");
    // Убираем возможные двойные точки, если %U пустой
    s = s.replace(/\.+/g, ".").replace(/^\.|\.$/g, "");
    return s;
}

btnRun.OnClick = function() {
    Undo.RecursiveChanging(Model);

    var rawInputCode = (pCode.Value || "889.00.000").replace(/^\s+|\s+$/g, "");
    var baseCode     = extractBaseProductCode(rawInputCode);
    var tpl          = (pTemplate.Value || "%A.%U.%P").replace(/^\s+|\s+$/g, "");
    var defaultUnit  = (pUnit.Value || "00").replace(/^\s+|\s+$/g, "");
    var digitsCount  = (pDigits.ItemIndex === 1) ? 2 : 3;
    var nameModeIdx  = pNameMode.ItemIndex;
    var orderVal     = (pOrder.Value || "").replace(/^\s+|\s+$/g, "");

    // Сохраняем выбранный шаблон в INI, чтобы он всегда открывался по умолчанию
    saveIniConfig({
        template: tpl,
        defaultUnit: defaultUnit,
        digitsMode: pDigits.ItemIndex,
        nameMode: nameModeIdx,
        lastCode: rawInputCode,
        lastOrder: orderVal
    });

    // Записываем базовый шифр изделия в Параметры изделия (Article.Code и Префикс обозначения)
    Article.Code = baseCode;
    Article.ShortSign = baseCode;
    if (orderVal) {
        Article.OrderName = orderVal;
        Article.OrderCode = orderVal;
    }

    // Вызываем штатную расстановку позиций БАЗИС для поиска идентичных деталей и подсборок
    try {
        ArrangePositions(FurnPositionMode.All, Model);
    } catch (e) {}

    var groupMap = {};
    var unitCounters = {};
    var totalPanels = 0;
    var sampleFirst = "";
    var sampleLast  = "";

    Model.forEachPanel(function(p) {
        if (!p) return;
        totalPanels++;
        StartEditing(p);

        var finalName = resolveGostPanelName(p.Name, p, nameModeIdx);
        p.Name = finalName;

        // Нормализуем толщину кромки (0.4 мм и 2.0 мм)
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
        var unitCode = detectPanelUnitCode(p, rawPos, defaultUnit);
        var sig = getPanelGeometrySignature(p, finalName);
        var key = unitCode + "|" + (rawPos ? ("POS_" + rawPos + "_" + sig) : ("SIG_" + sig));

        if (!groupMap[key]) {
            if (!unitCounters[unitCode]) unitCounters[unitCode] = 1;
            var idx = unitCounters[unitCode]++;
            var posStr = padNum(idx, digitsCount);
            var fullCipher = formatByTemplate(tpl, baseCode, unitCode, posStr, finalName);
            // Позиция внутри изделия (%P для штампа %A.%P и бирки SK1):
            var relPos = (tpl.indexOf("%U") >= 0 && unitCode !== "") ? (unitCode + "." + posStr) : posStr;
            groupMap[key] = {
                relPos: relPos,
                fullCipher: fullCipher,
                posStr: posStr
            };
        }

        var info = groupMap[key];
        p.ArtPos = info.relPos;
        p.Designation = info.fullCipher;
        p.Build();

        if (!sampleFirst) sampleFirst = info.fullCipher + " — " + finalName;
        sampleLast = info.fullCipher + " — " + finalName;
    });

    Action.Commit();
    alert(
        "Децимальные шифры деталей успешно заполнены по шаблону!\n\n" +
        "Базовый шифр изделия (%A): " + baseCode + "\n" +
        "Шаблон децимального номера: " + tpl + "\n" +
        "Обработано деталей: " + totalPanels + "\n" +
        "Первая деталь: " + sampleFirst + "\n" +
        "Последняя деталь: " + sampleLast + "\n\n" +
        "Обозначения и наименования записаны для штампа чертежа, спецификации, бирки и ведомостей раскроя."
    );
    Action.Finish();
};

Action.Continue();