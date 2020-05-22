@echo off

cd C:\Code\CWCE
python C:\Code\Python\DeviceRegression\regr.py -s COM4 --ntp off --cpa 10.183.129.106 CWCE

echo -----------
if %ERRORLEVEL% neq 0 (
	echo Python script failed with error level %ERRORLEVEL%
) ELSE (
	echo Python script successfully completed
)