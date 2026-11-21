"""Đóng gói một commit thành bản Chợ Nổi chạy cục bộ, dùng Python stdlib và Git."""

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "cho-noi/"
REQUIRED = (
    "README.md", "LICENSE", "CREDITS.md", "game.contract.json", "chonoi/live.py",
    "chonoi/web/index.html", "chonoi/web/game.css", "chonoi/web/navigation.css",
    "chonoi/web/river.js", "chonoi/web/cafe.js", "chonoi/web/scene.js",
    "chonoi/web/field.js", "chonoi/web/map.js", "chonoi/web/forage.js",
    "chonoi/web/service.js", "chonoi/web/flow.js", "chonoi/web/flow.css", "chonoi/web/forage.css",
    "chonoi/web/vendor/three.module.min.js", "chonoi/web/vendor/three.core.min.js",
    "chonoi/web/vendor/LICENSE",
)


def package(revision, destination):
    commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", "--end-of-options", revision + "^{commit}"],
        cwd=ROOT, text=True,
    ).strip()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".zip", delete=False) as fp:
        temporary = Path(fp.name)
    try:
        subprocess.run(["git", "archive", "--format=zip", "--prefix=" + PREFIX,
                        "-o", str(temporary), commit], cwd=ROOT, check=True)
        with ZipFile(temporary) as archive:
            entries = set(archive.namelist())
            missing = [name for name in REQUIRED if PREFIX + name not in entries]
            if missing:
                raise ValueError("Thiếu tệp bàn giao: " + ", ".join(missing))
            if archive.comment.decode("ascii") != commit or archive.testzip() is not None:
                raise ValueError("ZIP không khớp commit hoặc kiểm CRC thất bại.")
        digest = hashlib.sha256()
        with temporary.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        os.replace(temporary, destination)
        print(f"{commit}  {destination}\nSHA-256  {digest.hexdigest()}")
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revision", help="Commit hoặc ref Git đã có ở máy này")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        package(args.revision, args.out.resolve())
    except (OSError, subprocess.CalledProcessError, ValueError, BadZipFile) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
