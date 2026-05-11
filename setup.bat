@echo off
setlocal

set PYTHON=py -3.12
set VENV_DIR=%~dp0.venv

echo Verificando Python 3.12...
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python 3.12 nao encontrado. Instale em https://python.org
    pause
    exit /b 1
)

if not exist "%VENV_DIR%" (
    echo Criando venv em .venv ...
    %PYTHON% -m venv "%VENV_DIR%"
) else (
    echo Venv ja existe, pulando criacao.
)

echo Ativando venv...
call "%VENV_DIR%\Scripts\activate.bat"

echo Instalando dependencias...
python -m pip install --upgrade pip --quiet
pip install -r "%~dp0requirements.txt"

echo.
echo ============================================================
echo  Ambiente pronto. Para ativar manualmente:
echo    .venv\Scripts\activate
echo.
echo  Para rodar o treino com CSV:
echo    python -m training.train --source csv --csv-dir "C:\AI_RESISTANCE\PRODUCAO\CSV_PI"
echo.
echo  Para iniciar o agendador:
echo    python scheduler.py
echo ============================================================
echo.

cmd /k
