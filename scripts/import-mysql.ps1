param(
  [Parameter(Mandatory = $true)]
  [string]$SqlPath
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $SqlPath)) { throw "SQL file not found: $SqlPath" }

$mysqlBin = 'D:\phpStudy\MySQL\bin'
$mysqlExe = Join-Path $mysqlBin 'mysql.exe'
if (-not (Test-Path -LiteralPath $mysqlExe)) { throw "mysql.exe not found at $mysqlExe" }

$hostName = if ($env:MYSQL_HOST) { $env:MYSQL_HOST } else { '127.0.0.1' }
$port = if ($env:MYSQL_PORT) { $env:MYSQL_PORT } else { '3306' }
$user = if ($env:MYSQL_USER) { $env:MYSQL_USER } else { 'root' }
if (-not $env:MYSQL_PWD -and $env:MYSQL_PASSWORD) { $env:MYSQL_PWD = $env:MYSQL_PASSWORD }

Get-Content -LiteralPath $SqlPath -Raw | & $mysqlExe --host=$hostName --port=$port --user=$user --default-character-set=utf8mb4
if ($LASTEXITCODE -ne 0) { throw "mysql import failed with exit code $LASTEXITCODE" }
Write-Output "Imported $SqlPath"
