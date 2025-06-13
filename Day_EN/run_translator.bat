@echo off
REM 自动切换到脚本所在目录
cd /d "%~dp0"
REM 用包方式运行 main.py
python -m Day_EN.main
pause