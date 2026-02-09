# Overmortal Progression Tracker - Complete Toolkit
## Overview of All Components

### 🎯 Main Tools

#### 1. **overmortal_tracker.py** - Main Dashboard
The central hub that integrates all components.

**Usage:**
```bash
# Interactive menu
python overmortal_tracker.py

# Run complete pipeline
python overmortal_tracker.py all

# Extract from screenshots
python overmortal_tracker.py extract --images ./screenshots

# Analyze existing log
python overmortal_tracker.py analyze

# Generate visualizations
python overmortal_tracker.py visualize
```

**What it does:**
- Provides easy access to all features
- Runs complete analysis pipelines
- Interactive menu for guided usage

---

### 🔧 Core Components

#### 2. **log_parser.py** - Log File Parser
Parses your text log into structured JSON data.

**Usage:**
```python
from log_parser import LogParser

parser = LogParser("progression_log.txt")
entries = parser.parse()
parser.to_json("progression_data.json")
```

**Features:**
- Extracts dates, stages, G levels, percentages
- Handles various log formats
- Exports to JSON for further analysis
- Filters by stage or G level

---

#### 3. **progression_analyzer.py** - Statistical Analysis
Calculates statistics, rates, and predictions.

**Usage:**
```python
from progression_analyzer import ProgressionAnalyzer

analyzer = ProgressionAnalyzer("progression_data.json")
stats = analyzer.get_stage_statistics("Eternal Middle")
rate = analyzer.calculate_progression_rate()
prediction = analyzer.predict_breakthrough_date("Eternal Middle")
```

**Provides:**
- Stage progression statistics
- G level analysis
- Daily progression rates
- Time predictions
- Efficiency metrics
- Comprehensive reports

---

#### 4. **progression_visualizer.py** - Chart Generator
Creates beautiful visualizations of your progression.

**Usage:**
```python
from progression_visualizer import ProgressionVisualizer

visualizer = ProgressionVisualizer("progression_data.json")
visualizer.plot_overall_progression()
visualizer.plot_daily_progress_rate()
visualizer.generate_all_charts()
```

**Creates:**
- Overall progression timeline
- G level advancement charts
- Daily progress rate graphs
- Stage comparison charts
- Time-to-milestone predictions
- Stage-specific visualizations

---

#### 5. **improved_ocr.py** - Screenshot Extractor
Extracts game data from screenshots using OCR.

**Usage:**
```python
from improved_ocr import OvermortalOCR

extractor = OvermortalOCR(
    image_dir="/path/to/screenshots",
    output_dir="output"
)
extractor.run()
```

**Features:**
- Advanced image preprocessing
- Optimized OCR for game UI
- Automatic datetime extraction
- JSON and text output
- Batch processing

---

### 📚 Additional Resources

#### 6. **example_usage.py** - Usage Examples
Demonstrates all features with practical examples.

**Run it:**
```bash
python example_usage.py
```

**Shows:**
- How to parse logs
- How to run analysis
- How to create visualizations
- Custom analysis techniques

---

### 📊 Generated Outputs

#### **Charts** (in `charts/` directory)

1. **overall_progression.png**
   - Shows your progression through all stages over time
   - Color-coded by stage (Celestial/Eternal, Early/Middle/Late)

2. **g_level_progression.png**
   - Tracks your advancement through G levels
   - Shows all G levels or filtered by stage

3. **daily_progress_rate.png**
   - Your daily progress percentage
   - 7-day moving average for trend analysis

4. **stage_comparison.png**
   - Compares time spent in each stage
   - Shows average daily progress per stage

5. **time_to_milestone.png**
   - Estimated hours to next breakthrough
   - Tracks how this changes over time

6. **Stage-specific charts**
   - `g_level_eternal_early.png`
   - `g_level_eternal_middle.png`
   - `g_level_eternal_late.png`

#### **Data Files**

- `progression_data.json` - Structured data from your log
- `analysis_report.txt` - Comprehensive statistics report
- `ocr_results.json` - Raw OCR extraction data (if using screenshots)

---

### 🎓 How to Use This Toolkit

#### Scenario 1: You have a text log (like yours)
```bash
# Place your progression_log.txt in the directory
python overmortal_tracker.py all
```

#### Scenario 2: You have screenshots
```bash
# Put screenshots in a folder
python overmortal_tracker.py extract --images ./screenshots
# Then analyze
python overmortal_tracker.py all
```

#### Scenario 3: You want specific analysis
```bash
# Just get statistics
python overmortal_tracker.py analyze

# Just create charts
python overmortal_tracker.py visualize
```

#### Scenario 4: You want to code your own analysis
```python
# Use the components in your own scripts
from log_parser import LogParser
from progression_analyzer import ProgressionAnalyzer
from progression_visualizer import ProgressionVisualizer

# Your custom analysis here...
```

---

### 📋 Dependencies

Install all at once:
```bash
pip install -r requirements.txt
```

Or individually:
- `pytesseract` - OCR capabilities
- `opencv-python` - Image processing
- `Pillow` - Image handling
- `matplotlib` - Chart generation
- `numpy` - Numerical operations

**Note:** For OCR, you also need Tesseract OCR installed on your system.

---

### 💡 Pro Tips

1. **Regular Updates**: Run analysis daily for best trends
2. **Backup Your Data**: Keep copies of your progression log
3. **Compare Periods**: Use date filtering to compare different phases
4. **Custom Metrics**: Modify the analyzer for your specific needs
5. **Export Charts**: Use charts in progress reports or sharing

---

### 🔄 Workflow

```
Screenshots → Extract (OCR) → Parse → Analyze → Visualize
                ↓
           Manual Log → Parse → Analyze → Visualize
```

---

### 🎯 What's Next?

1. Review the generated charts in `charts/`
2. Read `analysis_report.txt` for insights
3. Try `example_usage.py` for advanced features
4. Customize for your needs
5. Share your progress!

---

**Questions?** Check the README.md for full documentation!
