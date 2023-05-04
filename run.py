import os
import sys
import subprocess

# Disabling output buffering so that the status window can be updated in real time
os.environ['PYTHONUNBUFFERED'] = '1'

print('Starting WhisperWriter...')
subprocess.run([sys.executable, os.path.join('src', 'main.py')])
