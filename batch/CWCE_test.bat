@echo off

cd C:\Code\CWCE
REM create a time string based file name
set LOG=%date:~10,4%%date:~4,2%%date:~7,2%-%time:~0,2%-%time:~3,2%-%time:~6,2%.log
REM replace spaces with '0'
set LOG=%LOG: =0%

pytest C:\Code\Python\DeviceRegression\tests\pytest_CWCE_sanity.py >  %LOG%
REM pytest C:\Code\Python\DeviceRegression\tests\pytest_CWCE_sanity.py

echo -----------
if %ERRORLEVEL% neq 0 (
	echo CWCE sanity tests failed with error level %ERRORLEVEL%
	ren %LOG% Fail-%LOG%
) ELSE (
	echo CWCE sanity tests passed!
)
