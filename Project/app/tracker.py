--- Lugovkin_JobTracker/app/tracker.py (原始)


+++ Lugovkin_JobTracker/app/tracker.py (修改后)
"""
Модуль Tracker - класс Application и JobTracker для отслеживания откликов
"""

from datetime import datetime, timedelta
from .vacancy import Vacancy


class Application:
    """Класс, представляющий отклик на вакансию"""

    # Frozenset для валидации статусов отклика
    VALID_STATUSES = frozenset(['submitted', 'viewed', 'rejected', 'offer', 'interview'])

    def __init__(self, application_id: str, vacancy: Vacancy,
                 status: str = 'submitted', notes: str = "",
                 applied_date: str = None, response_date: str = None):
        self._application_id = application_id
        self._vacancy = vacancy
        self._status = status
        self._notes = notes
        self._applied_date = applied_date or datetime.now().isoformat()
        self._response_date = response_date

        if status not in self.VALID_STATUSES:
            raise ValueError(f"Недопустимый статус: {status}. Доступные: {self.VALID_STATUSES}")

    @property
    def application_id(self):
        return self._application_id

    @property
    def vacancy(self):
        return self._vacancy

    @property
    def status(self):
        return self._status

    @property
    def notes(self):
        return self._notes

    @property
    def applied_date(self):
        return self._applied_date

    @property
    def response_date(self):
        return self._response_date

    def apply(self) -> bool:
        """Подать отклик на вакансию"""
        if self._status != 'submitted':
            return False
        self._applied_date = datetime.now().isoformat()
        return True

    def reject(self, reason: str = "") -> bool:
        """Отметить отклик как отклонённый"""
        self._status = 'rejected'
        if reason:
            self._notes = f"{self._notes} Отказ: {reason}".strip()
        self._response_date = datetime.now().isoformat()
        return True

    def get_status(self) -> str:
        """Вернуть текущий статус отклика"""
        return self._status

    def update_status(self, new_status: str) -> bool:
        """Обновить статус отклика"""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Недопустимый статус: {new_status}")
        self._status = new_status
        if new_status in ['rejected', 'offer']:
            self._response_date = datetime.now().isoformat()
        return True

    def get_waiting_days(self) -> int:
        """Вычислить количество дней ожидания ответа"""
        applied = datetime.fromisoformat(self._applied_date)
        if self._response_date:
            responded = datetime.fromisoformat(self._response_date)
            return (responded - applied).days
        else:
            return (datetime.now() - applied).days

    def __str__(self) -> str:
        return f"Application({self._vacancy.title} at {self._vacancy.company}, status={self._status})"

    def __repr__(self) -> str:
        return f"Application(id='{self._application_id}', vacancy_id='{self._vacancy.vacancy_id}', status='{self._status}')"

    def to_dict(self) -> dict:
        """Преобразует отклик в словарь для JSON сериализации"""
        return {
            'application_id': self._application_id,
            'vacancy': self._vacancy.to_dict(),
            'status': self._status,
            'notes': self._notes,
            'applied_date': self._applied_date,
            'response_date': self._response_date
        }

    @classmethod
    def from_dict(cls,  dict) -> 'Application':
        """Создаёт отклик из словаря"""
        vacancy = Vacancy.from_dict(data.get('vacancy', {}))
        return cls(
            application_id=data.get('application_id', ''),
            vacancy=vacancy,
            status=data.get('status', 'submitted'),
            notes=data.get('notes', ''),
            applied_date=data.get('applied_date'),
            response_date=data.get('response_date')
        )


class JobTracker:
    """Трекер для управления всеми откликами"""

    def __init__(self):
        self._applications: dict[str, Application] = {}
        self._next_id = 1

    def add_application(self, vacancy: Vacancy, notes: str = "") -> Application:
        """Добавить новый отклик на вакансию"""
        app_id = f"APP{self._next_id:04d}"
        self._next_id += 1
        application = Application(app_id, vacancy, notes=notes)
        self._applications[app_id] = application
        return application

    def get_application(self, app_id: str) -> Application | None:
        """Получить отклик по ID"""
        return self._applications.get(app_id)

    def get_all_applications(self) -> list[Application]:
        """Получить все отклики"""
        return list(self._applications.values())

    def get_applications_by_status(self, status: str) -> list[Application]:
        """Получить отклики по статусу с использованием lambda"""
        return list(filter(lambda app: app.status == status, self._applications.values()))

    def get_pending_applications(self) -> list[Application]:
        """Получить отклики, ожидающие ответа"""
        pending_statuses = {'submitted', 'viewed', 'interview'}
        return list(filter(lambda app: app.status in pending_statuses, self._applications.values()))

    def remove_application(self, app_id: str) -> bool:
        """Удалить отклик"""
        if app_id in self._applications:
            del self._applications[app_id]
            return True
        return False

    def get_statistics(self) -> dict:
        """Получить статистику по откликам"""
        stats = {status: 0 for status in Application.VALID_STATUSES}
        for app in self._applications.values():
            stats[app.status] += 1
        stats['total'] = len(self._applications)
        return stats

    def __len__(self) -> int:
        return len(self._applications)

    def __str__(self) -> str:
        return f"JobTracker(applications={len(self._applications)})"

    def __repr__(self) -> str:
        return f"JobTracker(total={len(self._applications)}, pending={len(self.get_pending_applications())})"