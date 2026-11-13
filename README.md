# Clavier: Old-World MIDI Piano Visualizer & Frame-Exact Lossless MP4 Renderer

> A self-contained, offline-first 88-key MIDI piano visualizer and deterministic MP4 video rendering engine. Designed with the aesthetic restraint of an 18th-century fortepiano workshop, engineered for pedagogical practice, and built to produce frame-exact, silent, lossless video exports for automated music pipelines.

---

## Table of Contents
1. [Core Purpose](#core-purpose)
2. [Aesthetic & Design Philosophy](#aesthetic--design-philosophy)
3. [The Frame-Exact Synchronization Guarantee](#the-frame-exact-synchronization-guarantee)
4. [Encoding Profiles & Lossless Reality](#encoding-profiles--lossless-reality)
5. [Architecture & Engine Design](#architecture--engine-design)
6. [Quick Start & Manual Usage](#quick-start--manual-usage)
7. [CLI & Headless Python Automation](#cli--headless-python-automation)
8. [Headless Browser Automation (Playwright / Puppeteer)](#headless-browser-automation-playwright--puppeteer)
9. [Skeptic Verification Suite](#skeptic-verification-suite)
10. [CI / GitHub Actions](#ci--github-actions)
11. [License](#license)

---

## Core Purpose

Clavier has exactly two non-negotiable jobs:

1. **Teaching & Practice (Human Focus):** A pianist or complete beginner watching the screen during an hour-long practice session must experience maximum note legibility, rhythm clarity, and keyboard geometry comprehension. Visual ornaments never compete with note arrival; key motions and falling note beams reflect physical acoustic mechanics.
2. **Deterministic Frame-Exact Lossless Rendering (Machine Focus):** Turns any Standard MIDI File (`.mid` / `.midi`) into a silent, constant-frame-rate (CFR) MP4 video alongside a machine-readable JSON synchronization manifest. When audio rendered from the same MIDI file is muxed over the exported video, every keypress strikes at the exact sub-millisecond frame with zero drift from measure 1 to the final cadence.

---

## Aesthetic & Design Philosophy

The interface evokes an ancient, old-world fortepiano workshop—sober, warm, and restrained:

- **Color Palette:**
  - Background Canvas: Warm iron-gall ink parchment (`#121110` / `#0a0908`)
  - White Ivory Keys: Aged museum ivory (`#faf5eb` to `#ded5c2`) with hand-crafted boxwood side-bevels
  - Black Ebony Keys: Matte chamfered bog-oak ebony (`#1b1816` to `#0d0c0b`) with 3D octagonal beveled shoulders
  - Damper Rail: Deep wine-stained baize / burgundy wool felt (`#3b1418` / `#581d22`)
  - Pinblock & Accents: Hand-rubbed brass foil (`#d4af37` / `#b8860b`)
- **Visual Mechanics:**
  - **Acoustic Hammer Bloom:** Velocity-sensitive luminescence blooming upward from key strikes onto the baize rail.
  - **Midiano Chamfered Sprites:** High-DPI cached ivory and ebony key sprites (`KeySpriteCache`) delivering flawless 60 FPS drawing with zero garbage-collection stutter.
  - **Active Range Auto-Zoom:** Dynamically expands the keyboard view to the active musical register when selected, while keeping an 88-key miniature overview strip docked beneath the damper rail.
  - **Pedagogical Color Modes:** Hand separation (Left Hand: Antique terracotta / Right Hand: Verdigris cerulean), Finger mapping (1=Thumb through 5=Pinky), Pitch-class spectrum, High-contrast Colorblind, and Monochrome.

---

## The Frame-Exact Synchronization Guarantee

### Mathematical Invariants

Let $t_{\text{midi}}$ be the elapsed time in seconds from MIDI tick 0 (with microsecond accumulation across all tempo and time-signature changes). Let $L$ be the configured lead-in duration in seconds (default: `2.0s`).

$$\begin{aligned}
t_{\text{video}} &= t_{\text{midi}} + L \\
\text{frameIndex} &= \operatorname{round}\left( (t_{\text{midi}} + L) \times \text{FPS} \right)
\end{aligned}$$

- **Zero Drift Guarantee:** Microsecond integer arithmetic ($\mu s$) is used throughout MIDI tempo maps to prevent floating-point drift over long multi-movement works.
- **Audio Exclusion:** The exported MP4 contains **strictly zero audio streams** (no silent PCM or AAC tracks).
- **Constant Frame Rate (CFR):** Every single frame in the MP4 has an identical packet duration ($1/\text{FPS}$), verified via `ffprobe`.
- **Machine-Readable Metadata:** The sync offset is recorded both in a companion `.sync.json` file and embedded directly within the MP4 container metadata (`format.tags.comment`).

### Post-Production Audio Muxing

To lay your independently rendered audio track over the exported MP4 video with frame-exact alignment:

```bash
ffmpeg -i video.mp4 -itsoffset 2.000000 -i rendered_audio.wav -c:v copy -c:a aac -b:a 320k muxed_performance.mp4
```
*(Replace `2.000000` with the `midiToVideoOffsetSeconds` value from `video.mp4.sync.json`)*.

---

## Encoding Profiles & Lossless Reality

| Profile | Pipeline | Codec & Container | Pixel Format | Lossless Guarantee | Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`rgb-lossless`** | CLI / Node / Python | `libx264rgb -qp 0` in MP4 | `rgb24` | **True Bit-Exact Lossless**<br>$\text{MAXDIFF} = 0, \text{MSE} = 0.0, \text{PSNR} = \infty$ | Archival master, automated video pipelines, frame analysis |
| **`yuv444-lossless`** | CLI / Node / Python | `libx264 -qp 0` in MP4 | `yuv444p` | **Full Chroma Lossless**<br>Zero quantization, 4:4:4 color | High-end video editors (DaVinci Resolve, Premiere Pro) |
| **`compatible-lossless`**| CLI / Node / Python | `libx264 -crf 10` in MP4 | `yuv420p` | **Perceptually Indistinguishable**<br>High Profile H.264 | Universal mobile & web video players |
| **In-Browser Export** | Web Browser UI | WebCodecs + `mp4-muxer` | `yuv420p` | **High-Bitrate Near-Lossless**<br>Streamed to disk via FileSystem API | Direct client-side export without installing FFmpeg |

> **Browser WebCodecs Technical Note:** The W3C `VideoEncoder` API in modern browsers mandates YUV 4:2:0 subsampling with discrete cosine transform quantization. True mathematical RGB lossless cannot be produced inside browser WebCodecs; it requires the CLI pipeline (`render_midi.py`). The browser exporter streams chunks directly to disk via `FileSystemWritableFileStreamTarget`, capping RAM usage below 60 MB and eliminating browser tab out-of-memory crashes.

---

## Architecture & Engine Design

```
├── .github/workflows/
│   └── verify.yml              # CI workflow: builds, renders, and runs skeptic verification
├── fixtures/
│   ├── torture_test.mid        # SMF Format 1 verification fixture (all 88 keys, tempo changes)
│   └── bach_846.mid            # Bach BWV 846 Prelude verification fixture
├── scripts/
│   ├── create_fixtures.py      # Synthesizes torture test MIDI and extracts repertoire
│   ├── render-cli.mjs          # Node headless engine renderer piping raw RGBA to FFmpeg
│   └── verify_export.py        # Frame-exact skeptic audit suite
├── src/
│   ├── engine/
│   │   ├── builtInMidis.ts     # Offline repertoire (Bach, Für Elise, Moonlight Sonata)
│   │   ├── midiEngine.ts       # Production SMF parser, $\mu s$ tempo map, Midiano DP fingering
│   │   ├── pianoRenderer.ts    # 60 FPS Canvas visualizer, KeySpriteCache, chamfered keys
│   │   └── videoExporter.ts    # Browser WebCodecs exporter with FileSystem disk streaming
│   ├── App.tsx                 # Decoupled React UI, automation hooks, settings drawer
│   └── main.tsx                # React 19 entry point with ClavierErrorBoundary
├── package.json                # Project configuration & npm scripts
├── render_midi.py              # Top-level Python CLI & importable rendering library
└── vite.config.ts              # Vite singlefile bundler configuration
```

---

## Quick Start & Manual Usage

### 1. Interactive Browser Application

```bash
# Install dependencies
npm install

# Run local development server
npm run dev

# Or build the self-contained single-file HTML bundle:
npm run build
# -> dist/index.html (100% self-contained, 0 CDN calls, runs offline)
```

Open `dist/index.html` in any modern browser (Chrome, Edge, Firefox, Safari).

### 2. URL Query Parameter Bootstrap

You can configure, load, and auto-export directly via URL query parameters:

```
dist/index.html?song=bach_846&fps=60&width=1920&height=1080&colormode=hand&autozoom=1
```

Supported query parameters:
- `song`: Built-in song ID (`bach_846`, `elise`, `mond_1`)
- `fps`: Target frame rate (`30`, `60`, `120`)
- `width` / `height`: Resolution dimensions (e.g. `1920` / `1080`)
- `leadin`: Constant lead-in seconds (default: `2.0`)
- `colormode`: `hand` | `finger` | `pitch` | `colorblind` | `monochrome`
- `notelabel`: `fingering` | `noteName` | `solfege` | `scaleDegree` | `none`
- `keylabel`: `onlyC` | `allWhite` | `all88` | `solfege` | `none`
- `autozoom`: `1` to zoom active pitch register
- `zen`: `1` to hide controls and run in clean presentation mode
- `autoexport`: `1` to trigger browser export immediately on load

---

## CLI & Headless Python Automation

### Basic CLI Command

Render any MIDI file to a frame-exact, lossless MP4:

```bash
python render_midi.py \
  --input fixtures/torture_test.mid \
  --output output/torture_test.mp4 \
  --width 1920 \
  --height 1080 \
  --fps 60 \
  --lead-in 2.0 \
  --quality rgb-lossless
```

### JSON Job Configuration

You can pass a complete configuration file via `--config`:

```json
{
  "input": "fixtures/bach_846.mid",
  "output": "output/bach_master.mp4",
  "width": 3840,
  "height": 2160,
  "fps": 60,
  "leadIn": 2.0,
  "tailOut": 1.5,
  "quality": "rgb-lossless",
  "colorMode": "hand",
  "noteLabel": "fingering",
  "fitRange": false
}
```

Execute with:
```bash
python render_midi.py --config job.json
```

### Python Library Interface

```python
from render_midi import render_midi_to_mp4

manifest = render_midi_to_mp4(
    input_midi="fixtures/bach_846.mid",
    output_mp4="output/bach.mp4",
    width=1920,
    height=1080,
    fps=60,
    lead_in=2.0,
    quality="rgb-lossless"
)

offset_seconds = manifest["synchronization"]["midiToVideoOffsetSeconds"]
total_frames = manifest["video"]["totalFrames"]
print(f"Rendered {total_frames} frames with {offset_seconds}s lead-in sync offset.")
```

---

## Headless Browser Automation (Playwright / Puppeteer)

The HTML visualizer registers complete programmatic automation surfaces on `window.Clavier` and `window.MidianoAncientAPI`:

```javascript
// Check readiness
const ready = window.Clavier.isReady();

// Seek to frame-exact video frame or MIDI timestamp
window.Clavier.seekToVideoFrame(120); // Exact frame where MIDI t=0.0s strikes
window.Clavier.seekToMidiTime(1.500); // 1.5 seconds into the MIDI piece

// Extract raw RGBA pixel buffer (for visual regression testing)
const pixelBytes = window.Clavier.getFramePixelsRGBA();

// Get base64 PNG data URL
const dataUrl = window.Clavier.getFrameDataUrl("image/png");

// Trigger in-browser WebCodecs export
window.Clavier.exportMp4({
  fps: 60,
  width: 1920,
  height: 1080,
  leadInSeconds: 2.0,
  onProgress: (pct, frame, total) => console.log(`Progress: ${pct.toFixed(1)}%`)
});

// Telemetry and DOM events
window.addEventListener("clavier-export-progress", (e) => console.log(e.detail));
window.addEventListener("clavier-export-complete", (e) => console.log("Export finished"));
```

---

## Skeptic Verification Suite

The verification suite (`scripts/verify_export.py`) performs an exhaustive frame-by-frame audit on actual exported MP4 files:

1. **Audio Stream Check:** Inspects stream headers with `ffprobe` to guarantee exactly 1 video stream and **0 audio streams**.
2. **Container & CFR Audit:** Verifies `start_time == 0.000000`, expected frame count, and constant packet duration across 100% of frames.
3. **Machine-Readable Sync Audit:** Validates that the `.sync.json` manifest matches the embedded MP4 container tag (`format.tags.comment`).
4. **Pixel-Level Key Depression Audit:** Streams frames from the MP4 at $(f_{\text{on}}-1)$ and $f_{\text{on}}$ across all 88 keys (including A0, C4, C8, Cmaj7 chords, and black keys C#5, D#5, F#5, G#5, A#5) across multiple tempo shifts (120 $\to$ 180 $\to$ 90 $\to$ 240 BPM), proving that keys depress on the exact calculated frame.
5. **Bit-Exact Lossless RGB Validation:** Computes SHA-256 digests of decoded MP4 frames against raw canvas renderer pixels, confirming $\text{MAXDIFF} = 0, \text{MSE} = 0.0$.
6. **Determinism Audit:** Renders the piece twice independently and verifies that full-video RGB24 SHA-256 hashes match identically.

To run the full verification suite:

```bash
python scripts/verify_export.py
```

---

## CI / GitHub Actions

Every commit and pull request runs automated tests via `.github/workflows/verify.yml`:
- Builds the single-file HTML bundle (`npm run build`).
- Synthesizes the 88-key torture test MIDI fixture.
- Renders 1280x720 @ 60fps bit-exact RGB24 MP4s.
- Executes `verify_export.py` and uploads the resulting MP4s and singlefile HTML bundle as artifacts.

---

## License

MIT License. Designed and engineered for musicians, educators, and audio/video pipeline developers.
