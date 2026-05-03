--- Lugovkin_JobTracker/app/analytics.py (原始)


+++ Lugovkin_JobTracker/app/analytics.py (修改后)
"""
Модуль Analytics - аналитика рынка труда и откликов
"""

from datetime import datetime
from typing import Optional
from .vacancy import Vacancy
from .tracker import Application, JobTracker


class Analytics:
    """Класс для аналитики вакансий и откликов"""

    def __init__(self, vacancies: list[Vacancy], applications: list[Application]):
        self._vacancies = vacancies
        self._applications = applications

    def get_average_salary_by_specialty(self, specialty_keywords: list[str]) -> dict:
        """
        Вычислить среднюю зарплату по специальностям с использованием lambda
        """
        result = {}

        for keyword in specialty_keywords:
            # Фильтрация вакансий через lambda
            filtered = list(filter(
                lambda v: keyword.lower() in v.title.lower() or keyword.lower() in ' '.join(v.skills).lower(),
                self._vacancies
            ))

            if filtered:
                # Вычисление средней зарплаты через map и lambda
                salaries = list(map(lambda v: v.get_average_salary(), filtered))
                avg_salary = sum(salaries) / len(salaries)
                result[keyword] = {
                    'average_salary': round(avg_salary, 2),
                    'vacancy_count': len(filtered),
                    'min_salary': min(salaries),
                    'max_salary': max(salaries)
                }
            else:
                result[keyword] = {
                    'average_salary': 0,
                    'vacancy_count': 0,
                    'min_salary': 0,
                    'max_salary': 0
                }

        return result

    def get_top_employers(self, limit: int = 5) -> list[tuple[str, int]]:
        """
        Получить топ работодателей по количеству вакансий
        Использует sorted с lambda
        """
        employer_count = {}

        for vacancy in self._vacancies:
            employer = vacancy.company
            employer_count[employer] = employer_count.get(employer, 0) + 1

        # Сортировка через lambda
        sorted_employers = sorted(
            employer_count.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_employers[:limit]

    def get_salary_statistics(self) -> dict:
        """Получить общую статистику по зарплатам"""
        if not self._vacancies:
            return {'average': 0, 'median': 0, 'min': 0, 'max': 0}

        # Получаем все средние зарплаты через map
        salaries = list(map(lambda v: v.get_average_salary(), self._vacancies))
        salaries_sorted = sorted(salaries)

        n = len(salaries)
        median = (salaries_sorted[n // 2 - 1] + salaries_sorted[n // 2]) / 2 if n % 2 == 0 else salaries_sorted[n // 2]

        return {
            'average': round(sum(salaries) / n, 2),
            'median': round(median, 2),
            'min': min(salaries),
            'max': max(salaries),
            'total_vacancies': n
        }

    def get_application_success_rate(self) -> float:
        """Вычислить процент успешных откликов"""
        if not self._applications:
            return 0.0

        successful = len(list(filter(lambda a: a.status == 'offer', self._applications)))
        total = len(self._applications)

        return round((successful / total) * 100, 2)

    def get_average_response_time(self) -> float:
        """Вычислить среднее время ответа от работодателей"""
        responded_apps = list(filter(lambda a: a.response_date is not None, self._applications))

        if not responded_apps:
            return 0.0

        total_days = sum(app.get_waiting_days() for app in responded_apps)
        return round(total_days / len(responded_apps), 2)

    def get_status_distribution(self) -> dict:
        """Получить распределение откликов по статусам"""
        distribution = {}

        for status in Application.VALID_STATUSES:
            count = len(list(filter(lambda a: a.status == status, self._applications)))
            distribution[status] = count

        distribution['total'] = len(self._applications)
        return distribution

    def get_skills_demand(self, top_n: int = 10) -> list[tuple[str, int]]:
        """Получить самые востребованные навыки"""
        skills_count = {}

        for vacancy in self._vacancies:
            for skill in vacancy.skills:
                skills_count[skill] = skills_count.get(skill, 0) + 1

        # Сортировка через lambda
        sorted_skills = sorted(
            skills_count.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_skills[:top_n]

    def generate_report(self) -> str:
        """Сгенерировать текстовый отчёт по аналитике"""
        report = []
        report.append("=" * 50)
        report.append("АНАЛИТИКА РЫНКА ТРУДА И ОТКЛИКОВ")
        report.append("=" * 50)
        report.append("")

        # Статистика по зарплатам
        salary_stats = self.get_salary_statistics()
        report.append("📊 СТАТИСТИКА ПО ЗАРПЛАТАМ:")
        report.append(f"   Средний уровень: {salary_stats['average']:,.0f} руб.")
        report.append(f"   Медианный уровень: {salary_stats['median']:,.0f} руб.")
        report.append(f"   Минимум: {salary_stats['min']:,.0f} руб.")
        report.append(f"   Максимум: {salary_stats['max']:,.0f} руб.")
        report.append(f"   Всего вакансий: {salary_stats['total_vacancies']}")
        report.append("")

        # Топ работодателей
        report.append("🏢 ТОП РАБОТОДАТЕЛЕЙ:")
        for i, (employer, count) in enumerate(self.get_top_employers(5), 1):
            report.append(f"   {i}. {employer} - {count} вакансий")
        report.append("")

        # Востребованные навыки
        report.append("💼 ВОСТРЕБОВАННЫЕ НАВЫКИ:")
        for i, (skill, count) in enumerate(self.get_skills_demand(5), 1):
            report.append(f"   {i}. {skill} - {count} упоминаний")
        report.append("")

        # Статусы откликов
        report.append("📋 СТАТУСЫ ОТКЛИКОВ:")
        status_dist = self.get_status_distribution()
        for status, count in status_dist.items():
            if status != 'total' and count > 0:
                report.append(f"   {status}: {count}")
        report.append("")

        # Успешность
        success_rate = self.get_application_success_rate()
        response_time = self.get_average_response_time()
        report.append(f"✅ Процент успешных откликов: {success_rate}%")
        report.append(f"⏱️ Среднее время ответа: {response_time} дн.")
        report.append("")
        report.append("=" * 50)

        return "\n".join(report)

    def __str__(self) -> str:
        return f"Analytics(vacancies={len(self._vacancies)}, applications={len(self._applications)})"

    def __repr__(self) -> str:
        return f"Analytics(total_vacancies={len(self._vacancies)}, total_apps={len(self._applications)})"