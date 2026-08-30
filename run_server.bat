@echo off
chcp 65001 >nul
title TV Guide Server - دليل التلفزيون
echo ========================================================
echo        جاري تشغيل خادم دليل التلفزيون الفضائي
echo ========================================================
echo.
echo افتح المتصفح على الرابط التالي:
echo http://localhost:8000
echo.
echo للإنهاء أو إيقاف السيرفر: اضغط Ctrl + C
echo ========================================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
)

pause

