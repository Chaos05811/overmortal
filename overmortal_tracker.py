#!/usr/bin/env python3
"""
Overmortal Progression Tracker - Main Dashboard

This tool integrates OCR extraction, data parsing, analysis, and visualization
for tracking your Overmortal game progression.

Usage:
    python overmortal_tracker.py [command] [options]

Commands:
    extract     - Extract data from screenshots using OCR
    parse       - Parse existing progression log into structured data
    analyze     - Analyze progression and generate statistics
    visualize   - Create progression charts and visualizations
    all         - Run complete pipeline (parse + analyze + visualize)
    report      - Generate comprehensive text report
"""

import argparse
import os
import sys
from datetime import datetime, date

def check_dependencies():
    """Check if required dependencies are installed"""
    required = {
        'pytesseract': 'pytesseract',
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'matplotlib': 'matplotlib',
        'numpy': 'numpy'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("Missing required packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nInstall with:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def run_extraction(image_dir: str, output_dir: str = "output"):
    """Run OCR extraction on screenshots"""
    print("\n" + "="*60)
    print("EXTRACTING DATA FROM SCREENSHOTS")
    print("="*60 + "\n")
    
    try:
        from improved_ocr import OvermortalOCR
        
        if not os.path.exists(image_dir):
            print(f"Error: Image directory '{image_dir}' not found!")
            return False
        
        extractor = OvermortalOCR(image_dir, output_dir)
        extractor.run()
        return True
    
    except Exception as e:
        print(f"Error during extraction: {e}")
        return False


def run_parsing(log_file: str = "progression_log.txt", output_file: str = "progression_data.json"):
    """Parse progression log into structured JSON"""
    print("\n" + "="*60)
    print("PARSING PROGRESSION LOG")
    print("="*60 + "\n")
    
    try:
        from log_parser import LogParser
        
        if not os.path.exists(log_file):
            print(f"Error: Log file '{log_file}' not found!")
            print("Have you run the extraction step or do you have an existing log?")
            return False
        
        parser = LogParser(log_file)
        entries = parser.parse()
        
        print(f"Parsed {len(entries)} entries from log")
        
        parser.to_json(output_file)
        print(f"Saved structured data to {output_file}")
        
        return True
    
    except Exception as e:
        print(f"Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_analysis(data_file: str = "progression_data.json", output_file: str = "analysis_report.txt"):
    """Run analysis and generate report"""
    print("\n" + "="*60)
    print("ANALYZING PROGRESSION DATA")
    print("="*60 + "\n")
    
    try:
        from progression_analyzer import ProgressionAnalyzer
        
        if not os.path.exists(data_file):
            print(f"Error: Data file '{data_file}' not found!")
            print("Have you run the parsing step?")
            return False
        
        analyzer = ProgressionAnalyzer(data_file)
        
        # Generate and display report
        report = analyzer.get_summary_report()
        print(report)
        
        # Save to file
        with open(output_file, 'w') as f:
            f.write(report)
        
        print(f"\nReport saved to {output_file}")
        
        return True
    
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_visualization(data_file: str = "progression_data.json", output_dir: str = "charts"):
    """Generate visualizations"""
    print("\n" + "="*60)
    print("GENERATING VISUALIZATIONS")
    print("="*60 + "\n")
    
    try:
        from progression_visualizer import ProgressionVisualizer
        
        if not os.path.exists(data_file):
            print(f"Error: Data file '{data_file}' not found!")
            print("Have you run the parsing step?")
            return False
        
        visualizer = ProgressionVisualizer(data_file)
        visualizer.generate_all_charts(output_dir)
        
        print(f"\nCharts saved to {output_dir}/ directory")
        
        return True
    
    except Exception as e:
        print(f"Error during visualization: {e}")
        import traceback
        traceback.print_exc()
        return False


def add_entry(log_file: str = "prog.txt"):
    """Add a new progression entry to the log file via interactive prompts."""
    print("\n" + "=" * 60)
    print("ADD NEW PROGRESSION ENTRY")
    print("=" * 60 + "\n")

    # --- Date ---
    today = date.today()
    default_date = today.strftime("%B %d")  # e.g. "February 09"
    date_input = input(f"Date [{default_date}]: ").strip()
    if not date_input:
        date_input = default_date

    # --- Time ---
    now = datetime.now()
    default_time = now.strftime("%I:%M %p").lstrip("0")  # e.g. "8:53 AM"
    time_input = input(f"Time [{default_time}]: ").strip()
    if not time_input:
        time_input = default_time

    # --- Realm Phase ---
    realm_phase = input("Realm Phase (e.g. Eternal Late): ").strip()
    if not realm_phase:
        print("Realm Phase is required. Aborting.")
        return False

    # --- Overall % ---
    overall_pct = input("Overall % (e.g. 95.9): ").strip()
    if not overall_pct:
        print("Overall % is required. Aborting.")
        return False

    # Build header line:  "February 09, 8:53 AM - Eternal Late (95.9%)"
    header = f"{date_input}, {time_input} - {realm_phase} ({overall_pct}%)"

    # --- Optional action / context ---
    action = input("Action/context line (e.g. After Reset, Pills, Respires) [skip]: ").strip()

    # --- Grade status ---
    grade = input("Grade status (e.g. G20 at 49.4%  OR  bt to G5 at 1.6%) [skip]: ").strip()

    # --- Time remaining ---
    time_remaining = input("Time remaining (e.g. 616.458 Yrs or 154 Hrs 6 Min to G21) [skip]: ").strip()

    # --- Optional prediction / EST note ---
    prediction = input("EST / prediction note [skip]: ").strip()

    # Assemble entry
    lines = [header]
    if action:
        lines.append(action)
    if grade:
        lines.append(grade)
    if time_remaining:
        lines.append(time_remaining)
    if prediction:
        lines.append(prediction)

    entry_text = "\n".join(lines)

    # Preview
    print("\n--- Preview ---")
    print(entry_text)
    print("--- End Preview ---\n")

    confirm = input("Append this entry? [Y/n]: ").strip().lower()
    if confirm in ("n", "no"):
        print("Entry discarded.")
        return False

    # Append to file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\n" + entry_text + "\n")

    print(f"Entry appended to {log_file}")
    return True


def run_all_pipeline(log_file: str = "progression_log.txt"):
    """Run complete analysis pipeline"""
    print("\n" + "="*60)
    print("RUNNING COMPLETE ANALYSIS PIPELINE")
    print("="*60)
    
    # Parse
    if not run_parsing(log_file):
        return False
    
    # Analyze
    if not run_analysis():
        return False
    
    # Visualize
    if not run_visualization():
        return False
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETE!")
    print("="*60)
    print("\nGenerated files:")
    print("  - progression_data.json (structured data)")
    print("  - analysis_report.txt (statistics and insights)")
    print("  - charts/ (visualization charts)")
    print()
    
    return True


def interactive_mode():
    """Run interactive menu"""
    while True:
        print("\n" + "="*60)
        print("OVERMORTAL PROGRESSION TRACKER")
        print("="*60)
        print("\nWhat would you like to do?")
        print("  1. Extract data from screenshots (OCR)")
        print("  2. Parse progression log")
        print("  3. Analyze progression")
        print("  4. Generate visualizations")
        print("  5. Run complete pipeline (parse + analyze + visualize)")
        print("  6. Generate text report only")
        print("  7. Add new progression entry")
        print("  0. Exit")
        print()
        
        choice = input("Enter your choice (0-7): ").strip()
        
        if choice == '0':
            print("Goodbye!")
            break
        
        elif choice == '1':
            image_dir = input("Enter image directory path [./screenshots]: ").strip() or "./screenshots"
            run_extraction(image_dir)
        
        elif choice == '2':
            log_file = input("Enter log file path [progression_log.txt]: ").strip() or "progression_log.txt"
            run_parsing(log_file)
        
        elif choice == '3':
            run_analysis()
        
        elif choice == '4':
            run_visualization()
        
        elif choice == '5':
            log_file = input("Enter log file path [progression_log.txt]: ").strip() or "progression_log.txt"
            run_all_pipeline(log_file)
        
        elif choice == '6':
            run_analysis()
        
        elif choice == '7':
            log_file = input("Enter log file path [prog.txt]: ").strip() or "prog.txt"
            add_entry(log_file)
        
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Overmortal Progression Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract data from screenshots
  python overmortal_tracker.py extract --images ./screenshots

  # Parse existing log file
  python overmortal_tracker.py parse --log progression_log.txt

  # Run complete analysis
  python overmortal_tracker.py all

  # Run in interactive mode
  python overmortal_tracker.py
        """
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        choices=['extract', 'parse', 'analyze', 'visualize', 'all', 'report', 'add'],
        help='Command to run (omit for interactive mode)'
    )
    
    parser.add_argument(
        '--images',
        default='./screenshots',
        help='Directory containing screenshot images (for extract command)'
    )
    
    parser.add_argument(
        '--log',
        default='progression_log.txt',
        help='Progression log file path'
    )
    
    parser.add_argument(
        '--output',
        default='output',
        help='Output directory'
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Run command
    if args.command is None:
        # Interactive mode
        interactive_mode()
    
    elif args.command == 'extract':
        run_extraction(args.images, args.output)
    
    elif args.command == 'parse':
        run_parsing(args.log)
    
    elif args.command == 'analyze':
        run_analysis()
    
    elif args.command == 'visualize':
        run_visualization()
    
    elif args.command == 'all':
        run_all_pipeline(args.log)
    
    elif args.command == 'report':
        run_analysis()

    elif args.command == 'add':
        add_entry(args.log if args.log != 'progression_log.txt' else 'prog.txt')


if __name__ == "__main__":
    main()
