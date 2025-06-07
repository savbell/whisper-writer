#!/usr/bin/env python3
"""
CUDA Compatibility Checker for WhisperWriter

This script helps users identify their CUDA version and provides recommendations
for the appropriate CTranslate2 version to ensure compatibility with faster-whisper.

Usage: python check_cuda_compatibility.py
"""

import subprocess
import sys
import re
from typing import Optional, Tuple

def get_cuda_version() -> Optional[Tuple[int, int]]:
    """
    Detect the installed CUDA version.
    
    Returns:
        Tuple of (major, minor) version numbers, or None if CUDA not found
    """
    try:
        # Try nvidia-smi first
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Look for CUDA Version: X.Y in nvidia-smi output
            match = re.search(r'CUDA Version: (\d+)\.(\d+)', result.stdout)
            if match:
                return (int(match.group(1)), int(match.group(2)))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    try:
        # Try nvcc --version as fallback
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Look for release X.Y in nvcc output
            match = re.search(r'release (\d+)\.(\d+)', result.stdout)
            if match:
                return (int(match.group(1)), int(match.group(2)))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return None

def get_cudnn_version() -> Optional[str]:
    """
    Try to detect cuDNN version (limited detection capability).
    
    Returns:
        cuDNN version string if detectable, None otherwise
    """
    try:
        import ctranslate2
        # If ctranslate2 is installed, try to get version info
        return "Detected via ctranslate2 installation"
    except ImportError:
        pass
    
    return None

def get_ctranslate2_recommendation(cuda_version: Optional[Tuple[int, int]]) -> str:
    """
    Get CTranslate2 version recommendation based on CUDA version.
    
    Args:
        cuda_version: Tuple of (major, minor) CUDA version
        
    Returns:
        Recommendation string with installation command
    """
    if cuda_version is None:
        return """
🔍 CUDA not detected or not available.
📦 Recommendation: Use CPU-only installation
   Command: pip install ctranslate2
   Note: Will use CPU for inference (slower but compatible)
"""
    
    major, minor = cuda_version
    
    if major >= 12:
        return f"""
🎯 CUDA {major}.{minor} detected
📦 Recommendation: Latest CTranslate2 (supports CUDA 12 + cuDNN 9)
   Command: pip install ctranslate2>=4.5.0
   
   If you encounter issues, try:
   - For cuDNN 8: pip install ctranslate2==4.4.0
   - For older compatibility: pip install ctranslate2==4.2.1
"""
    
    elif major == 11:
        return f"""
⚠️  CUDA {major}.{minor} detected (older version)
📦 Recommendation: Compatible CTranslate2 for CUDA 11
   Command: pip install ctranslate2==3.24.0
   
   Note: This is the last version supporting CUDA 11
   Consider upgrading to CUDA 12 for latest features
"""
    
    else:
        return f"""
❌ CUDA {major}.{minor} detected (unsupported)
📦 Recommendation: Upgrade CUDA or use CPU-only
   - Upgrade to CUDA 11+ for GPU support
   - Or use CPU: pip install ctranslate2 (CPU-only)
"""

def check_current_installation():
    """Check current installation status of relevant packages."""
    packages = ['ctranslate2', 'faster-whisper', 'openai']
    print("📋 Current Installation Status:")
    print("=" * 40)
    
    for package in packages:
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'show', package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                version_line = next((line for line in lines if line.startswith('Version:')), None)
                if version_line:
                    version = version_line.split(': ')[1]
                    print(f"✅ {package}: {version}")
                else:
                    print(f"✅ {package}: installed (version unknown)")
            else:
                print(f"❌ {package}: not installed")
        except Exception as e:
            print(f"❌ {package}: error checking ({str(e)})")
    print()

def main():
    """Main function to check CUDA compatibility and provide recommendations."""
    print("🔧 WhisperWriter CUDA Compatibility Checker")
    print("=" * 50)
    print()
    
    # Check current installation
    check_current_installation()
    
    # Detect CUDA version
    print("🔍 Detecting CUDA Installation...")
    cuda_version = get_cuda_version()
    
    if cuda_version:
        print(f"✅ CUDA {cuda_version[0]}.{cuda_version[1]} detected")
    else:
        print("❌ CUDA not detected or not available")
    
    print()
    
    # Get recommendation
    recommendation = get_ctranslate2_recommendation(cuda_version)
    print("💡 Recommendations:")
    print(recommendation)
    
    # Additional notes
    print("📝 Additional Notes:")
    print("=" * 20)
    print("• For best performance, use the latest compatible versions")
    print("• If you encounter 'libcudnn' errors, check your cuDNN installation")
    print("• CPU-only mode is always available as a fallback")
    print("• Check the WhisperWriter README for detailed installation instructions")
    print()
    
    print("🚀 To update your installation:")
    print("1. Backup your current environment")
    print("2. Run the recommended pip install command above")
    print("3. Test with: python -c 'import ctranslate2; print(ctranslate2.__version__)'")

if __name__ == "__main__":
    main() 