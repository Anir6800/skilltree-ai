# SkillTree AI Development Environment Launcher
# Run this script to start all necessary services in separate windows.

$Host.UI.RawUI.WindowTitle = "SkillTree AI - Launcher"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   SkillTree AI Development Launcher" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$root = Get-Location

# Function to launch a task in a new PowerShell window
function Launch-Task {
    param (
        [string]$Title,
        [string]$Directory,
        [string]$Command
    )
    Write-Host "Launching $Title..." -ForegroundColor Green
    $FullCommand = "cd $Directory; `$Host.UI.RawUI.WindowTitle = '$Title'; $Command"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "$FullCommand"
}

Write-Host "Checking Redis connectivity..." -ForegroundColor Cyan
try {
    $redisCheck = Test-NetConnection -ComputerName localhost -Port 6379 -ErrorAction Stop
    if ($redisCheck.TcpTestSucceeded) {
        Write-Host "Redis is active." -ForegroundColor Green
    } else {
        Write-Host "WARNING: Redis is NOT reachable on port 6379. Celery and caching will fail." -ForegroundColor Red
    }
} catch {
    Write-Host "WARNING: Could not check Redis. Ensure it is running." -ForegroundColor Yellow
}

# 1. Django API
Launch-Task -Title "Django API" -Directory "backend" -Command ".\venv\Scripts\activate; python manage.py runserver"

# 2. Celery Worker
Launch-Task -Title "Celery Worker" -Directory "backend" -Command ".\venv\Scripts\activate; celery -A core worker --loglevel=info --pool=solo"

# 3. Celery Beat
Launch-Task -Title "Celery Beat" -Directory "backend" -Command ".\venv\Scripts\activate; celery -A core beat --loglevel=info"

# 4. React Frontend
Launch-Task -Title "React Frontend" -Directory "frontend" -Command "npm start"

Write-Host "`nAll processes have been launched in separate windows." -ForegroundColor Yellow
Write-Host "Happy coding!" -ForegroundColor Cyan
