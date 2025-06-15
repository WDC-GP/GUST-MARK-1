@echo off
echo Creating .gitignore file...
echo.

REM Create .gitignore file with Python and project-specific ignores
echo # Python > .gitignore
echo __pycache__/ >> .gitignore
echo *.py[cod] >> .gitignore
echo *$py.class >> .gitignore
echo *.so >> .gitignore
echo .Python >> .gitignore
echo build/ >> .gitignore
echo develop-eggs/ >> .gitignore
echo dist/ >> .gitignore
echo downloads/ >> .gitignore
echo eggs/ >> .gitignore
echo .eggs/ >> .gitignore
echo lib/ >> .gitignore
echo lib64/ >> .gitignore
echo parts/ >> .gitignore
echo sdist/ >> .gitignore
echo var/ >> .gitignore
echo wheels/ >> .gitignore
echo *.egg-info/ >> .gitignore
echo .installed.cfg >> .gitignore
echo *.egg >> .gitignore
echo. >> .gitignore

echo # Virtual Environment >> .gitignore
echo venv/ >> .gitignore
echo env/ >> .gitignore
echo ENV/ >> .gitignore
echo .venv/ >> .gitignore
echo. >> .gitignore

echo # IDE >> .gitignore
echo .vscode/ >> .gitignore
echo .idea/ >> .gitignore
echo *.swp >> .gitignore
echo *.swo >> .gitignore
echo *~ >> .gitignore
echo. >> .gitignore

echo # OS >> .gitignore
echo .DS_Store >> .gitignore
echo Thumbs.db >> .gitignore
echo. >> .gitignore

echo # Logs >> .gitignore
echo *.log >> .gitignore
echo logs/ >> .gitignore
echo. >> .gitignore

echo # Environment variables >> .gitignore
echo .env >> .gitignore
echo .env.local >> .gitignore
echo .env.production >> .gitignore
echo. >> .gitignore

echo # Session files >> .gitignore
echo gp-session.json >> .gitignore
echo. >> .gitignore

echo # Sensitive data files (review these) >> .gitignore
echo data/banned_users.json >> .gitignore
echo data/tempBans.json >> .gitignore
echo. >> .gitignore

echo # Node modules (if using npm) >> .gitignore
echo node_modules/ >> .gitignore
echo. >> .gitignore

echo # Database >> .gitignore
echo *.db >> .gitignore
echo *.sqlite3 >> .gitignore

echo.
echo ✅ .gitignore file created successfully!
echo.
echo ⚠️  IMPORTANT: Review the following files before committing:
echo    - gp-session.json (contains session data)
echo    - data/banned_users.json (may contain personal data)
echo    - data/tempBans.json (may contain personal data)
echo.
echo 💡 Consider creating template versions of sensitive data files
echo    Example: banned_users.json.template
echo.
pause