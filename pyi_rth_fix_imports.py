# pyi_rth_fix_imports.py
# PyInstaller runtime hook to fix import paths

import sys
import os

# Add the _internal directory to sys.path so relative imports work
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # We're running in a PyInstaller bundle
    bundle_dir = sys._MEIPASS
    
    # Add _internal to path if needed
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)
    
    # Ensure api, export, utils, core, mapping modules are findable
    for subdir in ['api', 'export', 'utils', 'core', 'mapping']:
        subdir_path = os.path.join(bundle_dir, subdir)
        if os.path.exists(subdir_path) and subdir_path not in sys.path:
            sys.path.insert(0, subdir_path)
