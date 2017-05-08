# -*- mode: python -*-

block_cipher = None

import os

def add_data_files(related_path, root_path="."):

    path = os.path.join(root_path, related_path)
    templates = []
    for resp_temp_file in os.listdir(path):
        templates.append((os.path.join(related_path, resp_temp_file),
                          os.path.join(path, resp_temp_file),
                          "DATA"))
    return templates

a = Analysis(['main.py'],
             pathex=["."],
             binaries=None,
             datas=[],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None,
             excludes=None,
             win_no_prefer_redirects=None,
             win_private_assemblies=None,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='PolatisPython',
          debug=False,
          strip=None,
          upx=True,
          console=True,
          version='version.txt',
          icon="img/icon.ico"
          )
