@echo off
chcp 65001 >nul
echo ====================================
echo   Life Manager - نصب برنامه
echo ====================================
echo.
python --version >nul 2>&1
if errorlevel 1 ( echo [ERROR] Python پیدا نشد. & pause & exit /b 1 )
echo [1/3] نصب وابستگی‌ها...
pip install -r requirements.txt --quiet
if errorlevel 1 ( echo [ERROR] خطا در نصب. & pause & exit /b 1 )
echo [2/3] ساخت پوشه‌ها...
for %%d in (data\backups\daily data\backups\weekly data\backups\monthly data\backups\manual data\logs) do (
    if not exist "%%d" mkdir "%%d"
)
echo [3/3] نصب کامل شد!
echo برای اجرا: python main.py
pause
