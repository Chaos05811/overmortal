#!/usr/bin/env python3
"""
Robust parser for Overmortal progression logs.
Handles all format variations found in real log data including:
- Year tracking with automatic rollover (Dec -> Jan)
- Multiple date formats (Month Day(suffix) - Time, Month Day, Time -)
- Typos (Celesital, MIin, Ys, etc.)
- Various G-level patterns (bt to, Breakthrough to, G{N} at)
- Flexible time-to-next parsing (missing 'or', dash, 'and' instead of 'Hrs')
- Unknown/missing values (??.??%)
- Mixed-content lines (breakthrough + time on same line)
"""

import re
from datetime import datetime
from typing import List, Dict, Optional
import json

MONTH_MAP = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}

MONTH_NAMES_RE = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'


class ProgressionEntry:
    """Represents a single progression log entry"""

    def __init__(self):
        self.raw_text = ""
        self.date = None
        self.time = None
        self.stage_name = None
        self.stage_percent = None
        self.g_level = None
        self.g_percent = None
        self.years_to_next = None
        self.hours_to_next = None
        self.minutes_to_next = None
        self.next_milestone = None
        self.is_breakthrough = False
        self.notes = []
        self.is_predicted = False

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        return {
            'date': self.date.isoformat() if self.date else None,
            'time': self.time,
            'stage_name': self.stage_name,
            'stage_percent': self.stage_percent,
            'g_level': self.g_level,
            'g_percent': self.g_percent,
            'years_to_next': self.years_to_next,
            'hours_to_next': self.hours_to_next,
            'minutes_to_next': self.minutes_to_next,
            'next_milestone': self.next_milestone,
            'is_breakthrough': self.is_breakthrough,
            'notes': self.notes,
            'is_predicted': self.is_predicted,
        }


class LogParser:
    """Robust parser for Overmortal progression logs"""

    def __init__(self, log_file: str):
        self.log_file = log_file
        self.entries: List[ProgressionEntry] = []
        self.base_year = 2025

    def parse(self) -> List[ProgressionEntry]:
        """Parse the entire log file into structured entries"""
        with open(self.log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract base year from header (e.g. "2025" on its own line)
        year_match = re.search(r'^\s*(\d{4})\s*$', content, re.MULTILINE)
        if year_match:
            self.base_year = int(year_match.group(1))

        # Split content into entry blocks at month-name boundaries
        pattern = rf'(?=\s*{MONTH_NAMES_RE}\s+\d{{1,2}})'
        raw_blocks = re.split(pattern, content, flags=re.IGNORECASE)

        current_year = self.base_year
        prev_month = None

        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue

            # Skip non-entry blocks (headers, notes)
            if not re.match(MONTH_NAMES_RE, block, re.IGNORECASE):
                continue

            entry = self._parse_block(block, current_year)
            if not entry or not entry.date:
                continue

            # Year rollover detection: Dec -> Jan
            month = entry.date.month
            if prev_month is not None and prev_month >= 10 and month <= 2:
                current_year += 1
                entry.date = entry.date.replace(year=current_year)
            prev_month = month

            self.entries.append(entry)

        return self.entries

    # ------------------------------------------------------------------ #
    #  Block-level parsing
    # ------------------------------------------------------------------ #

    def _parse_block(self, block: str, year: int) -> Optional[ProgressionEntry]:
        """Parse a single entry block into a ProgressionEntry"""
        lines = block.strip().split('\n')
        if not lines:
            return None

        header = lines[0].strip()

        entry = ProgressionEntry()
        entry.raw_text = block

        # --- Header fields ---
        entry.date = self._parse_date(header, year)
        entry.time = self._parse_time(header)
        entry.stage_name = self._parse_stage(header)
        entry.stage_percent = self._parse_stage_percent(header)
        entry.is_predicted = bool(re.search(r'predicted|chatgpt', header, re.IGNORECASE))

        if not entry.date:
            return None

        # --- Body fields (search all text for robustness) ---
        all_text = '\n'.join(lines)
        body_text = '\n'.join(lines[1:]) if len(lines) > 1 else ''

        self._parse_breakthrough(all_text, entry)
        self._parse_g_info(body_text or all_text, entry)
        self._parse_time_to_next(all_text, entry)

        # Collect notes from body lines
        for line in lines[1:]:
            stripped = line.strip()
            if stripped:
                entry.notes.append(stripped)

        return entry

    # ------------------------------------------------------------------ #
    #  Header field extractors
    # ------------------------------------------------------------------ #

    def _parse_date(self, header: str, year: int) -> Optional[datetime]:
        """Extract datetime from header, handling multiple formats"""
        match = re.search(
            rf'({MONTH_NAMES_RE})\s+(\d{{1,2}})(?:st|nd|rd|th)?',
            header, re.IGNORECASE,
        )
        if not match:
            return None

        month_str = match.group(1).lower()
        day = int(match.group(2))
        month = MONTH_MAP.get(month_str)
        if not month:
            return None

        # Extract time component
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', header, re.IGNORECASE)
        hour, minute = 12, 0  # default noon if time unknown
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            ampm = time_match.group(3).upper()
            if ampm == 'PM' and hour != 12:
                hour += 12
            elif ampm == 'AM' and hour == 12:
                hour = 0

        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            try:
                return datetime(year, month, min(day, 28), hour, minute)
            except Exception:
                return None

    def _parse_time(self, header: str) -> Optional[str]:
        """Extract display time string"""
        m = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', header, re.IGNORECASE)
        if m:
            return f"{m.group(1)}:{m.group(2)} {m.group(3).upper()}"
        return None

    def _parse_stage(self, header: str) -> Optional[str]:
        """Extract stage name, handling typos like 'Celesital'"""
        m = re.search(r'(Celesti\w+|Eternal)\s+(Early|Middle|Late)', header, re.IGNORECASE)
        if m:
            realm = 'Celestial' if m.group(1).lower().startswith('celesti') else 'Eternal'
            return f"{realm} {m.group(2).capitalize()}"
        return None

    def _parse_stage_percent(self, header: str) -> Optional[float]:
        """Extract stage completion percentage from (XX.X%)"""
        m = re.search(r'\((\d+\.?\d*)%\)', header)
        return float(m.group(1)) if m else None

    # ------------------------------------------------------------------ #
    #  Body field extractors
    # ------------------------------------------------------------------ #

    def _parse_breakthrough(self, text: str, entry: ProgressionEntry):
        """Extract breakthrough info (supports 'bt to' and 'Breakthrough to')"""
        patterns = [
            # "Breakthrough to Celestial Middle G1 at 6%"
            r'(?:bt|[Bb]reakthrough)\s+to\s+(?:Celestial|Eternal)\s+\w+\s+G(\d+)\s+at\s+(\d+\.?\d*)%',
            # "Breakthrough to G3 at 16.3%"
            r'(?:bt|[Bb]reakthrough)\s+to\s+G(\d+)\s+at\s+(\d+\.?\d*)%',
            # "Breakthrough to Celestial Middle G1" (no percent)
            r'(?:bt|[Bb]reakthrough)\s+to\s+(?:Celestial|Eternal)\s+\w+\s+G(\d+)',
            # "Breakthrough to G8" (no percent)
            r'(?:bt|[Bb]reakthrough)\s+to\s+G(\d+)',
            # "Breakthrough to Celestial Middle" (stage transition, no G level)
            r'(?:bt|[Bb]reakthrough)\s+to\s+(?:Celestial|Eternal)\s+(?:Early|Middle|Late)',
        ]

        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                entry.is_breakthrough = True
                groups = m.groups()
                if groups and groups[0] and groups[0].isdigit():
                    entry.g_level = int(groups[0])
                if len(groups) >= 2 and groups[1]:
                    entry.g_percent = float(groups[1])
                return

        # Catch-all for any other breakthrough mention
        if re.search(r'(?:bt|breakthrough)\s+to\s+', text, re.IGNORECASE):
            entry.is_breakthrough = True

    def _parse_g_info(self, text: str, entry: ProgressionEntry):
        """Extract G-level and percentage from body text"""
        # "G{N} at {X}%"
        matches = re.findall(r'G(\d+)\s+at\s+(\d+\.?\d*)\s*%', text, re.IGNORECASE)
        if matches:
            g_str, pct_str = matches[-1]  # last match is most relevant
            entry.g_level = int(g_str)
            entry.g_percent = float(pct_str)
            return

        # "currently at X%" (for "Almost Breakthrough" lines)
        if entry.g_percent is None:
            m = re.search(r'currently\s+at\s+(\d+\.?\d*)%', text, re.IGNORECASE)
            if m:
                entry.g_percent = float(m.group(1))

    def _parse_time_to_next(self, text: str, entry: ProgressionEntry):
        """Extract time-to-next-milestone, handling many format quirks"""
        # --- Years: "Yrs", "Ys", "Year", "Years" ---
        m = re.search(r'(\d+\.?\d*)\s*(?:Yrs?|Ys|Years?)\b', text, re.IGNORECASE)
        if m:
            entry.years_to_next = float(m.group(1))

        # --- Hours: "Hrs", "Hr", "Hours", "hrs" ---
        m = re.search(r'(\d+)\s*(?:Hrs?|Hours?|hrs)\b', text, re.IGNORECASE)
        if m:
            entry.hours_to_next = int(m.group(1))

        # --- Minutes: "Min", "Minutes", "MIin", "MIn" ---
        m = re.search(r'(\d+)\s*(?:Min(?:utes?)?|MIin|MIn)\b', text, re.IGNORECASE)
        if m:
            entry.minutes_to_next = int(m.group(1))

        # Special: "157 and 27 Min" (hours written without "Hrs" label)
        if entry.hours_to_next is None:
            m = re.search(r'(\d+)\s+and\s+(\d+)\s*(?:Min|MIin|MIn)', text, re.IGNORECASE)
            if m:
                entry.hours_to_next = int(m.group(1))
                entry.minutes_to_next = int(m.group(2))

        # --- Next milestone: take the LAST "to {target}" occurrence ---
        milestone_hits = re.findall(
            r'to\s+(G\d+|(?:Celestial|Eternal)\s+(?:Early|Middle|Late)(?:\s+G\d+)?)',
            text, re.IGNORECASE,
        )
        if milestone_hits:
            entry.next_milestone = milestone_hits[-1]

    # ------------------------------------------------------------------ #
    #  Export helpers
    # ------------------------------------------------------------------ #

    def to_json(self, output_file: str):
        """Export all entries to JSON"""
        data = [e.to_dict() for e in self.entries]
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def get_stage_entries(self, stage_name: str) -> List[ProgressionEntry]:
        """Filter entries by stage name"""
        return [e for e in self.entries if e.stage_name == stage_name]

    def get_g_level_entries(self, g_level: int) -> List[ProgressionEntry]:
        """Filter entries by G level"""
        return [e for e in self.entries if e.g_level == g_level]


# ----------------------------------------------------------------------- #
#  Standalone test
# ----------------------------------------------------------------------- #

if __name__ == "__main__":
    parser = LogParser("prog.txt")
    entries = parser.parse()

    print(f"Parsed {len(entries)} entries")
    parser.to_json("progression_data.json")
    print("Exported to progression_data.json")

    # Show first 5 entries
    for entry in entries[:5]:
        print(f"\n{entry.date} - {entry.stage_name} ({entry.stage_percent}%)")
        if entry.g_level is not None:
            pct = f" at {entry.g_percent}%" if entry.g_percent is not None else ""
            print(f"  G{entry.g_level}{pct}")
        if entry.is_breakthrough:
            print("  [BREAKTHROUGH]")
        if entry.hours_to_next is not None:
            mins = entry.minutes_to_next or 0
            print(f"  {entry.years_to_next} Yrs / {entry.hours_to_next} Hrs {mins} Min -> {entry.next_milestone}")

    print(f"\n--- Last 3 entries ---")
    for entry in entries[-3:]:
        print(f"\n{entry.date} - {entry.stage_name} ({entry.stage_percent}%)")
        if entry.g_level is not None:
            pct = f" at {entry.g_percent}%" if entry.g_percent is not None else ""
            print(f"  G{entry.g_level}{pct}")
        if entry.hours_to_next is not None:
            mins = entry.minutes_to_next or 0
            print(f"  {entry.years_to_next} Yrs / {entry.hours_to_next} Hrs {mins} Min -> {entry.next_milestone}")
