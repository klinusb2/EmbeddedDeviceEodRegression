@echo off
cd C:\Code\test

REM execute test script
python C:\Code\Python\test\test.py

echo -----------
if %ERRORLEVEL% neq 0 (
	echo Python script failed with error level %ERRORLEVEL%
) ELSE (
	echo Python script successfully completed
)