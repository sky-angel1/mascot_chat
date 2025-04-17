@echo off
REM Pythonのパスを確認し、適切な環境を設定してください
REM 例: C:\Python39\python.exe
set PYTHON_PATH=python

REM スクリプトのディレクトリに移動
cd /d c:\Users\poco\private_pro\mascot_chat

REM mascot_system_v5.py を実行
%PYTHON_PATH% mascot_system_v5.py

REM 実行後に一時停止
pause