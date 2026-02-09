# Overmortal Progression Tracker

A comprehensive toolkit for tracking, analyzing, and visualizing your progression in the Overmortal mobile game.

## Features

- **📸 OCR Extraction**: Automatically extract game data from screenshots
- **📊 Data Analysis**: Calculate statistics, progression rates, and efficiency metrics
- **📈 Visualizations**: Generate beautiful charts and graphs of your progression
- **🎯 Predictions**: Estimate time to reach future milestones
- **📝 Reports**: Generate comprehensive text reports with insights

## Installation

### Requirements

- Python 3.7 or higher
- pip (Python package installer)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- pytesseract (for OCR)
- opencv-python (image processing)
- Pillow (image handling)
- matplotlib (charts and visualizations)
- numpy (numerical operations)

### Install Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Quick Start

### Method 1: Interactive Mode

Simply run the tracker without arguments:

```bash
python overmortal_tracker.py
```

This will present an interactive menu where you can choose what to do.

### Method 2: Command Line

**Analyze existing progression log:**

```bash
python overmortal_tracker.py all
```

This will parse your log, run analysis, and generate visualizations.

**Extract data from screenshots:**

```bash
python overmortal_tracker.py extract --images /path/to/screenshots
```

**Generate visualizations:**

```bash
python overmortal_tracker.py visualize
```

## Usage Guide

### 1. Extracting Data from Screenshots

If you have screenshots of your game progress:

1. Save all screenshots to a folder (e.g., `screenshots/`)
2. Run the extraction:

```bash
python overmortal_tracker.py extract --images ./screenshots
```

This will:
- Process each screenshot using OCR
- Extract game data (stage, G level, percentages, etc.)
- Create `progression_log.txt` with formatted entries
- Save raw data to `ocr_results.json`

### 2. Parsing Existing Log

If you already have a text log (like the one you maintain):

```bash
python overmortal_tracker.py parse --log progression_log.txt
```

This converts the text log into structured JSON data (`progression_data.json`).

### 3. Analyzing Your Progression

Generate statistics and insights:

```bash
python overmortal_tracker.py analyze
```

This creates `analysis_report.txt` with:
- Overall progression statistics
- Stage-by-stage breakdown
- Recent progression rates
- Efficiency metrics
- Time predictions

### 4. Creating Visualizations

Generate charts and graphs:

```bash
python overmortal_tracker.py visualize
```

Creates charts in the `charts/` directory:
- `overall_progression.png` - Your progression over time
- `g_level_progression.png` - G level advancement
- `daily_progress_rate.png` - Daily progress rate with moving average
- `stage_comparison.png` - Time and progress comparison across stages
- `time_to_milestone.png` - Hours to next breakthrough over time
- Stage-specific G level charts

### 5. Complete Pipeline

Run everything at once:

```bash
python overmortal_tracker.py all
```

This will parse → analyze → visualize in one command.

## File Structure

```
overmortal-tracker/
├── overmortal_tracker.py      # Main dashboard
├── improved_ocr.py             # OCR extraction tool
├── log_parser.py               # Log file parser
├── progression_analyzer.py     # Statistical analysis
├── progression_visualizer.py   # Chart generation
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── progression_log.txt         # Your progression log (input)
├── progression_data.json       # Structured data (generated)
├── analysis_report.txt         # Analysis results (generated)
│
└── charts/                     # Visualization outputs
    ├── overall_progression.png
    ├── g_level_progression.png
    └── ...
```

## Understanding Your Log Format

Your progression log should follow this format:

```
February 09, 6:41 PM - Eternal Early (20.4%)
After Reset, Pills, Respires
G8 at 93.9%
434.68 Yrs or 108 Hrs 40 Min to G9
```

Each entry contains:
- **Date and time**
- **Stage** (Celestial/Eternal + Early/Middle/Late) with overall percentage
- **G level** and percentage at that level
- **Time to next milestone** in game years and real hours

## Advanced Usage

### Custom Analysis

You can import the modules in your own scripts:

```python
from progression_analyzer import ProgressionAnalyzer

# Load and analyze data
analyzer = ProgressionAnalyzer('progression_data.json')

# Get specific statistics
stage_stats = analyzer.get_stage_statistics('Eternal Middle')
g_level_stats = analyzer.get_g_level_statistics()

# Calculate progression rate
rate = analyzer.calculate_progression_rate(last_n_days=7)

# Predict breakthrough
prediction = analyzer.predict_breakthrough_date('Eternal Middle')
```

### Custom Visualizations

```python
from progression_visualizer import ProgressionVisualizer

visualizer = ProgressionVisualizer('progression_data.json')

# Generate specific chart
visualizer.plot_overall_progression('my_chart.png')
visualizer.plot_stage_comparison('comparison.png')

# Generate all charts
visualizer.generate_all_charts(output_dir='my_charts')
```

## Tips for Best Results

### For OCR Extraction:

1. **Clear screenshots**: Ensure text is readable and not blurred
2. **Consistent format**: Take screenshots of the same game screen
3. **Good lighting**: Avoid dark or overexposed screenshots
4. **Name files with timestamps**: Format like `Screenshot_2025-02-09-18-30-00.jpg`

### For Manual Logs:

1. **Consistent format**: Follow the same format for each entry
2. **Regular updates**: Update daily for better trend analysis
3. **Complete data**: Include all fields (date, time, stage, G level, etc.)

## Troubleshooting

### OCR not working

- Make sure Tesseract is installed and in your PATH
- Check image quality and resolution
- Try adjusting the preprocessing in `improved_ocr.py`

### Missing data in charts

- Ensure your log has enough entries (at least 10-20)
- Check that dates are properly formatted
- Verify the JSON data file was created successfully

### Import errors

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.7+)

## Contributing

Feel free to modify and extend this tool for your needs!

Some ideas for enhancements:
- Add database support for larger datasets
- Web dashboard interface
- Auto-sync with cloud storage
- Achievement tracking
- Compare with other players
- Mobile app integration

## License

Free to use and modify for personal use.

## Contact

For questions or issues, please check the GitHub repository.

---

**Happy tracking, and may your cultivations be swift!** 🎮
