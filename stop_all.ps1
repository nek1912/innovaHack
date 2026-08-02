# Agent Finance - Stop All Services
$ports = @(8181, 8000, 3000)
foreach ($port in $ports) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
      Select-Object -ExpandProperty OwningProcess -Unique |
      ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
}
Stop-Process -Name "cloudflared" -Force -ErrorAction SilentlyContinue
# `next dev` runs as node.exe, so kill by command line too
Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
  Where-Object { $_.CommandLine -like "*agent-finance*" -and $_.CommandLine -like "*next*" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Write-Host "All services stopped" -ForegroundColor Yellow
