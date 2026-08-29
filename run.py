#!/usr/bin/env python3
"""PixelSmith starter: run the Python or Rust version straight from source.

Usage:
    python run.py --rust  [--debug]  [-- cargo args...]    # cargo run (rust/)
    python run.py --python [-- pixelfixer args...]         # current interpreter
    python run.py --uv     [-- pixelfixer args...]         # uv-managed env (default)

Everything after a `--` separator (or any unrecognized argument) is passed
straight to the underlying tool. Paths are resolved from YOUR current
directory, so relative paths behave exactly as if you ran the tool directly.

Examples:
    python run.py examples/frog.png
    python run.py -- examples/frog.png --extract out.png
    python run.py --rust -- process examples/frog.png out.png
    python run.py --rust --debug -- fast examples/frog.png

Python CLI  : <input.png|folder> [--extract out.png] [--overlay grid.png] [--json out.json]
Rust CLI    : process <image> <out.png> [full|fast] | fast <image...> | recon ... (see rust/src/main.rs)
"""
import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PY_DIR = os.path.join(ROOT, "python")
RUST_MANIFEST = os.path.join(ROOT, "rust", "Cargo.toml")


def main():
    # Split args on the first `--`; everything after it belongs to the tool.
    argv = sys.argv[1:]
    if "--" in argv:
        split = argv.index("--")
        mode_args, tool_args = argv[:split], argv[split + 1:]
    else:
        mode_args, tool_args = argv, []

    ap = argparse.ArgumentParser(
        prog="run.py",
        description="Run PixelSmith from source (default mode: --uv).",
        add_help=False,
    )
    ap.add_argument("--rust", action="store_true", help="run the Rust binary via cargo")
    ap.add_argument("--python", action="store_true", help="run python/pixelfixer with the current interpreter")
    ap.add_argument("--uv", action="store_true", help="run python/pixelfixer in a uv-managed environment (default)")
    ap.add_argument("--debug", action="store_true", help="(rust) build without --release")
    ap.add_argument("-h", "--help", action="store_true", help="show this help")
    mode, tool_extra = ap.parse_known_args(mode_args)
    tool_args = tool_extra + tool_args

    modes = [m for m, on in (("--rust", mode.rust), ("--python", mode.python), ("--uv", mode.uv)) if on]
    if mode.help or (not modes and not tool_args):
        ap.print_help()
        return 0
    if len(modes) > 1:
        sys.exit(f"run.py: pick one of --rust / --python / --uv (got {' + '.join(modes)})")
    selected = modes[0] if modes else "--uv"
    if not modes:
        print("run.py: no mode given, defaulting to --uv", file=sys.stderr)

    if selected == "--rust":
        cargo = shutil.which("cargo")
        if not cargo:
            sys.exit("run.py: cargo not found. Install Rust: https://rustup.rs")
        cmd = [cargo, "run", "--manifest-path", RUST_MANIFEST] + \
            ([] if mode.debug else ["--release"]) + ["--"] + tool_args
        return subprocess.call(cmd)

    if selected == "--python":
        env = dict(os.environ, PYTHONPATH=PY_DIR + (os.pathsep + env_path
                                                    if (env_path := os.environ.get("PYTHONPATH")) else ""))
        return subprocess.call([sys.executable, "-m", "pixelfixer.cli", *tool_args], env=env)

    uv = shutil.which("uv")
    if not uv:
        sys.exit("run.py: uv not found. Install it: https://docs.astral.sh/uv/getting-started/install/"
                 "\n(or fall back to: python run.py --python ...)")
    return subprocess.call([uv, "run", "--project", PY_DIR, "python", "-m", "pixelfixer.cli", *tool_args])


if __name__ == "__main__":
    sys.exit(main())
