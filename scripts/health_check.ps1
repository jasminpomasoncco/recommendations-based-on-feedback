param(
  [string]$BaseUrl = 'http://127.0.0.1:8000'
)

$ErrorActionPreference = 'Stop'

# Checks the /health endpoint
# Usage: .\scripts\health_check.ps1

$healthUrl = "$BaseUrl/health"
Invoke-RestMethod -Method Get -Uri $healthUrl | ConvertTo-Json
