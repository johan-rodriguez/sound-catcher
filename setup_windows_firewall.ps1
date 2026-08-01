# Windows PowerShell script to configure firewall rules for Sound Catcher network streaming.
# Run as Administrator.

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Sound Catcher Windows Firewall Configuration  " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

try {
    New-NetFirewallRule -DisplayName "SoundCatcher TCP" -Direction Inbound -Protocol TCP -LocalPort 50005 -Action Allow -ErrorAction Stop
    Write-Host "[OK] Inbound TCP Rule on Port 50005 created successfully!" -ForegroundColor Green
} catch {
    Write-Host "[!] TCP Rule already exists or notice: $_" -ForegroundColor Yellow
}

try {
    New-NetFirewallRule -DisplayName "SoundCatcher UDP" -Direction Inbound -Protocol UDP -LocalPort 50005 -Action Allow -ErrorAction Stop
    Write-Host "[OK] Inbound UDP Rule on Port 50005 created successfully!" -ForegroundColor Green
} catch {
    Write-Host "[!] UDP Rule already exists or notice: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[OK] Done! Port 50005 is now open for network audio streaming." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
pause
