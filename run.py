import os
import sys
from pathlib import Path
import subprocess
from dotenv import load_dotenv
import glob

def set_cuda_paths():
    """Set up CUDA paths for GPU support."""
    try:
        # Find all CUDA installations in a version-agnostic way
        cuda_base_path = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
        if os.path.exists(cuda_base_path):
            # Get all v12.x folders, sorted by version number (newest first)
            cuda_versions = glob.glob(os.path.join(cuda_base_path, "v12.*"))
            cuda_versions.sort(key=lambda x: [int(n) for n in x.split('v')[1].split('.')], reverse=True)
            
            if cuda_versions:
                system_cuda_path = cuda_versions[0]  # Use the newest version
                cuda_version = os.path.basename(system_cuda_path)[1:]  # Remove 'v' prefix
                print(f'Found system CUDA version: {cuda_version}')
                
                # Use system CUDA
                paths_to_add = [
                    os.path.join(system_cuda_path, 'bin'),
                    os.path.join(system_cuda_path, 'libnvvp'),
                ]
                
                # Add cuDNN paths if present
                cudnn_path = os.path.join(system_cuda_path, 'cudnn')
                if os.path.exists(cudnn_path):
                    paths_to_add.append(os.path.join(cudnn_path, 'bin'))
                
                print(f'Using system CUDA from: {system_cuda_path}')
            else:
                print('No CUDA 12.x installation found in system')
                return check_bundled_cuda()
        else:
            print('NVIDIA CUDA Toolkit folder not found')
            return check_bundled_cuda()
            
        # Update environment variables
        env_vars = ['CUDA_PATH', f'CUDA_PATH_V{cuda_version.replace(".", "_")}', 'PATH']
        for env_var in env_vars:
            current_value = os.environ.get(env_var, '')
            new_value = os.pathsep.join(paths_to_add + [current_value] if current_value else paths_to_add)
            os.environ[env_var] = new_value
            
        print('CUDA paths set up successfully')
        
    except Exception as e:
        print(f'Error setting up CUDA paths: {e}')
        print('Falling back to CPU mode')

def check_bundled_cuda():
    """Check for bundled CUDA in virtual environment."""
    venv_base = Path(sys.executable).parent.parent
    nvidia_base_path = venv_base / 'Lib' / 'site-packages' / 'nvidia'
    
    if not nvidia_base_path.exists():
        print('No CUDA installation found (neither system nor bundled), using CPU mode')
        return
        
    cuda_path = nvidia_base_path / 'cuda_runtime' / 'bin'
    cublas_path = nvidia_base_path / 'cublas' / 'bin'
    cudnn_path = nvidia_base_path / 'cudnn' / 'bin'
    
    if not all(p.exists() for p in [cuda_path, cublas_path, cudnn_path]):
        print('Some bundled CUDA components missing, using CPU mode')
        return
        
    paths_to_add = [str(cuda_path), str(cublas_path), str(cudnn_path)]
    print('Using bundled CUDA from virtual environment')
    
    # Update environment variables
    env_vars = ['CUDA_PATH', 'CUDA_PATH_V12_4', 'PATH']
    for env_var in env_vars:
        current_value = os.environ.get(env_var, '')
        new_value = os.pathsep.join(paths_to_add + [current_value] if current_value else paths_to_add)
        os.environ[env_var] = new_value

# Set CUDA paths before anything else
set_cuda_paths()

print('Starting WhisperWriter...')
load_dotenv()
subprocess.run([sys.executable, os.path.join('src', 'main.py')])
