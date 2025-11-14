"""
Bot Package

Core bot components:
- coordinator: Main bot coordinator that wires orchestrators together
- lifecycle: Bot initialization, configuration, and module management
- scheduler: Task scheduling wrapper around APScheduler
"""

from src.bot.coordinator import BotCoordinator
from src.bot.lifecycle import BotLifecycle
from src.bot.scheduler import TaskScheduler

__all__ = ['BotCoordinator', 'BotLifecycle', 'TaskScheduler']
