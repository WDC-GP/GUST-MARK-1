# GUST_BOT Project Analysis Script
# Run this from your GUST-MARK-1 directory

Write-Host "🔍 GUST_BOT Project Analysis Starting..." -ForegroundColor Green

# 1. CREATE BACKUP
$backupDir = "GUST_BOT_BACKUP_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Host "📦 Creating backup: $backupDir" -ForegroundColor Yellow
Copy-Item -Path "." -Destination "../$backupDir" -Recurse -Force
Write-Host "✅ Backup created at ../$backupDir" -ForegroundColor Green

# 2. ANALYZE PROJECT STRUCTURE
Write-Host "`n📊 Analyzing project structure..." -ForegroundColor Yellow

# Count lines in key files
$mainApp = Get-Content "app.py" | Measure-Object -Line
$routeFiles = Get-ChildItem "routes/*.py" | ForEach-Object {
    $lines = Get-Content $_.FullName | Measure-Object -Line
    [PSCustomObject]@{
        File = $_.Name
        Lines = $lines.Lines
    }
}

Write-Host "📈 Code Analysis:"
Write-Host "  app.py: $($mainApp.Lines) lines"
$routeFiles | ForEach-Object { Write-Host "  routes/$($_.File): $($_.Lines) lines" }

# 3. IDENTIFY ROUTE PATTERNS
Write-Host "`n🔍 Analyzing route patterns..." -ForegroundColor Yellow

# Check for inline routes in app.py
$inlineRoutes = Select-String -Path "app.py" -Pattern "@app\.route" | Measure-Object
$blueprintReg = Select-String -Path "app.py" -Pattern "register_blueprint" | Measure-Object

Write-Host "📍 Route Analysis:"
Write-Host "  Inline routes in app.py: $($inlineRoutes.Count)"
Write-Host "  Blueprint registrations: $($blueprintReg.Count)"

# 4. DATABASE ANALYSIS
Write-Host "`n💾 Analyzing database usage..." -ForegroundColor Yellow

# Check for MongoDB collections
$dbCollections = Select-String -Path "*.py" -Pattern "db\." -AllMatches | 
    ForEach-Object { $_.Matches.Value } | 
    Sort-Object -Unique

Write-Host "📚 Database Collections Found:"
$dbCollections | ForEach-Object { Write-Host "  $_" }

# 5. API ENDPOINT ANALYSIS
Write-Host "`n🌐 Analyzing API endpoints..." -ForegroundColor Yellow

# Find all API routes
$apiRoutes = Select-String -Path "routes/*.py","app.py" -Pattern "@.*\.route.*api" | 
    ForEach-Object { 
        [PSCustomObject]@{
            File = Split-Path $_.Filename -Leaf
            Line = $_.Line.Trim()
        }
    }

Write-Host "🔗 API Endpoints Found: $($apiRoutes.Count)"
$apiRoutes | Group-Object File | ForEach-Object {
    Write-Host "  $($_.Name): $($_.Count) endpoints"
}

# 6. FRONTEND ANALYSIS
Write-Host "`n🎨 Analyzing frontend structure..." -ForegroundColor Yellow

$jsFiles = Get-ChildItem "static/js" -Recurse -Filter "*.js" | Measure-Object
$templates = Get-ChildItem "templates" -Recurse -Filter "*.html" | Measure-Object

Write-Host "🎯 Frontend Analysis:"
Write-Host "  JavaScript files: $($jsFiles.Count)"
Write-Host "  HTML templates: $($templates.Count)"

# 7. DEPENDENCY ANALYSIS
Write-Host "`n📦 Analyzing dependencies..." -ForegroundColor Yellow

if (Test-Path "requirements.txt") {
    $deps = Get-Content "requirements.txt" | Where-Object { $_ -and $_ -notmatch "^#" } | Measure-Object
    Write-Host "📋 Dependencies: $($deps.Count) packages"
    
    # Check for critical packages
    $criticalPackages = @("Flask", "PyMongo", "flask-socketio", "pymongo")
    $criticalPackages | ForEach-Object {
        $found = Select-String -Path "requirements.txt" -Pattern $_ -Quiet
        $status = if ($found) { "✅" } else { "❌" }
        Write-Host "  $status $_"
    }
}

# 8. GENERATE ANALYSIS REPORT
Write-Host "`n📝 Generating analysis report..." -ForegroundColor Yellow

$reportContent = @"
# GUST_BOT Project Analysis Report
Generated: $(Get-Date)

## Project Structure
- Main app: $($mainApp.Lines) lines
- Route files: $($routeFiles.Count) files
- Inline routes: $($inlineRoutes.Count)
- Blueprint registrations: $($blueprintReg.Count)

## Database Collections
$($dbCollections | ForEach-Object { "- $_" } | Out-String)

## API Endpoints
- Total API endpoints: $($apiRoutes.Count)
$($apiRoutes | Group-Object File | ForEach-Object { "- $($_.Name): $($_.Count) endpoints" } | Out-String)

## Frontend
- JavaScript files: $($jsFiles.Count)
- HTML templates: $($templates.Count)

## Next Steps
1. Review hybrid route architecture (inline + blueprints)
2. Plan database schema migration strategy
3. Design server isolation framework
4. Create development environment setup
"@

$reportContent | Out-File "PROJECT_ANALYSIS_REPORT.md" -Encoding UTF8
Write-Host "✅ Analysis report saved to PROJECT_ANALYSIS_REPORT.md" -ForegroundColor Green

Write-Host "`n🎯 Analysis Complete!" -ForegroundColor Green
Write-Host "Next: Review the report and decide on implementation approach" -ForegroundColor Cyan