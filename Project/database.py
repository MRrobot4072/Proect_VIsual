"""Модуль работы с базой данных (Data Access Layer)"""

import sqlite3
import hashlib
from config import DB_PATH
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS citizens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    last_name VARCHAR(50) NOT NULL,
                    first_name VARCHAR(50) NOT NULL,
                    middle_name VARCHAR(50),
                    phone VARCHAR(20) NOT NULL UNIQUE,
                    email VARCHAR(100) UNIQUE,
                    snils_inn VARCHAR(20) UNIQUE,
                    registration_date DATE DEFAULT CURRENT_DATE
                );
                CREATE TABLE IF NOT EXISTS service_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT
                );
                CREATE TABLE IF NOT EXISTS appeal_statuses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(50) NOT NULL UNIQUE,
                    description TEXT
                );
                CREATE TABLE IF NOT EXISTS repeat_reasons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT
                );
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    login VARCHAR(50) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    last_active TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS appeals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    citizen_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    status_id INTEGER NOT NULL DEFAULT 1,
                    responsible_user_id INTEGER,
                    repeat_reason_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT NOT NULL,
                    is_repeat BOOLEAN NOT NULL DEFAULT FALSE,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (citizen_id) REFERENCES citizens(id),
                    FOREIGN KEY (category_id) REFERENCES service_categories(id),
                    FOREIGN KEY (status_id) REFERENCES appeal_statuses(id),
                    FOREIGN KEY (responsible_user_id) REFERENCES users(id),
                    FOREIGN KEY (repeat_reason_id) REFERENCES repeat_reasons(id)
                );
            """)

            # ---- Миграция статусов: удаляем "Закрыто", если есть ----
            cursor.execute("SELECT id FROM appeal_statuses WHERE name = 'Закрыто'")
            closed = cursor.fetchone()
            if closed:
                closed_id = closed[0]
                cursor.execute("SELECT id FROM appeal_statuses WHERE name = 'Решено'")
                resolved = cursor.fetchone()
                if resolved:
                    resolved_id = resolved[0]
                    cursor.execute("UPDATE appeals SET status_id = ? WHERE status_id = ?", (resolved_id, closed_id))
                cursor.execute("DELETE FROM appeal_statuses WHERE name = 'Закрыто'")
            
            # Вставляем нужные статусы
            cursor.executemany("INSERT OR IGNORE INTO appeal_statuses (name, description) VALUES (?, ?)", [
                ("Новое", "Обращение зарегистрировано и ожидает обработки"),
                ("В работе", "Оператор приступил к решению проблемы"),
                ("На проверке", "Обращение проверяется специалистом"),
                ("Решено", "Проблема устранена"),
                ("Отклонено", "Обращение отклонено")
            ])

            # Остальные справочники (категории, причины повторов, пользователи, тестовые данные)
            cursor.executemany("INSERT OR IGNORE INTO service_categories (name, description) VALUES (?, ?)", [
                ("ЖКХ", "Проблемы с жилищно-коммунальными услугами"),
                ("Соцзащита", "Вопросы социального обеспечения"),
                ("Образование", "Проблемы с образовательными сервисами"),
                ("Портал госуслуг", "Проблемы со входом, СМС-коды, МЧД"),
                ("Мобильное приложение", "Сбои, вылеты, синхронизация"),
                ("Личный кабинет", "Отображение данных, ошибки интерфейса"),
                ("Здравоохранение", "Проблемы с медицинскими сервисами"),
                ("Транспорт", "Проблемы с транспортными сервисами")
            ])
            cursor.executemany("INSERT OR IGNORE INTO repeat_reasons (name, description) VALUES (?, ?)", [
                ("Не решено с первого раза", "Проблема осталась после первого обращения"),
                ("Сбой в работе сервиса", "Техническая ошибка на стороне сервиса"),
                ("Недостаточная консультация", "Получен неполный ответ"),
                ("Истек срок решения", "Превышены регламентные сроки")
            ])

            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO users (login, password_hash, full_name, role)
                    VALUES (?, ?, ?, ?)
                """, ("admin", self._hash_password("admin123"), "Иванов А.С.", "Оператор"))

            # Тестовые граждане и обращения (оставляем как было)
            cursor.execute("SELECT COUNT(*) FROM citizens")
            if cursor.fetchone()[0] == 0:
                test_citizens = [
                    ("Петров", "Александр", "Иванович", "+79991234567", "petrov@mail.ru"),
                    ("Сидорова", "Мария", "Васильевна", "+79991234568", "sidorova@mail.ru"),
                    ("Иванов", "Дмитрий", "Сергеевич", "+79991234569", "ivanov@mail.ru"),
                    ("Козлова", "Наталья", "Петровна", "+79991234570", "kozlova@mail.ru"),
                    ("Новиков", "Виктор", "Алексеевич", "+79991234571", "novikov@mail.ru"),
                ]
                cursor.executemany(
                    "INSERT INTO citizens (last_name, first_name, middle_name, phone, email) VALUES (?, ?, ?, ?, ?)",
                    test_citizens
                )
                for i, (ln, fn, mn, ph, em) in enumerate(test_citizens):
                    cursor.execute("SELECT id FROM citizens WHERE phone = ?", (ph,))
                    cid = cursor.fetchone()[0]
                    cat_id = (i % 3) + 1
                    status_id = (i % 3) + 1
                    # Обратите внимание: статус id 1,2,3 соответствуют Новое, В работе, На проверке (после миграции)
                    cursor.execute(
                        f"""INSERT INTO appeals (citizen_id, category_id, status_id, description, is_repeat, created_at)
                        VALUES (?, ?, ?, ?, ?, datetime('now', '-{i} days'))""",
                        (cid, cat_id, status_id, f"Тестовое обращение #{i+1}", i == 2)
                    )
            conn.commit()

    def authenticate(self, login, password):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            password_hash = self._hash_password(password)
            cursor.execute(
                "SELECT id, login, full_name, role FROM users WHERE login = ? AND password_hash = ?",
                (login, password_hash)
            )
            return cursor.fetchone()

    def get_stats(self):
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM appeals WHERE status_id = 1 AND is_repeat = 0")
            new_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM appeals WHERE is_repeat = 1")
            repeat_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM appeals WHERE status_id = 2")
            work_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM appeals WHERE status_id IN (4, 5)")
            done_count = c.fetchone()[0]
            return {"new": new_count, "repeat": repeat_count, "work": work_count, "done": done_count}

    def get_categories(self):
        with self._get_connection() as conn:
            return [r['name'] for r in conn.execute("SELECT name FROM service_categories").fetchall()]

    def get_statuses(self):
        with self._get_connection() as conn:
            return [r['name'] for r in conn.execute("SELECT name FROM appeal_statuses").fetchall()]

    def add_appeal(self, citizen_data, category_name, description):
        with self._get_connection() as conn:
            cur = conn.cursor()
            # Проверяем, существует ли гражданин
            cur.execute("SELECT id, last_name, first_name FROM citizens WHERE phone = ? OR (email IS NOT NULL AND email = ?)",
                        (citizen_data['phone'], citizen_data['email']))
            citizen = cur.fetchone()
            if citizen:
                citizen_id = citizen['id']
                cur.execute("""UPDATE citizens 
                            SET last_name = ?, first_name = ?, middle_name = ?, phone = ?, email = ?
                            WHERE id = ?""",
                            (citizen_data['last_name'], citizen_data['first_name'], 
                            citizen_data.get('middle_name'), citizen_data['phone'], 
                            citizen_data['email'], citizen_id))
            else:
                cur.execute("""INSERT INTO citizens (last_name, first_name, middle_name, phone, email) 
                            VALUES (?, ?, ?, ?, ?)""",
                            (citizen_data['last_name'], citizen_data['first_name'],
                            citizen_data.get('middle_name'), citizen_data['phone'], 
                            citizen_data['email']))
                citizen_id = cur.lastrowid

            # Получаем ID категории
            cur.execute("SELECT id FROM service_categories WHERE name = ?", (category_name,))
            category_id = cur.fetchone()['id']

            # Проверяем повторность (по гражданину и категории)
            cur.execute("""
                SELECT COUNT(*) as cnt 
                FROM appeals a
                WHERE a.citizen_id = ? AND a.category_id = ?
            """, (citizen_id, category_id))
            cnt = cur.fetchone()['cnt']
            is_repeat = cnt > 0

            # Получаем текущее локальное время
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cur.execute("""INSERT INTO appeals (citizen_id, category_id, status_id, description, is_repeat, created_at) 
                        VALUES (?, ?, 1, ?, ?, ?)""",
                        (citizen_id, category_id, description, is_repeat, now))
            conn.commit()
            return cur.lastrowid

    def update_appeal(self, appeal_id, citizen_data, category_name, description, status_name):
        with self._get_connection() as conn:
            cur = conn.cursor()
            # Обновляем данные гражданина
            cur.execute("""
                UPDATE citizens
                SET last_name = ?, first_name = ?, middle_name = ?, phone = ?, email = ?
                WHERE id = (SELECT citizen_id FROM appeals WHERE id = ?)
            """, (citizen_data['last_name'], citizen_data['first_name'], 
                citizen_data.get('middle_name'), citizen_data['phone'], 
                citizen_data['email'], appeal_id))
            # Обновляем обращение
            cur.execute("SELECT id FROM service_categories WHERE name = ?", (category_name,))
            category_id = cur.fetchone()['id']
            cur.execute("SELECT id FROM appeal_statuses WHERE name = ?", (status_name,))
            status_id = cur.fetchone()['id']
            # Текущее локальное время для updated_at
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute("""
                UPDATE appeals
                SET category_id = ?, description = ?, status_id = ?, updated_at = ?
                WHERE id = ?
            """, (category_id, description, status_id, now, appeal_id))
            conn.commit()

    def get_appeals_list(self, limit=100):
        with self._get_connection() as conn:
            query = """
                SELECT a.id, 
                       c.last_name || ' ' || substr(c.first_name, 1, 1) || '.' || 
                       CASE WHEN c.middle_name THEN substr(c.middle_name, 1, 1) || '.' ELSE '' END as citizen_short,
                       c.last_name || ' ' || c.first_name || ' ' || COALESCE(c.middle_name, '') as citizen_full,
                       sc.name as category, ast.name as status,
                       a.created_at, a.is_repeat, c.phone, c.email
                FROM appeals a
                JOIN citizens c ON a.citizen_id = c.id
                JOIN service_categories sc ON a.category_id = sc.id
                JOIN appeal_statuses ast ON a.status_id = ast.id
                ORDER BY a.created_at DESC LIMIT ?
            """
            return conn.execute(query, (limit,)).fetchall()

    def get_appeals_filtered(self, status=None, category=None, date_from=None, date_to=None, 
                             is_repeat=None, limit=10, offset=0, 
                             sort_column="created_at", sort_direction="DESC"):
        with self._get_connection() as conn:
            query = """
                SELECT a.id, 
                       c.last_name || ' ' || c.first_name || ' ' || COALESCE(c.middle_name, '') as citizen_full,
                       sc.name as category, ast.name as status,
                       a.created_at, a.is_repeat
                FROM appeals a
                JOIN citizens c ON a.citizen_id = c.id
                JOIN service_categories sc ON a.category_id = sc.id
                JOIN appeal_statuses ast ON a.status_id = ast.id
                WHERE 1=1
            """
            params = []
            if status:
                query += " AND ast.name = ?"
                params.append(status)
            if category:
                query += " AND sc.name = ?"
                params.append(category)
            if date_from:
                query += " AND a.created_at >= ?"
                params.append(date_from)
            if date_to:
                query += " AND a.created_at <= ?"
                params.append(date_to + " 23:59:59")
            if is_repeat is not None:
                query += " AND a.is_repeat = ?"
                params.append(1 if is_repeat else 0)
            
            valid_columns = {
                "id": "a.id",
                "citizen_full": "c.last_name || ' ' || c.first_name || ' ' || COALESCE(c.middle_name, '')",
                "category": "sc.name",
                "status": "ast.name",
                "created_at": "a.created_at"
            }
            if sort_column not in valid_columns:
                sort_column = "created_at"
            if sort_direction not in ["ASC", "DESC"]:
                sort_direction = "DESC"
            
            query += f" ORDER BY {valid_columns[sort_column]} {sort_direction} LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            return conn.execute(query, params).fetchall()

    def get_appeals_count(self, status=None, category=None, date_from=None, date_to=None, is_repeat=None):
        with self._get_connection() as conn:
            query = """
                SELECT COUNT(*) as cnt
                FROM appeals a
                JOIN citizens c ON a.citizen_id = c.id
                JOIN service_categories sc ON a.category_id = sc.id
                JOIN appeal_statuses ast ON a.status_id = ast.id
                WHERE 1=1
            """
            params = []
            if status:
                query += " AND ast.name = ?"
                params.append(status)
            if category:
                query += " AND sc.name = ?"
                params.append(category)
            if date_from:
                query += " AND a.created_at >= ?"
                params.append(date_from)
            if date_to:
                query += " AND a.created_at <= ?"
                params.append(date_to + " 23:59:59")
            if is_repeat is not None:
                query += " AND a.is_repeat = ?"
                params.append(1 if is_repeat else 0)
            
            return conn.execute(query, params).fetchone()['cnt']

    def delete_appeal(self, appeal_id):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM appeals WHERE id = ?", (appeal_id,))
            conn.commit()

    def get_total_stats(self):
        """Общая статистика по обращениям"""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as total FROM appeals")
            total = c.fetchone()['total']
            c.execute("SELECT COUNT(*) as cnt FROM appeals WHERE is_repeat = 1")
            repeat = c.fetchone()['cnt']
            c.execute("SELECT COUNT(*) as cnt FROM appeals WHERE is_repeat = 0")
            primary = c.fetchone()['cnt']
            c.execute("SELECT COUNT(DISTINCT citizen_id) as cnt FROM appeals")
            unique_citizens = c.fetchone()['cnt']
            return {
                "total": total,
                "repeat": repeat,
                "primary": primary,
                "unique_citizens": unique_citizens,
                "repeat_percent": round(repeat / total * 100, 1) if total > 0 else 0
            }

    def get_category_stats(self):
        """Статистика по категориям сервисов"""
        with self._get_connection() as conn:
            query = """
                SELECT sc.name as category, 
                       COUNT(a.id) as total,
                       SUM(CASE WHEN a.is_repeat = 1 THEN 1 ELSE 0 END) as repeat_count
                FROM appeals a
                JOIN service_categories sc ON a.category_id = sc.id
                GROUP BY sc.name
                ORDER BY total DESC
            """
            return conn.execute(query).fetchall()

    def get_status_stats(self):
        """Статистика по статусам обращений"""
        with self._get_connection() as conn:
            query = """
                SELECT ast.name as status, COUNT(a.id) as count
                FROM appeals a
                JOIN appeal_statuses ast ON a.status_id = ast.id
                GROUP BY ast.name
                ORDER BY count DESC
            """
            return conn.execute(query).fetchall()

    def get_repeat_reasons_stats(self):
        """Статистика по причинам повторных обращений"""
        with self._get_connection() as conn:
            query = """
                SELECT COALESCE(rr.name, 'Не указана') as reason, COUNT(a.id) as count
                FROM appeals a
                LEFT JOIN repeat_reasons rr ON a.repeat_reason_id = rr.id
                WHERE a.is_repeat = 1
                GROUP BY rr.name
                ORDER BY count DESC
            """
            return conn.execute(query).fetchall()

    def get_daily_stats(self, days=7):
        """Динамика обращений за последние N дней"""
        with self._get_connection() as conn:
            query = f"""
                SELECT DATE(created_at) as day, COUNT(*) as count
                FROM appeals
                WHERE created_at >= datetime('now', '-{days} days')
                GROUP BY DATE(created_at)
                ORDER BY day ASC
            """
            return conn.execute(query).fetchall()
        
    def get_appeal_details(self, appeal_id):
        with self._get_connection() as conn:
            query = """
                SELECT a.id, c.last_name, c.first_name, c.middle_name, c.phone, c.email,
                       sc.name as category, ast.name as status, a.description, 
                       a.created_at, a.is_repeat,
                       CASE WHEN a.is_repeat THEN rr.name ELSE 'Не применимо' END as repeat_reason
                FROM appeals a
                JOIN citizens c ON a.citizen_id = c.id
                JOIN service_categories sc ON a.category_id = sc.id
                JOIN appeal_statuses ast ON a.status_id = ast.id
                LEFT JOIN repeat_reasons rr ON a.repeat_reason_id = rr.id
                WHERE a.id = ?
            """
            return conn.execute(query, (appeal_id,)).fetchone()