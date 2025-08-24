# Claude Code Status Monitor
# PowerShell script for real-time status display

function Update-ClaudeStatus {
    Clear-Host
    Write-Host "🔋 T:$(Get-ClaudeTokens) | $:$(Get-ClaudeCost) | ⌛️$(Get-ClaudeTime) | Usage:$(Get-ClaudeUsage)%" -ForegroundColor Green
    Write-Host "Press Ctrl+C to exit" -ForegroundColor Gray
}

function Get-ClaudeTokens {
    try {
        $result = claude-statusbar 2>$null
        if ($result) {
            if ($result -match "T:(\d+)") {
                return $matches[1]
            }
        }
        return "N/A"
    } catch {
        return "N/A"
    }
}

function Get-ClaudeCost {
    try {
        $result = claude-statusbar 2>$null
        if ($result) {
            if ($result -match "\$(\d+\.\d+)/") {
                return "$($matches[1])"
            }
        }
        return "N/A"
    } catch {
        return "N/A"
    }
}

function Get-ClaudeTime {
    try {
        $result = claude-statusbar 2>$null
        if ($result) {
            if ($result -match "⌛️(\d+h \d+m)") {
                return $matches[1]
            }
        }
        return "N/A"
    } catch {
        return "N/A"
    }
}

function Get-ClaudeUsage {
    try {
        $result = claude-statusbar 2>$null
        if ($result) {
            if ($result -match "Usage:(\d+)%") {
                return $matches[1]
            }
        }
        return "N/A"
    } catch {
        return "N/A"
    }
}

# Main loop
Write-Host "Starting Claude Code Status Monitor..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to exit" -ForegroundColor Gray

try {
    while ($true) {
        Update-ClaudeStatus
        Start-Sleep -Seconds 5  # Update every 5 seconds
    }
} catch {
    Write-Host "`nStatus monitor stopped." -ForegroundColor Yellow
}