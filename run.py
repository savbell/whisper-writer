import os
import sys
import subprocess
from dotenv import load_dotenv

print('Starting WhisperWriter...')
load_dotenv()
subprocess.run([sys.executable, os.path.join('src', 'main.py')])
