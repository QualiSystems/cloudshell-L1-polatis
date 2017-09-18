set driver_exe="PolatisPython.exe"
set datamodel_xml="polatis_datamodel.xml"
set config_json="polatis_python_runtime_configuration.json"

@echo off
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ok
) else (
    echo This program must be run from an administrator cmd prompt
    goto :end
)
@echo on

pip install pyinstaller
pip install cloudshell-core
pip install requests
pip install paramiko


@rem Build driver EXE

mkdir dist
pyinstaller --onefile driver.spec


@rem Populate release directory

mkdir release
copy %datamodel_xml%    release\
copy dist\%driver_exe%  release\
copy %config_json%      release\


@rem Install the driver EXE on the current machine

taskkill /f /im %driver_exe%
timeout 3

set driverdir="c:\Program Files (x86)\QualiSystems\CloudShell\Server\Drivers"
IF EXIST %driverdir% GOTO :havecs
set driverdir="c:\Program Files (x86)\QualiSystems\TestShell\Server\Drivers"
:havecs

copy dist\%driver_exe%  %driverdir%
copy %config_json%      %driverdir%


:end
