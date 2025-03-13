import os
import sys
import logging
from app import app, db
from models import Recipient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def import_recipients_from_file(file_path):
    """
    Импортирует получателей из текстового файла

    Args:
        file_path (str): Путь к файлу

    Returns:
        bool: Успешность операции
    """
    from app import db, app
    from models import Recipient
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Проверка существования файла
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            print(f"Ошибка: Файл не найден: {file_path}")
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            recipients_list = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        if not recipients_list:
            logger.warning(f"Файл {file_path} пуст или не содержит валидных получателей")
            print(f"Предупреждение: Файл {file_path} не содержит получателей")
            return False

        logger.info(f"Импорт получателей из файла: {file_path}, найдено: {len(recipients_list)}")
        print(f"Импорт получателей из файла: {file_path}")
        added = 0
        skipped = 0

        with app.app_context():
            for recipient in recipients_list:
                # Проверка формата (должен начинаться с @ или +)
                if not (recipient.startswith('@') or recipient.startswith('+')):
                    logger.warning(f"Некорректный формат: {recipient}")
                    print(f"Пропущен (некорректный формат): {recipient}")
                    skipped += 1
                    continue

                # Проверка на существование
                existing = Recipient.query.filter_by(identifier=recipient).first()
                if not existing:
                    # Добавление нового получателя
                    new_recipient = Recipient(identifier=recipient)
                    db.session.add(new_recipient)
                    logger.info(f"Добавлен получатель: {recipient}")
                    print(f"Добавлен: {recipient}")
                    added += 1
                else:
                    logger.info(f"Получатель уже существует: {recipient}")
                    print(f"Пропущен (уже существует): {recipient}")
                    skipped += 1

            # Сохраняем изменения
            db.session.commit()

            # Проверяем, что данные действительно добавились
            total_recipients = Recipient.query.count()
            logger.info(f"Всего получателей в базе после импорта: {total_recipients}")

        print("\nРезультаты импорта:")
        print(f"- Добавлено: {added}")
        print(f"- Пропущено: {skipped}")

        return added > 0

    except Exception as e:
        logger.error(f"Ошибка при импорте получателей: {e}")
        print(f"Ошибка при импорте получателей: {e}")
        return False

if __name__ == "__main__":
    # Определяем путь к файлу
    file_path = "recipients.txt"
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    # Импортируем получателей
    import_recipients_from_file(file_path)