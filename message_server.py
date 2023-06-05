import configparser
import logging
import os
import sys
import threading
from argparse import ArgumentParser
from select import select
from socket import socket, AF_INET, SOCK_STREAM

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from decorator import logs
from descriptor import WrongPort, WrongAddress
from metaclasses import ServerVerifier
from server_database import ServerDatabase
from server_gui import MainWindow, gui_create_model, ConfigWindow, HistoryWindow, create_stat_model, AllClientsWindow, \
    create_all_users_model
from utils import get_message, send_message
import log.server_log_config

server_logger = logging.getLogger('server')

new_connection = False
conflag_lock = threading.Lock()


@logs
def arg_parser(default_port):
    parser = ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    return listen_address, listen_port


class Server(threading.Thread, metaclass=ServerVerifier):
    port = WrongPort()
    address = WrongAddress()

    def __init__(self, listen_address, listen_port, database):
        self.address = listen_address
        self.port = listen_port
        self.clients_list = []
        self.messages_list = []
        self.names = dict()
        self.database = database

        super().__init__()

    def init_socket(self):
        server_logger.info(
            f'Запущен сервер, порт для подключений: {self.port}, '
            f'адрес с которого принимаются подключения: {self.address}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')
        s = socket(AF_INET, SOCK_STREAM)
        s.bind((self.address, self.port))
        s.settimeout(0.5)
        self.s = s
        s.listen(5)

    def run(self):
        self.init_socket()

        while True:
            try:
                client, client_address = self.s.accept()
            except OSError as e:
                pass
            else:
                server_logger.info(f'Установлено соедение с ПК {client_address}')
                self.clients_list.append(client)

            r = []
            w = []
            try:
                if self.clients_list:
                    r, w, e = select(self.clients_list, self.clients_list, [], 1)
            except OSError:
                pass

            if r:
                for client_with_message in r:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except:
                        server_logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.client_logout(name)
                                del self.names[name]
                                break
                        self.clients_list.remove(client_with_message)

            for i in self.messages_list:
                try:
                    self.message_to_client(i, w)
                except:
                    server_logger.info(f'Связь с клиентом с именем {i["destination"]} была потеряна')
                    self.clients_list.remove(self.names[i['destination']])
                    self.database.client_logout(i['destination'])
                    del self.names[i['destination']]
            self.messages_list.clear()

    def process_client_message(self, msg, client):
        global new_connection
        server_logger.debug(f'Разбор сообщения от клиента : {msg}')
        if 'action' in msg and msg['action'] == 'presence' and 'time' in msg and \
                'user' in msg:
            if msg['user']['account_name'] not in self.names.keys():
                self.names[msg['user']['account_name']] = client
                client_ip, client_port = client.getpeername()
                self.database.client_login(msg['user']['account_name'], client_ip)
                send_message(client, {'response': 200})
                with conflag_lock:
                    new_connection = True
            else:
                send_message(client, {'response': 400, 'error': 'Имя пользователя уже занято.'})
                self.clients_list.remove(client)
                client.close()
            return

        elif 'action' in msg and msg['action'] == 'message' and 'time' in msg and 'sender' in msg and \
                'destination' in msg and 'message_text' in msg:
            self.messages_list.append(msg)
            return
        elif 'action' in msg and msg['action'] == 'exit' and 'user' in msg and self.names[msg['user']] == client:
            self.database.client_logout(msg['user'])
            self.clients_list.remove(self.names[msg['user']])
            self.names[msg['user']].close()
            del self.names[msg['user']]
            return

        elif 'action' in msg and msg['action'] == 'get_contacts' and 'user' in msg and self.names[
            msg['user']] == client:
            response = {'response': 202, 'alert': self.database.get_contacts(msg['user'])}
            send_message(client, response)

        elif 'action' in msg and msg['action'] == 'add_contact' and 'contact' in msg and 'user' in msg \
                and self.names[msg['user']] == client:
            self.database.add_contact_to_client(msg['user'], msg['contact'])
            send_message(client, {'response': 200})

        elif 'action' in msg and msg['action'] == 'delete_contact' and 'contact' in msg and 'user' in msg \
                and self.names[msg['user']] == client:
            self.database.delete_contact_from_client(msg['user'], msg['contact'])
            send_message(client, {'response': 200})

        elif 'action' in msg and msg['action'] == 'clients_request' and 'user' in msg \
                and self.names[msg['user']] == client:
            response = {'response': 202, 'alert': [user[0] for user in self.database.get_clients_list()]}
            send_message(client, response)

        else:
            send_message(client, {'response': 400, 'error': 'Bad Request'})
            return

    def message_to_client(self, msg, listen_socks):
        if msg['destination'] in self.names and self.names[msg['destination']] in listen_socks:
            send_message(self.names[msg['destination']], msg)
            server_logger.info(
                f'Отправлено сообщение пользователю {msg["destination"]} от пользователя {msg["sender"]}.')
        else:
            server_logger.error(f'Отправка сообщения невозможна.')


def main():
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    listen_address, listen_port = arg_parser(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    database = ServerDatabase(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    # Создаём графическое окуружение для сервера:
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Инициализируем параметры в окна
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    # Функция создающяя окно со списком всех клиентов
    def show_all_clients():
        global all_clients
        all_clients = AllClientsWindow()
        all_clients.all_clients_table.setModel(create_all_users_model(database))
        all_clients.all_clients_table.resizeColumnsToContents()
        all_clients.all_clients_table.resizeRowsToContents()
        all_clients.show()

    # Функция обновляющяя список подключённых, проверяет флаг подключения, и если надо обновляет список
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # Функция создающяя окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.all_clients_button.triggered.connect(show_all_clients)
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()


if __name__ == '__main__':
    main()
