#!/usr/bin/env python3
"""
Example usage script demonstrating all features of the Overmortal Tracker

This script shows how to use each component individually or together.
"""

from log_parser import LogParser, ProgressionEntry
from progression_analyzer import ProgressionAnalyzer
from progression_visualizer import ProgressionVisualizer
import json

def example_parsing():
    """Example: Parse a progression log file"""
    print("="*60)
    print("EXAMPLE 1: Parsing Progression Log")
    print("="*60)
    
    # Parse the log file
    parser = LogParser("progression_log.txt")
    entries = parser.parse()
    
    print(f"\nParsed {len(entries)} entries")
    
    # Show first entry
    if entries:
        first = entries[0]
        print(f"\nFirst entry:")
        print(f"  Date: {first.date}")
        print(f"  Stage: {first.stage_name} ({first.stage_percent}%)")
        print(f"  G Level: G{first.g_level} at {first.g_percent}%")
        print(f"  Time to next: {first.hours_to_next} hours")
    
    # Export to JSON
    parser.to_json("progression_data.json")
    print(f"\nExported to progression_data.json")
    
    # Filter by stage
    eternal_entries = parser.get_stage_entries("Eternal Middle")
    print(f"\nFound {len(eternal_entries)} Eternal Middle entries")
    
    print()

def example_analysis():
    """Example: Analyze progression data"""
    print("="*60)
    print("EXAMPLE 2: Analyzing Progression")
    print("="*60)
    
    analyzer = ProgressionAnalyzer("progression_data.json")
    
    # Get stage statistics
    print("\n--- Celestial Early Statistics ---")
    stats = analyzer.get_stage_statistics("Celestial Early")
    if stats:
        print(f"Duration: {stats['days_spent']} days")
        print(f"Progress: {stats['start_percent']}% → {stats['end_percent']}%")
        print(f"Daily progress: {stats['daily_progress_avg']:.3f}%")
    
    # Get recent progression rate
    print("\n--- Recent Progression Rate (7 days) ---")
    rate = analyzer.calculate_progression_rate(last_n_days=7)
    if rate:
        print(f"Period: {rate['period_days']} days")
        print(f"Rate: {rate['percent_per_day']:.3f}% per day")
        if rate['projected_days_to_100']:
            print(f"Days to 100%: {rate['projected_days_to_100']:.1f}")
    
    # Get G level statistics
    print("\n--- G Level Statistics ---")
    g_stats = analyzer.get_g_level_statistics()
    for stat in g_stats[:5]:  # Show first 5
        print(f"G{stat['g_level']}:")
        print(f"  Stage: {stat['stage_name']}")
        if stat['time_spent_days']:
            print(f"  Time: {stat['time_spent_days']:.1f} days")
    
    # Get efficiency metrics
    print("\n--- Efficiency by Stage ---")
    efficiency = analyzer.get_efficiency_metrics()
    for stage, metrics in efficiency.items():
        print(f"{stage}:")
        print(f"  Hours per 1%: {metrics['hours_per_percent']:.2f}")
        print(f"  % per day: {metrics['percent_per_day']:.3f}")
    
    # Predict breakthrough
    prediction = analyzer.predict_breakthrough_date("Celestial Early", 50)
    if prediction:
        print(f"\n--- Prediction ---")
        print(f"Expected to reach 50%: {prediction.strftime('%B %d, %Y')}")
    
    print()

def example_visualization():
    """Example: Create visualizations"""
    print("="*60)
    print("EXAMPLE 3: Creating Visualizations")
    print("="*60)
    
    visualizer = ProgressionVisualizer("progression_data.json")
    
    print("\nGenerating charts...")
    
    # Generate individual charts
    visualizer.plot_overall_progression("overall_progression.png")
    print("  ✓ Overall progression chart")
    
    visualizer.plot_g_level_progression(output_file="g_level_progression.png")
    print("  ✓ G level progression chart")
    
    visualizer.plot_daily_progress_rate("daily_progress_rate.png")
    print("  ✓ Daily progress rate chart")
    
    visualizer.plot_stage_comparison("stage_comparison.png")
    print("  ✓ Stage comparison chart")
    
    visualizer.plot_hours_to_next_milestone("time_to_milestone.png")
    print("  ✓ Time to milestone chart")
    
    # Generate all charts at once
    # visualizer.generate_all_charts(output_dir='all_charts')
    
    print("\nCharts saved successfully!")
    print()

def example_custom_analysis():
    """Example: Custom analysis using the data"""
    print("="*60)
    print("EXAMPLE 4: Custom Analysis")
    print("="*60)
    
    # Load data
    with open("progression_data.json", 'r') as f:
        data = json.load(f)
    
    # Find fastest G level progression
    from datetime import datetime
    
    g_times = {}
    for i in range(len(data) - 1):
        curr = data[i]
        next_entry = data[i + 1]
        
        if (curr['g_level'] and next_entry['g_level'] and 
            curr['g_level'] == next_entry['g_level'] and
            curr['date'] and next_entry['date']):
            
            curr_date = datetime.fromisoformat(curr['date'])
            next_date = datetime.fromisoformat(next_entry['date'])
            hours = (next_date - curr_date).total_seconds() / 3600
            
            g_level = curr['g_level']
            if g_level not in g_times:
                g_times[g_level] = []
            g_times[g_level].append(hours)
    
    print("\n--- Average Time per G Level ---")
    for g_level in sorted(g_times.keys())[:10]:
        avg_hours = sum(g_times[g_level]) / len(g_times[g_level])
        print(f"G{g_level}: {avg_hours:.1f} hours average")
    
    # Calculate total playtime
    if data:
        first_date = datetime.fromisoformat(data[0]['date'])
        last_date = datetime.fromisoformat(data[-1]['date'])
        total_days = (last_date - first_date).days + 1
        
        print(f"\n--- Overall Stats ---")
        print(f"Total tracking period: {total_days} days")
        print(f"Total entries: {len(data)}")
        print(f"Average entries per day: {len(data) / total_days:.1f}")
    
    print()

def main():
    """Run all examples"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║  OVERMORTAL PROGRESSION TRACKER - USAGE EXAMPLES         ║")
    print("╚" + "="*58 + "╝")
    print()
    
    # Run examples
    try:
        example_parsing()
        example_analysis()
        example_visualization()
        example_custom_analysis()
        
        print("="*60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*60)
        print()
        print("Generated files:")
        print("  - progression_data.json")
        print("  - overall_progression.png")
        print("  - g_level_progression.png")
        print("  - daily_progress_rate.png")
        print("  - stage_comparison.png")
        print("  - time_to_milestone.png")
        print()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
