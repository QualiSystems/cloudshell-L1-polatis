# -*- mode: python -*-

block_cipher = None

import os

CS_L1_NETCORE = "../cloudshell-L1-networking-core"

def add_data_files(related_path, root_path="."):

    path = os.path.join(root_path, related_path)
    templates = []
    for resp_temp_file in os.listdir(path):
        templates.append((os.path.join(related_path, resp_temp_file),
                          os.path.join(path, resp_temp_file),
                          "DATA"))
    return templates

a = Analysis(['main.py'],
             pathex=[".", CS_L1_NETCORE, "../cloudshell-core"],
             binaries=None,
             datas=[],
             hiddenimports=[
                "common.cli.tcp_session",
                "common.cli.telnet_session",
                "common.cli.console_session",
                "common.cli.ssh_session",
                "polatis.polatis_driver_handler"
             ],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries + add_data_files("configuration") + add_data_files("common/response_template", CS_L1_NETCORE) ,
          a.zipfiles,
          a.datas,
          name='Polatis',
          debug=False,
          strip=None,
          upx=True,
          console=True,
          version='version.txt',
          icon=os.path.join(CS_L1_NETCORE, "img/icon.ico")
          )
