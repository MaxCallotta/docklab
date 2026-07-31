param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000
)

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

Write-Host "[1/2] 启动 FastAPI 后端 (http://${Host}:${Port})"
Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","app.main:app","--host",$Host,"--port",$Port -WorkingDirectory $Backend -WindowStyle Hidden

Write-Host "[2/2] 启动 Vite 前端 (http://localhost:5173)"
Set-Location $Frontend
npm run dev
