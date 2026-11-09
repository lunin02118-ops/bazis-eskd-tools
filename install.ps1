# ============================================================================
# Установщик инструментария и конфигурации БАЗИС 2021 (ГОСТ / ЕСКД / Раскрой / ЧПУ / Бирка)
# Автоматически адаптирует пути под текущего пользователя Windows ($env:USERPROFILE)
# ============================================================================

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetAppData = Join-Path $env:APPDATA "Bazis"
$TargetDocs    = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Bazis"
$BackupDir     = Join-Path $TargetAppData ("Backup_" + (Get-Date -Format "yyyyMMdd_HHmmss"))

Write-Host "=== Установка инструментария БАЗИС 2021 (ГОСТ / ЕСКД) ===" -ForegroundColor Cyan
Write-Host "Профиль пользователя: $env:USERPROFILE"
Write-Host "Папка настроек AppData: $TargetAppData"
Write-Host "Папка документов Bazis: $TargetDocs"

# 1. Создание резервной копии текущих настроек
if (Test-Path $TargetAppData) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Get-ChildItem -Path $TargetAppData -Filter "*.xml" -File -ErrorAction SilentlyContinue | ForEach-Object {
        Copy-Item $_.FullName -Destination $BackupDir -Force
    }
    Write-Host "[OK] Резервная копия текущих XML сохранена в: $BackupDir" -ForegroundColor Green
}

# 2. Создание целевых директорий
$dirsToCreate = @(
    $TargetAppData,
    (Join-Path $TargetAppData "CutSettings"),
    $TargetDocs,
    (Join-Path $TargetDocs "Scripts"),
    (Join-Path $TargetDocs "Шаблоны бирки"),
    (Join-Path $TargetDocs "Файлы для ЧПУ\MPR"),
    "C:\SawTransfer\B200\labels"
)
foreach ($d in $dirsToCreate) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
    }
}

$cp1251 = [System.Text.Encoding]::GetEncoding(1251)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$SourceUserPath = "C:\Users\VladimirWorkPC"
$CurrentUserPath = $env:USERPROFILE

# 3. Установка скриптов F9 / F10 (в кодировке Windows-1251 для БАЗИС 2021)
Get-ChildItem -Path (Join-Path $RepoRoot "scripts\cp1251") -File | ForEach-Object {
    $dest = Join-Path $TargetDocs "Scripts\$($_.Name)"
    $content = [System.IO.File]::ReadAllText($_.FullName, $cp1251)
    $content = $content.Replace($SourceUserPath, $CurrentUserPath)
    $content = $content.Replace(($SourceUserPath -replace "\\", "\\\\"), ($CurrentUserPath -replace "\\", "\\\\"))
    [System.IO.File]::WriteAllText($dest, $content, $cp1251)
}
Write-Host "[OK] Установлены скрипты F9 / F10 и шаблон децимальных номеров (cipher_template.ini)" -ForegroundColor Green

# 4. Установка конфигураций AppData\Roaming\Bazis
Get-ChildItem -Path (Join-Path $RepoRoot "config\appdata") -File | ForEach-Object {
    $dest = Join-Path $TargetAppData $_.Name
    if ($_.Extension -match "\.(xml|cfg)$") {
        $text = [System.IO.File]::ReadAllText($_.FullName, [System.Text.Encoding]::UTF8)
        $text = $text.Replace($SourceUserPath, $CurrentUserPath)
        [System.IO.File]::WriteAllText($dest, $text, $utf8NoBom)
    } else {
        Copy-Item $_.FullName -Destination $dest -Force
    }
}

Get-ChildItem -Path (Join-Path $RepoRoot "config\appdata\CutSettings") -File | ForEach-Object {
    $dest = Join-Path $TargetAppData "CutSettings\$($_.Name)"
    $text = [System.IO.File]::ReadAllText($_.FullName, [System.Text.Encoding]::UTF8)
    $text = $text.Replace($SourceUserPath, $CurrentUserPath)
    [System.IO.File]::WriteAllText($dest, $text, $utf8NoBom)
}
Write-Host "[OK] Установлены конфигурации БАЗИС-Мебельщик, Шкаф, Раскрой, ЧПУ и Выпуск чертежей ГОСТ" -ForegroundColor Green

# 5. Установка шаблонов бирок, справочника наименований ГОСТ и профилей ЧПУ/раскроя
Copy-Item -Path (Join-Path $RepoRoot "config\documents\Наименования_деталей_ГОСТ.ish") -Destination (Join-Path $TargetDocs "Наименования_деталей_ГОСТ.ish") -Force

$cutCfgSrc = Join-Path $RepoRoot "config\documents\Holzma_CadLink3_SAWTEQ_B200.cutconfig"
$cutCfgDst = Join-Path $TargetDocs "Holzma_CadLink3_SAWTEQ_B200.cutconfig"
$cutCfgTxt = [System.IO.File]::ReadAllText($cutCfgSrc, [System.Text.Encoding]::UTF8).Replace($SourceUserPath, $CurrentUserPath)
[System.IO.File]::WriteAllText($cutCfgDst, $cutCfgTxt, $utf8NoBom)

Get-ChildItem -Path (Join-Path $RepoRoot "config\documents\Шаблоны бирки") -Filter "*.brx" -File | ForEach-Object {
    $dest1 = Join-Path $TargetDocs "Шаблоны бирки\$($_.Name)"
    $dest2 = Join-Path $TargetDocs $_.Name
    $brxTxt = [System.IO.File]::ReadAllText($_.FullName, [System.Text.Encoding]::UTF8).Replace($SourceUserPath, $CurrentUserPath)
    [System.IO.File]::WriteAllText($dest1, $brxTxt, $utf8NoBom)
    [System.IO.File]::WriteAllText($dest2, $brxTxt, $utf8NoBom)
}

Copy-Item -Path (Join-Path $RepoRoot "config\documents\Файлы для ЧПУ\*") -Destination (Join-Path $TargetDocs "Файлы для ЧПУ\") -Recurse -Force
Write-Host "[OK] Установлены шаблоны этикеток Pioneer RP310 (100x50), справочник ГОСТ и профили ЧПУ" -ForegroundColor Green

Write-Host ""
Write-Host "=== Установка успешно завершена! ===" -ForegroundColor Cyan
Write-Host "Горячие клавиши в БАЗИС-Мебельщик 2021:"
Write-Host "  F9  — Смена цвета ЛДСП, парных кромок (2.0 / 0.4 мм) и номера заказа в 1 клик"
Write-Host "  F10 — Заполнение децимальных номеров деталей по шаблону (%A.%U.%P) и наименований ГОСТ"
