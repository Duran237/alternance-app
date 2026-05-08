@echo off
echo ========================================
echo   Alternance App - Frontend (React)
echo ========================================

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo Installation des dependances npm...
    npm install
)

echo.
echo Demarrage du serveur frontend sur http://localhost:5173
echo.

npm run dev
