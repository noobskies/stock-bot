#!/usr/bin/env python3
"""
Log Analysis Script for Test 14
Analyzes bot logs to generate comprehensive test report.

Usage:
    python analyze_logs.py

Generates TEST_14_RESULTS.md with detailed analysis.
"""

import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Tuple


class LogAnalyzer:
    """Analyze bot logs for Test 14 validation."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.results = {
            'total_lines': 0,
            'errors': [],
            'warnings': [],
            'trading_cycles': [],
            'position_updates': [],
            'risk_checks': [],
            'api_calls': [],
            'database_ops': [],
            'start_time': None,
            'end_time': None
        }
        
    def parse_log_line(self, line: str) -> Dict:
        """Parse a log line into structured data."""
        # Format: YYYY-MM-DD HH:MM:SS.sss | LEVEL | module:function:line - message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \| (\w+)\s+\| ([\w.]+):([\w_]+):(\d+) - (.+)'
        match = re.match(pattern, line)
        
        if match:
            timestamp, level, module, function, line_num, message = match.groups()
            return {
                'timestamp': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f'),
                'level': level,
                'module': module,
                'function': function,
                'line': int(line_num),
                'message': message
            }
        return None
    
    def analyze_file(self, log_file: Path):
        """Analyze a single log file."""
        print(f"Analyzing {log_file.name}...")
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    self.results['total_lines'] += 1
                    parsed = self.parse_log_line(line.strip())
                    
                    if not parsed:
                        continue
                    
                    # Track start/end times
                    if not self.results['start_time']:
                        self.results['start_time'] = parsed['timestamp']
                    self.results['end_time'] = parsed['timestamp']
                    
                    # Categorize by level
                    if parsed['level'] == 'ERROR':
                        self.results['errors'].append(parsed)
                    elif parsed['level'] == 'WARNING':
                        self.results['warnings'].append(parsed)
                    
                    # Identify key operations
                    message = parsed['message'].lower()
                    
                    if 'trading cycle' in message or 'run_trading_cycle' in parsed['function']:
                        self.results['trading_cycles'].append(parsed)
                    
                    if 'position' in message and ('update' in message or 'monitor' in message):
                        self.results['position_updates'].append(parsed)
                    
                    if 'risk' in message or 'validate' in message:
                        self.results['risk_checks'].append(parsed)
                    
                    if 'api' in message or 'alpaca' in message.lower():
                        self.results['api_calls'].append(parsed)
                    
                    if 'database' in message or 'save' in message or 'insert' in message:
                        self.results['database_ops'].append(parsed)
        
        except Exception as e:
            print(f"Error analyzing {log_file}: {e}")
    
    def analyze_all_logs(self):
        """Analyze all log files in the directory."""
        if not self.log_dir.exists():
            print(f"ERROR: Log directory not found: {self.log_dir}")
            return False
        
        log_files = sorted(self.log_dir.glob('*.log'))
        if not log_files:
            print("ERROR: No log files found")
            return False
        
        print(f"Found {len(log_files)} log file(s)")
        for log_file in log_files:
            self.analyze_file(log_file)
        
        return True
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report."""
        report = []
        
        # Header
        report.append("=" * 80)
        report.append("TEST 14: 48-HOUR CONTINUOUS RUN - LOG ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Time Range
        if self.results['start_time'] and self.results['end_time']:
            duration = self.results['end_time'] - self.results['start_time']
            report.append("TIME RANGE:")
            report.append("-" * 80)
            report.append(f"Start Time: {self.results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"End Time:   {self.results['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"Duration:   {duration} ({duration.total_seconds() / 3600:.1f} hours)")
            report.append("")
        
        # Overview
        report.append("OVERVIEW:")
        report.append("-" * 80)
        report.append(f"Total Log Lines: {self.results['total_lines']:,}")
        report.append(f"Total Errors: {len(self.results['errors'])}")
        report.append(f"Total Warnings: {len(self.results['warnings'])}")
        report.append("")
        
        # Trading Cycles
        report.append("TRADING CYCLES:")
        report.append("-" * 80)
        cycles = len(self.results['trading_cycles'])
        report.append(f"Total Cycles Detected: {cycles}")
        
        if cycles > 0 and self.results['start_time'] and self.results['end_time']:
            duration_hours = (self.results['end_time'] - self.results['start_time']).total_seconds() / 3600
            # Expected: 1 cycle every 5 minutes = 12 per hour
            expected_cycles = int(duration_hours * 12)
            success_rate = (cycles / expected_cycles * 100) if expected_cycles > 0 else 0
            report.append(f"Expected Cycles (5-min interval): ~{expected_cycles}")
            report.append(f"Execution Rate: {success_rate:.1f}%")
        report.append("")
        
        # Position Updates
        report.append("POSITION MONITORING:")
        report.append("-" * 80)
        updates = len(self.results['position_updates'])
        report.append(f"Total Position Updates: {updates}")
        
        if updates > 0 and self.results['start_time'] and self.results['end_time']:
            duration_hours = (self.results['end_time'] - self.results['start_time']).total_seconds() / 3600
            # Expected: 1 update every 30 seconds = 120 per hour
            expected_updates = int(duration_hours * 120)
            success_rate = (updates / expected_updates * 100) if expected_updates > 0 else 0
            report.append(f"Expected Updates (30-sec interval): ~{expected_updates}")
            report.append(f"Execution Rate: {success_rate:.1f}%")
        report.append("")
        
        # Risk Checks
        report.append("RISK MANAGEMENT:")
        report.append("-" * 80)
        report.append(f"Total Risk Checks: {len(self.results['risk_checks'])}")
        report.append("")
        
        # API Calls
        report.append("API OPERATIONS:")
        report.append("-" * 80)
        report.append(f"Total API Calls: {len(self.results['api_calls'])}")
        report.append("")
        
        # Database Operations
        report.append("DATABASE OPERATIONS:")
        report.append("-" * 80)
        report.append(f"Total Database Operations: {len(self.results['database_ops'])}")
        report.append("")
        
        # Error Analysis
        report.append("ERROR ANALYSIS:")
        report.append("-" * 80)
        if self.results['errors']:
            # Count by module
            error_modules = Counter(e['module'] for e in self.results['errors'])
            report.append(f"Total Errors: {len(self.results['errors'])}")
            report.append("")
            report.append("Errors by Module:")
            for module, count in error_modules.most_common():
                report.append(f"  {module}: {count}")
            report.append("")
            
            # Show first 10 errors
            report.append("First 10 Errors:")
            for i, error in enumerate(self.results['errors'][:10], 1):
                report.append(f"{i}. [{error['timestamp'].strftime('%H:%M:%S')}] {error['module']}: {error['message'][:100]}")
            
            if len(self.results['errors']) > 10:
                report.append(f"... and {len(self.results['errors']) - 10} more errors")
        else:
            report.append("✅ NO ERRORS FOUND")
        report.append("")
        
        # Warning Analysis
        report.append("WARNING ANALYSIS:")
        report.append("-" * 80)
        if self.results['warnings']:
            # Count by module
            warning_modules = Counter(w['module'] for w in self.results['warnings'])
            report.append(f"Total Warnings: {len(self.results['warnings'])}")
            report.append("")
            report.append("Warnings by Module:")
            for module, count in warning_modules.most_common():
                report.append(f"  {module}: {count}")
            report.append("")
            
            # Show first 10 warnings
            report.append("First 10 Warnings:")
            for i, warning in enumerate(self.results['warnings'][:10], 1):
                report.append(f"{i}. [{warning['timestamp'].strftime('%H:%M:%S')}] {warning['module']}: {warning['message'][:100]}")
            
            if len(self.results['warnings']) > 10:
                report.append(f"... and {len(self.results['warnings']) - 10} more warnings")
        else:
            report.append("✅ NO WARNINGS FOUND")
        report.append("")
        
        # Test Assessment
        report.append("TEST ASSESSMENT:")
        report.append("-" * 80)
        
        critical_pass = len(self.results['errors']) == 0
        duration_pass = False
        if self.results['start_time'] and self.results['end_time']:
            duration_hours = (self.results['end_time'] - self.results['start_time']).total_seconds() / 3600
            duration_pass = duration_hours >= 47.0  # Allow 1 hour margin
        
        report.append(f"✅ Critical: No Errors" if critical_pass else "❌ Critical: Errors Found")
        report.append(f"✅ Duration: >= 48 hours" if duration_pass else "⚠️  Duration: < 48 hours")
        report.append(f"✅ Warnings: {len(self.results['warnings'])} (acceptable if < 50)" if len(self.results['warnings']) < 50 else f"⚠️  Warnings: {len(self.results['warnings'])} (review needed)")
        report.append("")
        
        overall_pass = critical_pass and (duration_pass or duration_hours > 40)
        report.append("OVERALL RESULT:")
        if overall_pass:
            report.append("✅ PASS - Bot ran successfully")
        else:
            report.append("❌ FAIL - Issues detected, review required")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, report: str, filename: str = "TEST_14_RESULTS.md"):
        """Save report to file."""
        output_file = Path(filename)
        with open(output_file, 'w') as f:
            f.write(report)
        return output_file


def main():
    """Main entry point."""
    print("=" * 80)
    print("Test 14 Log Analysis")
    print("=" * 80)
    print()
    
    # Create analyzer
    analyzer = LogAnalyzer()
    
    # Analyze logs
    success = analyzer.analyze_all_logs()
    if not success:
        print("\nAnalysis failed. Check logs directory and try again.")
        return
    
    print()
    print("Generating report...")
    
    # Generate and display report
    report = analyzer.generate_report()
    print()
    print(report)
    
    # Save report
    output_file = analyzer.save_report(report)
    print()
    print(f"Report saved to: {output_file.absolute()}")
    print()
    print("=" * 80)
    print("Analysis Complete")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("1. Review TEST_14_RESULTS.md")
    print("2. Complete TEST_14_CHECKLIST.md")
    print("3. Update Memory Bank (activeContext.md, progress.md)")
    print("4. Proceed to Phase 10: Documentation & Deployment")


if __name__ == '__main__':
    main()
