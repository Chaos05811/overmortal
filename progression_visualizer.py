import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import List, Dict
import numpy as np

class ProgressionVisualizer:
    """Creates visualizations for Overmortal progression data"""
    
    def __init__(self, data_file: str):
        with open(data_file, 'r') as f:
            self.data = json.load(f)
        
        # Convert date strings to datetime
        for entry in self.data:
            if entry['date']:
                entry['date'] = datetime.fromisoformat(entry['date'])
        
        # Sort by date
        self.data.sort(key=lambda x: x['date'] if x['date'] else datetime.min)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
    
    def plot_overall_progression(self, output_file: str = 'overall_progression.png'):
        """Plot overall stage progression over time"""
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Group by stage
        stages = {}
        for entry in self.data:
            if entry['stage_name'] and entry['date'] and entry['stage_percent'] is not None:
                if entry['stage_name'] not in stages:
                    stages[entry['stage_name']] = {'dates': [], 'percents': []}
                stages[entry['stage_name']]['dates'].append(entry['date'])
                stages[entry['stage_name']]['percents'].append(entry['stage_percent'])
        
        # Plot each stage
        colors = {
            'Celestial Early': '#3498db',
            'Celestial Middle': '#2ecc71',
            'Celestial Late': '#f39c12',
            'Eternal Early': '#e74c3c',
            'Eternal Middle': '#9b59b6',
            'Eternal Late': '#1abc9c'
        }
        
        for stage_name, stage_data in stages.items():
            color = colors.get(stage_name, '#95a5a6')
            ax.plot(stage_data['dates'], stage_data['percents'], 
                   marker='o', markersize=3, linewidth=2, 
                   label=stage_name, color=color, alpha=0.8)
        
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Stage Progress (%)', fontsize=12, fontweight='bold')
        ax.set_title('Overmortal Progression Over Time', fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='best', framealpha=0.9, fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved overall progression chart to {output_file}")
        plt.close()
    
    def plot_g_level_progression(self, stage_name: str = None, 
                                 output_file: str = 'g_level_progression.png'):
        """Plot G level progression"""
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Filter data
        filtered_data = self.data
        if stage_name:
            filtered_data = [e for e in self.data if e['stage_name'] == stage_name]
        
        # Group by G level
        g_levels = {}
        for entry in filtered_data:
            if entry['g_level'] and entry['date'] and entry['g_percent'] is not None:
                if entry['g_level'] not in g_levels:
                    g_levels[entry['g_level']] = {'dates': [], 'percents': []}
                g_levels[entry['g_level']]['dates'].append(entry['date'])
                g_levels[entry['g_level']]['percents'].append(entry['g_percent'])
        
        # Plot each G level
        cmap = plt.get_cmap('tab20')
        for idx, (g_level, g_data) in enumerate(sorted(g_levels.items())):
            color = cmap(idx / max(len(g_levels), 1))
            ax.plot(g_data['dates'], g_data['percents'], 
                   marker='o', markersize=2, linewidth=1.5,
                   label=f'G{g_level}', color=color, alpha=0.7)
        
        title = f'G Level Progression - {stage_name}' if stage_name else 'G Level Progression - All Stages'
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('G Level Progress (%)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Only show legend if not too many items
        if len(g_levels) <= 15:
            ax.legend(loc='best', framealpha=0.9, fontsize=8, ncol=2)
        
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved G level progression chart to {output_file}")
        plt.close()
    
    def plot_daily_progress_rate(self, output_file: str = 'daily_progress_rate.png'):
        """Plot daily progress rate"""
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Calculate daily progress rates
        dates = []
        rates = []
        
        for i in range(1, len(self.data)):
            prev = self.data[i-1]
            curr = self.data[i]
            
            if (prev['date'] and curr['date'] and 
                prev['stage_percent'] is not None and 
                curr['stage_percent'] is not None and
                prev['stage_name'] == curr['stage_name']):
                
                days = (curr['date'] - prev['date']).days or 1
                progress = curr['stage_percent'] - prev['stage_percent']
                
                if progress > 0:  # Only positive progress
                    rate = progress / days
                    dates.append(curr['date'])
                    rates.append(rate)
        
        # Plot
        ax.plot(dates, rates, marker='o', markersize=3, linewidth=1.5, 
               color='#3498db', alpha=0.7)
        
        # Add moving average
        if len(rates) >= 7:
            window = 7
            moving_avg = np.convolve(rates, np.ones(window)/window, mode='valid')
            moving_avg_dates = dates[window-1:]
            ax.plot(moving_avg_dates, moving_avg, linewidth=3, 
                   color='#e74c3c', label=f'{window}-day Moving Average', alpha=0.8)
        
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Progress Rate (% per day)', fontsize=12, fontweight='bold')
        ax.set_title('Daily Progression Rate', fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved daily progress rate chart to {output_file}")
        plt.close()
    
    def plot_stage_comparison(self, output_file: str = 'stage_comparison.png'):
        """Compare time spent and progress rate across stages"""
        from progression_analyzer import ProgressionAnalyzer
        
        analyzer = ProgressionAnalyzer('progression_data.json')
        
        stages = ['Celestial Early', 'Celestial Middle', 'Celestial Late',
                  'Eternal Early', 'Eternal Middle', 'Eternal Late']
        
        stage_stats = []
        for stage in stages:
            stats = analyzer.get_stage_statistics(stage)
            if stats and stats.get('days_spent'):
                stage_stats.append(stats)
        
        if not stage_stats:
            print("Not enough data for stage comparison")
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Plot 1: Days spent per stage
        stage_names = [s['stage_name'] for s in stage_stats]
        days_spent = [s['days_spent'] for s in stage_stats]
        
        colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#1abc9c']
        ax1.bar(range(len(stage_names)), days_spent, color=colors[:len(stage_names)], alpha=0.8)
        ax1.set_xticks(range(len(stage_names)))
        ax1.set_xticklabels([s.replace(' ', '\n') for s in stage_names], fontsize=9)
        ax1.set_ylabel('Days Spent', fontsize=12, fontweight='bold')
        ax1.set_title('Time Spent per Stage', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Plot 2: Average daily progress
        daily_progress = [s['daily_progress_avg'] for s in stage_stats]
        ax2.bar(range(len(stage_names)), daily_progress, color=colors[:len(stage_names)], alpha=0.8)
        ax2.set_xticks(range(len(stage_names)))
        ax2.set_xticklabels([s.replace(' ', '\n') for s in stage_names], fontsize=9)
        ax2.set_ylabel('Daily Progress (%)', fontsize=12, fontweight='bold')
        ax2.set_title('Average Daily Progress per Stage', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved stage comparison chart to {output_file}")
        plt.close()
    
    def plot_hours_to_next_milestone(self, output_file: str = 'time_to_milestone.png'):
        """Plot estimated hours to next milestone over time"""
        fig, ax = plt.subplots(figsize=(14, 7))
        
        dates = []
        hours = []
        
        for entry in self.data:
            if entry['date'] and entry['hours_to_next'] is not None:
                dates.append(entry['date'])
                hours.append(entry['hours_to_next'])
        
        if not dates:
            print("No milestone data available")
            return
        
        ax.plot(dates, hours, marker='o', markersize=3, linewidth=1.5, 
               color='#9b59b6', alpha=0.7)
        
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Hours to Next Milestone', fontsize=12, fontweight='bold')
        ax.set_title('Time to Next Breakthrough Over Time', fontsize=16, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Saved time to milestone chart to {output_file}")
        plt.close()
    
    def generate_all_charts(self, output_dir: str = '.'):
        """Generate all available charts"""
        import os
        
        if output_dir != '.' and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print("Generating charts...")
        self.plot_overall_progression(f'{output_dir}/overall_progression.png')
        self.plot_g_level_progression(output_file=f'{output_dir}/g_level_progression.png')
        self.plot_daily_progress_rate(f'{output_dir}/daily_progress_rate.png')
        self.plot_stage_comparison(f'{output_dir}/stage_comparison.png')
        self.plot_hours_to_next_milestone(f'{output_dir}/time_to_milestone.png')
        
        # Generate stage-specific G level charts
        for stage in ['Eternal Early', 'Eternal Middle', 'Eternal Late']:
            safe_name = stage.replace(' ', '_').lower()
            self.plot_g_level_progression(stage, f'{output_dir}/g_level_{safe_name}.png')
        
        print("\nAll charts generated successfully!")


if __name__ == "__main__":
    visualizer = ProgressionVisualizer('progression_data.json')
    visualizer.generate_all_charts(output_dir='charts')
