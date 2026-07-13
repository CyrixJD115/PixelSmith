# pixelfixer (Rust)

The native core of the [Pixel Art Fixer](../README.md): one dependency-free
binary, built for servers and batch jobs. It is a line-faithful port of the
[Python reference](../python/) and produces the same answers, 11-24x faster at
2.5-4x lower memory.

## Build

Requires a stable Rust toolchain. No system libraries, no OpenCV, nothing to
`apt install`. It builds the same on Linux, macOS, Windows, and ARM.

```bash
cargo build --release        # -> target/release/pixelfixer
```

Dependencies (pure Rust): `image`, `rustfft`, `rayon`, `serde`.

## Commands

```bash
# detect + reconstruct, writing the fixed image (mode defaults to full)
pixelfixer process    <image> <out.png> [full|fast]

# detection only, one JSON line per image
pixelfixer full       <image...>
pixelfixer fast       <image...>

# reconstruct with a known grid
pixelfixer recon      <image> <step_x> <step_y> <cols> <rows> <out.png>

# single channels, for debugging
pixelfixer autocorr   <image...>
pixelfixer runlengths <image...>
pixelfixer selfsim    <image...>
```

`process` prints one JSON line:

```json
{"file": "input.png", "cols": 104, "rows": 138, "step_x": 10.44,
 "step_y": 10.49, "consensus": "fast:ac+rl(S)", "mode": "full",
 "detect_s": 0.19, "recon_s": 0.11, "peak_rss_mb": 147.6}
```

## Performance

Measured on an AMD 5800X, a fresh process per image:

- Typical 256-512 px inputs: 0.1-0.3 s.
- Worst-case 4 MP arbitrated images: about 1.5 s.
- Peak memory: roughly 50-170 MB per running job.

One process handles one image using all cores (rayon). For a busy endpoint, run
requests through a small job queue, or cap threads with `RAYON_NUM_THREADS` and
run a few processes in parallel.

## Parity with the reference

Every module is verified against the Python reference on a graded benchmark
before it counts as ported: detection results are identical (the one difference
across the bench is a single row on an image both implementations mis-grade
identically), and reconstruction is pixel-exact on the large majority of images,
the rest differing only on a fraction of a percent of cells from float tie
ordering. Detection is robust to the one legitimate source of divergence (JPEG
decoders differ in their IDCT), so pixel-exact comparison is meaningful on PNG
inputs.

The algorithm is documented in full in
[`../docs/HOW_IT_WORKS.md`](../docs/HOW_IT_WORKS.md).
