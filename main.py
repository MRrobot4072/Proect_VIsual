import sqlite3
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import re
import hashlib
from datetime import datetime

DB_PATH = "monitoring_system.db"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def validate_name(name):
    """Проверяет, что имя/фамилия содержит только буквы, дефис и пробел."""
    return bool(re.fullmatch(r"[A-Za-zА-Яа-яЁё\- ]+", name.strip()))


def format_datetime(dt_str):
    """Преобразует строку даты из БД в формат ДД.ММ.ГГГГ ЧЧ:ММ."""
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return dt_str


def format_date_only(dt_str):
    """Преобразует строку даты в формат ДД.ММ.ГГГГ."""
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d.%m.%Y")
    except:
        return dt_str


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

            cursor.executemany("INSERT OR IGNORE INTO appeal_statuses (name, description) VALUES (?, ?)", [
                ("Новое", "Обращение зарегистрировано и ожидает обработки"),
                ("В работе", "Оператор приступил к решению проблемы"),
                ("На проверке", "Обращение проверяется специалистом"),
                ("Решено", "Проблема устранена"),
                ("Закрыто", "Обращение завершено"),
                ("Отклонено", "Обращение отклонено")
            ])
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
            cur.execute("SELECT id, last_name, first_name FROM citizens WHERE phone = ? OR (email IS NOT NULL AND email = ?)",
                        (citizen_data['phone'], citizen_data['email']))
            citizen = cur.fetchone()
            if citizen:
                citizen_id = citizen['id']
                cur.execute("""UPDATE citizens 
                               SET last_name = ?, first_name = ? 
                               WHERE id = ?""",
                            (citizen_data['last_name'], citizen_data['first_name'], citizen_id))
            else:
                cur.execute("""INSERT INTO citizens (last_name, first_name, phone, email) 
                               VALUES (?, ?, ?, ?)""",
                            (citizen_data['last_name'], citizen_data['first_name'],
                             citizen_data['phone'], citizen_data['email']))
                citizen_id = cur.lastrowid

            cur.execute("SELECT COUNT(*) as cnt FROM appeals WHERE citizen_id = ?", (citizen_id,))
            is_repeat = cur.fetchone()['cnt'] > 0

            cur.execute("SELECT id FROM service_categories WHERE name = ?", (category_name,))
            category_id = cur.fetchone()['id']

            cur.execute("""INSERT INTO appeals (citizen_id, category_id, status_id, description, is_repeat) 
                           VALUES (?, ?, 1, ?, ?)""",
                        (citizen_id, category_id, description, is_repeat))
            conn.commit()
            return cur.lastrowid

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
        """Получение обращений с фильтрацией, сортировкой и пагинацией"""
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
            
            # Добавляем сортировку с защитой от SQL-инъекций
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
        """Получение общего количества обращений с фильтрацией"""
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
        """Удаление обращения"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM appeals WHERE id = ?", (appeal_id,))
            conn.commit()

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


# --------------------- ОКНО АВТОРИЗАЦИИ ---------------------
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Вход в систему")
        self.geometry("420x520")
        self.resizable(False, False)
        self.db = DatabaseManager()
        self.user_data = None
        self._center_window()
        self._build_ui()

    def _center_window(self):
        self.update_idletasks()
        w, h = 420, 520
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        ctk.CTkLabel(self, text="Система мониторинга обращений граждан",
                     font=ctk.CTkFont(size=16, weight="bold"), text_color="#1e293b").pack(pady=(50, 5))
        ctk.CTkLabel(self, text="Войдите в свой аккаунт", font=ctk.CTkFont(size=11), text_color="#64748b").pack(pady=(0, 30))

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill=tk.X, padx=40)

        ctk.CTkLabel(form_frame, text="Логин *", font=ctk.CTkFont(size=10, weight="bold"), text_color="#1e293b", anchor="w").pack(fill=tk.X, pady=(0, 5))
        self.ent_login = ctk.CTkEntry(form_frame, placeholder_text="Введите логин", height=40, font=ctk.CTkFont(size=11))
        self.ent_login.pack(fill=tk.X, pady=(0, 15))

        ctk.CTkLabel(form_frame, text="Пароль *", font=ctk.CTkFont(size=10, weight="bold"), text_color="#1e293b", anchor="w").pack(fill=tk.X, pady=(0, 5))
        self.ent_password = ctk.CTkEntry(form_frame, placeholder_text="Введите пароль", show="•", height=40, font=ctk.CTkFont(size=11))
        self.ent_password.pack(fill=tk.X, pady=(0, 20))
        self.ent_password.bind("<Return>", lambda e: self._do_login())

        ctk.CTkButton(self, text="Войти", font=ctk.CTkFont(size=11, weight="bold"), fg_color="#0d6efd", hover_color="#0b5ed7", height=40, command=self._do_login).pack(fill=tk.X, padx=40)

        link = ctk.CTkLabel(self, text="Забыли пароль?", font=ctk.CTkFont(size=10), text_color="#0d6efd", cursor="hand2")
        link.pack(pady=15)
        link.bind("<Button-1>", lambda e: messagebox.showinfo("Восстановление", "Обратитесь к администратору системы для сброса пароля."))

        ctk.CTkFrame(self, height=1, fg_color="#e2e8f0").pack(fill=tk.X, padx=40, pady=15)
        ctk.CTkLabel(self, text="Внутренняя система • Регистрация недоступна", font=ctk.CTkFont(size=9), text_color="#94a3b8").pack(pady=(0, 20))

    def _do_login(self):
        login = self.ent_login.get().strip()
        password = self.ent_password.get().strip()
        if not login or not password:
            messagebox.showwarning("Ошибка входа", "Пожалуйста, заполните все обязательные поля.")
            return
        user = self.db.authenticate(login, password)
        if user:
            self.user_data = dict(user)
            self.destroy()
        else:
            messagebox.showerror("Ошибка входа", "Неверный логин или пароль.")
            self.ent_password.delete(0, tk.END)
            self.ent_password.focus_set()


# --------------------- UI КОМПОНЕНТЫ ---------------------
class StatCard(ctk.CTkFrame):
    def __init__(self, parent, title, value, subtitle, icon, accent_color="#2563eb"):
        super().__init__(parent, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        self.accent = accent_color

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill=tk.X, padx=15, pady=(15, 0))
        ctk.CTkLabel(top, text=icon, font=ctk.CTkFont(size=18), text_color=accent_color).pack(side=tk.LEFT)
        ctk.CTkLabel(top, text=title.upper(), font=ctk.CTkFont(size=10, weight="bold"), text_color="#64748b").pack(side=tk.LEFT, padx=8)

        self.value_label = ctk.CTkLabel(self, text=str(value), font=ctk.CTkFont(size=32, weight="bold"), text_color="#1e293b")
        self.value_label.pack(pady=(5, 2))

        self.subtitle_label = ctk.CTkLabel(self, text=subtitle, font=ctk.CTkFont(size=11), text_color=accent_color)
        self.subtitle_label.pack(pady=(0, 15))

    def update_value(self, value, subtitle=None):
        self.value_label.configure(text=str(value))
        if subtitle:
            self.subtitle_label.configure(text=subtitle)


class TagLabel(ctk.CTkFrame):
    def __init__(self, parent, text, bg_color="#dbeafe", text_color="#1d4ed8"):
        super().__init__(parent, fg_color=bg_color, corner_radius=6, height=26)
        self.pack_propagate(False)
        ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=10, weight="bold"), text_color=text_color).pack(padx=8, pady=3)


class AddAppealWindow(ctk.CTkToplevel):
    def __init__(self, parent, db_manager, refresh_callback):
        super().__init__(parent)
        self.db = db_manager
        self.refresh_callback = refresh_callback
        self.title("Новое обращение")
        self.geometry("500x600")
        self.transient(parent)
        self.grab_set()

        header = ctk.CTkFrame(self, fg_color="#2563eb", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=" Новое обращение", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(pady=18)

        content = ctk.CTkScrollableFrame(self, fg_color="#f8fafc")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ctk.CTkLabel(content, text="Данные гражданина", font=ctk.CTkFont(size=13, weight="bold"), text_color="#1e293b").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ctk.CTkLabel(content, text="Фамилия *", text_color="#64748b", anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_last_name = ctk.CTkEntry(content, width=300, placeholder_text="Иванов")
        self.ent_last_name.grid(row=1, column=1, pady=5)

        ctk.CTkLabel(content, text="Имя *", text_color="#64748b", anchor="w").grid(row=2, column=0, sticky="w", pady=5)
        self.ent_first_name = ctk.CTkEntry(content, width=300, placeholder_text="Иван")
        self.ent_first_name.grid(row=2, column=1, pady=5)

        ctk.CTkLabel(content, text="Телефон *", text_color="#64748b", anchor="w").grid(row=3, column=0, sticky="w", pady=5)
        self.ent_phone = ctk.CTkEntry(content, width=300, placeholder_text="+79991234567")
        self.ent_phone.grid(row=3, column=1, pady=5)

        ctk.CTkLabel(content, text="Email", text_color="#64748b", anchor="w").grid(row=4, column=0, sticky="w", pady=5)
        self.ent_email = ctk.CTkEntry(content, width=300, placeholder_text="email@example.com")
        self.ent_email.grid(row=4, column=1, pady=5)

        ctk.CTkLabel(content, text="Данные обращения", font=ctk.CTkFont(size=13, weight="bold"), text_color="#1e293b").grid(row=5, column=0, columnspan=2, sticky="w", pady=(20, 10))

        ctk.CTkLabel(content, text="Категория *", text_color="#64748b", anchor="w").grid(row=6, column=0, sticky="w", pady=5)
        self.cmb_category = ctk.CTkComboBox(content, width=300, values=self.db.get_categories())
        self.cmb_category.grid(row=6, column=1, pady=5)
        if self.cmb_category.cget("values"):
            self.cmb_category.set(self.cmb_category.cget("values")[0])

        ctk.CTkLabel(content, text="Описание проблемы *", text_color="#64748b", anchor="nw").grid(row=7, column=0, sticky="nw", pady=5)
        self.txt_description = ctk.CTkTextbox(content, width=300, height=80)
        self.txt_description.grid(row=7, column=1, pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="#f8fafc")
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        ctk.CTkButton(btn_frame, text="Сохранить", fg_color="#2563eb", hover_color="#1d4ed8", font=ctk.CTkFont(size=12, weight="bold"), command=self.validate_and_save).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(btn_frame, text="Отмена", fg_color="#e2e8f0", hover_color="#cbd5e1", text_color="#1e293b", font=ctk.CTkFont(size=12, weight="bold"), command=self.destroy).pack(side=tk.LEFT, padx=5)

    def validate_and_save(self):
        last_name = self.ent_last_name.get().strip()
        first_name = self.ent_first_name.get().strip()
        phone = self.ent_phone.get().strip()
        email = self.ent_email.get().strip()
        category = self.cmb_category.get()
        description = self.txt_description.get("1.0", tk.END).strip()

        if not all([last_name, first_name, phone, category, description]):
            messagebox.showerror("Ошибка валидации", "Заполните все обязательные поля (*)")
            return

        if not validate_name(last_name):
            messagebox.showerror("Ошибка валидации", "Фамилия может содержать только буквы, дефис и пробел.")
            return
        if not validate_name(first_name):
            messagebox.showerror("Ошибка валидации", "Имя может содержать только буквы, дефис и пробел.")
            return

        if not re.match(r"^\+?[0-9\s\-]{10,15}$", phone):
            messagebox.showerror("Ошибка валидации", "Некорректный формат телефона (+79991234567)")
            return

        if email and not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            messagebox.showerror("Ошибка валидации", "Некорректный email")
            return

        try:
            self.db.add_appeal({'last_name': last_name, 'first_name': first_name,
                                'phone': phone, 'email': email or None}, category, description)
            messagebox.showinfo("Успех", "Обращение зарегистрировано!")
            self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


class AppealDetailsWindow(ctk.CTkToplevel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.title(f"Карточка обращения №{data['id']}")
        self.geometry("550x540")
        self.transient(parent)
        self.grab_set()

        header = ctk.CTkFrame(self, fg_color="#2563eb", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=f"📋 Обращение №{data['id']}", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(pady=18)

        content = ctk.CTkScrollableFrame(self, fg_color="white")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        repeat_color = "#ef4444" if data['is_repeat'] else "#22c55e"
        repeat_text = "️ ДА — Повторное обращение" if data['is_repeat'] else "✅ НЕТ — Первичное"
        repeat_bg = "#fef2f2" if data['is_repeat'] else "#f0fdf4"

        rf = ctk.CTkFrame(content, fg_color=repeat_bg, corner_radius=8, height=40)
        rf.pack(fill=tk.X, pady=(0, 15))
        rf.pack_propagate(False)
        ctk.CTkLabel(rf, text=repeat_text, text_color=repeat_color, font=ctk.CTkFont(size=11, weight="bold")).pack(pady=10)

        created_fmt = format_datetime(data['created_at'])

        fields = [
            ("Дата создания:", created_fmt),
            ("Статус:", data['status']),
            ("Категория:", data['category']),
            ("ФИО:", f"{data['last_name']} {data['first_name']} {data['middle_name'] or ''}"),
            ("Телефон:", data['phone']),
            ("Email:", data['email'] or "Не указан"),
            ("Причина повтора:", data['repeat_reason']),
        ]
        for label, value in fields:
            row = ctk.CTkFrame(content, fg_color="transparent")
            row.pack(fill=tk.X, pady=3)
            ctk.CTkLabel(row, text=label, width=150, anchor="w", text_color="#64748b", font=ctk.CTkFont(size=11)).pack(side=tk.LEFT)
            ctk.CTkLabel(row, text=str(value), text_color="#1e293b", font=ctk.CTkFont(size=11, weight="bold")).pack(side=tk.LEFT, fill=tk.X, expand=True)

        ctk.CTkLabel(content, text="Описание проблемы:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#1e293b").pack(anchor="w", pady=(15, 5))
        df = ctk.CTkFrame(content, fg_color="#f8fafc", corner_radius=8)
        df.pack(fill=tk.BOTH, expand=True, pady=5)
        ctk.CTkLabel(df, text=data['description'], text_color="#1e293b", font=ctk.CTkFont(size=11), justify="left", wraplength=480).pack(padx=15, pady=15)

        ctk.CTkButton(self, text="Закрыть", fg_color="#e2e8f0", hover_color="#cbd5e1", text_color="#1e293b", font=ctk.CTkFont(size=12, weight="bold"), command=self.destroy).pack(pady=15)


# --------------------- ГЛАВНОЕ ОКНО ---------------------
class AppMainWindow(ctk.CTk):
    def __init__(self, user_data):
        super().__init__()
        self.title("Система мониторинга повторных обращений")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.user_data = user_data
        self.db = DatabaseManager()
        self.appeals_data = []
        self.col_widths = [140, 200, 180, 180, 120]
        
        # Переменные для вкладки "Обращения"
        self.current_page = 1
        self.page_size = 10
        self.selected_rows = set()
        self.filter_status = None
        self.filter_category = None
        self.filter_date_from = None
        self.filter_date_to = None
        self.filter_repeat = None
        
        # Переменные для сортировки
        self.sort_column = "created_at"
        self.sort_direction = "DESC"

        self._build_topbar()
        self._build_home_view()
        self._build_appeals_view()
        self.show_home_view()

    def _build_topbar(self):
        self.topbar = ctk.CTkFrame(self, fg_color="#2563eb", height=56)
        self.topbar.pack(fill=tk.X)
        self.topbar.pack_propagate(False)

        nav = ctk.CTkFrame(self.topbar, fg_color="transparent")
        nav.pack(side=tk.LEFT, padx=20)
        self.nav_buttons = {}
        nav_items = [("🏠 Главная", "home"), ("📋 Обращения", "appeals"), ("📊 Отчёты", "reports"), ("👤 Профиль", "profile")]
        for text, key in nav_items:
            btn = ctk.CTkButton(nav, text=text, fg_color="#1d4ed8" if key == "home" else "transparent",
                          hover_color="#1d4ed8", text_color="white",
                          font=ctk.CTkFont(size=12), border_width=0, height=36,
                          cursor="hand2", command=lambda k=key: self._switch_view(k))
            btn.pack(side=tk.LEFT, padx=3)
            self.nav_buttons[key] = btn

        right = ctk.CTkFrame(self.topbar, fg_color="transparent")
        right.pack(side=tk.RIGHT, padx=20)
        ctk.CTkButton(right, text="🔔", fg_color="transparent", hover_color="#1d4ed8",
                      text_color="white", font=ctk.CTkFont(size=16), width=36, height=36,
                      border_width=0, cursor="hand2").pack(side=tk.LEFT, padx=3)

        profile = ctk.CTkFrame(right, fg_color="#1d4ed8", corner_radius=8)
        profile.pack(side=tk.LEFT, padx=8)
        info = ctk.CTkFrame(profile, fg_color="transparent")
        info.pack(side=tk.LEFT, padx=8, pady=8)
        ctk.CTkLabel(info, text=self.user_data['full_name'], font=ctk.CTkFont(size=11, weight="bold"), text_color="white").pack()
        ctk.CTkLabel(info, text=self.user_data['role'], font=ctk.CTkFont(size=9), text_color="#bfdbfe").pack()

    def _switch_view(self, view_key):
        for key, btn in self.nav_buttons.items():
            btn.configure(fg_color="#1d4ed8" if key == view_key else "transparent")
        
        if view_key == "home":
            self.show_home_view()
        elif view_key == "appeals":
            self.show_appeals_view()
        else:
            self.home_view.pack_forget()
            self.appeals_view.pack_forget()

    def _build_home_view(self):
        """Главная вкладка со статистикой"""
        self.home_view = ctk.CTkScrollableFrame(self, fg_color="#f8fafc")
        
        self.stats_frame = ctk.CTkFrame(self.home_view, fg_color="transparent")
        self.stats_frame.pack(fill=tk.X, padx=30, pady=(20, 10))
        self.stat_new = StatCard(self.stats_frame, "Новые", "0", "+0 за сегодня", "✉️", "#2563eb")
        self.stat_new.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.stat_repeat = StatCard(self.stats_frame, "Повторные", "0", "Требуют внимания", "️", "#f59e0b")
        self.stat_repeat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.stat_work = StatCard(self.stats_frame, "В работе", "0", "Обрабатываются", "️", "#64748b")
        self.stat_work.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.stat_done = StatCard(self.stats_frame, "Решено", "0", "За этот месяц", "✅", "#22c55e")
        self.stat_done.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        search_frame = ctk.CTkFrame(self.home_view, fg_color="transparent")
        search_frame.pack(fill=tk.X, padx=30, pady=(10, 15))
        search_box = ctk.CTkFrame(search_frame, fg_color="white", corner_radius=8, border_width=1, border_color="#e2e8f0")
        search_box.pack(fill=tk.X)
        ctk.CTkLabel(search_box, text="🔍", font=ctk.CTkFont(size=14), text_color="#94a3b8").pack(side=tk.LEFT, padx=12)
        self.search_entry = ctk.CTkEntry(search_box, placeholder_text="ФИО / телефон / email", fg_color="transparent", border_width=0, height=40, font=ctk.CTkFont(size=12))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ctk.CTkButton(search_box, text="Найти", fg_color="#2563eb", hover_color="#1d4ed8", text_color="white", font=ctk.CTkFont(size=11, weight="bold"), width=80, height=32, cursor="hand2").pack(side=tk.RIGHT, padx=8)

        self.table_container = ctk.CTkFrame(self.home_view, fg_color="white", corner_radius=12, border_width=1, border_color="#e2e8f0")
        self.table_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 20))

        th = ctk.CTkFrame(self.table_container, fg_color="transparent")
        th.pack(fill=tk.X, padx=20, pady=(20, 10))
        ctk.CTkLabel(th, text="Последние обращения", font=ctk.CTkFont(size=16, weight="bold"), text_color="#1e293b").pack(side=tk.LEFT)
        self.count_label = ctk.CTkLabel(th, text="0 записей", font=ctk.CTkFont(size=11), text_color="#64748b", fg_color="#f1f5f9", corner_radius=6)
        self.count_label.pack(side=tk.RIGHT, padx=10, pady=5)

        # Заголовки таблицы
        col_frame = ctk.CTkFrame(self.table_container, fg_color="#f8fafc")
        col_frame.pack(fill=tk.X, padx=1, pady=0)
        
        for col_idx in range(5):
            col_frame.grid_columnconfigure(col_idx, weight=0, minsize=self.col_widths[col_idx])
        col_frame.grid_columnconfigure(5, weight=1)
        
        columns = ["ID ОБРАЩЕНИЯ", "ГРАЖДАНИН", "КАТЕГОРИЯ", "ДАТА И ВРЕМЯ", "СТАТУС"]
        for col_idx, col in enumerate(columns):
            ctk.CTkLabel(col_frame, text=col, font=ctk.CTkFont(size=10, weight="bold"), 
                        text_color="#64748b", anchor="w", fg_color="transparent").grid(row=0, column=col_idx, padx=15, pady=10, sticky="w")
        
        ctk.CTkFrame(self.table_container, fg_color="#e2e8f0", height=1).pack(fill=tk.X, padx=1, pady=0)

        self.table_body = ctk.CTkFrame(self.table_container, fg_color="transparent")
        self.table_body.pack(fill=tk.BOTH, expand=True, padx=1, pady=0)

        tf = ctk.CTkFrame(self.table_container, fg_color="transparent")
        tf.pack(fill=tk.X, padx=20, pady=15)
        self.footer_label = ctk.CTkLabel(tf, text="Показаны последние 0 обращений", font=ctk.CTkFont(size=11), text_color="#94a3b8")
        self.footer_label.pack(side=tk.LEFT)
        ctk.CTkButton(tf, text="➕ Новое обращение", fg_color="#2563eb", hover_color="#1d4ed8", text_color="white", font=ctk.CTkFont(size=11, weight="bold"), height=32, cursor="hand2", command=self.open_add_appeal).pack(side=tk.RIGHT)

    def _build_appeals_view(self):
        """Вкладка Обращения с фильтрами, сортировкой и пагинацией"""
        self.appeals_view = ctk.CTkScrollableFrame(self, fg_color="#ffffff")
        
        # Заголовок
        header_frame = ctk.CTkFrame(self.appeals_view, fg_color="transparent")
        header_frame.pack(fill=tk.X, padx=30, pady=(20, 10))
        ctk.CTkLabel(header_frame, text="Обращения", font=ctk.CTkFont(size=20, weight="bold"), text_color="#1e293b").pack(side=tk.LEFT)
        
        # Кнопки обновления и настроек
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side=tk.RIGHT)
        ctk.CTkButton(btn_frame, text="🔄", fg_color="transparent", hover_color="#e2e8f0", text_color="#64748b", width=36, height=36, cursor="hand2", command=self.refresh_appeals_view).pack(side=tk.LEFT, padx=3)
        ctk.CTkButton(btn_frame, text="⚙️", fg_color="transparent", hover_color="#e2e8f0", text_color="#64748b", width=36, height=36, cursor="hand2").pack(side=tk.LEFT, padx=3)
        
        # Поиск
        search_box = ctk.CTkFrame(self.appeals_view, fg_color="white", corner_radius=8, border_width=1, border_color="#e2e8f0", height=40)
        search_box.pack(fill=tk.X, padx=30, pady=(10, 15))
        search_box.pack_propagate(False)
        ctk.CTkLabel(search_box, text="🔍", font=ctk.CTkFont(size=14), text_color="#94a3b8").pack(side=tk.LEFT, padx=12)
        ctk.CTkEntry(search_box, placeholder_text="Поиск обращений...", fg_color="transparent", border_width=0, font=ctk.CTkFont(size=12)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Фильтры
        filters_frame = ctk.CTkFrame(self.appeals_view, fg_color="transparent")
        filters_frame.pack(fill=tk.X, padx=30, pady=(0, 15))
        
        # Статус
        ctk.CTkComboBox(filters_frame, values=["Все статусы"] + self.db.get_statuses(), width=140, 
                       font=ctk.CTkFont(size=11), command=self._on_status_filter_change).pack(side=tk.LEFT, padx=5)
        
        # Категория
        ctk.CTkComboBox(filters_frame, values=["Все категории"] + self.db.get_categories(), width=160,
                       font=ctk.CTkFont(size=11), command=self._on_category_filter_change).pack(side=tk.LEFT, padx=5)
        
        # Диапазон дат
        ctk.CTkButton(filters_frame, text="📅 Диапазон дат", fg_color="white", hover_color="#f1f5f9", 
                     text_color="#1e293b", border_width=1, border_color="#e2e8f0",
                     font=ctk.CTkFont(size=11), width=160, height=32, cursor="hand2",
                     command=self._open_date_filter).pack(side=tk.LEFT, padx=5)
        
        # Повторные
        self.repeat_checkbox = ctk.CTkCheckBox(filters_frame, text="Повторные", font=ctk.CTkFont(size=11),
                                              command=self._on_repeat_filter_change)
        self.repeat_checkbox.pack(side=tk.LEFT, padx=5)
        
        # Таблица
        self.appeals_table_container = ctk.CTkFrame(self.appeals_view, fg_color="white", corner_radius=8, border_width=1, border_color="#e2e8f0")
        self.appeals_table_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=(0, 15))
        
        # Заголовки таблицы (с сортировкой)
        col_headers_frame = ctk.CTkFrame(self.appeals_table_container, fg_color="#f1f5f9")
        col_headers_frame.pack(fill=tk.X, padx=1, pady=1)
        
        self.appeals_col_widths = [50, 100, 250, 180, 150, 100]
        # (заголовок, ключ сортировки или None)
        col_headers = [("", None), ("№", "id"), ("Гражданин", "citizen_full"), 
                       ("Категория", "category"), ("Статус", "status"), ("", None)]
        
        for i, (header, sort_key) in enumerate(col_headers):
            col_headers_frame.grid_columnconfigure(i, weight=0, minsize=self.appeals_col_widths[i])
            if sort_key:
                # Индикатор сортировки
                if self.sort_column == sort_key:
                    sort_indicator = " ▲" if self.sort_direction == "ASC" else " ▼"
                else:
                    sort_indicator = ""
                
                btn = ctk.CTkButton(col_headers_frame, 
                           text=header + sort_indicator, 
                           font=ctk.CTkFont(size=11, weight="bold"),
                           text_color="#64748b", anchor="w", fg_color="transparent",
                           hover_color="#e2e8f0", cursor="hand2",
                           command=lambda k=sort_key: self._toggle_sort(k))
                btn.grid(row=0, column=i, padx=10, pady=10, sticky="w")
            else:
                ctk.CTkLabel(col_headers_frame, text=header, font=ctk.CTkFont(size=11, weight="bold"),
                            text_color="#64748b", anchor="w", fg_color="transparent").grid(row=0, column=i, padx=10, pady=10, sticky="w")
        col_headers_frame.grid_columnconfigure(6, weight=1)
        
        # Тело таблицы
        self.appeals_table_body = ctk.CTkFrame(self.appeals_table_container, fg_color="transparent")
        self.appeals_table_body.pack(fill=tk.BOTH, expand=True, padx=1)
        
        # Пагинация
        pagination_frame = ctk.CTkFrame(self.appeals_view, fg_color="transparent")
        pagination_frame.pack(fill=tk.X, padx=30, pady=(5, 15))
        
        self.pagination_info = ctk.CTkLabel(pagination_frame, text="Показано 0 из 0", font=ctk.CTkFont(size=11), text_color="#64748b")
        self.pagination_info.pack(side=tk.LEFT)
        
        self.pagination_buttons = ctk.CTkFrame(pagination_frame, fg_color="transparent")
        self.pagination_buttons.pack(side=tk.RIGHT)
        
        # Кнопки действий
        actions_frame = ctk.CTkFrame(self.appeals_view, fg_color="transparent")
        actions_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        ctk.CTkButton(actions_frame, text="Добавить", fg_color="#2563eb", hover_color="#1d4ed8",
                     text_color="white", font=ctk.CTkFont(size=11, weight="bold"), height=36, cursor="hand2",
                     command=self.open_add_appeal).pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(actions_frame, text="Редактировать", fg_color="#e2e8f0", hover_color="#cbd5e1",
                     text_color="#1e293b", font=ctk.CTkFont(size=11, weight="bold"), height=36, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        ctk.CTkButton(actions_frame, text="Удалить", fg_color="#fef2f2", hover_color="#fee2e2",
                     text_color="#dc2626", font=ctk.CTkFont(size=11, weight="bold"), height=36, 
                     border_width=1, border_color="#fecaca", cursor="hand2",
                     command=self._delete_selected).pack(side=tk.LEFT, padx=5)

    def show_home_view(self):
        self.appeals_view.pack_forget()
        self.home_view.pack(fill=tk.BOTH, expand=True)
        self.refresh_all()

    def show_appeals_view(self):
        self.home_view.pack_forget()
        self.appeals_view.pack(fill=tk.BOTH, expand=True)
        self.refresh_appeals_view()

    def refresh_appeals_view(self):
        self.current_page = 1
        self.selected_rows.clear()
        self._load_appeals_table()

    def _on_status_filter_change(self, value):
        self.filter_status = None if value == "Все статусы" else value
        self.current_page = 1
        self._load_appeals_table()

    def _on_category_filter_change(self, value):
        self.filter_category = None if value == "Все категории" else value
        self.current_page = 1
        self._load_appeals_table()

    def _on_repeat_filter_change(self):
        self.filter_repeat = self.repeat_checkbox.get()
        self.current_page = 1
        self._load_appeals_table()

    def _open_date_filter(self):
        """Открытие окна выбора диапазона дат"""
        date_window = ctk.CTkToplevel(self)
        date_window.title("Диапазон дат")
        date_window.geometry("350x200")
        date_window.transient(self)
        date_window.grab_set()
        
        ctk.CTkLabel(date_window, text="Дата с:", font=ctk.CTkFont(size=11)).pack(pady=(20, 5))
        date_from_entry = ctk.CTkEntry(date_window, placeholder_text="ДД.ММ.ГГГГ", width=250)
        date_from_entry.pack(pady=5)
        
        ctk.CTkLabel(date_window, text="Дата по:", font=ctk.CTkFont(size=11)).pack(pady=(10, 5))
        date_to_entry = ctk.CTkEntry(date_window, placeholder_text="ДД.ММ.ГГГГ", width=250)
        date_to_entry.pack(pady=5)
        
        def apply_dates():
            try:
                if date_from_entry.get():
                    self.filter_date_from = datetime.strptime(date_from_entry.get(), "%d.%m.%Y").strftime("%Y-%m-%d")
                if date_to_entry.get():
                    self.filter_date_to = datetime.strptime(date_to_entry.get(), "%d.%m.%Y").strftime("%Y-%m-%d")
                self.current_page = 1
                self._load_appeals_table()
                date_window.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ДД.ММ.ГГГГ")
        
        ctk.CTkButton(date_window, text="Применить", fg_color="#2563eb", command=apply_dates).pack(pady=15)

    def _toggle_sort(self, column):
        """Переключение сортировки по колонке"""
        if self.sort_column == column:
            # Меняем направление на противоположное
            self.sort_direction = "DESC" if self.sort_direction == "ASC" else "ASC"
        else:
            # Новая колонка - сортируем по убыванию по умолчанию
            self.sort_column = column
            self.sort_direction = "DESC"
        # Перерисовываем заголовки с новыми индикаторами
        self._refresh_column_headers()
        self._load_appeals_table()

    def _refresh_column_headers(self):
        """Обновление заголовков колонок с индикаторами сортировки"""
        # Удаляем старые заголовки
        for child in self.appeals_table_container.winfo_children():
            if isinstance(child, ctk.CTkFrame) and child.cget("fg_color") == "#f1f5f9":
                child.destroy()
                break
        
        # Создаём новые заголовки
        col_headers_frame = ctk.CTkFrame(self.appeals_table_container, fg_color="#f1f5f9")
        col_headers_frame.pack(fill=tk.X, padx=1, pady=1)
        col_headers_frame.pack_forget()
        col_headers_frame.pack(fill=tk.X, padx=1, pady=1, before=self.appeals_table_body)
        
        col_headers = [("", None), ("№", "id"), ("Гражданин", "citizen_full"), 
                    ("Категория", "category"), ("Статус", "status"), ("", None)]
        
        for i, (header, sort_key) in enumerate(col_headers):
            col_headers_frame.grid_columnconfigure(i, weight=0, minsize=self.appeals_col_widths[i])
            if sort_key:
                if self.sort_column == sort_key:
                    sort_indicator = " ▲" if self.sort_direction == "ASC" else " ▼"
                else:
                    sort_indicator = ""
                
                btn = ctk.CTkButton(col_headers_frame, 
                        text=header + sort_indicator, 
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color="#64748b", anchor="w", fg_color="transparent",
                        hover_color="#e2e8f0", cursor="hand2",
                        command=lambda k=sort_key: self._toggle_sort(k))
                btn.grid(row=0, column=i, padx=10, pady=10, sticky="w")
            else:
                ctk.CTkLabel(col_headers_frame, text=header, font=ctk.CTkFont(size=11, weight="bold"),
                            text_color="#64748b", anchor="w", fg_color="transparent").grid(row=0, column=i, padx=10, pady=10, sticky="w")
        col_headers_frame.grid_columnconfigure(6, weight=1)

    def _load_appeals_table(self):
        """Загрузка таблицы обращений с фильтрацией, сортировкой и пагинацией"""
        for child in self.appeals_table_body.winfo_children():
            child.destroy()
        
        offset = (self.current_page - 1) * self.page_size
        appeals = self.db.get_appeals_filtered(
            status=self.filter_status,
            category=self.filter_category,
            date_from=self.filter_date_from,
            date_to=self.filter_date_to,
            is_repeat=self.filter_repeat,
            limit=self.page_size,
            offset=offset,
            sort_column=self.sort_column,
            sort_direction=self.sort_direction
        )
        
        total_count = self.db.get_appeals_count(
            status=self.filter_status,
            category=self.filter_category,
            date_from=self.filter_date_from,
            date_to=self.filter_date_to,
            is_repeat=self.filter_repeat
        )
        
        for i, row in enumerate(appeals):
            bg = "white" if i % 2 == 0 else "#fafafa"
            row_frame = ctk.CTkFrame(self.appeals_table_body, fg_color=bg, corner_radius=0)
            row_frame.pack(fill=tk.X, padx=1, pady=1)
            
            # ВАЖНО: Настраиваем grid_columnconfigure для КАЖДОЙ строки с теми же ширинами
            for col_idx in range(6):
                row_frame.grid_columnconfigure(col_idx, weight=0, minsize=self.appeals_col_widths[col_idx])
            row_frame.grid_columnconfigure(6, weight=1)
            
            # Чекбокс (колонка 0)
            cb = ctk.CTkCheckBox(row_frame, text="", width=20, 
                                command=lambda rid=row['id']: self._toggle_row(rid))
            cb.grid(row=0, column=0, padx=10, pady=8, sticky="w")
            
            # Номер (колонка 1)
            ctk.CTkLabel(row_frame, text=f"2024-{row['id']:03d}", 
                        font=ctk.CTkFont(size=11), text_color="#64748b", anchor="w").grid(row=0, column=1, padx=10, pady=8, sticky="w")
            
            # Гражданин (колонка 2)
            ctk.CTkLabel(row_frame, text=row['citizen_full'], 
                        font=ctk.CTkFont(size=11, weight="bold"), text_color="#1e293b", anchor="w").grid(row=0, column=2, padx=10, pady=8, sticky="w")
            
            # Категория (колонка 3)
            bg_c, fg_c = self.get_category_colors(row['category'])
            TagLabel(row_frame, row['category'], bg_c, fg_c).grid(row=0, column=3, padx=10, pady=8, sticky="w")
            
            # Статус (колонка 4)
            display_status = "Повторное" if row['is_repeat'] else row['status']
            bg_s, fg_s = self.get_status_colors(display_status)
            status_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            status_frame.grid(row=0, column=4, padx=10, pady=8, sticky="w")
            TagLabel(status_frame, display_status, bg_s, fg_s).pack(side=tk.LEFT)
            if row['is_repeat']:
                TagLabel(status_frame, "⚠ Повтор", "#fef3c7", "#b45309").pack(side=tk.LEFT, padx=3)
            
            # Действия (колонка 5)
            ctk.CTkButton(row_frame, text="⋮", fg_color="transparent", hover_color="#e2e8f0", 
                        text_color="#64748b", width=30, height=30, font=ctk.CTkFont(size=14),
                        command=lambda r=row: self._show_row_menu(r)).grid(row=0, column=5, padx=10, pady=8, sticky="w")
        
        # Обновление пагинации
        start = offset + 1 if total_count > 0 else 0
        end = min(offset + self.page_size, total_count)
        self.pagination_info.configure(text=f"Показано {start}-{end} из {total_count}")
        
        self._build_pagination_buttons(total_count)

    def _build_pagination_buttons(self, total_count):
        """Построение кнопок пагинации"""
        for child in self.pagination_buttons.winfo_children():
            child.destroy()
        
        total_pages = max(1, (total_count + self.page_size - 1) // self.page_size)
        
        ctk.CTkButton(self.pagination_buttons, text="←", fg_color="white", hover_color="#f1f5f9", 
                     text_color="#64748b", width=32, height=32, border_width=1, border_color="#e2e8f0",
                     command=self._prev_page if self.current_page > 1 else None).pack(side=tk.LEFT, padx=2)
        
        for page in range(1, min(total_pages + 1, 6)):
            color = "#2563eb" if page == self.current_page else "white"
            text_color = "white" if page == self.current_page else "#1e293b"
            ctk.CTkButton(self.pagination_buttons, text=str(page), fg_color=color, hover_color="#f1f5f9",
                         text_color=text_color, width=32, height=32, border_width=1, border_color="#e2e8f0",
                         command=lambda p=page: self._go_to_page(p)).pack(side=tk.LEFT, padx=2)
        
        ctk.CTkButton(self.pagination_buttons, text="→", fg_color="white", hover_color="#f1f5f9",
                     text_color="#64748b", width=32, height=32, border_width=1, border_color="#e2e8f0",
                     command=self._next_page if self.current_page < total_pages else None).pack(side=tk.LEFT, padx=2)

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._load_appeals_table()

    def _next_page(self):
        self.current_page += 1
        self._load_appeals_table()

    def _go_to_page(self, page):
        self.current_page = page
        self._load_appeals_table()

    def _toggle_row(self, appeal_id):
        if appeal_id in self.selected_rows:
            self.selected_rows.remove(appeal_id)
        else:
            self.selected_rows.add(appeal_id)

    def _show_row_menu(self, row):
        """Меню действий для строки"""
        menu_window = ctk.CTkToplevel(self)
        menu_window.title("Действия")
        menu_window.geometry("200x150")
        menu_window.transient(self)
        menu_window.grab_set()
        
        ctk.CTkButton(menu_window, text="📋 Просмотр", fg_color="#2563eb", command=lambda: [self.show_details(row), menu_window.destroy()]).pack(fill=tk.X, padx=10, pady=5)
        ctk.CTkButton(menu_window, text="✏️ Редактировать", fg_color="#e2e8f0", text_color="#1e293b").pack(fill=tk.X, padx=10, pady=5)
        ctk.CTkButton(menu_window, text="🗑 Удалить", fg_color="#fef2f2", text_color="#dc2626",
                     command=lambda: [self._delete_single(row['id']), menu_window.destroy()]).pack(fill=tk.X, padx=10, pady=5)

    def _delete_single(self, appeal_id):
        if messagebox.askyesno("Подтверждение", f"Удалить обращение #{appeal_id}?"):
            self.db.delete_appeal(appeal_id)
            self._load_appeals_table()

    def _delete_selected(self):
        if not self.selected_rows:
            messagebox.showwarning("Внимание", "Выберите хотя бы одно обращение для удаления.")
            return
        if messagebox.askyesno("Подтверждение", f"Удалить выбранные обращения ({len(self.selected_rows)} шт.)?"):
            for appeal_id in self.selected_rows:
                self.db.delete_appeal(appeal_id)
            self.selected_rows.clear()
            self._load_appeals_table()

    def get_category_colors(self, cat):
        return {
            "ЖКХ": ("#fce7f3", "#be185d"), "Соцзащита": ("#dcfce7", "#15803d"),
            "Образование": ("#dbeafe", "#1d4ed8"), "Портал госуслуг": ("#fef3c7", "#b45309"),
            "Мобильное приложение": ("#f3e8ff", "#7e22ce"),
            "Личный кабинет": ("#e0e7ff", "#4338ca"),
            "Здравоохранение": ("#dcfce7", "#15803d"),
            "Транспорт": ("#fef3c7", "#b45309")
        }.get(cat, ("#f1f5f9", "#475569"))

    def get_status_colors(self, status):
        return {
            "Решено": ("#dcfce7", "#15803d"), "Закрыто": ("#dcfce7", "#15803d"),
            "В работе": ("#fef3c7", "#b45309"), "Новое": ("#dbeafe", "#1d4ed8"),
            "На проверке": ("#fef3c7", "#b45309"),
            "Повторное": ("#fef3c7", "#b45309"),
            "Отклонено": ("#fee2e2", "#dc2626")
        }.get(status, ("#f1f5f9", "#475569"))

    def refresh_all(self):
        stats = self.db.get_stats()
        self.stat_new.update_value(stats['new'], "+0 за сегодня")
        self.stat_repeat.update_value(stats['repeat'], "Требуют внимания")
        self.stat_work.update_value(stats['work'], "Обрабатываются")
        self.stat_done.update_value(stats['done'], "За этот месяц")
        self.load_table()

    def load_table(self):
        self.appeals_data = self.db.get_appeals_list(limit=5)
        for child in self.table_body.winfo_children():
            child.destroy()

        for i, row in enumerate(self.appeals_data):
            bg = "white" if i % 2 == 0 else "#f8fafc"
            row_frame = ctk.CTkFrame(self.table_body, fg_color=bg, corner_radius=0)
            row_frame.pack(fill=tk.X, padx=0, pady=0)
            row_frame.bind("<Button-1>", lambda e, r=row: self.show_details(r))

            for col_idx in range(5):
                row_frame.grid_columnconfigure(col_idx, weight=0, minsize=self.col_widths[col_idx])
            row_frame.grid_columnconfigure(5, weight=1)

            ctk.CTkLabel(row_frame, text=f"#AP-2024-{row['id']:03d}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2563eb", anchor="w").grid(row=0, column=0, padx=15, pady=10, sticky="w")
            ctk.CTkLabel(row_frame, text=row['citizen_short'], font=ctk.CTkFont(size=11), text_color="#1e293b", anchor="w").grid(row=0, column=1, padx=15, sticky="w")
            
            bg_c, fg_c = self.get_category_colors(row['category'])
            TagLabel(row_frame, row['category'], bg_c, fg_c).grid(row=0, column=2, padx=15, sticky="w")
            
            date_str = format_datetime(row['created_at'])
            ctk.CTkLabel(row_frame, text=date_str, font=ctk.CTkFont(size=11), text_color="#64748b", anchor="w").grid(row=0, column=3, padx=15, sticky="w")
            
            display_status = "Повторное" if row['is_repeat'] else row['status']
            bg_s, fg_s = self.get_status_colors(display_status)
            TagLabel(row_frame, display_status, bg_s, fg_s).grid(row=0, column=4, padx=15, sticky="w")

            ctk.CTkFrame(self.table_body, fg_color="#e2e8f0", height=1).pack(fill=tk.X, padx=0, pady=0)

        count = len(self.appeals_data)
        self.count_label.configure(text=f"{count} записей")
        self.footer_label.configure(text=f"Показаны последние {count} обращений")

    def show_details(self, row):
        details = self.db.get_appeal_details(row['id'])
        if details:
            AppealDetailsWindow(self, details)

    def open_add_appeal(self):
        AddAppealWindow(self, self.db, self.refresh_all)


def main():
    login_window = LoginWindow()
    login_window.mainloop()
    if login_window.user_data:
        app = AppMainWindow(login_window.user_data)
        app.mainloop()


if __name__ == "__main__":
    main()