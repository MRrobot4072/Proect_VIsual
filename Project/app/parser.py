--- Lugovkin_JobTracker/app/parser.py (原始)


+++ Lugovkin_JobTracker/app/parser.py (修改后)
"""
Модуль Parser - парсинг вакансий с открытых источников
"""

import urllib.request
import urllib.error
import re
import json
from datetime import datetime
from typing import Optional
from .vacancy import Vacancy


class JobParser:
    """Парсер вакансий с открытых источников"""

    def __init__(self):
        self._parsed_vacancies: list[Vacancy] = []
        self._next_id = 1000  # ID для спаршенных вакансий

    def check_robots_txt(self, url: str) -> bool:
        """Проверить robots.txt сайта на возможность парсинга"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            req = urllib.request.Request(
                robots_url,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; JobTrackerBot/1.0)'}
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                content = response.read().decode('utf-8', errors='ignore')

                # Простая проверка - ищемDisallow для нашего user-agent или *
                lines = content.split('\n')
                in_user_agent_section = False

                for line in lines:
                    line = line.strip().lower()
                    if line.startswith('user-agent:'):
                        agent = line.split(':')[1].strip()
                        in_user_agent_section = agent in ['*', 'jobtrackerbot', 'python-bot']
                    elif line.startswith('disallow:') and in_user_agent_section:
                        path = line.split(':')[1].strip()
                        if path and parsed.path.startswith(path):
                            print(f"⚠️ Парсинг запрещён robots.txt для пути {parsed.path}")
                            return False

                return True

        except Exception as e:
            print(f"⚠️ Не удалось проверить robots.txt: {e}")
            return True  # Разрешаем парсинг если не смогли проверить

    def parse_hh_vacancies(self, search_query: str = "Python", city: str = "Москва") -> list[Vacancy]:
        """
        Парсинг вакансий с hh.ru через API
        Возвращает список вакансий
        """
        vacancies = []

        try:
            # Используем открытое API hh.ru
            api_url = f"https://api.hh.ru/vacancies?text={search_query}&area=1&per_page=20"

            req = urllib.request.Request(
                api_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; JobTrackerBot/1.0)',
                    'Accept': 'application/json'
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

                for item in data.get('items', [])[:10]:  # Берём максимум 10 вакансий
                    salary_min = 0
                    salary_max = 0

                    if item.get('salary'):
                        salary_min = item['salary'].get('from') or 0
                        salary_max = item['salary'].get('to') or 0

                    vacancy = Vacancy(
                        vacancy_id=f"PARSED{self._next_id}",
                        title=item.get('name', 'Без названия'),
                        company=item.get('employer', {}).get('name', 'Не указано') if item.get('employer') else 'Не указано',
                        salary_min=salary_min,
                        salary_max=salary_max,
                        city=city,
                        employment_type=self._map_employment_type(item.get('employment', {}).get('name', '')),
                        experience_level=self._map_experience_level(item.get('experience', {}).get('name', '')),
                        skills=[],
                        description=item.get('snippet', {}).get('requirement', '') or '',
                        source_url=item.get('alternate_url', ''),
                        published_date=item.get('published_at', datetime.now().isoformat())
                    )

                    vacancies.append(vacancy)
                    self._next_id += 1

                print(f"✅ Спаршено {len(vacancies)} вакансий с hh.ru")

        except urllib.error.URLError as e:
            print(f"❌ Ошибка при парсинге hh.ru: {e.reason}")
            # Возвращаем тестовые данные если API недоступно
            vacancies = self._get_mock_vacancies(search_query, city)
        except Exception as e:
            print(f"❌ Ошибка при парсинге: {e}")
            vacancies = self._get_mock_vacancies(search_query, city)

        self._parsed_vacancies.extend(vacancies)
        return vacancies

    def _map_employment_type(self, hh_type: str) -> str:
        """Преобразует тип занятости из hh.ru в наш формат"""
        mapping = {
            'полная занятость': 'full-time',
            'частичная занятость': 'part-time',
            'проектная работа': 'contract',
            'стажировка': 'internship',
            'удаленная работа': 'remote'
        }
        return mapping.get(hh_type.lower(), 'full-time')

    def _map_experience_level(self, hh_exp: str) -> str:
        """Преобразует уровень опыта из hh.ru в наш формат"""
        mapping = {
            'нет опыта': 'no-experience',
            'начинающий специалист': 'junior',
            'специалист': 'middle',
            'старший специалист': 'senior',
            'ведущий специалист': 'lead'
        }
        return mapping.get(hh_exp.lower(), 'no-experience')

    def _get_mock_vacancies(self, search_query: str, city: str) -> list[Vacancy]:
        """Возвращает тестовые вакансии если парсинг не удался"""
        mock_data = [
            {
                'title': f'{search_query} Developer',
                'company': 'TechCorp',
                'salary_min': 120000,
                'salary_max': 180000,
                'employment': 'full-time',
                'experience': 'middle',
                'skills': ['Python', 'Django', 'PostgreSQL'],
                'description': 'Разработка веб-приложений на Python'
            },
            {
                'title': f'Senior {search_query} Engineer',
                'company': 'DataSoft',
                'salary_min': 200000,
                'salary_max': 300000,
                'employment': 'remote',
                'experience': 'senior',
                'skills': ['Python', 'FastAPI', 'Docker', 'Kubernetes'],
                'description': 'Разработка микросервисов и API'
            },
            {
                'title': f'{search_query} Backend Developer',
                'company': 'WebStudio',
                'salary_min': 100000,
                'salary_max': 150000,
                'employment': 'full-time',
                'experience': 'junior',
                'skills': ['Python', 'Flask', 'MySQL'],
                'description': 'Разработка backend части веб-приложений'
            },
            {
                'title': f'{search_query} Data Analyst',
                'company': 'AnalyticsPro',
                'salary_min': 90000,
                'salary_max': 140000,
                'employment': 'part-time',
                'experience': 'middle',
                'skills': ['Python', 'Pandas', 'NumPy', 'SQL'],
                'description': 'Анализ данных и построение отчётов'
            },
            {
                'title': f'Junior {search_query} Developer',
                'company': 'StartUp Hub',
                'salary_min': 60000,
                'salary_max': 90000,
                'employment': 'internship',
                'experience': 'no-experience',
                'skills': ['Python', 'Git', 'Linux'],
                'description': 'Стажировка с возможностью роста'
            }
        ]

        vacancies = []
        for data in mock_
            vacancy = Vacancy(
                vacancy_id=f"MOCK{self._next_id}",
                title=data['title'],
                company=data['company'],
                salary_min=data['salary_min'],
                salary_max=data['salary_max'],
                city=city,
                employment_type=data['employment'],
                experience_level=data['experience'],
                skills=data['skills'],
                description=data['description'],
                source_url='https://example.com/vacancy',
                published_date=datetime.now().isoformat()
            )
            vacancies.append(vacancy)
            self._next_id += 1

        print(f"✅ Создано {len(vacancies)} тестовых вакансий")
        return vacancies

    def get_parsed_vacancies(self) -> list[Vacancy]:
        """Вернуть все спаршенные вакансии"""
        return self._parsed_vacancies.copy()

    def clear_parsed(self):
        """Очистить список спаршенных вакансий"""
        self._parsed_vacancies.clear()

    def __str__(self) -> str:
        return f"JobParser(parsed={len(self._parsed_vacancies)} vacancies)"

    def __repr__(self) -> str:
        return f"JobParser(total_parsed={len(self._parsed_vacancies)})"