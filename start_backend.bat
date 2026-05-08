@echo off
echo ========================================
echo   Alternance App - Backend (FastAPI)
echo ========================================

cd /d "%~dp0backend"

if not exist "venv" (
    echo Installation de l'environnement virtuel...
    python -m venv venv
)

call venv\Scripts\activate

echo Installation des dependances...
pip install -r requirements.txt -q

echo.
echo Demarrage du serveur backend sur http://localhost:8000
echo Documentation API disponible sur http://localhost:8000/docs
echo.

venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
