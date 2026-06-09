"""Конфигурация приложения"""

DB_PATH = "monitoring_system.db"

# Цветовая палитра
COLORS = {
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "secondary": "#e2e8f0",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#dc2626",
    "text_primary": "#1e293b",
    "text_secondary": "#64748b",
    "text_muted": "#94a3b8",
    "background": "#f8fafc",
    "white": "#ffffff",
}

# Категории сервисов и их цвета
CATEGORY_COLORS = {
    "ЖКХ": ("#fce7f3", "#be185d"),
    "Соцзащита": ("#dcfce7", "#15803d"),
    "Образование": ("#dbeafe", "#1d4ed8"),
    "Портал госуслуг": ("#fef3c7", "#b45309"),
    "Мобильное приложение": ("#f3e8ff", "#7e22ce"),
    "Личный кабинет": ("#e0e7ff", "#4338ca"),
    "Здравоохранение": ("#dcfce7", "#15803d"),
    "Транспорт": ("#fef3c7", "#b45309"),
}

# Статусы и их цвета
STATUS_COLORS = {
    "Новое": ("#dbeafe", "#1d4ed8"),
    "В работе": ("#fef3c7", "#b45309"),
    "На проверке": ("#fef3c7", "#b45309"),
    "Решено": ("#dcfce7", "#15803d"),
    "Отклонено": ("#fee2e2", "#dc2626"),
}