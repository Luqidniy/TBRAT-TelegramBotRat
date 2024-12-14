import os
import subprocess
import shutil
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Компилятор Telegram Бота")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
        QMainWindow {
            background-color: #1a1a1a;
        }
        QLabel {
            font-size: 14px;
            color: #e0e0e0;
        }
        QLineEdit {
            padding: 8px;
            border: 1px solid #8a2be2;
            border-radius: 10px;
            font-size: 14px;
            background-color: rgba(138, 43, 226, 0.1);
            color: #e0e0e0;
        }
        QPushButton {
            background-color: #8a2be2;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 10px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #9b30ff;
        }
    """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        self.bot_token_entry = self.create_input("Токен бота:", layout)
        self.chat_id_entry = self.create_input("Chat ID:", layout)
        self.output_name_entry = self.create_input("Имя выходного файла:", layout)
        
        icon_layout = QHBoxLayout()
        self.icon_path_entry = QLineEdit()
        icon_layout.addWidget(QLabel("Иконка (необязательно):"))
        icon_layout.addWidget(self.icon_path_entry)
        browse_icon_button = QPushButton("Выбрать")
        browse_icon_button.clicked.connect(self.browse_icon)
        icon_layout.addWidget(browse_icon_button)
        layout.addLayout(icon_layout)

        compile_button = QPushButton("Компилировать")
        compile_button.clicked.connect(self.compile_to_exe)
        layout.addWidget(compile_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def create_input(self, label_text, layout):
        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel(label_text))
        entry = QLineEdit()
        input_layout.addWidget(entry)
        layout.addLayout(input_layout)
        return entry

    def browse_icon(self):
        icon_path, _ = QFileDialog.getOpenFileName(self, "Выберите иконку", "", "Icon files (*.ico)")
        if icon_path:
            self.icon_path_entry.setText(icon_path)

    def compile_to_exe(self):
        bot_token = self.bot_token_entry.text()
        chat_id = self.chat_id_entry.text()
        output_name = self.output_name_entry.text()
        icon_path = self.icon_path_entry.text()

        if not bot_token or not chat_id or not output_name:
            QMessageBox.critical(self, "Ошибка", "Пожалуйста, заполните все поля!")
            return

        source_file_path = os.path.join("bin", "main.py")
    
        if not os.path.exists(source_file_path):
            QMessageBox.critical(self, "Ошибка", "Файл main.py не найден в папке bin!")
            return

        temp_script_path = "temp_bot_script.py"
    
        with open(source_file_path, "r", encoding="utf-8") as f:
            script_content = f.read()

        # Замена значений BOT_TOKEN и CHAT_ID
        script_content = script_content.replace("BOT_TOKEN = ''", f"BOT_TOKEN = '{bot_token}'")
        script_content = script_content.replace("CHAT_ID = ''", f"CHAT_ID = '{chat_id}'")

        with open(temp_script_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        pyinstaller_command = [
            "pyinstaller",
            "--onefile",
            "--noconsole",
            f"--name={output_name}",
        ]

        if icon_path:
            pyinstaller_command.append(f"--icon={icon_path}")

        pyinstaller_command.append(temp_script_path)

        try:
            subprocess.run(pyinstaller_command, check=True)
            QMessageBox.information(self, "Успех", f"Компиляция завершена! Файл создан: dist/{output_name}.exe")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при компиляции: {e}")
        finally:
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
            build_folder = "build"
            spec_file = f"{output_name}.spec"
            if os.path.exists(build_folder):
                shutil.rmtree(build_folder)
            if os.path.exists(spec_file):
                os.remove(spec_file)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

