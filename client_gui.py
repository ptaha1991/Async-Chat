from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, qApp, QMainWindow, QMessageBox

from main_client_window_ui import Ui_MainClientWindow


class ClientMainWindow(QMainWindow):
    def __init__(self, database, transport):
        super().__init__()
        self.database = database
        self.transport = transport

        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        # Кнопки
        self.ui.menu.triggered.connect(qApp.exit)
        self.ui.btn_send_message.clicked.connect(self.send_message)
        self.ui.btn_add_contact.clicked.connect(self.add_contact_action)
        self.ui.btn_delete_contact.clicked.connect(self.delete_contact_action)

        # Атрибуты
        self.contacts_model = None
        self.new_contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_contact = None
        self.new_current_contact = None
        self.ui.list_message_history.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_message_history.setWordWrap(True)

        self.ui.list_contacts.doubleClicked.connect(self.select_contact)
        self.ui.list_known_clients.doubleClicked.connect(self.select_new_contact)

        self.contacts_list_update()
        self.new_contacts_list_update()
        self.set_disabled_input()
        self.show()

    def set_disabled_input(self):
        self.ui.label_new_message.setText('Дважды кликните на контакте.')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        self.ui.btn_send_message.setDisabled(True)
        self.ui.text_message.setDisabled(True)
        self.ui.btn_add_contact.setDisabled(True)
        self.ui.btn_delete_contact.setDisabled(True)

    def history_list_update(self):
        list_history = sorted(self.database.get_history(self.current_contact), key=lambda item: item[3])
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_message_history.setModel(self.history_model)
        self.history_model.clear()
        length = len(list_history)
        start_index = 0
        if length > 20:
            start_index = length - 20
        # Заполнение модели записями, так-же стоит разделить входящие и исходящие выравниванием и разным фоном.
        # Записи в обратном порядке, поэтому выбираем их с конца и не более 20
        for i in range(start_index, length):
            item = list_history[i]
            if item[1] == 'in':
                mess = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Исходящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_message_history.scrollToBottom()

    def select_contact(self):
        self.current_contact = self.ui.list_contacts.currentIndex().data()
        self.set_contact()

    def set_contact(self):
        self.ui.label_new_message.setText(f'Введите сообщенние для {self.current_contact}:')
        self.ui.btn_send_message.setDisabled(False)
        self.ui.text_message.setDisabled(False)
        self.history_list_update()
        self.ui.btn_delete_contact.setDisabled(False)

    def select_new_contact(self):
        self.new_current_contact = self.ui.list_known_clients.currentIndex().data()
        self.ui.btn_add_contact.setDisabled(False)

    def contacts_list_update(self):
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    def new_contacts_list_update(self):
        contacts_list = set(self.database.get_contacts())
        new_contacts_list = set(self.database.get_clients())
        new_contacts_list.remove(self.transport.account_name)
        new_contacts_list -= contacts_list
        self.new_contacts_model = QStandardItemModel()
        for i in sorted(new_contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.new_contacts_model.appendRow(item)
        self.ui.list_known_clients.setModel(self.new_contacts_model)

    def add_contact_action(self):
        try:
            self.transport.add_contact(self.new_current_contact)
        except Exception as err:
            self.messages.critical(self, 'Ошибка сервера', str(err))
        else:
            self.database.add_contact(self.new_current_contact)
            new_contact = QStandardItem(self.new_current_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            self.new_contacts_list_update()
            self.messages.information(self, 'Успех', 'Контакт успешно добавлен.')
            self.new_current_contact = None
            self.ui.btn_add_contact.setDisabled(True)

    def delete_contact_action(self):
        try:
            self.transport.delete_contact(self.current_contact)
        except Exception as err:
            self.messages.critical(self, 'Ошибка сервера', str(err))
        else:
            self.database.del_contact(self.current_contact)
            self.contacts_list_update()
            self.new_contacts_list_update()
            self.messages.information(self, 'Успех', 'Контакт успешно удалён.')
            self.current_contact = None
            self.set_disabled_input()

    def send_message(self):
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return
        try:
            self.transport.send_message_to_server(self.current_contact, message_text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.database.save_message(self.current_contact, 'out', message_text)
            self.history_list_update()
        else:
            self.database.save_message(self.current_contact, 'out', message_text)
            self.history_list_update()

    @pyqtSlot(str)
    def message(self, sender):
        if sender == self.current_contact:
            self.history_list_update()
        else:
            if self.database.check_contact(sender):
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}, открыть чат с ним?',
                                          QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    self.current_contact = sender
                    self.set_contact()
            else:
                if self.messages.question(self, 'Новое сообщение',
                                          f'Получено новое сообщение от {sender}.\n '
                                          f'Данного пользователя нет в вашем контакт-листе.\n '
                                          f'Добавить в контакты и открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.new_current_contact = sender
                    self.add_contact_action()
                    self.current_contact = sender
                    self.set_contact()

    # Слот потери соединения
    # Выдаёт сообщение о ошибке и завершает работу приложения
    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с сервером. ')
        self.close()

    def make_connection(self, trans_obj):
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)


class UserNameDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle('Выбор имени')
        self.setFixedSize(175, 93)

        self.label = QLabel('Введите имя:', self)
        self.label.move(10, 10)
        self.label.setFixedSize(150, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.btn_ok = QPushButton('Начать', self)
        self.btn_ok.move(10, 60)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Выход', self)
        self.btn_cancel.move(90, 60)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    def click(self):
        if self.client_name.text():
            self.ok_pressed = True
            qApp.exit()
