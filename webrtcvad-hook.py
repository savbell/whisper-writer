from PyInstaller.utils.hooks import collect_dynamic_libs, get_package_paths
import os

# Get the package path
pkg_base, pkg_dir = get_package_paths('webrtcvad_wheels')

# Collect all DLL files
binaries = []
for root, dirs, files in os.walk(pkg_dir):
    for file in files:
        if file.endswith('.dll') or file.endswith('.pyd'):
            full_path = os.path.join(root, file)
            binaries.append((full_path, '.'))

hiddenimports = ['webrtcvad_wheels']