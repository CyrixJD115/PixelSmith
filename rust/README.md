# pixelfixer (Rust server core)

Native port of the production detector (`detector/`) — both modes — built
for the server: low latency, low memory, zero interpreter startup. The
Python package stays as the numerical reference; every Rust module is
verified against it on the 27 user-truth bench images before it counts as
ported.

## Build

```
cargo build --release        # -> target/release/pixelfixer.exe
```

Toolchain: stable Rust, `x86_64-pc-windows-gnu` (no VS Build Tools needed).
Deps: `image` (PNG/JPEG), `rustfft`, `rayon`.

## Commands

```
pixelfixer process    <image> <out.png> [full|fast] [legacy]  # detect + reconstruct
pixelfixer fast       <image...>            # fast-mode detection, JSON per line
pixelfixer full       <image...>            # full-mode detection (arbitration)
pixelfixer recon      <image> <sx> <sy> <cols> <rows> <out.png> [dark] [palette]
pixelfixer autocorr   <image...>            # single channel (debug)
pixelfixer runlengths <image...>            # single channel (debug)
pixelfixer selfsim    <image...>            # single channel (debug)
```

`process` defaults to full-mode detection + **two-stage packing** reconstruction
(`two_stage_pack`): quantise-for-structure (crisp lines) then color each cell
from the original pixels of its winning label (accurate colors, no palette
loss), on a regular even grid with adaptive K. Pass `legacy` for the old
grid-cut / mode-pool reconstructor. Prints one JSON line: cols/rows/steps/
consensus/mode/detect_s/recon_s/peak_rss_mb.

## What is ported

| module          | mirrors                  | verification (27 bench images) |
|-----------------|--------------------------|--------------------------------|
| gray, acf       | autocorr.py features/ACF | via autocorr                   |
| autocorr.rs     | autocorr.py              | 27/27 identical                |
| runlengths.rs   | runlengths.py            | 27/27 identical                |
| selfsim.rs      | selfsim.py               | 27/27 identical                |
| core.rs fast    | core.py mode="fast"      | 27/27 identical incl. consensus strings |
| core.rs full    | core.py mode="full"      | 26/27 identical sizes + consensus; the diff is 1 row on the known dither-locked miss (both fail its truth identically). Same truth pass rate: 25/27 both. |
| fusionchan.rs   | fusion.py lean + channels.py actives | via core full |
| varcontrast.rs  | varcontrast.py z-curve   | via core full |
| reconsearch.rs  | reconsearch.py (nbc=1)   | via core full |
| kmeans.rs       | quantize.py + adaptive_k | k-means labels for two-stage (seeding differs from cv2) |
| reconstruct.rs `two_stage_pack` | reconstruct.py `two_stage_pack` | **default recon**; ~1 gray level/pixel vs Python (k-means seeding) |
| reconstruct.rs `reconstruct` (legacy) | reconstruct.py `reconstruct` (mode) | 19/27 pixel-exact, rest differ on 0.01–0.1% of cells (float-tie; one JPEG differs by decoder IDCT) |

Not ported: palette_snap (server API default is off). dark_stroke IS
ported (opt-in). Known non-parity source: k-means (cv2 uses OpenCV's
global RNG — irreproducible across implementations); the Rust port uses a
deterministic k-means++ with the same criteria. Measured effect on the
bench: zero decision changes.

## Measured vs Python (5800X, fresh process per image)

mode="fast":

| case                    | py wall | rust wall | py peak RSS | rust peak RSS |
|-------------------------|---------|-----------|-------------|---------------|
| Test.png (small)        | 2.6 s   | 0.23 s    | 200 MB      | 78 MB         |
| weird-pixels (tiny)     | 2.0 s   | 0.16 s    | 133 MB      | 46 MB         |
| 752d… (selfsim path)    | 10.3 s  | 0.79 s    | 331 MB      | 151 MB        |
| 155e5a… (1.6 MP worst)  | 11.6 s  | 0.83 s    | 356 MB      | 166 MB        |

11–14x faster wall, 2.2–2.9x lower peak memory, identical answers.
Per-module compute on the bench: autocorr 4.7x, runlengths 3.8x,
selfsim 31x, reconstruct 5.5x vs numpy.

mode="full": whole 27-image bench 163.9 s (Python) -> 7.8 s (Rust), 21x.
Arbitrated 1.6 MP worst case end-to-end (detect + reconstruct + PNG):
1.2 s / 170 MB vs Python's 29 s / 730 MB — 24x faster, 4.3x less memory.

## Fidelity rules that made 27/27 possible

The comb scores are razor-thin in step-space; "close enough" float behavior
is NOT enough. The port matches numpy/Python semantics exactly:

- `np.round` / python `round()` are banker's rounding -> `round_ties_even()`,
  never `round()`.
- `astype(np.uint8)` truncates toward zero -> `as u8`, never `.round()`.
- numpy accumulates f32 arrays in f32: band profiles and reduceat-style tile
  sums are computed in f64 then rounded through f32 at the same stage
  boundaries the reference has.
- `np.argmax` returns the FIRST maximum; every parallel map reduces
  sequentially in reference order so float sums stay bit-identical.
- `np.linspace(0, n, k+1)` values are `i * (n/k)`, not `(n*i)/k`.
- JPEG decoders legally differ (IDCT): zune-jpeg vs libjpeg-turbo produce
  slightly different pixels. Detection is robust to it; pixel-exact recon
  comparison is only meaningful on PNG inputs.

## Verification harness

```
python verify_autocorr.py     # module vs detector/autocorr.py
python verify_runlengths.py   # module vs detector/runlengths.py
python verify_fast.py         # selfsim + core fast path vs Python
python verify_full.py         # full-mode core vs Python + truth scoring
python verify_recon.py        # reconstruct vs Python, pixel-exact
python bench_compare.py       # wall time + peak RSS head-to-head
```

Run from the repo root (they import `detector/` and `tools/bench_common`).
