import distutils.util
import glob
import os
import os.path
import sys
import zipfile

from cx_Freeze import setup, Executable

name = 'sblistenerng'

icon = '%s.ico' % name

build_exe_options = {
    'packages': [],
    'excludes': [
        '_ctypes',
        '_hashlib',
        '_ssl',
        '_threading_local',
        'atexit',
        'bdb',
        'bz2',
        'calendar',
        'cmd',
        'difflib',
        'dis',
        'doctest',
        'dummy_thread',
        'dummy_threading',
        'fnmatch',
        'getopt',
        'gettext',
        'hashlib',
        'inspect',
        'io',
        'locale',
        'logging',
        'opcode',
        'optparse',
        'pdb',
        'pprint',
        'random',
        'shlex',
        'ssl',
        'tempfile',
        'textwrap',
        'token',
        'tokenize',
        'unittest',
    ],
    'include_files': [
        icon,
    ],
    'compressed': True,
    'optimize': 2,
    'append_script_to_exe': True,
    'create_shared_zip': False,
    'include_in_shared_zip': False,
    'include_msvcr': True,
    'icon': icon,
}

setup(
    name=name,
    version='0.1',
    description='SmartBus Listener NG',
    options={
        'build_exe': build_exe_options,
    },
    executables=[
        Executable(
            script='%s.py' % name,
            base="Win32GUI",
        ),
    ]
)
