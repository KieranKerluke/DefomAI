# Deployment script for Suna backend
# This script will:
# 1. Commit all changes
# 2. Push to the repository
# 3. Trigger a deployment on Railway

# Get current timestamp for commit message
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Commit all changes
Write-Host "Committing changes..."
git add .
git commit -m "Fix: Token limit issues and database column name fixes - $timestamp"

# Push to repository
Write-Host "Pushing changes to repository..."
git push

Write-Host "Deployment triggered. Changes will be live in a few minutes."
Write-Host "Please check your Railway dashboard for deployment status."
