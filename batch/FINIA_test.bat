@echo off

cd C:\Code\FINIA
REM create a time string based file name
set LOG=%date:~10,4%%date:~4,2%%date:~7,2%-%time:~0,2%-%time:~3,2%-%time:~6,2%.log
REM replace spaces with '0'
set LOG=%LOG: =0%

pytest C:\Code\Python\DeviceRegression\tests\pytest_FINIA_sanity.py >  %LOG%
REM pytest C:\Code\Python\DeviceRegression\tests\pytest_FINIA_sanity.py

echo -----------
if %ERRORLEVEL% neq 0 (
	echo FINIA sanity tests failed with error level %ERRORLEVEL%
	ren %LOG% Fail-%LOG%
) ELSE (
	echo FINIA sanity tests passed!
)
