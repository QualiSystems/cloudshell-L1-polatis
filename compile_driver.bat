@echo off
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ok
) else (
    echo This program must be run from an administrator cmd prompt
    goto :fail
)

@echo on

pyinstaller --onefile driver.spec

taskkill /f /im PolatisPython.exe

sleep 3

set driverdir="c:\Program Files (x86)\QualiSystems\CloudShell\Server\Drivers"
IF EXIST %driverdir% GOTO :havecs
set driverdir="c:\Program Files (x86)\QualiSystems\TestShell\Server\Drivers"
:havecs

copy dist\PolatisPython.exe             %driverdir%
copy polatis_python_runtime_configuration.json %driverdir%

copy polatis_datamodel.xml               release\
copy dist\PolatisPython.exe              release\
copy polatis_python_runtime_configuration.json  release\

:fail
