# Stripe CLI Setup Script
# Purpose: Find stripe.exe and add to PATH, then login

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Stripe CLI Setup Assistant" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Find stripe.exe
Write-Host "[1/4] Searching for stripe.exe..." -ForegroundColor Yellow

$commonPaths = @(
    "$env:USERPROFILE\Downloads",
    "$env:USERPROFILE\Desktop",
    "C:\stripe",
    "C:\tools\stripe",
    "C:\Program Files\stripe",
    "$env:LOCALAPPDATA\stripe"
)

$stripePath = $null

foreach ($path in $commonPaths) {
    if (Test-Path $path) {
        $found = Get-ChildItem -Path $path -Filter stripe.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $stripePath = $found.FullName
            Write-Host "Found: $stripePath" -ForegroundColor Green
            break
        }
    }
}

if (-not $stripePath) {
    Write-Host "stripe.exe not found in common locations" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please enter the full path to stripe.exe:" -ForegroundColor Yellow
    Write-Host "Example: C:\stripe\stripe.exe" -ForegroundColor Gray
    $stripePath = Read-Host "Path"
    
    if (-not (Test-Path $stripePath)) {
        Write-Host "File does not exist: $stripePath" -ForegroundColor Red
        exit 1
    }
}

$stripeDir = Split-Path $stripePath -Parent
Write-Host "Stripe directory: $stripeDir" -ForegroundColor Gray
Write-Host ""

# Step 2: Check if already in PATH
Write-Host "[2/4] Checking PATH environment variable..." -ForegroundColor Yellow

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -like "*$stripeDir*") {
    Write-Host "Stripe directory already in PATH" -ForegroundColor Green
} else {
    Write-Host "Adding Stripe directory to PATH..." -ForegroundColor Yellow
    
    $newPath = $currentPath + ";" + $stripeDir
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    
    Write-Host "Added to PATH (User level)" -ForegroundColor Green
    Write-Host "Please restart PowerShell for PATH to take effect" -ForegroundColor Yellow
    Write-Host ""
    
    # Temporarily add to current session
    $env:Path += ";$stripeDir"
    Write-Host "Temporarily added to current session PATH" -ForegroundColor Green
}

Write-Host ""

# Step 3: Verify installation
Write-Host "[3/4] Verifying Stripe CLI..." -ForegroundColor Yellow

try {
    $version = & "$stripePath" --version 2>&1
    Write-Host "Stripe CLI version: $version" -ForegroundColor Green
} catch {
    Write-Host "Cannot run Stripe CLI: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 4: Login prompt
Write-Host "[4/4] Ready to login to Stripe..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Next step: stripe login" -ForegroundColor Cyan
Write-Host "Please follow the prompts:" -ForegroundColor Yellow
Write-Host "  1. Press Enter to open browser" -ForegroundColor Gray
Write-Host "  2. Login to Stripe account in browser" -ForegroundColor Gray
Write-Host "  3. Confirm pairing code" -ForegroundColor Gray
Write-Host ""
$confirm = Read-Host "Press Enter to continue, or 'q' to skip login"

if ($confirm -ne 'q') {
    Write-Host ""
    Write-Host "Starting login process..." -ForegroundColor Cyan
    & "$stripePath" login
} else {
    Write-Host "Skipped login. You can run 'stripe login' later" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. If PATH was updated, restart PowerShell" -ForegroundColor Gray
Write-Host "  2. Run: stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe/" -ForegroundColor Gray
Write-Host "  3. Copy the whsec_*** secret to .env file" -ForegroundColor Gray
Write-Host ""
