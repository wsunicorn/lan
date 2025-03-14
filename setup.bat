@echo off
chcp 65001 > nul
title Cài đặt Ứng dụng

:: Chuyển đến thư mục chứa script
cd /d "%~dp0"

:: Kiểm tra và yêu cầu quyền Admin
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :start
) else (
    echo =============================================
    echo    YÊU CẦU QUYỀN QUẢN TRỊ (ADMINISTRATOR)
    echo =============================================
    echo.
    echo Script này cần quyền Administrator để cài đặt.
    echo Vui lòng chạy lại với quyền Administrator.
    echo.
    pause
    exit /b 1
)

:start
cls
echo =============================================
echo         CHƯƠNG TRÌNH CÀI ĐẶT TỰ ĐỘNG
echo =============================================
echo.

:: Kiểm tra thư mục hiện tại
echo Thư mục hiện tại: %CD%
echo.

:: Kiểm tra file app.py trước khi tiếp tục
if not exist "app.py" (
    echo [LỖI] Không tìm thấy file app.py trong thư mục hiện tại!
    echo Vui lòng đảm bảo bạn đang chạy script trong thư mục chứa ứng dụng.
    echo.
    pause
    exit /b 1
)

:: Tạo thư mục tạm
set "TEMP_DIR=%TEMP%\python_setup"
mkdir "%TEMP_DIR%" 2>nul

:: Tải Python
echo Đang tải Python 3.11.8...
powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe', '%TEMP_DIR%\python_installer.exe')"
if errorlevel 1 (
    echo [LỖI] Không thể tải Python! Vui lòng kiểm tra kết nối internet.
    goto :cleanup
)

:: Cài đặt Python
echo.
echo Đang cài đặt Python...
"%TEMP_DIR%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1
if errorlevel 1 (
    echo [LỖI] Không thể cài đặt Python!
    goto :cleanup
)

:: Cập nhật PATH
echo.
echo Đang cập nhật PATH...
set "PATH=%PATH%;C:\Program Files\Python311;C:\Program Files\Python311\Scripts"
setx PATH "%PATH%" /M

:: Đợi system refresh
timeout /t 5 /nobreak > nul

:: Xóa môi trường ảo cũ nếu tồn tại
if exist "venv" (
    echo Đang xóa môi trường ảo cũ...
    rmdir /s /q "venv"
)

:: Tạo môi trường ảo mới
echo.
echo Đang tạo môi trường ảo...
python -m venv venv
if errorlevel 1 (
    echo [LỖI] Không thể tạo môi trường ảo!
    goto :cleanup
)

:: Kích hoạt môi trường ảo
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [LỖI] Không thể kích hoạt môi trường ảo!
    goto :cleanup
)

:: Cài đặt các gói cần thiết
echo.
echo Đang cài đặt các thư viện...
python -m pip install --upgrade pip
python -m pip install flask flask-sqlalchemy flask-login werkzeug

:: Tạo cấu trúc thư mục
if not exist "instance" mkdir instance
if not exist "static\uploads" mkdir static\uploads

cls
echo =============================================
echo             CÀI ĐẶT HOÀN TẤT!
echo =============================================
echo.
echo THÔNG TIN ĐĂNG NHẬP:
echo - Username: admin
echo - Password: admin123
echo.
echo Đang khởi động ứng dụng...
echo.
echo Truy cập: http://localhost:5000
echo.
echo LƯU Ý: KHÔNG ĐÓNG CỬA SỔ NÀY!
echo.

python app.py

:cleanup
:: Dọn dẹp
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
pause
exit /b