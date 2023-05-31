import logging
import sys
import threading
import time
from argparse import ArgumentParser
from socket import AF_INET, SOCK_STREAM, socket

from client_database import ClientDatabase
from metaclasses import ClientVerifier
from utils import create_presence, send_message, process_ans, get_message, clients_list_request, contacts_list_request, \
    add_contact, delete_contact
import log.client_log_config

client_logger = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


def args_parser():
    default_address = '127.0.0.1'
    default_port = 7777
    parser = ArgumentParser()
    parser.add_argument('address', default=default_address, nargs='?')
    parser.add_argument('port', default=default_port, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.address
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < namespace.port < 65536:
        client_logger.critical(f'Порт "{server_port}" введен некорректно. '
                               f'Необходимо ввести значение от 1024 до 65535.')
        sys.exit(1)

    return server_address, server_port, client_name


class ClientReader(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, s, database):
        super().__init__()
        self.daemon = True
        self.account_name = account_name
        self.s = s
        self.database = database

    def run(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    msg = get_message(self.s)
                except OSError as err:
                    if err.errno:
                        client_logger.critical(f'Потеряно соединение с сервером.')
                        break
                except Exception as e:
                    print(e)
                    client_logger.critical(f'Потеряно соединение с сервером.')
                    break
                else:
                    if 'action' in msg and msg['action'] == 'message' and 'time' in msg and 'sender' in msg \
                            and 'destination' in msg and 'message_text' in msg \
                            and msg['destination'] == self.account_name:
                        print(f'Получено сообщение от пользователя {msg["sender"]}: {msg["message_text"]}')
                        with database_lock:
                            try:
                                self.database.save_message(msg["sender"], self.account_name, msg["message_text"])
                            except:
                                client_logger.error('Ошибка взаимодействия с базой данных')
                        client_logger.info(f'Получено сообщение от пользователя {msg["sender"]}: {msg["message_text"]}')
                    else:
                        client_logger.error(f'Получено некорректное сообщение с сервера: {msg}')


class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, s, database):
        super().__init__()
        self.daemon = True
        self.account_name = account_name
        self.s = s
        self.database = database

    def run(self):
        print('Отправить сообщение (send), История сообщений (history), Мои Контакты (contacts), '
              'Редактировать контакт (edit), выйти (exit)')
        while True:
            command = input('Введите команду: ')
            if command == 'send':
                with sock_lock:
                    try:
                        send_message(self.s, self.create_message())
                        client_logger.info(f'Сообщение  от пользователя {self.account_name} успешно отправлено')

                    except:
                        client_logger.critical('Потеряно соединение с сервером.')
                        sys.exit(1)

            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            elif command == 'edit':
                self.edit_contacts()

            elif command == 'history':
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от '
                          f'{message[3]}\n{message[2]}')

            elif command == 'exit':
                with sock_lock:
                    send_message(self.s, self.create_exit_message())
                    print('Завершение соединения.')
                time.sleep(1)
                break
            else:
                print('Что то пошло не так, попробуйте еще раз!')

    def create_exit_message(self):
        exit_msg = {
            'action': 'exit',
            'time': time.time(),
            'user': self.account_name
        }
        return exit_msg

    def create_message(self):
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение: ')

        with database_lock:
            if not self.database.check_user(to_user):
                client_logger.error(f'Попытка отправить сообщение незарегистрированому получателю: {to_user}')
                return

        dict_message = {
            'action': 'message',
            'time': time.time(),
            'sender': self.account_name,
            'destination': to_user,
            'message_text': message
        }

        with database_lock:
            self.database.save_message(self.account_name, to_user, message)

        return dict_message

    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемого контакта: ')
            if self.database.check_contact(edit):
                with database_lock:
                    self.database.del_contact(edit)
                with sock_lock:
                    try:
                        delete_contact(self.s, self.account_name, edit)
                    except:
                        client_logger.error('Не удалось отправить информацию на сервер.')

            else:
                client_logger.error('Попытка удаления несуществующего контакта.')

        elif ans == 'add':
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.s, self.account_name, edit)
                    except:
                        client_logger.error('Не удалось отправить информацию на сервер.')


def database_load(sock, database, username):
    try:
        users_list = clients_list_request(sock, username)
    except:
        client_logger.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except:
        client_logger.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    server_address, server_port, client_name = args_parser()
    if not client_name:
        client_name = input('Введите свое имя: ')

    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(1)
        s.connect((server_address, server_port))
        msg = create_presence(client_name)
        send_message(s, msg)
        answer = process_ans(get_message(s))
        client_logger.info(f'Принят ответ от сервера {answer}')
    except ConnectionRefusedError:
        client_logger.error('Неудачная попытка подключения к серверу!')
        sys.exit(1)

    # 2 потока на прием и отправку сообщений
    database = ClientDatabase(client_name)
    database_load(s, database, client_name)

    reader = ClientReader(client_name, s, database)
    reader.start()

    sender = ClientSender(client_name, s, database)
    sender.start()

    while True:
        time.sleep(1)
        if reader.is_alive() and sender.is_alive():
            continue
        break


if __name__ == '__main__':
    main()
