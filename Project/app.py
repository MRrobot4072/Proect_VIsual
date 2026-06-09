import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from functools import wraps
from database import DatabaseManager
from datetime import datetime
import io
import csv
from datetime import datetime
from config import CATEGORY_COLORS, STATUS_COLORS
from utils import validate_name, validate_phone, validate_email

app = Flask(__name__)
app.secret_key = 'supersecretkeychangeinproduction'  # В реальном проекте используйте переменные окружения
db = DatabaseManager()

# Контекстный процессор для передачи цветов в шаблоны
@app.context_processor
def inject_colors():
    return dict(category_colors=CATEGORY_COLORS, status_colors=STATUS_COLORS)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        user = db.authenticate(login, password)
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_role'] = user['role']
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    appeals = db.get_appeals_list(limit=5)
    return render_template('index.html', appeals=appeals)

@app.route('/appeals')
@login_required
def appeals():
    # Получение параметров
    status = request.args.get('status')
    if status == 'Все статусы':
        status = None
    category = request.args.get('category')
    if category == 'Все категории':
        category = None
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    is_repeat = request.args.get('is_repeat')
    if is_repeat == 'on':
        is_repeat = True
    elif is_repeat == 'off' or is_repeat is None:
        is_repeat = None

    page = request.args.get('page', 1, type=int)
    per_page = 10
    sort_column = request.args.get('sort', 'created_at')
    sort_direction = request.args.get('dir', 'DESC')

    valid_columns = ['id', 'citizen_full', 'category', 'status', 'created_at']
    if sort_column not in valid_columns:
        sort_column = 'created_at'
    if sort_direction not in ['ASC', 'DESC']:
        sort_direction = 'DESC'

    offset = (page - 1) * per_page
    appeals_list = db.get_appeals_filtered(
        status=status, category=category, date_from=date_from, date_to=date_to,
        is_repeat=is_repeat, limit=per_page, offset=offset,
        sort_column=sort_column, sort_direction=sort_direction
    )
    total_count = db.get_appeals_count(
        status=status, category=category, date_from=date_from, date_to=date_to, is_repeat=is_repeat
    )
    categories = ['Все категории'] + db.get_categories()
    statuses = ['Все статусы'] + db.get_statuses()

    # Подготовка аргументов для сохранения фильтров в ссылках сортировки
    args = request.args.to_dict()
    args.pop('sort', None)
    args.pop('dir', None)
    args.pop('page', None)

    return render_template('appeals.html',
                           appeals=appeals_list,
                           total=total_count,
                           page=page,
                           per_page=per_page,
                           categories=categories,
                           statuses=statuses,
                           current_status=status,
                           current_category=category,
                           current_date_from=date_from,
                           current_date_to=date_to,
                           current_repeat=is_repeat,
                           sort_column=sort_column,
                           sort_direction=sort_direction,
                           args=args)

@app.route('/appeal/<int:appeal_id>')
@login_required
def appeal_detail(appeal_id):
    appeal = db.get_appeal_details(appeal_id)
    if not appeal:
        flash('Обращение не найдено.', 'danger')
        return redirect(url_for('appeals'))
    return render_template('appeal_detail.html', appeal=appeal)

@app.route('/appeal/add', methods=['GET', 'POST'])
@login_required
def add_appeal():
    categories = db.get_categories()
    if request.method == 'POST':
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip() or None
        phone = request.form.get('phone', '').strip()
        email_raw = request.form.get('email', '').strip()
        email = email_raw if email_raw else None
        category = request.form.get('category')
        description = request.form.get('description', '').strip()

        errors = []
        if not all([last_name, first_name, phone, category, description]):
            flash('Заполните все обязательные поля!', 'danger')
        else:
            if not validate_name(last_name):
                errors.append('Фамилия может содержать только буквы, дефис и пробел.')
            if not validate_name(first_name):
                errors.append('Имя может содержать только буквы, дефис и пробел.')
            if middle_name and not validate_name(middle_name):
                errors.append('Отчество может содержать только буквы, дефис и пробел.')
            if not validate_phone(phone):
                errors.append('Некорректный формат телефона.')
            if email and not validate_email(email):
                errors.append('Некорректный формат email.')
            if errors:
                for err in errors:
                    flash(err, 'danger')
            else:
                try:
                    db.add_appeal({
                        'last_name': last_name,
                        'first_name': first_name,
                        'middle_name': middle_name,
                        'phone': phone,
                        'email': email
                    }, category, description)
                    flash('Обращение успешно добавлено!', 'success')
                    return redirect(url_for('appeals'))
                except Exception as e:
                    flash(f'Ошибка при добавлении: {str(e)}', 'danger')
    return render_template('add_appeal.html', categories=categories, appeal=None)

@app.route('/appeal/edit/<int:appeal_id>', methods=['GET', 'POST'])
@login_required
def edit_appeal(appeal_id):
    appeal = db.get_appeal_details(appeal_id)
    if not appeal:
        flash('Обращение не найдено.', 'danger')
        return redirect(url_for('appeals'))
    categories = db.get_categories()
    statuses = db.get_statuses()

    if request.method == 'POST':
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip() or None
        phone = request.form.get('phone', '').strip()
        email_raw = request.form.get('email', '').strip()
        email = email_raw if email_raw else None
        category = request.form.get('category')
        description = request.form.get('description', '').strip()
        status = request.form.get('status')

        errors = []
        if not all([last_name, first_name, phone, category, description, status]):
            flash('Заполните все поля!', 'danger')
        else:
            if not validate_name(last_name):
                errors.append('Фамилия может содержать только буквы, дефис и пробел.')
            if not validate_name(first_name):
                errors.append('Имя может содержать только буквы, дефис и пробел.')
            if middle_name and not validate_name(middle_name):
                errors.append('Отчество может содержать только буквы, дефис и пробел.')
            if not validate_phone(phone):
                errors.append('Некорректный формат телефона.')
            if email and not validate_email(email):
                errors.append('Некорректный формат email.')
            if errors:
                for err in errors:
                    flash(err, 'danger')
            else:
                try:
                    db.update_appeal(appeal_id, {
                        'last_name': last_name,
                        'first_name': first_name,
                        'middle_name': middle_name,
                        'phone': phone,
                        'email': email
                    }, category, description, status)
                    flash('Обращение обновлено!', 'success')
                    return redirect(url_for('appeal_detail', appeal_id=appeal_id))
                except Exception as e:
                    flash(f'Ошибка: {str(e)}', 'danger')
    return render_template('add_appeal.html', categories=categories, appeal=appeal, statuses=statuses)

@app.route('/appeal/delete/<int:appeal_id>', methods=['POST'])
@login_required
def delete_appeal(appeal_id):
    db.delete_appeal(appeal_id)
    flash('Обращение удалено.', 'success')
    return redirect(url_for('appeals'))

@app.route('/reports')
@login_required
def reports():
    total_stats = db.get_total_stats()
    category_stats = db.get_category_stats()
    status_stats = db.get_status_stats()
    reasons_stats = db.get_repeat_reasons_stats()
    daily_stats = db.get_daily_stats(days=7)
    
    # Преобразуем Row в dict для JSON-сериализации
    daily_list = [{'day': row['day'], 'count': row['count']} for row in daily_stats]
    
    return render_template('reports.html',
                           total=total_stats,
                           categories=category_stats,
                           statuses=status_stats,
                           reasons=reasons_stats,
                           daily=daily_list)

@app.route('/export/csv')
@login_required
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['ОТЧЁТ ПО ОБРАЩЕНИЯМ ГРАЖДАН'])
    writer.writerow([f'Дата формирования: {datetime.now().strftime("%d.%m.%Y %H:%M")}'])
    writer.writerow([])
    total_stats = db.get_total_stats()
    writer.writerow(['ОБЩАЯ СТАТИСТИКА'])
    writer.writerow(['Всего обращений', total_stats['total']])
    writer.writerow(['Первичных', total_stats['primary']])
    writer.writerow(['Повторных', total_stats['repeat']])
    writer.writerow(['Уникальных граждан', total_stats['unique_citizens']])
    writer.writerow(['Процент повторов', f"{total_stats['repeat_percent']}%"])
    writer.writerow([])
    writer.writerow(['ПО КАТЕГОРИЯМ СЕРВИСОВ'])
    writer.writerow(['Категория', 'Всего', 'Повторных', 'Процент повторов'])
    for row in db.get_category_stats():
        pct = round(row['repeat_count'] / row['total'] * 100, 1) if row['total'] > 0 else 0
        writer.writerow([row['category'], row['total'], row['repeat_count'], f"{pct}%"])
    writer.writerow([])
    writer.writerow(['ПО СТАТУСАМ'])
    writer.writerow(['Статус', 'Количество'])
    for row in db.get_status_stats():
        writer.writerow([row['status'], row['count']])
    writer.writerow([])
    writer.writerow(['ПРИЧИНЫ ПОВТОРНЫХ ОБРАЩЕНИЙ'])
    writer.writerow(['Причина', 'Количество'])
    for row in db.get_repeat_reasons_stats():
        writer.writerow([row['reason'], row['count']])
    writer.writerow([])
    writer.writerow(['ДИНАМИКА ЗА ПОСЛЕДНИЕ 7 ДНЕЙ'])
    writer.writerow(['Дата', 'Количество'])
    for row in db.get_daily_stats(days=7):
        date_fmt = datetime.strptime(row['day'], "%Y-%m-%d").strftime("%d.%m.%Y")
        writer.writerow([date_fmt, row['count']])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d.%m.%Y %H:%M'):
    """Форматирует дату-время из строки SQLite или datetime объекта."""
    if not value:
        return ''
    if isinstance(value, str):
        try:
            # Пробуем распарсить строку "YYYY-MM-DD HH:MM:SS" или "YYYY-MM-DD"
            if ' ' in value:
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            else:
                dt = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    elif isinstance(value, datetime):
        dt = value
    else:
        return str(value)
    return dt.strftime(format)

if __name__ == '__main__':
    app.run(debug=True)