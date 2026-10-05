# Ajaib Flow Library

Twelve editable motion studies: satin ribbon, light stream, traveling apertures, glass tide, sliding planes, soft light sweep, tapered current, dot current, scrolling chart, chart light flow, thread flow, and candlestick flow.

## Run locally

Requires Python 3.10 or newer.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Open **http://127.0.0.1:8048/flow-library/index.html**. On Windows, activate the environment with `.venv\Scripts\activate`.

Each editor includes a 9:16 preview and 1080 × 1920 MP4 export with framing, position, duration, and frame-rate controls. Keep the tab visible during recording. Transparent scenes use a solid background for MP4. Some editors also offer landscape MP4 and transparent WebM exports. Ribbon position and rotation apply to previews and exports.

## Static hosting

The root `index.html` opens the library. GitHub Pages can host the previews and saved media, but Python-backed MP4 exports require the local server above. No export server is exposed publicly. Browser-based candlestick WebM recording remains available on supported browsers.

## Assets

Saved originals are in `flow-library/assets/`. Editors do not overwrite these originals. The ribbon Lottie is an embedded raster sequence and is approximately 62 MB.

These are abstract motion studies, not live financial data. Generated artwork and brand elements are included for this project's design use; no third-party rights are transferred.
