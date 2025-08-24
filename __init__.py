import subprocess
import sys
import os

# Track if we've already tried installing requirements this session
_requirements_installed = False

def install_requirements():
    """Auto-install requirements from requirements.txt - one time per session"""
    global _requirements_installed
    
    if _requirements_installed:
        return
    
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        try:
            print("📦 Installing YTDL node requirements...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", requirements_path, 
                "--quiet", "--disable-pip-version-check"
            ])
            print("✅ YTDL requirements installed successfully!")
            _requirements_installed = True
        except Exception as e:
            print(f"⚠️  Could not install requirements: {e}")
            print("💡 You may need to manually install: pip install yt-dlp ffmpeg-python")
    else:
        print("⚠️  requirements.txt not found in YTDL nodes folder")

# Try to install requirements on first load
try:
    install_requirements()
except Exception as e:
    print(f"Requirements installation failed: {e}")

# Import the actual nodes
try:
    from .ytdl_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    __all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
    print("✅ YTDL nodes loaded successfully!")
except Exception as e:
    print(f"❌ Failed to import YTDL nodes: {e}")
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}
