# ============================================================================
# Скрипт сохранения (экспорта) текущих настроек и скриптов БАЗИС 2021 в репозиторий
# ============================================================================

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceAppData = Join-Path $env:APPDATA "Bazis"
$SourceDocs    = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Bazis"

$cp1251 = [System.Text.Encoding]::GetEncoding(1251)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$scriptFiles = @(
    "1_Смена_цвета_ЛДСП_и_кромки_(Типовой_заказ).js",
    "2_Расстановка_децимальных_шифров_ГОСТ.js",
    "cipher_template.ini"
)
foreach ($sf in $scriptFiles) {
    $src = Join-Path $SourceDocs "Scripts\$sf"
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination (Join-Path $RepoRoot "scripts\cp1251\$sf") -Force
        $txt = [System.IO.File]::ReadAllText($src, $cp1251)
        [System.IO.File]::WriteAllText((Join-Path $RepoRoot "scripts\utf8\$sf"), $txt, $utf8NoBom)
    }
}

Get-ChildItem -Path (Join-Path $RepoRoot "config\appdata") -File | ForEach-Object {
    $src = Join-Path $SourceAppData $_.Name
    if (Test-Path $src) { Copy-Item -Path $src -Destination $_.FullName -Force }
}
Copy-Item -Path (Join-Path $SourceAppData "CutSettings\*.xml") -Destination (Join-Path $RepoRoot "config\appdata\CutSettings\") -Force
Copy-Item -Path (Join-Path $SourceDocs "Наименования_деталей_ГОСТ.ish") -Destination (Join-Path $RepoRoot "config\documents\Наименования_деталей_ГОСТ.ish") -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $SourceDocs "Holzma_CadLink3_SAWTEQ_B200.cutconfig") -Destination (Join-Path $RepoRoot "config\documents\Holzma_CadLink3_SAWTEQ_B200.cutconfig") -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $SourceDocs "Шаблоны бирки\*.brx") -Destination (Join-Path $RepoRoot "config\documents\Шаблоны бирки\") -Force -ErrorAction SilentlyContinue

Write-Host "[OK] Настройки и скрипты БАЗИС 2021 успешно экспортированы в репозиторий." -ForegroundColor Green
