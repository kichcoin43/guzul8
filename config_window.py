import os
import sys
import logging
import platform
import tkinter as tk
from tkinter import ttk, messagebox

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ConfigWindow:
    """Окно конфигурации для настройки API ключей Telegram"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Bulk Messenger - Configuration")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Центрируем окно на экране
        self.center_window()
        
        # Настраиваем стиль
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 11))
        style.configure("TButton", font=("Arial", 11))
        style.configure("TEntry", font=("Arial", 11))
        style.configure("TCheckbutton", font=("Arial", 11))
        style.configure("Title.TLabel", font=("Arial", 14, "bold"))
        
        # Основной контейнер с отступами
        main_frame = ttk.Frame(root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Telegram API Configuration", style="Title.TLabel")
        title_label.pack(pady=(0, 20))
        
        # Фрейм для настроек Telegram API
        api_frame = ttk.LabelFrame(main_frame, text="Telegram API Settings", padding="10 10 10 10")
        api_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # API ID
        api_id_label = ttk.Label(api_frame, text="API ID:", anchor="w")
        api_id_label.pack(fill=tk.X, pady=(10, 5))
        
        self.api_id_var = tk.StringVar(value=os.environ.get("TELEGRAM_API_ID", ""))
        self.api_id_entry = ttk.Entry(api_frame, textvariable=self.api_id_var, width=50)
        self.api_id_entry.pack(fill=tk.X, pady=(0, 10))
        
        # API Hash
        api_hash_label = ttk.Label(api_frame, text="API Hash:", anchor="w")
        api_hash_label.pack(fill=tk.X, pady=(10, 5))
        
        self.api_hash_var = tk.StringVar(value=os.environ.get("TELEGRAM_API_HASH", ""))
        self.api_hash_entry = ttk.Entry(api_frame, textvariable=self.api_hash_var, width=50)
        self.api_hash_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Чекбокс для Demo Mode
        self.demo_mode_var = tk.BooleanVar(value=os.environ.get("TELEGRAM_DEMO_MODE", "False").lower() == "true")
        self.demo_mode_checkbox = ttk.Checkbutton(
            api_frame, 
            text="Demo Mode (no real messages will be sent)", 
            variable=self.demo_mode_var
        )
        self.demo_mode_checkbox.pack(fill=tk.X, pady=(10, 10))
        
        # Текст с инструкциями
        instruction_text = (
            "To use this application with your Telegram account, you need to get your own API keys:\n"
            "1. Visit https://my.telegram.org/auth and log in\n"
            "2. Go to 'API development tools'\n"
            "3. Create a new application\n"
            "4. Copy the API ID and API Hash values to the fields above\n\n"
            "If you just want to test the application without sending real messages, "
            "enable Demo Mode."
        )
        
        instruction_label = ttk.Label(api_frame, text=instruction_text, anchor="w", wraplength=500, justify="left")
        instruction_label.pack(fill=tk.X, pady=(10, 10))
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Save button
        save_button = ttk.Button(button_frame, text="Save & Start", command=self.save_and_start)
        save_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Cancel button
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.root.destroy)
        cancel_button.pack(side=tk.RIGHT)
        
    def center_window(self):
        """Центрирует окно на экране"""
        self.root.update_idletasks()
        
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def save_and_start(self):
        """Сохраняет настройки и закрывает окно конфигурации"""
        # Проверка API ID (должен быть числом)
        api_id = self.api_id_var.get().strip()
        if not api_id and not self.demo_mode_var.get():
            messagebox.showerror("Error", "API ID is required when not in Demo Mode.")
            return
        
        if api_id and not api_id.isdigit():
            messagebox.showerror("Error", "API ID must be a number.")
            return
        
        # Проверка API Hash (должен быть непустым)
        api_hash = self.api_hash_var.get().strip()
        if not api_hash and not self.demo_mode_var.get():
            messagebox.showerror("Error", "API Hash is required when not in Demo Mode.")
            return
        
        # Сохраняем настройки в переменные окружения
        os.environ["TELEGRAM_API_ID"] = api_id
        os.environ["TELEGRAM_API_HASH"] = api_hash
        os.environ["TELEGRAM_DEMO_MODE"] = str(self.demo_mode_var.get())
        
        logger.info(f"Configuration saved. Demo Mode: {self.demo_mode_var.get()}")
        
        # Закрываем окно конфигурации
        self.root.destroy()


def show_config_window():
    """Показывает окно конфигурации и возвращает результат настройки"""
    try:
        root = tk.Tk()
        app = ConfigWindow(root)
        root.mainloop()
        return True
    except Exception as e:
        logger.error(f"Error in configuration window: {str(e)}")
        return False

if __name__ == "__main__":
    # Для тестирования
    show_config_window()