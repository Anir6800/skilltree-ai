# SkillTree AI — PostgreSQL backup (run BEFORE migration / cutover)
# Usage:  .\scripts\backup_postgres.ps1
# Requires: pg_dump on PATH. Reads DATABASE_URL from environment or .env.
#
# Produces a timestamped logical dump you can restore with pg_restore.

$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $PSScriptRoot "..\_backups"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$dbUrl = $env:DATABASE_URL
if (-not $dbUrl) {
    Write-Host "DATABASE_URL not set in env." -ForegroundColor Yellow
    Write-Host "If you are on the default SQLite dev DB, just copy backend/db.sqlite3 instead:" -ForegroundColor Yellow
    Write-Host "  Copy-Item db.sqlite3 _backups\db_$stamp.sqlite3" -ForegroundColor Yellow
    $sqlite = Join-Path $PSScriptRoot "..\db.sqlite3"
    if (Test-Path $sqlite) {
        Copy-Item $sqlite (Join-Path $backupDir "db_$stamp.sqlite3")
        Write-Host "SQLite snapshot saved to _backups\db_$stamp.sqlite3" -ForegroundColor Green
    }
    exit 0
}

$outFile = Join-Path $backupDir "skilltree_pg_$stamp.dump"
Write-Host "Dumping PostgreSQL to $outFile ..." -ForegroundColor Cyan
# -Fc = custom format (compressed, restorable with pg_restore)
& pg_dump --dbname=$dbUrl -Fc -f $outFile
Write-Host "Backup complete: $outFile" -ForegroundColor Green
Write-Host "Restore with:  pg_restore --clean --dbname=`$env:DATABASE_URL $outFile" -ForegroundColor Cyan
