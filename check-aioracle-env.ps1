Write-Host ""
Write-Host "========== AI-ORACLE ENV CHECK ==========" -ForegroundColor Cyan
Write-Host ""

# 1. VENV
Write-Host "[1] Verificando entorno virtual..." -ForegroundColor Yellow
if ($env:VIRTUAL_ENV) {
    Write-Host "  OK - VENV detectado:" $env:VIRTUAL_ENV -ForegroundColor Green
} else {
    Write-Host "  ERROR - No se detecto entorno virtual" -ForegroundColor Red
}

# 2. Python
Write-Host ""
Write-Host "[2] Verificando Python..." -ForegroundColor Yellow
try {
    python --version
} catch {
    Write-Host "  ERROR - Python no disponible" -ForegroundColor Red
}

# 3. Docker
Write-Host ""
Write-Host "[3] Verificando Docker Desktop..." -ForegroundColor Yellow
try {
    docker --version
} catch {
    Write-Host "  ERROR - Docker no instalado" -ForegroundColor Red
}

# 4. Contenedores
Write-Host ""
Write-Host "[4] Contenedores activos..." -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 5. Puerto Lilly Engine
Write-Host ""
Write-Host "[5] Verificando puerto 8001..." -ForegroundColor Yellow
Test-NetConnection -Port 8001 -ComputerName localhost | Format-List

# 6. main.py
Write-Host ""
Write-Host "[6] Verificando main.py..." -ForegroundColor Yellow
$mainPath = "lilly_engine/main.py"
if (Test-Path $mainPath) {
    Write-Host "  OK - Encontrado:" $mainPath -ForegroundColor Green
} else {
    Write-Host "  ERROR - No se encontro main.py" -ForegroundColor Red
}

# 7. FastAPI app instances
Write-Host ""
Write-Host "[7] Verificando instancias de 'app = FastAPI()'..." -ForegroundColor Yellow
$appMatches = (Select-String -Path $mainPath -Pattern "app = FastAPI").Count
Write-Host "  Instancias encontradas:" $appMatches
if ($appMatches -eq 1) {
    Write-Host "  OK - Correcto, hay una sola instancia." -ForegroundColor Green
} else {
    Write-Host "  ERROR - Hay" $appMatches "instancias." -ForegroundColor Red
}

# 8. Resumen de imports
Write-Host ""
Write-Host "[8] Imports detectados en main.py:" -ForegroundColor Yellow
Select-String -Path $mainPath -Pattern "^from "

Write-Host ""
Write-Host "========== FIN DEL DIAGNOSTICO ==========" -ForegroundColor Cyan
