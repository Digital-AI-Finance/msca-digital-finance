# PowerShell script to create a Windows Task Scheduler task for monthly sync
# Run this script as Administrator

$TaskName = "MSCA-Digital-Finance-Monthly-Sync"
$TaskPath = "\Digital-Finance\"
$ScriptPath = "D:\Joerg\Research\slides\MSCA_Digital_Finance\msca-digital-finance\scripts\run_monthly_sync.bat"

# Create the task action
$Action = New-ScheduledTaskAction -Execute $ScriptPath

# Create monthly trigger (first day of each month at 3:00 AM)
$Trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At 3:00AM

# Create task settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

# Register the task
Register-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Action $Action -Trigger $Trigger -Settings $Settings -Description "Monthly sync of digital-finance-msca.com website content" -RunLevel Highest

Write-Host "Task created successfully!"
Write-Host "Task Name: $TaskName"
Write-Host "Schedule: First day of each month at 3:00 AM"
Write-Host ""
Write-Host "To test the task manually, run:"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName' -TaskPath '$TaskPath'"
Write-Host ""
Write-Host "To view the task:"
Write-Host "  Get-ScheduledTask -TaskName '$TaskName'"
