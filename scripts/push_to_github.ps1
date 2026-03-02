<#
Push to GitHub helper script
Usage: Run this script from PowerShell in the project root or provide full path.
This script will:
 - Check for Git
 - Optionally configure user.name and user.email (local)
 - Initialize repo if needed
 - Add, commit, and push to provided remote URL

Note: You must have created the GitHub repo at https://github.com/sabs-titan/ransom beforehand.
#>

param(
    [string]$RemoteUrl = "https://github.com/sabs-titan/ransom.git",
    [string]$CommitMessage = "Initial commit: Ransomware detection system with ML models and GUI",
    [string]$UserName = "sabs-titan",
    [string]$UserEmail = "your.email@example.com"
)

function Abort([string]$msg){
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}

# Ensure running from project root (where this script lives)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir
Set-Location ..

# Check Git
try{
    & git --version | Out-Null
}catch{
    Abort "Git not found. Install Git from https://git-scm.com/download/win and re-run this script."
}

Write-Host "Git detected." -ForegroundColor Green

# Optionally configure local git user
Write-Host "Configuring local git user (this will set local repo config, not global)."
& git config user.name "$UserName"
& git config user.email "$UserEmail"

# Initialize repository if not already
if (-not (Test-Path ".git")){
    Write-Host "Initializing new git repository..."
    & git init
} else {
    Write-Host "Existing git repository found." -ForegroundColor Yellow
}

# Add .gitignore if missing
if (-not (Test-Path ".gitignore")){
    Write-Host "No .gitignore found, creating default .gitignore..."
    @("__pycache__/", "*.pyc", "models/", "data/", "data_large/", "*.pkl") | Out-File -Encoding utf8 .gitignore
}

# Stage files
Write-Host "Staging files..."
& git add .

# Commit
# If there are no changes to commit, skip
$status = & git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)){
    Write-Host "No changes to commit." -ForegroundColor Yellow
} else {
    & git commit -m $CommitMessage
}

# Set branch to main
& git branch -M main 2>$null

# Add or update remote
$existingRemote = & git remote
if ($existingRemote -contains "origin"){
    Write-Host "Updating existing origin to $RemoteUrl"
    & git remote set-url origin $RemoteUrl
} else {
    Write-Host "Adding remote origin $RemoteUrl"
    & git remote add origin $RemoteUrl
}

# Push
Write-Host "Pushing to GitHub (origin/main). You may be prompted for credentials..."
try{
    & git push -u origin main
    Write-Host "Push completed." -ForegroundColor Green
}catch{
    Write-Host "Push failed. If this is the first push, ensure the remote repository exists and your credentials are correct." -ForegroundColor Red
}

Write-Host "Done. Visit $RemoteUrl to verify the repository." -ForegroundColor Cyan
