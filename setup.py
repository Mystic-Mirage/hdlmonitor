import distutils.util
import glob
import os.path
import zipfile

from cx_Freeze import setup, Executable

import patch

from hdlmonitor import __version__ as version


def rm_empty_subdirs(directory):
    for root, dirs, _ in os.walk(directory):
        for d in dirs:
            dr = os.path.join(root, d)
            try:
                os.rmdir(dr)
            except OSError:
                rm_empty_subdirs(dr)


name = 'hdlmonitor'
icon = '%s.ico' % name

arch = distutils.util.get_platform()
if arch == 'win-amd64':
    arch = 'win64'
target_name = '%s-%s' % (name, arch)
dist_dir = 'dist'
target = os.path.join(dist_dir, target_name)

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
    'build_exe': target,
}

setup(
    name=name,
    version=version,
    description='HDL Bus Monitor',
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

keep = [
    ['python27.dll'],
    ['hdlmonitor.exe'],
    ['hdlmonitor.ico'],
    ['tcl85.dll'],
    ['tk85.dll'],
    ['unicodedata.pyd'],
    ['_socket.pyd'],
    ['_tkinter.pyd'],
    ['microsoft.vc90.crt.manifest'],
    ['msvcr90.dll'],
    ['tcl', 'auto.tcl'],
    ['tcl', 'init.tcl'],
    ['tcl', 'tclindex'],
    ['tcl', 'encoding', '*'],
    ['tk', 'listbox.tcl'],
    ['tk', 'tk.tcl'],
    ['tk', 'ttk', 'button.tcl'],
    ['tk', 'ttk', 'combobox.tcl'],
    ['tk', 'ttk', 'entry.tcl'],
    ['tk', 'ttk', 'scrollbar.tcl'],
    ['tk', 'ttk', 'ttk.tcl'],
    ['tk', 'ttk', 'utils.tcl'],
    ['tk', 'ttk', 'wintheme.tcl'],
    ['tk', 'ttk', 'xptheme.tcl'],
]

keep_files = []
for k in keep:
    keep_files.extend(glob.glob(os.path.join(target, *k)))

print('Removing extra files...')
for root, _, files in os.walk(target):
    for f in files:
        fl = os.path.join(root, f)
        fll = fl.lower()
        if fll not in keep_files:
            os.remove(fl)
        else:
            os.rename(fl, fll)

print('Removing empty directories...')
rm_empty_subdirs(target)

print('Applying patches...')
for p in glob.glob('*.patch'):
    patchset = patch.fromfile(p)
    patchset.apply(1, target)

print('Zipping...')
os.chdir(dist_dir)
zip_name = '%s.zip' % target_name
try:
    os.remove(zip_name)
except OSError:
    pass
with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as dist_zip:
    for root, dirs, files in os.walk(target_name):
        for f in files:
            dist_zip.write(os.path.join(root, f))
