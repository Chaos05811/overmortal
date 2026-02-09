# Overmortal Progression Tracker

A toolkit for tracking, analyzing, and visualizing your Overmortal game progression — with a live web dashboard.

## Quick Start

```bash
pip install -r requirements.txt
python dashboard.py
```

This starts the dashboard at `http://localhost:5050` and opens it in your browser.

## Features

- **Web Dashboard** — interactive charts, stats, predictions, and a breakthrough timeline
- **Add Entries from the UI** — click "+ Add Entry" in the nav bar to log progress directly from the dashboard
- **Data Analysis** — stage statistics, daily rates, efficiency metrics, and completion predictions
- **Visualizations** — overall progression, G-level tracking, daily rate trends, time-to-milestone
- **OCR Extraction** — extract data from game screenshots (requires Tesseract)
- **CLI Tools** — parse, analyze, visualize, and add entries from the command line

## Entry Format

Entries in `prog.txt` follow this structure:

```
February 09, 8:53 AM - Eternal Late (95.9%)
G20 at 49.4%
616.458 Yrs or 154 Hrs 6 Min to G21
```

Each entry has:
- **Date & Time** — when the snapshot was taken
- **Realm Phase & Overall %** — e.g. Eternal Late (95.9%)
- **Action/context** (optional) — e.g. After Reset, Pills, Respires
- **Grade status** — current G-level and percentage
- **Time remaining** — game years / real hours to next milestone
- **EST/prediction** (optional) — notes on predicted values

## Adding Entries

### From the Dashboard

1. Run `python dashboard.py`
2. Click **"+ Add Entry"** in the top nav bar
3. Fill in the fields (date and time default to now, realm pre-selects current stage)
4. Submit — the entry is appended to `prog.txt` and the dashboard reloads

### From the CLI

```bash
python overmortal_tracker.py add
```

Walks you through interactive prompts and appends to `prog.txt`.

## CLI Commands

```bash
python overmortal_tracker.py              # Interactive menu
python overmortal_tracker.py parse        # Parse prog.txt into JSON
python overmortal_tracker.py analyze      # Generate analysis report
python overmortal_tracker.py visualize    # Generate chart PNGs
python overmortal_tracker.py all          # Parse + analyze + visualize
python overmortal_tracker.py add          # Add a new entry via prompts
python overmortal_tracker.py extract      # Extract from screenshots (OCR)
```

## File Structure

```
om_dash2/
├── dashboard.py               # Flask server + dashboard HTML generator
├── overmortal_tracker.py      # CLI entry point
├── log_parser.py              # Parses prog.txt into structured data
├── progression_analyzer.py    # Statistical analysis
├── progression_visualizer.py  # Chart generation (matplotlib)
├── improved_ocr.py            # OCR extraction from screenshots
├── example_usage.py           # Usage examples for the Python API
├── prog.txt                   # Progression log (your data)
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── INDEX.md                   # Component reference
└── QUICK_START.md             # Getting started guide
```

**Generated (gitignored):**

```
├── dashboard.html             # Generated dashboard (served by Flask)
├── progression_data.json      # Parsed structured data
├── analysis_report.txt        # Analysis output
├── charts/                    # Generated chart images
└── *.png                      # Individual chart files
```

## Requirements

- Python 3.7+
- Flask (for the web dashboard)
- matplotlib, numpy (for chart generation)
- pytesseract, opencv-python, Pillow (for OCR — optional)

Install everything:

```bash
pip install -r requirements.txt
```

For OCR, you also need [Tesseract](https://github.com/tesseract-ocr/tesseract) installed on your system.

## Python API

```python
from log_parser import LogParser
from progression_analyzer import ProgressionAnalyzer

parser = LogParser("prog.txt")
entries = parser.parse()
parser.to_json("progression_data.json")

analyzer = ProgressionAnalyzer("progression_data.json")
stats = analyzer.get_stage_statistics("Eternal Late")
rate = analyzer.calculate_progression_rate(last_n_days=7)
```

## License

Free to use and modify for personal use.
