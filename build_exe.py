import os
import sys
import subprocess
import logging
import platform
from build import build_executable

if __name__ == "__main__":
    print("=" * 60)
    print("Telegram Bulk Messenger - EXE Builder")
    print("=" * 60)
    
    # Проверяем наличие API ключей в переменных окружения
    api_id = os.environ.get('TELEGRAM_API_ID')
    api_hash = os.environ.get('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        print("\nWARNING: Telegram API credentials not found in environment variables.")
        print("The compiled application will use Demo Mode by default.")
        print("Users can configure their API keys in the application on first run.")
        
        # Запрашиваем подтверждение
        confirm = input("\nContinue with compilation? (yes/no): ")
        if confirm.lower() != 'yes':
            print("\nCompilation cancelled.")
            sys.exit(0)
    
    # Запускаем компиляцию
    print("\nStarting compilation process...")
    success = build_executable()
    
    if success:
        print("\nEXE build completed successfully!")
        
        # Получаем путь к исполняемому файлу
        if platform.system() == 'Windows':
            output_name = 'telegram_bulk_messenger.exe'
        else:
            output_name = 'telegram_bulk_messenger'
        
        dist_dir = os.path.join(os.getcwd(), 'dist')
        executable_path = os.path.join(dist_dir, output_name)
        
        print(f"\nExecutable location: {executable_path}")
        print("\nYou can now distribute this file to your users.")
        print("Remember that users will need to configure their own API keys on first run,")
        print("or the application will operate in Demo Mode only.")
    else:
        print("\nEXE build failed. Please check the logs for details.")
        sys.exit(1)