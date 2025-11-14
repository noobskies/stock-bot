"""
Task Scheduler

Wrapper around APScheduler for managing bot's scheduled tasks.
Separates scheduling concerns from business logic.
"""

from typing import Callable
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
import pytz


class TaskScheduler:
    """
    Manages scheduled tasks using APScheduler.
    
    Single Responsibility: Configure and manage task scheduling.
    Does NOT contain business logic - just schedules execution.
    """
    
    def __init__(self, timezone_str: str = 'America/New_York'):
        """
        Initialize task scheduler.
        
        Args:
            timezone_str: Timezone for scheduling (default: Eastern Time for market hours)
        """
        self.eastern_tz = pytz.timezone(timezone_str)
        self.scheduler = BackgroundScheduler(timezone=self.eastern_tz)
        self._jobs_configured = False
    
    def configure_jobs(
        self,
        trading_cycle_func: Callable,
        position_monitor_func: Callable,
        market_close_func: Callable
    ):
        """
        Configure all scheduled jobs.
        
        Args:
            trading_cycle_func: Function to run trading cycle
            position_monitor_func: Function to monitor positions
            market_close_func: Function to handle market close
        """
        if self._jobs_configured:
            logger.warning("Jobs already configured - skipping")
            return
        
        # Trading cycle: Every 5 minutes during market hours (9:30 AM - 4:00 PM ET)
        self.scheduler.add_job(
            func=trading_cycle_func,
            trigger='cron',
            day_of_week='mon-fri',
            hour='9-15',
            minute='*/5',
            id='trading_cycle',
            name='Trading Cycle',
            misfire_grace_time=60  # Allow 60s grace for missed executions
        )
        
        # Special handling for market open (9:30-9:55)
        self.scheduler.add_job(
            func=trading_cycle_func,
            trigger='cron',
            day_of_week='mon-fri',
            hour=9,
            minute='30,35,40,45,50,55',
            id='trading_cycle_open',
            name='Trading Cycle (Market Open)',
            misfire_grace_time=60
        )
        
        # Position monitoring: Every 30 seconds (runs continuously, checks market hours internally)
        self.scheduler.add_job(
            func=position_monitor_func,
            trigger='interval',
            seconds=30,
            id='position_monitor',
            name='Position Monitor',
            misfire_grace_time=30
        )
        
        # Market close handler: Daily at 4:00 PM ET
        self.scheduler.add_job(
            func=market_close_func,
            trigger='cron',
            day_of_week='mon-fri',
            hour=16,
            minute=0,
            id='market_close',
            name='Market Close Handler',
            misfire_grace_time=300  # 5 minute grace for market close
        )
        
        self._jobs_configured = True
        logger.info("Task scheduler configured with 4 jobs")
    
    def start(self):
        """Start the scheduler."""
        if not self._jobs_configured:
            logger.error("Cannot start scheduler - jobs not configured")
            return False
        
        if self.scheduler.running:
            logger.warning("Scheduler already running")
            return True
        
        try:
            self.scheduler.start()
            logger.info("Task scheduler started successfully")
            return True
        except Exception as e:
            logger.exception(f"Error starting scheduler: {e}")
            return False
    
    def stop(self):
        """Stop the scheduler gracefully."""
        if not self.scheduler.running:
            logger.warning("Scheduler not running")
            return True
        
        try:
            self.scheduler.shutdown(wait=True)
            logger.info("Task scheduler stopped successfully")
            return True
        except Exception as e:
            logger.exception(f"Error stopping scheduler: {e}")
            return False
    
    def pause(self):
        """Pause all scheduled jobs."""
        try:
            self.scheduler.pause()
            logger.info("Task scheduler paused")
            return True
        except Exception as e:
            logger.exception(f"Error pausing scheduler: {e}")
            return False
    
    def resume(self):
        """Resume all scheduled jobs."""
        try:
            self.scheduler.resume()
            logger.info("Task scheduler resumed")
            return True
        except Exception as e:
            logger.exception(f"Error resuming scheduler: {e}")
            return False
    
    def get_job_info(self) -> list:
        """
        Get information about all scheduled jobs.
        
        Returns:
            List of job info dicts
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': str(job.next_run_time) if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.scheduler.running if self.scheduler else False
