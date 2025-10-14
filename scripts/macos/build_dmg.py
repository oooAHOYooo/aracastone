#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    dist = root / "dist"
    app = dist / "ArcaStone.app"
    dmg = dist / "ArcaStone.dmg"
    if not app.exists():
        print(f"App not found: {app}. Build the .app first.", file=sys.stderr)
        return 1
    # Ensure dmgbuild is installed
    try:
        import dmgbuild  # type: ignore # noqa: F401
    except Exception:
        print("Installing dmgbuild...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "dmgbuild"])

    settings = f"""
application = "{app}"
format = "UDZO"
files = [application]
symlinks = {{'Applications': '/Applications'}}
icon_size = 128
window_rect = ((200, 120), (600, 400))
background = None
"""
    settings_path = dist / "dmg_settings.py"
    settings_path.write_text(settings, encoding="utf-8")

    import dmgbuild  # type: ignore

    dmgbuild.build_dmg(str(dmg), "ArcaStone", settings_file=str(settings_path))
    print(f"Created: {dmg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


