#!/usr/bin/env python3
"""
Test 14 Monitoring Script - 48-Hour Continuous Run
Monitors bot health, system resources, and generates status reports.

Usage:
    python test_14_monitor.py

This script should be run in a separate terminal while the bot is running.
"""

import os
import sys
import time
import psutil
from datetime import datetime
from pathlib import Path
from typing import Optional
import subprocess


class BotMonitor:
    """Monitor bot process health and system resources."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.report_dir = Path("test_14_reports")
        self.report_dir.mkdir(exist_ok=True)
        self.last_log_size = 0
        
    def find_bot_process(self) -> Optional[psutil.Process]:
        """Find the running bot process."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'python' in cmdline[0].lower() and any('main.py' in arg for arg in cmdline):
                    return psutil.Process(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def get_process_stats(self, process: psutil.Process) -> dict:
        """Get process statistics."""
        try:
            with process.oneshot():
                return {
                    'pid': process.pid,
                    'status': process.status(),
                    'cpu_percent': process.cpu_percent(interval=1.0),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'num_threads': process.num_threads(),
                    'create_time': datetime.fromtimestamp(process.create_time())
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def get_system_stats(self) -> dict:
        """Get system statistics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1.0),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
    
    def check_log_files(self) -> dict:
        """Check log file status."""
        log_dir = Path('logs')
        if not log_dir.exists():
            return {'status': 'ERROR', 'message': 'logs/ directory not found'}
        
        log_files = list(log_dir.glob('*.log'))
        if not log_files:
            return {'status': 'WARNING', 'message': 'No log files found'}
        
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        log_size = latest_log.stat().st_size / 1024  # KB
        
        # Check for recent activity (file modified in last 5 minutes)
        mtime = datetime.fromtimestamp(latest_log.stat().st_mtime)
        age_minutes = (datetime.now() - mtime).total_seconds() / 60
        
        return {
            'status': 'OK' if age_minutes < 5 else 'WARNING',
            'latest_log': latest_log.name,
            'size_kb': log_size,
            'last_modified': mtime.strftime('%Y-%m-%d %H:%M:%S'),
            'age_minutes': age_minutes
        }
    
    def check_database(self) -> dict:
        """Check database status."""
        db_path = Path('trading_bot.db')
        if not db_path.exists():
            return {'status': 'ERROR', 'message': 'Database not found'}
        
        size_mb = db_path.stat().st_size / 1024 / 1024
        mtime = datetime.fromtimestamp(db_path.stat().st_mtime)
        age_minutes = (datetime.now() - mtime).total_seconds() / 60
        
        return {
            'status': 'OK',
            'size_mb': size_mb,
            'last_modified': mtime.strftime('%Y-%m-%d %H:%M:%S'),
            'age_minutes': age_minutes
        }
    
    def tail_errors(self, n: int = 10) -> list:
        """Get last N errors from error log."""
        error_log = Path('logs/errors.log')
        if not error_log.exists():
            return []
        
        try:
            with open(error_log, 'r') as f:
                lines = f.readlines()
                return lines[-n:] if lines else []
        except Exception as e:
            return [f"Failed to read error log: {e}"]
    
    def generate_report(self) -> str:
        """Generate status report."""
        now = datetime.now()
        uptime = now - self.start_time
        
        report = []
        report.append("=" * 80)
        report.append(f"Bot Monitor Report - {now.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Monitor Uptime: {uptime}")
        report.append("=" * 80)
        report.append("")
        
        # Bot process status
        report.append("BOT PROCESS STATUS:")
        report.append("-" * 80)
        bot_process = self.find_bot_process()
        if bot_process:
            stats = self.get_process_stats(bot_process)
            if stats:
                bot_uptime = now - stats['create_time']
                report.append(f"✅ Bot is RUNNING (PID: {stats['pid']})")
                report.append(f"   Status: {stats['status']}")
                report.append(f"   Uptime: {bot_uptime}")
                report.append(f"   CPU: {stats['cpu_percent']:.1f}%")
                report.append(f"   Memory: {stats['memory_mb']:.1f} MB")
                report.append(f"   Threads: {stats['num_threads']}")
            else:
                report.append("⚠️  Bot process found but cannot read stats")
        else:
            report.append("❌ Bot is NOT RUNNING")
        report.append("")
        
        # System resources
        report.append("SYSTEM RESOURCES:")
        report.append("-" * 80)
        sys_stats = self.get_system_stats()
        report.append(f"CPU Usage: {sys_stats['cpu_percent']:.1f}%")
        report.append(f"Memory Usage: {sys_stats['memory_percent']:.1f}%")
        report.append(f"Disk Usage: {sys_stats['disk_percent']:.1f}%")
        report.append("")
        
        # Log files
        report.append("LOG FILES:")
        report.append("-" * 80)
        log_status = self.check_log_files()
        if log_status['status'] == 'OK':
            report.append(f"✅ Logs are active")
            report.append(f"   Latest: {log_status['latest_log']}")
            report.append(f"   Size: {log_status['size_kb']:.1f} KB")
            report.append(f"   Last Modified: {log_status['last_modified']} ({log_status['age_minutes']:.1f} min ago)")
        else:
            report.append(f"⚠️  {log_status['status']}: {log_status.get('message', 'Unknown issue')}")
        report.append("")
        
        # Database
        report.append("DATABASE:")
        report.append("-" * 80)
        db_status = self.check_database()
        if db_status['status'] == 'OK':
            report.append(f"✅ Database exists")
            report.append(f"   Size: {db_status['size_mb']:.2f} MB")
            report.append(f"   Last Modified: {db_status['last_modified']} ({db_status['age_minutes']:.1f} min ago)")
        else:
            report.append(f"❌ {db_status.get('message', 'Unknown issue')}")
        report.append("")
        
        # Recent errors
        report.append("RECENT ERRORS (last 10):")
        report.append("-" * 80)
        errors = self.tail_errors(10)
        if errors:
            for error in errors:
                report.append(error.rstrip())
        else:
            report.append("✅ No errors found")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_report(self, report: str):
        """Save report to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.report_dir / f"status_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        return report_file
    
    def run(self, interval: int = 3600):
        """Run monitoring loop."""
        print("=" * 80)
        print("Test 14 Monitor Started")
        print("=" * 80)
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Report Interval: {interval} seconds ({interval/60:.0f} minutes)")
        print(f"Reports saved to: {self.report_dir.absolute()}")
        print("=" * 80)
        print()
        print("Press Ctrl+C to stop monitoring")
        print()
        
        iteration = 0
        try:
            while True:
                iteration += 1
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Generating report #{iteration}...")
                
                report = self.generate_report()
                print(report)
                
                report_file = self.save_report(report)
                print(f"\nReport saved to: {report_file}")
                
                # Wait for next iteration
                print(f"\nNext report in {interval} seconds ({interval/60:.0f} minutes)...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
            print(f"Total reports generated: {iteration}")
            print(f"Total monitoring time: {datetime.now() - self.start_time}")


def main():
    """Main entry point."""
    # Check if logs directory exists
    if not Path('logs').exists():
        print("WARNING: logs/ directory not found")
        print("Make sure you're running this from the project root directory")
        print()
    
    # Check if database exists
    if not Path('trading_bot.db').exists():
        print("WARNING: trading_bot.db not found")
        print("The bot may not have been started yet")
        print()
    
    # Create monitor and run
    monitor = BotMonitor()
    
    # Allow custom interval via command line
    interval = 3600  # Default: 1 hour
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
            print(f"Using custom interval: {interval} seconds")
        except ValueError:
            print(f"Invalid interval: {sys.argv[1]}, using default: {interval} seconds")
    
    monitor.run(interval)


if __name__ == '__main__':
    main()
