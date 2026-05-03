
"""
Модуль Vacancy - класс вакансии
"""

from datetime import datetime


class Vacancy:
    """Класс, представляющий вакансию"""

    # Frozenset для валидации статусов и типов занятости
    VALID_EMPLOYMENT_TYPES = frozenset(['full-time', 'part-time', 'contract', 'internship', 'remote'])
    VALID_EXPERIENCE_LEVELS = frozenset(['no-experience', 'junior', 'middle', 'senior', 'lead'])

    def __init__(self, vacancy_id: str, title: str, company: str, salary_min: float,
                 salary_max: float, city: str, employment_type: str,
                 experience_level: str, skills: list, description: str,
                 source_url: str = "", published_date: str = None):
        self._vacancy_id = vacancy_id
        self._title = title
        self._company = company
        self._salary_min = salary_min
        self._salary_max = salary_max
        self._city = city
        self._employment_type = employment_type
        self._experience_level = experience_level
        self._skills = skills if skills else []
        self._description = description
        self._source_url = source_url
        self._published_date = published_date or datetime.now().isoformat()

        # Валидация
        if employment_type not in self.VALID_EMPLOYMENT_TYPES:
            raise ValueError(f"Недопустимый тип занятости: {employment_type}")
        if experience_level not in self.VALID_EXPERIENCE_LEVELS:
            raise ValueError(f"Недопустимый уровень опыта: {experience_level}")

    @property
    def vacancy_id(self):
        return self._vacancy_id

    @property
    def title(self):
        return self._title

    @property
    def company(self):
        return self._company

    @property
    def salary_min(self):
        return self._salary_min

    @property
    def salary_max(self):
        return self._salary_max

    @property
    def city(self):
        return self._city

    @property
    def employment_type(self):
        return self._employment_type

    @property
    def experience_level(self):
        return self._experience_level

    @property
    def skills(self):
        return self._skills.copy()

    @property
    def description(self):
        return self._description

    @property
    def source_url(self):
        return self._source_url

    @property
    def published_date(self):
        return self._published_date

    def get_average_salary(self) -> float:
        """Возвращает среднюю зарплату по вакансии"""
        if self._salary_max > 0:
            return (self._salary_min + self._salary_max) / 2
        return self._salary_min

    def has_skill(self, skill: str) -> bool:
        """Проверяет наличие навыка в вакансии"""
        return skill.lower() in [s.lower() for s in self._skills]

    def matches_keywords(self, keywords: list) -> bool:
        """Проверяет соответствие вакансии ключевым словам"""
        text = f"{self._title} {self._description} {' '.join(self._skills)}".lower()
        return any(kw.lower() in text for kw in keywords)

    def __str__(self) -> str:
        return f"Vacancy({self._title} at {self._company}, {self._city})"

    def __repr__(self) -> str:
        return f"Vacancy(id='{self._vacancy_id}', title='{self._title}', company='{self._company}', salary={self._salary_min}-{self._salary_max})"

    def to_dict(self) -> dict:
        """Преобразует вакансию в словарь для JSON сериализации"""
        return {
            'vacancy_id': self._vacancy_id,
            'title': self._title,
            'company': self._company,
            'salary_min': self._salary_min,
            'salary_max': self._salary_max,
            'city': self._city,
            'employment_type': self._employment_type,
            'experience_level': self._experience_level,
            'skills': self._skills,
            'description': self._description,
            'source_url': self._source_url,
            'published_date': self._published_date
        }

    @classmethod
    def from_dict(cls,  dict) -> 'Vacancy':
        """Создаёт вакансию из словаря"""
        return cls(
            vacancy_id=data.get('vacancy_id', ''),
            title=data.get('title', ''),
            company=data.get('company', ''),
            salary_min=data.get('salary_min', 0),
            salary_max=data.get('salary_max', 0),
            city=data.get('city', ''),
            employment_type=data.get('employment_type', 'full-time'),
            experience_level=data.get('experience_level', 'no-experience'),
            skills=data.get('skills', []),
            description=data.get('description', ''),
            source_url=data.get('source_url', ''),
            published_date=data.get('published_date')
        )