@echo off
REM Script to create virtual environment and install dependencies

echo Creating virtual environment using Python 3.12...
"C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe" -m venv venv

REM Check if Scripts or bin folder exists
if exist venv\Scripts\python.exe (
    set PYTHON=venv\Scripts\python.exe
) else (
    set PYTHON=venv\bin\python.exe
)

echo.
echo Upgrading pip...
call %PYTHON% -m pip install --upgrade pip

echo.
echo Installing dependencies from requirements.txt...
call %PYTHON% -m pip install -r requirements.txt

echo.
echo Installing imageio-ffmpeg (includes ffmpeg binary)...
call %PYTHON% -m pip install imageio-ffmpeg

echo.
echo ============================================
echo Virtual environment setup complete!
echo ============================================
echo.
echo To activate the virtual environment manually, run:
echo     call venv\Scripts\activate.bat
echo or:
echo     call venv\bin\activate.bat
echo.
echo To run python with the virtual environment:
echo     %PYTHON% your_script.py
echo.


