@echo off
chcp 65001 >nul
title GupkaScribe Studio — Автономный запуск

echo ========================================================
echo   🎙️ GupkaScribe Studio — Проверка и запуск окружения
echo ========================================================
echo.

:: 1. Проверяем наличие uv в системном PATH
where uv >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] Обнаружен пакетный менеджер uv.
    echo [INFO] Синхронизация зависимостей и запуск студии...
    uv run python app_gui.py
    goto :end
)

:: 2. Если uv нет в PATH, проверяем стандартные пути установки uv
if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
    echo [OK] Найден uv в каталоге .cargo.
    uv run python app_gui.py
    goto :end
)
if exist "%USERPROFILE%\.local\bin\uv.exe" (
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
    echo [OK] Найден uv в каталоге .local.
    uv run python app_gui.py
    goto :end
)

:: 3. Если uv не установлен, проверяем наличие системного Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ОШИБКА] На компьютере не найден Python или uv.
    echo.
    echo Для работы программы установите Python 3.12+ (https://www.python.org/downloads/)
    echo или установите uv: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    pause
    exit /b 1
)

:: 4. Попытка быстрой автоустановки uv через PowerShell
echo [INFO] Пакетный менеджер uv не обнаружен. Пробуем быструю автоустановку uv...
powershell -ExecutionPolicy ByPass -Command "try { irm https://astral.sh/uv/install.ps1 | iex; exit 0 } catch { exit 1 }" >nul 2>nul
if %errorlevel% equ 0 (
    set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"
    where uv >nul 2>nul
    if %errorlevel% equ 0 (
        echo [OK] uv успешно установлен автоматически!
        uv run python app_gui.py
        goto :end
    )
)

:: 5. Fallback на стандартный python venv
echo [INFO] Использование системного Python для создания изолированного окружения...
if not exist ".venv" (
    echo [INFO] Создание виртуального окружения .venv...
    python -m venv .venv
)

echo [INFO] Проверка и установка зависимостей из requirements.txt...
.venv\Scripts\pip install -r requirements.txt
echo [INFO] Запуск GupkaScribe Studio...
.venv\Scripts\python app_gui.py

:end
if %errorlevel% neq 0 (
    echo.
    echo [ВНИМАНИЕ] Программа завершилась с кодом ошибки: %errorlevel%
    pause
)
