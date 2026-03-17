@echo off
REM ============================================================
REM install_windows.bat — Cài đặt Right-click Context Menu trên Windows
REM Thêm "Chuyển MD sang DOCX" vào menu chuột phải cho file .md
REM ============================================================
REM Chạy với quyền Administrator!

echo.
echo ============================================================
echo   md2docx — Cài đặt Right-click Menu (Windows)
echo ============================================================
echo.

REM Lấy đường dẫn thư mục script
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Kiểm tra Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python chưa được cài. Cài từ python.org
    pause
    exit /b 1
)

REM Kiểm tra dependencies
echo [1/3] 📦 Kiểm tra dependencies...
pip show python-docx >nul 2>&1
if %errorlevel% neq 0 (
    echo    Đang cài python-docx...
    pip install -r "%SCRIPT_DIR%\requirements.txt" -q
)
echo    ✅ Dependencies OK

REM Tạo wrapper batch file
echo [2/3] 📝 Tạo wrapper script...
(
echo @echo off
echo cd /d "%%~dp1"
echo python "%SCRIPT_DIR%\convert_to_docx.py" "%%~1"
echo if %%errorlevel%% equ 0 (
echo     echo.
echo     echo ✅ Đã tạo: "%%~dpn1.docx"
echo ^) else (
echo     echo.
echo     echo ❌ Lỗi chuyển đổi!
echo ^)
echo pause
) > "%SCRIPT_DIR%\md2docx.bat"
echo    ✅ Tạo md2docx.bat

REM Thêm Registry entries
echo [3/3] 🔧 Thêm vào Registry (cần quyền Admin)...

REM Cho file .md
reg add "HKEY_CLASSES_ROOT\.md\shell\md2docx" /ve /d "Chuyển MD sang DOCX" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\.md\shell\md2docx" /v "Icon" /d "shell32.dll,1" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\.md\shell\md2docx\command" /ve /d "\"%SCRIPT_DIR%\md2docx.bat\" \"%%1\"" /f >nul 2>&1

if %errorlevel% neq 0 (
    echo.
    echo    ⚠️  Cần chạy với quyền Administrator!
    echo    Click phải vào file này → Run as administrator
    pause
    exit /b 1
)

REM Cho file .markdown
reg add "HKEY_CLASSES_ROOT\.markdown\shell\md2docx" /ve /d "Chuyển MD sang DOCX" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\.markdown\shell\md2docx" /v "Icon" /d "shell32.dll,1" /f >nul 2>&1
reg add "HKEY_CLASSES_ROOT\.markdown\shell\md2docx\command" /ve /d "\"%SCRIPT_DIR%\md2docx.bat\" \"%%1\"" /f >nul 2>&1

echo    ✅ Registry đã cập nhật

echo.
echo ============================================================
echo   ✅ CÀI ĐẶT HOÀN TẤT!
echo.
echo   Cách dùng:
echo   1. Click phải vào file .md trong File Explorer
echo   2. Chọn: "Chuyển MD sang DOCX"
echo   3. File .docx sẽ được tạo tại cùng thư mục
echo.
echo   ⚠️  Cần cài sẵn: Python, Pandoc, mmdc, d2
echo ============================================================
echo.
pause
