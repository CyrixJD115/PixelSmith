#!/usr/bin/env python3
"""PixelSmith build helper.

Usage:
    python build.py --rust          # cargo build --release  -> rust/target/release/pixelfixer
    python build.py --uv            # uv build               -> python/dist/*.whl + .tar.gz
    python build.py --py            # python -m build        -> python/dist/ (needs `pip install build`)
    python build.py --all           # --rust + --uv
    python build.py --clean         # remove rust/target, python/dist, python/build, *.egg-info

The Python package is distributed via PyPI only (`pixelfixer`); Rust is
built as a plain local binary, never published to crates.io.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PY_DIR = os.path.join(ROOT, "python")
RUST_DIR = os.path.join(ROOT, "rust")


def build_rust():
    cargo = shutil.which("cargo")
    if not cargo:
        sys.exit("build.py: cargo not found. Install Rust: https://rustup.rs")
    print("== cargo build --release (rust/) ==")
    subprocess.check_call([cargo, "build", "--release"], cwd=RUST_DIR)
    print(f"\nRust binary: {os.path.join('rust', 'target', 'release', 'pixelfixer')}")


def build_uv():
    uv = shutil.which("uv")
    if not uv:
        sys.exit("build.py: uv not found. Install it: https://docs.astral.sh/uv/getting-started/install/"
                 "\n(or use: python build.py --py)")
    print("== uv build (python/) ==")
    subprocess.check_call([uv, "build"], cwd=PY_DIR)
    _report_dist()


def build_py():
    # Probe via subprocess so we test the exact interpreter that will build.
    probe = subprocess.run([sys.executable, "-c", "import build"],
                           capture_output=True, text=True)
    if probe.returncode != 0:
        sys.exit("build.py: the `build` package is not available to this interpreter"
                 f" ({sys.executable})."
                 "\nFix one of:  pip install build   |   python build.py --uv")
    print("== python -m build (python/) ==")
    subprocess.check_call([sys.executable, "-m", "build"], cwd=PY_DIR)
    _report_dist()


def _report_dist():
    dist = os.path.join(PY_DIR, "dist")
    artifacts = sorted(glob.glob(os.path.join(dist, "*")))
    if not artifacts:
        sys.exit("build.py: no artifacts produced in python/dist/")
    print("\nPython package artifacts:")
    for a in artifacts:
        print(f"  {os.path.relpath(a, ROOT)}")


def clean():
    targets = [
        os.path.join(RUST_DIR, "target"),
        os.path.join(PY_DIR, "dist"),
        os.path.join(PY_DIR, "build"),
    ] + glob.glob(os.path.join(PY_DIR, "*.egg-info")) + \
        glob.glob(os.path.join(PY_DIR, ".venv"))
    for t in targets:
        if os.path.exists(t):
            print(f"rm -rf {os.path.relpath(t, ROOT)}")
            shutil.rmtree(t)
    print("clean.")


def main():
    ap = argparse.ArgumentParser(
        prog="build.py",
        description="Build PixelSmith artifacts. Default Python build uses --uv.")
    ap.add_argument("--rust", action="store_true", help="cargo build --release")
    ap.add_argument("--uv", action="store_true", help="uv build (sdist + wheel)")
    ap.add_argument("--py", action="store_true", help="python -m build (standard pip tooling)")
    ap.add_argument("--all", action="store_true", help="--rust + --uv")
    ap.add_argument("--clean", action="store_true", help="remove build artifacts")
    args = ap.parse_args()

    try:
        if args.clean:
            clean()
            return
        if not any((args.rust, args.uv, args.py, args.all)):
            ap.print_help()
            return
        if args.all or args.rust:
            build_rust()
        if args.all or args.uv:
            build_uv()
        if args.py:
            build_py()
    except subprocess.CalledProcessError as e:
        sys.exit(f"build.py: step failed with exit code {e.returncode}")


if __name__ == "__main__":
    main()
