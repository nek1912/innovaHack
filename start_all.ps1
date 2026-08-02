# Agent Finance - Start All Services
# Run from D:\Innova\agent-finance

$root = "D:\Innova\agent-finance"

Write-Host "=== Starting Agent Finance ===" -ForegroundColor Cyan

# 1. OPA
Write-Host "[1/4] Starting OPA on :8181..." -ForegroundColor Yellow
Start-Process -FilePath "$root\tools\opa.exe" -ArgumentList "run --server --watch --addr=0.0.0.0:8181 $root\policy" -WindowStyle Minimized
Start-Sleep -Seconds 2

# 2. Backend
Write-Host "[2/4] Starting FastAPI on :8000..." -ForegroundColor Yellow
Start-Process -FilePath "cmd" -ArgumentList "/c cd /d $root\backend && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000" -WindowStyle Minimized
Start-Sleep -Seconds 3

# 3. Frontend
Write-Host "[3/4] Starting Next.js on :3000..." -ForegroundColor Yellow
Start-Process -FilePath "cmd" -ArgumentList "/c cd /d $root\frontend && npm run dev" -WindowStyle Minimized
Start-Sleep -Seconds 3

# 4. Tunnel (cloudflared)
Write-Host "[4/4] Starting tunnel..." -ForegroundColor Yellow
$proc = Start-Process -FilePath "cmd" -ArgumentList "/c cloudflared tunnel --url http://localhost:8000 > $root\tunnel_output.txt 2>&1" -WindowStyle Minimized -PassThru
Start-Sleep -Seconds 8

# Get tunnel URL
if (Test-Path "$root\tunnel_output.txt") {
    $content = Get-Content "$root\tunnel_output.txt" -Raw
    if ($content -match "https://[a-zA-Z0-9-]+\.trycloudflare\.com") {
        $url = $Matches[0]
        Write-Host ""
        Write-Host "=== ALL SERVICES RUNNING ===" -ForegroundColor Green
        Write-Host "OPA:       http://localhost:8181"
        Write-Host "Backend:   http://localhost:8000"
        Write-Host "Frontend:  http://localhost:3000"
        Write-Host "Webhook:   $url/webhooks/razorpay" -ForegroundColor Magenta
        Write-Host ""
        Write-Host "Paste this webhook URL in RazorpayX Dashboard > Settings > Webhooks" -ForegroundColor Cyan
    } else {
        Write-Host "Tunnel started but URL not captured yet. Check tunnel_output.txt"
    }
}
