import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import statistics

class ProgressionAnalyzer:
    """Analyzes Overmortal progression data for insights and predictions"""
    
    def __init__(self, data_file: str):
        with open(data_file, 'r') as f:
            self.data = json.load(f)
        
        # Convert date strings back to datetime
        for entry in self.data:
            if entry['date']:
                entry['date'] = datetime.fromisoformat(entry['date'])
    
    def get_stage_statistics(self, stage_name: str) -> Dict:
        """Calculate statistics for a specific stage"""
        stage_entries = [e for e in self.data if e['stage_name'] == stage_name]
        
        if not stage_entries:
            return {}
        
        # Sort by date
        stage_entries.sort(key=lambda x: x['date'] if x['date'] else datetime.min)
        
        # Calculate time spent
        start_date = stage_entries[0]['date']
        end_date = stage_entries[-1]['date']
        
        if start_date and end_date:
            days_spent = (end_date - start_date).days + 1
        else:
            days_spent = None
        
        # Calculate average daily progress
        start_pct = stage_entries[0]['stage_percent']
        end_pct = stage_entries[-1]['stage_percent']
        
        if days_spent and start_pct is not None and end_pct is not None:
            daily_progress = (end_pct - start_pct) / days_spent
        else:
            daily_progress = None
        
        return {
            'stage_name': stage_name,
            'start_date': start_date.strftime('%B %d, %Y') if start_date else None,
            'end_date': end_date.strftime('%B %d, %Y') if end_date else None,
            'days_spent': days_spent,
            'start_percent': start_pct,
            'end_percent': end_pct,
            'total_progress': end_pct - start_pct if start_pct and end_pct else None,
            'daily_progress_avg': daily_progress,
            'entries_count': len(stage_entries)
        }
    
    def get_g_level_statistics(self, stage_name: str = None) -> List[Dict]:
        """Calculate statistics for each G level"""
        g_stats = defaultdict(list)
        
        # Group entries by G level
        for entry in self.data:
            if stage_name and entry['stage_name'] != stage_name:
                continue
            
            if entry['g_level'] and entry['date']:
                g_stats[entry['g_level']].append(entry)
        
        results = []
        for g_level, entries in sorted(g_stats.items()):
            entries.sort(key=lambda x: x['date'])
            
            start_date = entries[0]['date']
            end_date = entries[-1]['date']
            
            # Find breakthrough entry
            breakthrough_entry = None
            for e in entries:
                if e['g_percent'] and e['g_percent'] < 10:  # Likely just broke through
                    breakthrough_entry = e
                    break
            
            # Calculate time spent at this G level
            time_spent_hours = None
            if len(entries) > 1 and start_date and end_date:
                time_spent_hours = (end_date - start_date).total_seconds() / 3600
            
            results.append({
                'g_level': g_level,
                'stage_name': entries[0]['stage_name'],
                'start_date': start_date.strftime('%B %d, %Y') if start_date else None,
                'end_date': end_date.strftime('%B %d, %Y') if end_date else None,
                'time_spent_hours': round(time_spent_hours, 1) if time_spent_hours else None,
                'time_spent_days': round(time_spent_hours / 24, 1) if time_spent_hours else None,
                'entries_count': len(entries)
            })
        
        return results
    
    def calculate_progression_rate(self, stage_name: str = None, 
                                   last_n_days: int = 7) -> Dict:
        """Calculate recent progression rate"""
        recent_entries = []
        cutoff_date = datetime.now() - timedelta(days=last_n_days)
        
        for entry in self.data:
            if entry['date'] and entry['date'] >= cutoff_date:
                if stage_name is None or entry['stage_name'] == stage_name:
                    recent_entries.append(entry)
        
        if len(recent_entries) < 2:
            return {}
        
        recent_entries.sort(key=lambda x: x['date'])
        
        start = recent_entries[0]
        end = recent_entries[-1]
        
        if start['stage_percent'] and end['stage_percent']:
            days = (end['date'] - start['date']).days or 1
            pct_per_day = (end['stage_percent'] - start['stage_percent']) / days
            
            return {
                'period_days': days,
                'start_percent': start['stage_percent'],
                'end_percent': end['stage_percent'],
                'percent_per_day': round(pct_per_day, 3),
                'projected_days_to_100': round((100 - end['stage_percent']) / pct_per_day, 1) if pct_per_day > 0 else None
            }
        
        return {}
    
    def predict_breakthrough_date(self, stage_name: str, target_percent: float = 100) -> Optional[datetime]:
        """Predict when stage will reach target percentage"""
        rate = self.calculate_progression_rate(stage_name=stage_name)
        
        if not rate or not rate.get('percent_per_day'):
            return None
        
        recent_entries = [e for e in self.data if e['stage_name'] == stage_name]
        if not recent_entries:
            return None
        
        recent_entries.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)
        latest = recent_entries[0]
        
        if not latest['stage_percent'] or not latest['date']:
            return None
        
        remaining = target_percent - latest['stage_percent']
        days_needed = remaining / rate['percent_per_day']
        
        return latest['date'] + timedelta(days=days_needed)
    
    def get_efficiency_metrics(self) -> Dict:
        """Calculate overall efficiency metrics"""
        # Hours per percent progress at different stages
        efficiency_by_stage = {}
        
        for stage in ['Celestial Early', 'Celestial Middle', 'Celestial Late', 
                      'Eternal Early', 'Eternal Middle', 'Eternal Late']:
            stage_entries = [e for e in self.data if e['stage_name'] == stage]
            
            if len(stage_entries) < 2:
                continue
            
            stage_entries.sort(key=lambda x: x['date'] if x['date'] else datetime.min)
            
            total_hours = 0
            total_progress = 0
            
            for i in range(1, len(stage_entries)):
                prev = stage_entries[i-1]
                curr = stage_entries[i]
                
                if prev['date'] and curr['date'] and prev['stage_percent'] and curr['stage_percent']:
                    hours = (curr['date'] - prev['date']).total_seconds() / 3600
                    progress = curr['stage_percent'] - prev['stage_percent']
                    
                    if progress > 0:  # Only count forward progress
                        total_hours += hours
                        total_progress += progress
            
            if total_progress > 0:
                efficiency_by_stage[stage] = {
                    'hours_per_percent': round(total_hours / total_progress, 2),
                    'percent_per_day': round(24 * total_progress / total_hours, 3)
                }
        
        return efficiency_by_stage
    
    def get_summary_report(self) -> str:
        """Generate a comprehensive summary report"""
        lines = []
        lines.append("=" * 60)
        lines.append("OVERMORTAL PROGRESSION ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        # Overall statistics
        lines.append("OVERALL PROGRESS:")
        if self.data:
            first = min(self.data, key=lambda x: x['date'] if x['date'] else datetime.max)
            last = max(self.data, key=lambda x: x['date'] if x['date'] else datetime.min)
            
            lines.append(f"  Started: {first['date'].strftime('%B %d, %Y') if first['date'] else 'Unknown'}")
            lines.append(f"  Latest: {last['date'].strftime('%B %d, %Y') if last['date'] else 'Unknown'}")
            
            if first['date'] and last['date']:
                days = (last['date'] - first['date']).days + 1
                lines.append(f"  Total Days Tracked: {days}")
            
            lines.append(f"  Current Stage: {last['stage_name']} ({last['stage_percent']}%)")
            lines.append(f"  Current G Level: G{last['g_level']} ({last['g_percent']}%)")
        lines.append("")
        
        # Stage progression
        lines.append("STAGE PROGRESSION:")
        for stage in ['Celestial Early', 'Celestial Middle', 'Celestial Late',
                      'Eternal Early', 'Eternal Middle', 'Eternal Late']:
            stats = self.get_stage_statistics(stage)
            if stats and stats.get('days_spent'):
                lines.append(f"  {stage}:")
                lines.append(f"    Duration: {stats['days_spent']} days")
                lines.append(f"    Progress: {stats['start_percent']:.1f}% → {stats['end_percent']:.1f}%")
                if stats['daily_progress_avg']:
                    lines.append(f"    Avg Daily Progress: {stats['daily_progress_avg']:.3f}%")
        lines.append("")
        
        # Recent progression rate
        lines.append("RECENT PROGRESSION (Last 7 days):")
        rate = self.calculate_progression_rate(last_n_days=7)
        if rate:
            lines.append(f"  Period: {rate['period_days']} days")
            lines.append(f"  Progress: {rate['start_percent']:.1f}% → {rate['end_percent']:.1f}%")
            lines.append(f"  Rate: {rate['percent_per_day']:.3f}% per day")
            if rate['projected_days_to_100']:
                lines.append(f"  Projected Days to 100%: {rate['projected_days_to_100']}")
        lines.append("")
        
        # Efficiency metrics
        lines.append("EFFICIENCY BY STAGE:")
        efficiency = self.get_efficiency_metrics()
        for stage, metrics in efficiency.items():
            lines.append(f"  {stage}:")
            lines.append(f"    Hours per 1% progress: {metrics['hours_per_percent']}")
            lines.append(f"    Progress per day: {metrics['percent_per_day']}%")
        lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    analyzer = ProgressionAnalyzer("progression_data.json")
    
    # Print summary report
    print(analyzer.get_summary_report())
    
    # Get specific stage stats
    print("\nCelestial Early Stats:")
    print(json.dumps(analyzer.get_stage_statistics("Celestial Early"), indent=2))
    
    # Get G level stats
    print("\nG Level Statistics:")
    g_stats = analyzer.get_g_level_statistics()
    for stat in g_stats[:5]:
        print(json.dumps(stat, indent=2))
