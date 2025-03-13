#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Веб-интерфейс для отправителя сообщений Telegram
==============================================

Этот модуль обеспечивает веб-интерфейс к отправителю сообщений Telegram.
Веб-интерфейс позволяет настраивать отправителя и управлять отправкой сообщений.
"""

import os
import json
import logging
import time
import random
import telethon
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from telethon.sync import TelegramClient
from telethon.errors import (
    PhoneCodeExpiredError, PhoneCodeInvalidError,
    SessionPasswordNeededError, FloodWaitError,
    ApiIdInvalidError
)
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Определяем базовый класс моделей SQLAlchemy
class Base(DeclarativeBase):
    pass

# Инициализируем SQLAlchemy с базовым классом
db = SQLAlchemy(model_class=Base)

# Создаем приложение Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Конфигурируем базу данных
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Инициализируем расширение SQLAlchemy
db.init_app(app)

# Глобальная переменная для клиента Telegram
telegram_client = None

def init_telegram_client(api_id, api_hash, session_name="ua_session"):
    """Инициализация клиента Telegram"""
    global telegram_client
    try:
        if telegram_client is None or not telegram_client.is_connected():
            telegram_client = TelegramClient(session_name, api_id, api_hash)
            telegram_client.connect()
            logger.info("Telegram клиент инициализирован")
        return telegram_client.is_connected()
    except ApiIdInvalidError:
        logger.error("Неверные API ID или API Hash")
        return False
    except Exception as e:
        logger.error(f"Ошибка инициализации Telegram клиента: {e}")
        return False

def check_auth():
    """Проверка авторизации в Telegram"""
    global telegram_client
    try:
        # Если в сессии отмечено, что пользователь вышел, то считаем не авторизованным
        if session.get('logged_in') == False:
            logger.info("Пользователь вышел из аккаунта")
            return False
            
        # Переподключаемся если соединение потеряно
        api_id = os.environ.get('TELEGRAM_API_ID')
        api_hash = os.environ.get('TELEGRAM_API_HASH')

        if telegram_client is None or not telegram_client.is_connected():
            if not init_telegram_client(int(api_id), api_hash):
                return False

        is_authorized = telegram_client.is_user_authorized()
        logger.info(f"Проверка авторизации: {is_authorized}")
        
        # Сохраняем статус авторизации в сессии
        if is_authorized:
            session['logged_in'] = True
        
        return is_authorized
    except Exception as e:
        logger.error(f"Ошибка проверки авторизации: {e}")
        return False

@app.before_request
def before_request():
    """Проверяем подключение к Telegram перед каждым запросом и перенаправляем на авторизацию если нужно"""
    # Обработка страницы авторизации Telegram
    if request.path == '/auth':
        # Пропускаем цветочную страницу при авторизации
        session['from_flower'] = True
        return None
    
    # Для POST-запроса к странице авторизации не делаем перенаправлений
    if request.path == '/auth' and request.method == 'POST':
        return None
    
    # Сбрасываем флаги авторизации для других страниц
    if request.path not in ['/', '/auth', '/login']:
        session.pop('auth_in_progress', None)
    
    # Сбрасываем список получателей при первом входе
    if request.path == '/' and 'recipients_reset' not in session:
        try:
            # Очищаем таблицу получателей
            Recipient.query.delete()
            db.session.commit()
            session['recipients_reset'] = True
            logger.info("Список получателей сброшен при новом входе")
        except Exception as e:
            logger.error(f"Ошибка при сбросе списка получателей: {e}")
    
    # Показываем цветочную страницу при запросе к корню
    if request.path == '/' and 'skip_flower' not in session:
        session['on_flower_page'] = True
        return None
    
    # Показываем страницу авторизации после цветочной страницы
    if request.path == '/login' and session.get('from_flower') == True:
        session.pop('from_flower', None)
        return redirect(url_for('auth'))
    
    # Исключения для статических файлов и служебных маршрутов
    allowed_paths = ['/static/', '/', '/auth', '/login', '/logout', '/logout_telegram', '/help']
    is_allowed = False
    
    for path in allowed_paths:
        if request.path.startswith(path) or request.path == path:
            is_allowed = True
            break
    
    # Проверка авторизации для защищенных маршрутов
    if not is_allowed and not check_auth():
        if request.path not in ['/login', '/auth']:
            flash('Необходима авторизация для доступа к системе', 'warning')
            return redirect(url_for('flower_login'))
    
    # Инициализация клиента Telegram для всех маршрутов кроме статики
    if not request.path.startswith('/static') and request.path != '/':
        api_id = os.environ.get('TELEGRAM_API_ID')
        api_hash = os.environ.get('TELEGRAM_API_HASH')
        if api_id and api_hash:
            init_telegram_client(int(api_id), api_hash)

# Создаем таблицы в базе данных
with app.app_context():
    from models import MessageLog, BroadcastSession, User, Recipient # Assuming Recipient model is in models.py
    db.create_all()
    logger.info("База данных инициализирована")

# В начале файла, после импортов
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def flower_login():
    """Начальная страница с маскировкой под цветочный магазин"""
    # Сбрасываем флаг skip_flower при каждом посещении цветочной страницы
    session.pop('skip_flower', None)
    # Проверяем флаг, который установил before_request
    if session.get('on_flower_page'):
        session.pop('on_flower_page', None)  # Сразу удаляем флаг
        return render_template('flower_login.html')
    else:
        # Если зашли напрямую, устанавливаем флаг и возвращаем страницу
        session['on_flower_page'] = True
        return render_template('flower_login.html')

@app.route('/home')
def index():
    """Главная страница с информацией о приложении"""
    is_authorized = check_auth()
    
    # Перенаправляем на логин, если не авторизован
    if not is_authorized:
        return redirect(url_for('login'))
        
    stats = {
        'recipients': 0,
        'successful': 0,
        'failed': 0
    }

    try:
        # Получаем статистику из базы данных
        # Количество получателей
        stats['recipients'] = Recipient.query.count()

        # Количество успешно отправленных сообщений
        stats['successful'] = MessageLog.query.filter_by(status='success').count()

        # Количество ошибок отправки
        stats['failed'] = MessageLog.query.filter_by(status='failed').count()

        logger.info(f"Текущая статистика: получателей: {stats['recipients']}, успешно: {stats['successful']}, ошибок: {stats['failed']}")
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")

    return render_template('index.html', 
                         is_authorized=is_authorized,
                         stats=stats)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Страница настройки приложения"""
    config = load_config()

    if request.method == 'POST':
        config['api_id'] = int(request.form.get('api_id', 12345))
        config['api_hash'] = request.form.get('api_hash', '')
        config['session_name'] = request.form.get('session_name', 'ua_session')
        config['delay'] = float(request.form.get('delay', 2.0))

        if save_config(config):
            flash('Настройки успешно сохранены!', 'success')
        else:
            flash('Ошибка при сохранении настроек.', 'danger')

        return redirect(url_for('setup'))

    return render_template('setup.html', config=config)

# Функции работы с получателями
def load_recipients():
    """Загружает список получателей из базы данных"""
    try:
        recipients = Recipient.query.order_by(Recipient.added_at.desc()).all()
        return [r.identifier for r in recipients]
    except Exception as e:
        logger.error(f"Ошибка загрузки получателей из БД: {e}")
        return []

@app.route('/recipients', methods=['GET', 'POST'])
def recipients():
    """Страница управления получателями"""
    if not check_auth():
        flash('Пожалуйста, сначала авторизуйтесь в Telegram', 'warning')
        return redirect(url_for('auth'))

    try:
        # Загружаем список получателей
        recipients_list = Recipient.query.order_by(Recipient.added_at.desc()).all()
        logger.info(f"Загружено получателей: {len(recipients_list)}")

        if request.method == 'POST':
            action = request.form.get('action')
            logger.info(f"Получено действие: {action}")

            if action == 'add':
                new_recipient = request.form.get('recipient', '').strip()
                logger.info(f"Попытка добавить получателя: {new_recipient}")

                if new_recipient:
                    try:
                        # Проверяем существование получателя
                        existing = Recipient.query.filter_by(identifier=new_recipient).first()
                        if not existing:
                            # Создаем нового получателя
                            recipient = Recipient(identifier=new_recipient)
                            db.session.add(recipient)
                            db.session.commit()
                            logger.info(f"Успешно добавлен получатель: {new_recipient}")
                            flash(f'Получатель {new_recipient} добавлен!', 'success')
                        else:
                            logger.info(f"Получатель уже существует: {new_recipient}")
                            flash('Такой получатель уже существует.', 'warning')
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Ошибка добавления получателя {new_recipient}: {str(e)}")
                        flash('Ошибка при добавлении получателя.', 'danger')
                else:
                    flash('Получатель не может быть пустым.', 'warning')

            elif action == 'delete':
                recipient_id = request.form.get('recipient')
                logger.info(f"Попытка удалить получателя: {recipient_id}")

                try:
                    recipient = Recipient.query.filter_by(identifier=recipient_id).first()
                    if recipient:
                        db.session.delete(recipient)
                        db.session.commit()
                        logger.info(f"Успешно удален получатель: {recipient_id}")
                        flash(f'Получатель {recipient_id} удален!', 'success')
                    else:
                        logger.warning(f"Получатель не найден: {recipient_id}")
                        flash('Получатель не найден.', 'warning')
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Ошибка удаления получателя {recipient_id}: {str(e)}")
                    flash('Ошибка при удалении получателя.', 'danger')

            elif action == 'import':
                try:
                    # Проверяем наличие загруженного файла
                    if 'recipients_file' not in request.files:
                        flash('Файл не был загружен.', 'warning')
                        return redirect(url_for('recipients'))
                    
                    file = request.files['recipients_file']
                    
                    # Проверяем, что файл выбран
                    if file.filename == '':
                        flash('Не выбран файл.', 'warning')
                        return redirect(url_for('recipients'))
                    
                    # Проверяем расширение файла
                    if not file.filename.lower().endswith('.txt'):
                        flash('Пожалуйста, загрузите текстовый файл (.txt).', 'warning')
                        return redirect(url_for('recipients'))
                    
                    # Создаем временный файл
                    temp_path = 'uploaded_recipients.txt'
                    file.save(temp_path)
                    
                    # Импортируем получателей из файла
                    from import_recipients import import_recipients_from_file
                    result = import_recipients_from_file(temp_path)
                    
                    # Удаляем временный файл
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                    
                    if result:
                        flash(f'Импорт получателей выполнен успешно!', 'success')
                    else:
                        flash(f'Ошибка при импорте получателей.', 'danger')
                except Exception as e:
                    logger.error(f"Ошибка импорта получателей: {str(e)}")
                    flash(f'Ошибка импорта: {str(e)}', 'danger')

            return redirect(url_for('recipients'))

        # Получаем список для отображения
        recipients = [r.identifier for r in recipients_list]
        logger.info(f"Отображение списка получателей: {recipients}")
        return render_template('recipients.html', recipients=recipients)

    except Exception as e:
        logger.error(f"Общая ошибка при работе с получателями: {str(e)}")
        flash('Произошла ошибка при работе с получателями.', 'danger')
        return render_template('recipients.html', recipients=[])

@app.route('/send', methods=['GET', 'POST'])
def send():
    """Страница отправки сообщений"""
    if not check_auth():
        flash('Пожалуйста, сначала авторизуйтесь в Telegram', 'warning')
        return redirect(url_for('auth'))

    try:
        # Загружаем список получателей
        recipients = Recipient.query.order_by(Recipient.added_at.desc()).all()
        recipients_list = [r.identifier for r in recipients]
        logger.info(f"Загружено получателей для отправки: {len(recipients_list)}")

        # Дополнительное логирование для отладки
        for idx, recipient in enumerate(recipients_list):
            logger.info(f"Получатель #{idx+1}: {recipient}")

        if not recipients_list:
            logger.warning("Список получателей пуст! Проверьте таблицу Recipient в базе данных.")
            flash('Добавьте получателей перед отправкой сообщений.', 'warning')
            return redirect(url_for('recipients'))

        if request.method == 'POST':
            message = request.form.get('message', '').strip()
            selected_recipients = request.form.getlist('selected_recipients')
            logger.info(f"Попытка отправки сообщения {len(selected_recipients)} получателям")

            # Дополнительное логирование выбранных получателей
            for idx, recipient in enumerate(selected_recipients):
                logger.info(f"Выбранный получатель #{idx+1}: {recipient}")

            if not message:
                flash('Сообщение не может быть пустым!', 'warning')
                return redirect(url_for('send'))

            if not selected_recipients:
                logger.warning("Не выбрано ни одного получателя!")
                flash('Необходимо выбрать хотя бы одного получателя!', 'warning')
                return redirect(url_for('send'))

            try:
                successful_count = 0
                failed_count = 0

                # Инициализация анти-спам системы
                from anti_spam import AntiSpamThrottler
                throttler = AntiSpamThrottler()

                # Создаем запись о текущей рассылке
                broadcast_session = BroadcastSession(
                    phone_number=session.get('phone', 'Неизвестно'),
                    recipient_count=len(selected_recipients),
                    start_time=datetime.utcnow(),
                    status='in_progress'
                )
                db.session.add(broadcast_session)
                db.session.commit()
                
                for recipient in selected_recipients:
                    try:
                        # Применяем задержку между сообщениями
                        min_delay = float(os.environ.get('MIN_DELAY', '1.5'))  # Минимальная задержка в секундах
                        max_delay = float(os.environ.get('MAX_DELAY', '5.5'))  # Максимальная задержка в секундах
                        
                        # Рассчитываем случайную задержку в заданном диапазоне
                        base_delay = random.uniform(min_delay, max_delay)
                        
                        # Добавляем случайность для большей естественности (±15%)
                        jitter = random.uniform(-0.15, 0.15) * base_delay
                        final_delay = max(0.5, base_delay + jitter)  # Минимум 0.5 секунд
                        
                        logger.info(f"Применяем задержку {final_delay:.2f} секунд перед отправкой")
                        time.sleep(final_delay)
                        
                        # Отправляем сообщение
                        telegram_client.send_message(recipient, message)
                        successful_count += 1
                        throttler.record_success()  # Отмечаем успешную отправку

                        # Логируем успешную отправку
                        log = MessageLog(
                            phone_number=session.get('phone', 'Неизвестно'),
                            recipient=recipient,
                            message_preview=message[:100],
                            status='success'
                        )
                        db.session.add(log)
                        db.session.commit()
                        logger.info(f"Сообщение успешно отправлено: {recipient}")

                    except FloodWaitError as e:
                        # Обработка ограничения частоты отправки от Telegram
                        wait_seconds = e.seconds
                        logger.warning(f"FloodWaitError: необходимо подождать {wait_seconds} секунд")
                        throttler.adjust_for_flood_wait(wait_seconds)
                        
                        # Логируем ошибку
                        log = MessageLog(
                            phone_number=session.get('phone', 'Неизвестно'),
                            recipient=recipient,
                            message_preview=message[:100],
                            status='failed',
                            error_message=f"FloodWaitError: {wait_seconds} секунд"
                        )
                        db.session.add(log)
                        db.session.commit()
                        
                        # Ждем указанное время и повторяем попытку
                        if wait_seconds < 300:  # Повторяем попытку только если ожидание меньше 5 минут
                            time.sleep(wait_seconds)
                            try:
                                telegram_client.send_message(recipient, message)
                                successful_count += 1
                                throttler.record_success()
                                
                                # Обновляем статус сообщения на успешный
                                log.status = 'success'
                                log.error_message = None
                                db.session.commit()
                            except Exception as retry_error:
                                failed_count += 1
                                throttler.record_failure()
                                logger.error(f"Повторная ошибка отправки {recipient}: {retry_error}")
                        else:
                            failed_count += 1
                            throttler.record_failure()
                            
                    except Exception as e:
                        failed_count += 1
                        throttler.record_failure()  # Отмечаем неудачную отправку
                        
                        # Логируем ошибку
                        log = MessageLog(
                            phone_number=session.get('phone', 'Неизвестно'),
                            recipient=recipient,
                            message_preview=message[:100],
                            status='failed',
                            error_message=str(e)
                        )
                        db.session.add(log)
                        db.session.commit()
                        logger.error(f"Ошибка отправки сообщения получателю {recipient}: {e}")
                
                # Завершаем запись о рассылке
                broadcast_session.successful_count = successful_count
                broadcast_session.failed_count = failed_count
                broadcast_session.end_time = datetime.utcnow()
                broadcast_session.status = 'completed'
                db.session.commit()

                if successful_count > 0:
                    flash(f'Успешно отправлено сообщений: {successful_count}', 'success')
                if failed_count > 0:
                    flash(f'Не удалось отправить сообщений: {failed_count}', 'warning')

                return redirect(url_for('index'))

            except Exception as e:
                logger.error(f"Общая ошибка отправки сообщений: {e}")
                flash(f'Произошла ошибка при отправке сообщений: {e}', 'danger')
                return redirect(url_for('send'))

        return render_template('send.html', recipients=recipients_list, recipients_count=len(recipients_list))

    except Exception as e:
        logger.error(f"Ошибка при загрузке страницы отправки: {e}")
        flash('Произошла ошибка при загрузке получателей.', 'danger')
        return render_template('send.html', recipients=[], recipients_count=0)

@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    """Страница подтверждения отправки"""
    message = session.get('message', '')
    selected_recipients = session.get('selected_recipients', [])
    delay = session.get('delay', 2.0)

    if not message or not selected_recipients:
        flash('Информация о сообщении отсутствует. Пожалуйста, вернитесь на страницу отправки.', 'warning')
        return redirect(url_for('send'))

    if request.method == 'POST':
        # Здесь будет код для запуска отправки сообщений
        # Создаем сессию рассылки в базе данных
        broadcast_session = BroadcastSession(
            phone_number=session.get('phone', 'Неизвестно'),
            recipient_count=len(selected_recipients),
            successful_count=0,
            failed_count=0,
            start_time=datetime.utcnow(),
            status='in_progress'
        )
        db.session.add(broadcast_session)
        db.session.commit()

        # Запускаем процесс отправки в фоновом режиме
        # В реальном приложении здесь будет асинхронный запуск отправки
        flash(f'Отправка сообщения {len(selected_recipients)} получателям запущена!', 'success')

        # Очищаем сессию
        session.pop('message', None)
        session.pop('selected_recipients', None)
        session.pop('delay', None)

        return redirect(url_for('index'))

    return render_template('confirm.html', 
                           message=message, 
                           recipients=selected_recipients, 
                           delay=delay)

@app.route('/login')
def login():
    """Страница входа в систему"""
    # Если пользователь уже авторизован, перенаправляем на главную
    if check_auth():
        return redirect(url_for('index'))
    
    # Сбрасываем флаг авторизации для показа формы при каждом посещении
    session.pop('logged_in', None)
    session['skip_flower'] = True  # Устанавливаем флаг, чтобы избежать перенаправления на flower_login
    return render_template('login.html')

@app.route('/compose')
def compose():
    """Страница создания сообщения"""
    if not check_auth():
        flash('Пожалуйста, сначала авторизуйтесь в Telegram', 'warning')
        return redirect(url_for('login'))
    
    # Загружаем список получателей для выбора
    recipients = Recipient.query.order_by(Recipient.added_at.desc()).all()
    recipients_list = [r.identifier for r in recipients]
    
    return render_template('compose.html', recipients=recipients_list, recipients_count=len(recipients_list))


@app.route('/logout_telegram', methods=['GET', 'POST'])
def logout_telegram():
    """Выход из аккаунта Telegram"""
    global telegram_client
    try:
        if telegram_client and telegram_client.is_connected():
            # Закрываем соединение клиента
            telegram_client.disconnect()
            telegram_client = None
            
        # Очищаем сессию от данных авторизации
        session.pop('phone', None)
        session.pop('logged_in', None)
        
        # Удаляем файл сессии
        if os.path.exists('ua_session.session'):
            try:
                os.remove('ua_session.session')
                if os.path.exists('ua_session.session-journal'):
                    os.remove('ua_session.session-journal')
            except Exception as e:
                logger.error(f"Ошибка удаления файла сессии: {e}")
                
        flash('Вы вышли из аккаунта Telegram. Теперь вы можете войти в другой аккаунт.', 'success')
    except Exception as e:
        logger.error(f"Ошибка при выходе из аккаунта: {e}")
        flash(f'Ошибка при выходе из аккаунта: {e}', 'danger')
        
    return redirect(url_for('auth'))

@app.route('/logout')
def logout():
    """Полный выход из системы"""
    global telegram_client
    try:
        if telegram_client and telegram_client.is_connected():
            telegram_client.disconnect()
            telegram_client = None
            
        # Очищаем все данные сессии
        session.clear()
        
        # Удаляем файл сессии
        if os.path.exists('ua_session.session'):
            try:
                os.remove('ua_session.session')
                if os.path.exists('ua_session.session-journal'):
                    os.remove('ua_session.session-journal')
            except Exception as e:
                logger.error(f"Ошибка удаления файла сессии: {e}")
                
        flash('Вы успешно вышли из системы.', 'success')
    except Exception as e:
        logger.error(f"Ошибка при выходе из системы: {e}")
        flash(f'Ошибка при выходе из системы: {e}', 'danger')
        
    return redirect(url_for('index'))

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    """Страница авторизации в Telegram"""
    # Проверяем наличие флага form_flower в POST-запросе
    if request.method == 'POST' and request.form.get('from_flower') == 'true':
        # Если форма отправлена со страницы авторизации, сохраняем флаг в сессии
        session['from_flower'] = True

    # Сбрасываем данные авторизации при первом посещении страницы авторизации
    if 'auth_initialized' not in session:
        session['auth_initialized'] = True
        session.pop('logged_in', None)
        
        # Удаляем все данные получателей из базы только при первом посещении страницы авторизации
        try:
            Recipient.query.delete()
            db.session.commit()
            session['auth_recipients_reset'] = True
            logger.info("Список получателей сброшен при входе на страницу авторизации")
        except Exception as e:
            logger.error(f"Ошибка при сбросе списка получателей: {e}")
    
    # Загружаем API credentials из окружения
    api_id = os.environ.get('TELEGRAM_API_ID')
    api_hash = os.environ.get('TELEGRAM_API_HASH')

    # Проверяем наличие API credentials
    if not api_id or not api_hash:
        flash('Отсутствуют API credentials для Telegram. Пожалуйста, настройте их в настройках.', 'danger')
        return redirect(url_for('setup'))

    phone = session.get('phone', '')

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'request_code':
            phone = request.form.get('phone', '').strip()
            if not phone:
                flash('Номер телефона не может быть пустым!', 'warning')
                return render_template('auth.html', phone=phone)
            else:
                try:
                    # Инициализируем клиент
                    if not init_telegram_client(int(api_id), api_hash):
                        flash('Ошибка подключения к Telegram! Проверьте API credentials.', 'danger')
                        return render_template('auth.html', phone=phone)

                    # Отправляем запрос на код
                    telegram_client.send_code_request(phone)
                    session['phone'] = phone
                    flash(f'Код подтверждения отправлен на номер {phone}!', 'success')
                    # Устанавливаем флаг, чтобы знать, что запрос кода выполнен
                    session['code_requested'] = True
                    # Возвращаем страницу авторизации без перенаправления
                    return render_template('auth.html', phone=phone)
                except ApiIdInvalidError:
                    flash('Неверные API ID или API Hash. Проверьте настройки.', 'danger')
                except Exception as e:
                    flash(f'Ошибка запроса кода: {e}', 'danger')

        elif action == 'verify_code':
            code = request.form.get('code', '').strip()
            password = request.form.get('password', '').strip()
            phone = session.get('phone', '')

            if not code:
                flash('Код подтверждения не может быть пустым!', 'warning')
                return render_template('auth.html', phone=phone)
            elif not phone:
                flash('Сначала запросите код подтверждения!', 'warning')
                return render_template('auth.html', phone=phone)
            else:
                try:
                    # Пробуем войти с кодом
                    telegram_client.sign_in(phone=phone, code=code)
                    session['logged_in'] = True
                    flash('Авторизация успешно выполнена!', 'success')
                    return redirect(url_for('index'))
                except SessionPasswordNeededError:
                    # Требуется 2FA
                    if not password:
                        flash('Требуется пароль двухфакторной аутентификации!', 'warning')
                        return render_template('auth.html', phone=phone, need_2fa=True)
                    else:
                        try:
                            telegram_client.sign_in(password=password)
                            session['logged_in'] = True
                            flash('Авторизация успешно выполнена!', 'success')
                            return redirect(url_for('index'))
                        except Exception as e:
                            flash(f'Ошибка входа с 2FA: {e}', 'danger')
                            return render_template('auth.html', phone=phone, need_2fa=True)
                except PhoneCodeExpiredError:
                    flash('Код подтверждения истек. Пожалуйста, запросите новый код.', 'warning')
                    return render_template('auth.html', phone=phone)
                except PhoneCodeInvalidError:
                    flash('Неверный код подтверждения. Попробуйте еще раз.', 'warning')
                    return render_template('auth.html', phone=phone)
                except Exception as e:
                    flash(f'Ошибка авторизации: {e}', 'danger')
                    return render_template('auth.html', phone=phone)

        # Вместо перенаправления возвращаем шаблон напрямую
        return render_template('auth.html', phone=session.get('phone', ''))

    return render_template('auth.html', phone=phone)

@app.route('/help')
def help_page():
    """Страница помощи"""
    return render_template('help.html')

# Функции для работы с конфигурацией
def load_config():
    """Загружает конфигурацию из файла"""
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'api_id': 12345,  # Значения по умолчанию
            'api_hash': 'abcdef1234567890abcdef1234567890',
            'session_name': 'ua_session',
            'delay': 2.0
        }
    except Exception as e:
        logger.error(f"Ошибка загрузки конфигурации: {e}")
        return {
            'api_id': 12345,
            'api_hash': 'abcdef1234567890abcdef1234567890',
            'session_name': 'ua_session',
            'delay': 2.0
        }

def save_config(config):
    """Сохраняет конфигурацию в файл"""
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения конфигурации: {e}")
        return False


# Запускаем приложение
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)