"""
Smart Launcher for NovaStock Inventory & Sales Management System.
Automatically locates the correct Python environment (Python 3.11/3.12/3.13)
and starts the Flask server.
"""

import os
import sys
import subprocess
import webbrowser
import time

def find_python():
    """Finds Python interpreter with flask installed."""
    candidates = ["py -3.11", "python3", "python", "py"]
    for cmd in candidates:
        try:
            res = subprocess.run(
                f"{cmd} -c \"import flask, pandas, matplotlib; print('OK')\"",
                shell=True,
                capture_output=True,
                text=True
            )
            if "OK" in res.stdout:
                return cmd
        except Exception:
            continue
    return sys.executable

def main():
    port = int(os.environ.get("PORT", 5000))
    current_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 60)
    print("⚡ NovaStock - Inventory & Sales Management System")
    print(f">> Starting server on port {port}...")
    print(f">> Local URL: http://127.0.0.1:{port}")
    print(f">> Network URL: http://0.0.0.0:{port}")
    print(f">> Presentation: http://127.0.0.1:{port}/presentation")
    print("=" * 60)

    # Change to current directory
    os.chdir(current_dir)
    sys.path.insert(0, current_dir)

    from app import app
    app.run(host="0.0.0.0", port=port, debug=False)

if __name__ == "__main__":
    main()
