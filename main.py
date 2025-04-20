import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit,
    QComboBox, QDateEdit, QSpinBox, QFileDialog, QProgressBar, QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QListWidget, QHBoxLayout
)
from fpdf import FPDF
from PyQt6.QtCore import Qt, QTimer, QDate
from cryptography.fernet import Fernet
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

class InsuranceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.contracts = self.load_contracts()  # Загружаем историю договоров
        self.update_contracts_list()

    def initUI(self):
        self.setWindowTitle("Страховой договор")
        self.setGeometry(200, 200, 800, 600)  # Увеличиваем окно для дополнительных функций

        main_layout = QHBoxLayout()  # Основной горизонтальный layout

        # Слева - список договоров
        left_layout = QVBoxLayout()

        # Поиск по договору
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Поиск по ФИО или типу")
        self.search_input.textChanged.connect(self.search_contracts)
        left_layout.addWidget(self.search_input)

        # Кнопки сортировки
        self.sort_fio_button = QPushButton("Сортировать по ФИО", self)
        self.sort_fio_button.clicked.connect(self.sort_by_fio)
        left_layout.addWidget(self.sort_fio_button)

        self.sort_type_button = QPushButton("Сортировать по типу", self)
        self.sort_type_button.clicked.connect(self.sort_by_type)
        left_layout.addWidget(self.sort_type_button)

        self.sort_date_button = QPushButton("Сортировать по дате", self)
        self.sort_date_button.clicked.connect(self.sort_by_date)
        left_layout.addWidget(self.sort_date_button)

        # Список договоров
        self.contract_list = QListWidget(self)
        self.contract_list.clicked.connect(self.show_password_dialog)
        left_layout.addWidget(self.contract_list)

        main_layout.addLayout(left_layout)

        # Справа - форма создания договора
        form_layout = QVBoxLayout()

        self.fio_input = QLineEdit(self)
        self.fio_input.setPlaceholderText("ФИО клиента")
        form_layout.addWidget(QLabel("ФИО Клиента:"))
        form_layout.addWidget(self.fio_input)

        self.birth_date = QDateEdit(self)
        form_layout.addWidget(QLabel("Дата рождения:"))
        form_layout.addWidget(self.birth_date)

        self.passport_input = QLineEdit(self)
        self.passport_input.setPlaceholderText("Серия и номер паспорта")
        form_layout.addWidget(QLabel("Паспортные данные:"))
        form_layout.addWidget(self.passport_input)

        self.phone_input = QLineEdit(self)
        self.phone_input.setPlaceholderText("Контактный телефон")
        form_layout.addWidget(QLabel("Контактный телефон:"))
        form_layout.addWidget(self.phone_input)

        self.insurance_type = QComboBox(self)
        self.insurance_type.addItems(["Автострахование", "Медицинское", "Недвижимость", "Жизнь", "Туризм"])
        form_layout.addWidget(QLabel("Тип страхования:"))
        form_layout.addWidget(self.insurance_type)

        self.duration = QSpinBox(self)
        self.duration.setRange(1, 36)
        form_layout.addWidget(QLabel("Срок страхования (мес):"))
        form_layout.addWidget(self.duration)

        self.amount = QSpinBox(self)
        self.amount.setRange(10000, 10000000)
        self.amount.setSingleStep(10000)
        form_layout.addWidget(QLabel("Страховая сумма (₽):"))
        form_layout.addWidget(self.amount)

        self.create_button = QPushButton("Создать договор", self)
        self.create_button.clicked.connect(self.create_contract)
        form_layout.addWidget(self.create_button)

        self.print_button = QPushButton("Печать договора", self)
        self.print_button.clicked.connect(self.print_contract)
        form_layout.addWidget(self.print_button)

        self.clear_button = QPushButton("Очистить форму", self)
        self.clear_button.clicked.connect(self.clear_form)
        form_layout.addWidget(self.clear_button)

        self.delete_button = QPushButton("Удалить договор", self)
        self.delete_button.clicked.connect(self.delete_contract)
        form_layout.addWidget(self.delete_button)

        self.progress = QProgressBar(self)
        self.progress.setValue(0)
        form_layout.addWidget(self.progress)

        main_layout.addLayout(form_layout)  # Размещение формы справа

        self.setLayout(main_layout)

    def create_contract(self):
        if not self.validate_inputs():
            return

        dialog = PasswordDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            password = dialog.get_password()
            try:
                decrypted_password = decrypt_password()
                if password == decrypted_password:
                    self.progress.setValue(0)
                    self.timer = QTimer(self)
                    self.timer.timeout.connect(self.update_progress)
                    self.progress_value = 0
                    self.timer.start(500)
                else:
                    QMessageBox.warning(self, "Ошибка", "Неверный пароль!")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", "Не удалось расшифровать пароль!")

    def update_progress(self):
        if self.progress_value < 100:
            self.progress_value += 25
            self.progress.setValue(self.progress_value)
        else:
            self.timer.stop()
            self.save_contract()

    def save_contract(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить договор", "contract.pdf", "PDF Files (*.pdf)")
        if filename:
            pdf = FPDF()
            pdf.add_page()
            pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
            pdf.set_font("DejaVu", size=12)

            pdf.set_fill_color(200, 220, 255)
            pdf.cell(200, 10, "ДОГОВОР СТРАХОВАНИЯ", ln=True, align='C', fill=True)
            pdf.ln(10)

            pdf.set_font("DejaVu", size=10)
            pdf.cell(200, 6, f"ФИО Клиента: {self.fio_input.text()}", ln=True, border=1)
            pdf.cell(200, 6, f"Дата рождения: {self.birth_date.date().toString('dd.MM.yyyy')}", ln=True, border=1)
            pdf.cell(200, 6, f"Паспорт: {self.passport_input.text()}", ln=True, border=1)
            pdf.cell(200, 6, f"Телефон: {self.phone_input.text()}", ln=True, border=1)
            pdf.cell(200, 6, f"Тип страхования: {self.insurance_type.currentText()}", ln=True, border=1)
            pdf.cell(200, 6, f"Срок страхования: {self.duration.value()} мес.", ln=True, border=1)
            pdf.cell(200, 6, f"Страховая сумма: {self.amount.value()} ₽", ln=True, border=1)

            pdf.ln(10)
            pdf.cell(200, 6, "Общие условия:", ln=True, align='C', fill=True)
            pdf.multi_cell(0, 6, "1. Данный договор регламентирует страховые условия согласно законодательству.\n"
                                 "2. Клиент обязан соблюдать все условия, указанные в договоре.\n"
                                 "3. Страховая выплата производится согласно правилам страхования.")

            pdf.ln(50)
            pdf.cell(200, 6, "_________________    __________________", ln=True, align='C')
            pdf.cell(200, 6, "     Подпись клиента        Подпись компании", ln=True, align='C')
            pdf.ln(10)
            pdf.cell(200, 6, f"Дата создания: {QDate.currentDate().toString('dd.MM.yyyy')}", ln=True,
                     align='C')  # Дата создания документа
            pdf.image("stamp.png", x=100, y=120, w=40)
            pdf.output(filename, 'F')
            self.progress.setValue(100)

            # Сохраняем данные договора в историю, включая дату создания
            contract_data = {
                'fio': self.fio_input.text(),
                'birth_date': self.birth_date.date().toString('dd.MM.yyyy'),
                'passport': self.passport_input.text(),
                'phone': self.phone_input.text(),
                'insurance_type': self.insurance_type.currentText(),
                'duration': self.duration.value(),
                'amount': self.amount.value(),
                'creation_date': QDate.currentDate().toString('dd.MM.yyyy')  # Добавляем дату создания
            }
            self.contracts.append(contract_data)
            self.save_contracts()
            self.update_contracts_list()



    def print_contract(self):
        printer = QPrinter()
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() == QDialog.DialogCode.Accepted:
            self.save_contract()  # Сначала сохраняем договор, потом отправляем его на печать

    def clear_form(self):
        self.fio_input.clear()
        self.passport_input.clear()
        self.phone_input.clear()
        self.insurance_type.setCurrentIndex(0)
        self.duration.setValue(1)
        self.amount.setValue(10000)

    def validate_inputs(self):
        if not self.fio_input.text() or not self.passport_input.text() or not self.phone_input.text():
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля!")
            return False
        return True

    def show_password_dialog(self):
        dialog = PasswordDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            password = dialog.get_password()
            try:
                decrypted_password = decrypt_password()
                if password == decrypted_password:
                    self.load_selected_contract()
                else:
                    QMessageBox.warning(self, "Ошибка", "Неверный пароль!")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", "Не удалось расшифровать пароль!")

    def load_selected_contract(self):
        selected_row = self.contract_list.currentRow()
        if selected_row >= 0:
            contract = self.contracts[selected_row]
            self.fio_input.setText(contract['fio'])
            self.passport_input.setText(contract['passport'])
            self.phone_input.setText(contract['phone'])
            self.insurance_type.setCurrentText(contract['insurance_type'])
            self.duration.setValue(contract['duration'])
            self.amount.setValue(contract['amount'])
            birth_date = QDate.fromString(contract['birth_date'], 'dd.MM.yyyy')
            self.birth_date.setDate(birth_date)

    def load_contracts(self):
        try:
            with open('contracts_history.json', 'r') as file:
                contracts = json.load(file)
                # Добавляем дату создания для старых записей, если она отсутствует
                for contract in contracts:
                    if 'creation_date' not in contract:
                        contract['creation_date'] = QDate.currentDate().toString('dd.MM.yyyy')
                return contracts
        except FileNotFoundError:
            return []

    def save_contracts(self):
        with open('contracts_history.json', 'w') as file:
            json.dump(self.contracts, file)

    def update_contracts_list(self):
        self.contract_list.clear()
        for contract in self.contracts:
            contract_info = f"{contract['fio']} - {contract['insurance_type']} - {contract['creation_date']}"
            self.contract_list.addItem(contract_info)

    def search_contracts(self):
        search_text = self.search_input.text().lower()
        filtered_contracts = [contract for contract in self.contracts if search_text in contract['fio'].lower() or search_text in contract['insurance_type'].lower()]
        self.contract_list.clear()
        for contract in filtered_contracts:
            contract_info = f"{contract['fio']} - {contract['insurance_type']} - {contract['creation_date']}"
            self.contract_list.addItem(contract_info)

    def delete_contract(self):
        selected_row = self.contract_list.currentRow()
        if selected_row >= 0:
            confirmation = QMessageBox.question(self, "Удаление договора",
                                                "Вы уверены, что хотите удалить этот договор?",
                                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirmation == QMessageBox.StandardButton.Yes:
                del self.contracts[selected_row]
                self.save_contracts()
                self.update_contracts_list()
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите договор для удаления")

    def sort_by_fio(self):
        self.contracts.sort(key=lambda x: x['fio'].lower())
        self.update_contracts_list()

    def sort_by_type(self):
        self.contracts.sort(key=lambda x: x['insurance_type'].lower())
        self.update_contracts_list()

    def sort_by_date(self):
        self.contracts.sort(key=lambda x: QDate.fromString(x['creation_date'], 'dd.MM.yyyy'))
        self.update_contracts_list()

class PasswordDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Подтверждение менеджера")

        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QFormLayout()
        layout.addRow("Введите пароль:", self.password_input)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def get_password(self):
        return self.password_input.text()

# Функции для шифрования и расшифровки пароля
def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

def load_key():
    return open("secret.key", "rb").read()

def encrypt_password(password):
    key = load_key()
    f = Fernet(key)
    encrypted_password = f.encrypt(password.encode())
    with open("password.enc", "wb") as password_file:
        password_file.write(encrypted_password)

def decrypt_password():
    key = load_key()
    f = Fernet(key)
    with open("password.enc", "rb") as password_file:
        encrypted_password = password_file.read()
    return f.decrypt(encrypted_password).decode()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InsuranceApp()
    window.show()
    sys.exit(app.exec())
