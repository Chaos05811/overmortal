# QUICK START GUIDE
## Overmortal Progression Tracker

### 🚀 Get Started in 3 Steps

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Run the Tracker
```bash
# Interactive mode (easiest)
python overmortal_tracker.py

# Or run everything at once
python overmortal_tracker.py all
```

#### 3. View Your Results
- Check `analysis_report.txt` for statistics
- Open `charts/` folder to see visualizations

---

### 📊 What You Get

**Analysis Report** (`analysis_report.txt`):
- Overall progression statistics
- Stage-by-stage breakdown  
- Recent progression rate
- Time predictions
- Efficiency metrics

**Visualizations** (`charts/` folder):
- Overall progression over time
- G level advancement charts
- Daily progress rate trends
- Stage comparison analysis
- Time to breakthrough predictions

---

### 🎯 Common Tasks

**Analyze Your Current Log:**
```bash
python overmortal_tracker.py all
```

**Extract from Screenshots:**
```bash
python overmortal_tracker.py extract --images /path/to/screenshots
```

**Generate Only Charts:**
```bash
python overmortal_tracker.py visualize
```

**See Detailed Report:**
```bash
python overmortal_tracker.py analyze
```

---

### 💡 Tips

1. **For Manual Logs**: Just place your `progression_log.txt` in the same directory and run
2. **For Screenshots**: Save them in a folder and use the extract command
3. **Regular Updates**: Run daily for best trend analysis
4. **Custom Analysis**: See `example_usage.py` for advanced features

---

### 📁 File Structure

```
overmortal-tracker/
├── overmortal_tracker.py      # Main tool (run this!)
├── log_parser.py               # Parses your log
├── progression_analyzer.py     # Analyzes data
├── progression_visualizer.py   # Creates charts
├── improved_ocr.py             # Extracts from screenshots
├── example_usage.py            # Advanced examples
│
├── progression_log.txt         # Your log (input)
├── progression_data.json       # Structured data
├── analysis_report.txt         # Statistics
└── charts/                     # All charts
```

---

### ❓ Need Help?

- See `README.md` for full documentation
- Run `python overmortal_tracker.py --help` for command options
- Check `example_usage.py` for code examples

---

**Happy tracking! May your cultivation be swift! 🎮**
