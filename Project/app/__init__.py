"""
Агрегатор вакансий и трекер поиска работы
Пакет приложения для отслеживания вакансий и откликов
"""

from .vacancy import Vacancy
from .tracker import Application, JobTracker
from .parser import JobParser
from .analytics import Analytics

__all__ = ['Vacancy', 'Application', 'JobTracker', 'JobParser', 'Analytics']
