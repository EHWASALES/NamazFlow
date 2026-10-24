"""Build without resolving native libraries from unrelated apps on the host PATH."""

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def main():
    if sys.platform != "win32":
        raise SystemExit("Windows build requires Windows")
    env = os.environ.copy()
    windows = Path(env["WINDIR"])
    env["PATH"] = os.pathsep.join(
        map(
            str,
            (
                Path(sys.executable).parent,
                Path(sys.base_prefix),
                windows / "System32",
                windows,
            ),
        )
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/make_windows_icon.py")],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--windowed",
            "--onefile",
            "--add-data",
            "namazflow/fonts;namazflow/fonts",
            "--add-data",
            "namazflow/assets;namazflow/assets",
            "--icon",
            "assets/namazflow.ico",
            "--name",
            "NamazFlow",
            "main.py",
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )
    # An import/startup failure must fail the build, not be shipped as an installer.
    subprocess.run(
        [str(ROOT / "dist/NamazFlow.exe"), "--smoke-test"],
        cwd=ROOT,
        env=env,
        timeout=40,
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


if __name__ == "__main__":
    main()
