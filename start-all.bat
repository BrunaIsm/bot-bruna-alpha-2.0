@echo off
cls
echo ================================================
echo    BOT BRUNA ALPHA - SERVIDOR COMPLETO
echo ================================================
echo.

cd /D "%~dp0"

echo Iniciando Backend (Flask)...
start "Backend - Flask API" /MIN cmd /k "cd api && python run_simple.py"

echo Aguardando 3 segundos...
timeout /t 3 /nobreak >nul

echo Iniciando Frontend (Vite)...
start "Frontend - Vite React" cmd /k "npm run dev"

echo.
echo ================================================
echo   SERVIDORES INICIADOS!
echo ================================================
echo   Backend:  http://localhost:5000
echo   Frontend: http://localhost:8080
echo ================================================
echo.
echo Duas janelas CMD foram abertas.
echo Feche as janelas CMD para parar os servidores.
echo.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul
