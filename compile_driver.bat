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

taskkill /f /im Polatis7.exe

sleep 3

copy dist\Polatis7.exe                     "c:\Program Files (x86)\QualiSystems\TestShell\Server\Drivers"
copy polatis_runtime_configuration.json "c:\Program Files (x86)\QualiSystems\TestShell\Server\Drivers"

copy polatis_datamodel.xml               release\
copy dist\Polatis7.exe                      release\
copy polatis_runtime_configuration.json  release\

:fail
