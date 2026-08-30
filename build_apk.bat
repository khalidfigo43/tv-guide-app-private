@echo off
chcp 65001 >nul
echo ======================================================================
echo           TV GUIDE - ANDROID APK BUILDER (STANDALONE)
echo ======================================================================
echo.

rem 1. Locate Java JDK 17
if exist "C:\Program Files\Java\jdk-17" (
    set "JAVA_HOME=C:\Program Files\Java\jdk-17"
) else if defined JAVA_HOME (
    rem use existing
) else (
    echo [!] JAVA_HOME is not set. Please ensure Java 17 is installed.
)

set "PATH=%JAVA_HOME%\bin;%PATH%"

echo [*] Using Java:
java -version
echo.

rem 2. Set Android SDK environment
set "ANDROID_HOME=%~dp0android\sdk"
set "ANDROID_SDK_ROOT=%~dp0android\sdk"
set "PATH=%ANDROID_HOME%\cmdline-tools\latest\bin;%PATH%"

rem 3. Navigate to android folder and build APK
cd /d "%~dp0android"
echo [*] Building Android APK (assembleDebug)...
call gradlew.bat assembleDebug

if %ERRORLEVEL% equ 0 (
    echo.
    echo ======================================================================
    echo  [SUCCESS] Android APK built successfully!
    echo ======================================================================
    echo.
    echo Your APK file is ready at:
    echo   %~dp0android\app\build\outputs\apk\debug\app-debug.apk
    echo.
    pause
) else (
    echo.
    echo [ERROR] Build failed. Please check the error messages above.
    echo.
    pause
)

