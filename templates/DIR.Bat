@echo off
REM ============================================================================
REM GUST Bot Enhanced - Template Modularization Setup
REM ============================================================================
REM This batch file creates the complete directory structure and placeholder
REM files for modularizing the enhanced_dashboard.html template.
REM 
REM Place this file in the templates/ folder and run it to create the
REM complete modular structure as documented in the modularization guide.
REM ============================================================================

echo.
echo ========================================================================
echo  🚀 GUST Bot Enhanced - Template Modularization Setup
echo ========================================================================
echo.
echo Creating modular template structure...
echo.

REM Check if we're in the templates directory
if not exist "enhanced_dashboard.html" (
    echo ❌ ERROR: enhanced_dashboard.html not found!
    echo    This script should be run from the templates/ directory
    echo    where enhanced_dashboard.html is located.
    echo.
    pause
    exit /b 1
)

echo ✅ Found enhanced_dashboard.html - proceeding with setup...
echo.

REM ============================================================================
REM Create Base Directory Structure
REM ============================================================================

echo 📁 Creating base directories...

if not exist "base" mkdir base
if not exist "components" mkdir components
if not exist "views" mkdir views
if not exist "scripts" mkdir scripts
if not exist "partials" mkdir partials

echo    ✓ base/
echo    ✓ components/
echo    ✓ views/
echo    ✓ scripts/
echo    ✓ partials/
echo.

REM ============================================================================
REM Create Base Template Files
REM ============================================================================

echo 📄 Creating base template files...

REM base/layout.html
echo ^<!-- Base HTML Layout Structure --^> > "base\layout.html"
echo ^<head^> >> "base\layout.html"
echo     ^<meta charset="UTF-8"^> >> "base\layout.html"
echo     ^<meta name="viewport" content="width=device-width, initial-scale=1.0"^> >> "base\layout.html"
echo     ^<title^>GUST Bot - Enhanced with Live Console (FIXED)^</title^> >> "base\layout.html"
echo     ^<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet"^> >> "base\layout.html"
echo ^</head^> >> "base\layout.html"

REM base/sidebar.html
echo ^<!-- Navigation Sidebar Component --^> > "base\sidebar.html"
echo ^<div class="w-64 bg-gray-800 p-4 overflow-y-auto"^> >> "base\sidebar.html"
echo     ^<!-- Sidebar content will be moved here --^> >> "base\sidebar.html"
echo ^</div^> >> "base\sidebar.html"

REM base/styles.html
echo ^<!-- CSS Styles and Animations --^> > "base\styles.html"
echo ^<style^> >> "base\styles.html"
echo     /* All CSS styling will be moved here */ >> "base\styles.html"
echo ^</style^> >> "base\styles.html"

echo    ✓ base/layout.html
echo    ✓ base/sidebar.html  
echo    ✓ base/styles.html
echo.

REM ============================================================================
REM Create Component Template Files
REM ============================================================================

echo 🧩 Creating component template files...

REM Component templates
echo ^<!-- Individual Server Card Component --^> > "components\server_card.html"
echo ^<!-- Console Message Formatting Component --^> > "components\console_message.html"
echo ^<!-- Status Indicator Component --^> > "components\status_indicator.html"
echo ^<!-- Loading Spinner Component --^> > "components\loading_spinner.html"
echo ^<!-- Confirmation Modal Component --^> > "components\confirmation_modal.html"

echo    ✓ components/server_card.html
echo    ✓ components/console_message.html
echo    ✓ components/status_indicator.html
echo    ✓ components/loading_spinner.html
echo    ✓ components/confirmation_modal.html
echo.

REM ============================================================================
REM Create View Template Files
REM ============================================================================

echo 👁️ Creating view template files...

REM View templates
echo ^<!-- Dashboard View Content --^> > "views\dashboard.html"
echo ^<div id="dashboard-view" class="view"^> >> "views\dashboard.html"
echo     ^<h2 class="text-3xl font-bold mb-6"^>📊 Dashboard^</h2^> >> "views\dashboard.html"
echo     ^<!-- Dashboard content will be moved here --^> >> "views\dashboard.html"
echo ^</div^> >> "views\dashboard.html"

echo ^<!-- Server Manager View Content --^> > "views\server_manager.html"
echo ^<div id="server-manager-view" class="view hidden"^> >> "views\server_manager.html"
echo     ^<h2 class="text-3xl font-bold mb-6"^>🖥️ Server Manager^</h2^> >> "views\server_manager.html"
echo     ^<!-- Server manager content will be moved here --^> >> "views\server_manager.html"
echo ^</div^> >> "views\server_manager.html"

echo ^<!-- Console View Content --^> > "views\console.html"
echo ^<div id="console-view" class="view hidden"^> >> "views\console.html"
echo     ^<h2 class="text-3xl font-bold mb-6"^>🔧 Console ^& Live Monitor^</h2^> >> "views\console.html"
echo     ^<!-- Console content will be moved here --^> >> "views\console.html"
echo ^</div^> >> "views\console.html"

echo ^<!-- Events View Content --^> > "views\events.html"
echo ^<div id="events-view" class="view hidden"^> >> "views\events.html"
echo     ^<h2 class="text-3xl font-bold mb-6"^>🎯 Events^</h2^> >> "views\events.html"
echo     ^<!-- Events content will be moved here --^> >> "views\events.html"
echo ^</div^> >> "views\events.html"

echo ^<!-- Economy View Content --^> > "views\economy.html"
echo ^<div id="economy-view" class="view hidden"^> >> "views\economy.html"
echo     ^<h2 class="text-3xl font-bold mb-6"^>💰 Economy^</h2^> >> "views\economy.html"
echo     ^<!-- Economy content will be moved here --^> >> "views\economy.html"
echo ^</div^> >> "views\economy.html"

echo ^<!-- Gambling View Content --^> > "views\gambling.html"
echo ^<div id="gambling-view" class="view hidden"^> >> "views\gambling.html"
echo     ^<h2 class="text-3xl font-bold mb-6"^>🎰 Gambling^</h2^> >> "views\gambling.html"
echo     ^<!-- Gambling content will be moved here --^> >> "views\gambling.html"
echo ^</div^> >> "views\gambling.html"

echo ^<!-- Clans View Content --^> > "views\clans.html"
echo ^<div id="clans-view" class="view hidden"^> >> "views\clans.html"
echo     ^<h2 class="text-3xl font-bold mb-6"^>🛡️ Clans^</h2^> >> "views\clans.html"
echo     ^<!-- Clans content will be moved here --^> >> "views\clans.html"
echo ^</div^> >> "views\clans.html"

echo ^<!-- User Management View Content --^> > "views\user_management.html"
echo ^<div id="bans-view" class="view hidden"^> >> "views\user_management.html"
echo     ^<h2 class="text-3xl font-bold mb-6"^>🚫 User Management^</h2^> >> "views\user_management.html"
echo     ^<!-- User management content will be moved here --^> >> "views\user_management.html"
echo ^</div^> >> "views\user_management.html"

echo    ✓ views/dashboard.html
echo    ✓ views/server_manager.html
echo    ✓ views/console.html
echo    ✓ views/events.html
echo    ✓ views/economy.html
echo    ✓ views/gambling.html
echo    ✓ views/clans.html
echo    ✓ views/user_management.html
echo.

REM ============================================================================
REM Create Script Template Files
REM ============================================================================

echo 📜 Creating script template files...

REM Script templates
echo ^<!-- Core JavaScript Functionality --^> > "scripts\main.js.html"
echo ^<script^> >> "scripts\main.js.html"
echo     // Core initialization and shared utilities >> "scripts\main.js.html"
echo     // Tab switching functionality >> "scripts\main.js.html"
echo ^</script^> >> "scripts\main.js.html"

echo ^<!-- Dashboard JavaScript --^> > "scripts\dashboard.js.html"
echo ^<script^> >> "scripts\dashboard.js.html"
echo     // Dashboard-specific functionality >> "scripts\dashboard.js.html"
echo ^</script^> >> "scripts\dashboard.js.html"

echo ^<!-- Server Manager JavaScript --^> > "scripts\server_manager.js.html"
echo ^<script^> >> "scripts\server_manager.js.html"
echo     // Server management functionality >> "scripts\server_manager.js.html"
echo ^</script^> >> "scripts\server_manager.js.html"

echo ^<!-- Console JavaScript --^> > "scripts\console.js.html"
echo ^<script^> >> "scripts\console.js.html"
echo     // Console and WebSocket functionality >> "scripts\console.js.html"
echo ^</script^> >> "scripts\console.js.html"

echo ^<!-- Events JavaScript --^> > "scripts\events.js.html"
echo ^<script^> >> "scripts\events.js.html"
echo     // Event management functionality >> "scripts\events.js.html"
echo ^</script^> >> "scripts\events.js.html"

echo ^<!-- Economy JavaScript --^> > "scripts\economy.js.html"
echo ^<script^> >> "scripts\economy.js.html"
echo     // Economy system functionality >> "scripts\economy.js.html"
echo ^</script^> >> "scripts\economy.js.html"

echo ^<!-- Gambling JavaScript --^> > "scripts\gambling.js.html"
echo ^<script^> >> "scripts\gambling.js.html"
echo     // Gambling games functionality >> "scripts\gambling.js.html"
echo ^</script^> >> "scripts\gambling.js.html"

echo ^<!-- Clans JavaScript --^> > "scripts\clans.js.html"
echo ^<script^> >> "scripts\clans.js.html"
echo     // Clan management functionality >> "scripts\clans.js.html"
echo ^</script^> >> "scripts\clans.js.html"

echo ^<!-- User Management JavaScript --^> > "scripts\user_management.js.html"
echo ^<script^> >> "scripts\user_management.js.html"
echo     // User administration functionality >> "scripts\user_management.js.html"
echo ^</script^> >> "scripts\user_management.js.html"

echo    ✓ scripts/main.js.html
echo    ✓ scripts/dashboard.js.html
echo    ✓ scripts/server_manager.js.html
echo    ✓ scripts/console.js.html
echo    ✓ scripts/events.js.html
echo    ✓ scripts/economy.js.html
echo    ✓ scripts/gambling.js.html
echo    ✓ scripts/clans.js.html
echo    ✓ scripts/user_management.js.html
echo.

REM ============================================================================
REM Create Partial Template Files
REM ============================================================================

echo 🧱 Creating partial template files...

REM Partial templates
echo ^<!-- Reusable Form Components --^> > "partials\form_components.html"
echo ^<!-- Input fields, selects, buttons with consistent styling --^> >> "partials\form_components.html"

echo ^<!-- Button Group Components --^> > "partials\button_groups.html"
echo ^<!-- Action button groups and toolbar components --^> >> "partials\button_groups.html"

echo ^<!-- Table Components --^> > "partials\table_components.html"
echo ^<!-- Table headers, rows, and pagination elements --^> >> "partials\table_components.html"

echo ^<!-- Notification Toast Template --^> > "partials\notification_toast.html"
echo ^<!-- Success/error notification templates --^> >> "partials\notification_toast.html"

echo    ✓ partials/form_components.html
echo    ✓ partials/button_groups.html
echo    ✓ partials/table_components.html
echo    ✓ partials/notification_toast.html
echo.

REM ============================================================================
REM Create Documentation Files
REM ============================================================================

echo 📚 Creating documentation files...

REM Create README for the modular structure
echo # GUST Bot Enhanced - Modular Templates > "MODULAR_README.md"
echo. >> "MODULAR_README.md"
echo This directory contains the modular template structure for GUST Bot Enhanced. >> "MODULAR_README.md"
echo. >> "MODULAR_README.md"
echo ## Directory Structure: >> "MODULAR_README.md"
echo - **base/**: Core layout, sidebar, and styling components >> "MODULAR_README.md"
echo - **components/**: Reusable UI components >> "MODULAR_README.md"
echo - **views/**: Main content views for each tab >> "MODULAR_README.md"
echo - **scripts/**: JavaScript functionality by feature area >> "MODULAR_README.md"
echo - **partials/**: Common form elements and UI patterns >> "MODULAR_README.md"
echo. >> "MODULAR_README.md"
echo ## Next Steps: >> "MODULAR_README.md"
echo 1. Move content from enhanced_dashboard.html to appropriate modular files >> "MODULAR_README.md"
echo 2. Update enhanced_dashboard.html to use includes >> "MODULAR_README.md"
echo 3. Test each component independently >> "MODULAR_README.md"
echo 4. Verify complete functionality after modularization >> "MODULAR_README.md"

echo    ✓ MODULAR_README.md
echo.

REM ============================================================================
REM Create Backup of Original File
REM ============================================================================

echo 💾 Creating backup of original template...

if exist "enhanced_dashboard.html" (
    copy "enhanced_dashboard.html" "enhanced_dashboard_BACKUP_%date:~-4,4%%date:~-10,2%%date:~-7,2%.html" >nul 2>&1
    echo    ✓ enhanced_dashboard_BACKUP_%date:~-4,4%%date:~-10,2%%date:~-7,2%.html
) else (
    echo    ⚠️ Original enhanced_dashboard.html not found for backup
)
echo.

REM ============================================================================
REM Summary and Next Steps
REM ============================================================================

echo ========================================================================
echo  ✅ MODULAR TEMPLATE SETUP COMPLETE!
echo ========================================================================
echo.
echo 📊 Created Structure:
echo    • 5 directories (base, components, views, scripts, partials)
echo    • 25 template files ready for content migration
echo    • 1 documentation file with next steps
echo    • 1 backup of original enhanced_dashboard.html
echo.
echo 🎯 Next Steps:
echo    1. Follow the modularization guide to move content
echo    2. Update enhanced_dashboard.html to use includes
echo    3. Test each component after migration
echo    4. Verify all functionality works correctly
echo.
echo 📖 Documentation:
echo    • Read MODULAR_README.md for detailed guidance
echo    • Follow the modularization documentation
echo    • Test thoroughly after each migration step
echo.
echo 🚀 Happy Modularizing!
echo ========================================================================
echo.
pause