param(
  [Parameter(Mandatory = $true)]
  [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$mysqlBin = 'D:\phpStudy\MySQL\bin'
$dumpExe = Join-Path $mysqlBin 'mysqldump.exe'
if (-not (Test-Path -LiteralPath $dumpExe)) { throw "mysqldump.exe not found at $dumpExe" }

$database = if ($env:MYSQL_DATABASE) { $env:MYSQL_DATABASE } else { 'ailovemoney' }
$hostName = if ($env:MYSQL_HOST) { $env:MYSQL_HOST } else { '127.0.0.1' }
$port = if ($env:MYSQL_PORT) { $env:MYSQL_PORT } else { '3306' }
$user = if ($env:MYSQL_USER) { $env:MYSQL_USER } else { 'root' }
if (-not $env:MYSQL_PWD -and $env:MYSQL_PASSWORD) { $env:MYSQL_PWD = $env:MYSQL_PASSWORD }

& $dumpExe --host=$hostName --port=$port --user=$user --single-transaction --routines --events --default-character-set=utf8mb4 --databases $database | Out-File -LiteralPath $OutputPath -Encoding utf8
if ($LASTEXITCODE -ne 0) { throw "mysqldump failed with exit code $LASTEXITCODE" }
Write-Output "Exported $database to $OutputPath"
