import logging
import sys
import threading
import time
from argparse import ArgumentParser
from socket import AF_INET, SOCK_STREAM, socket

from metaclasses import ClientVerifier
from utils import create_presence, send_message, process_ans, get_message
import log.client_log_config

client_logger = logging.getLogger('client')


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
    def __init__(self, account_name, s):
        super().__init__()
        self.daemon = True
        self.account_name = account_name
        self.s = s

    def run(self):
        while True:
            try:
                msg = get_message(self.s)
                if 'action' in msg and msg['action'] == 'message' and 'time' in msg and 'sender' in msg \
                        and 'destination' in msg and 'message_text' in msg \
                        and msg['destination'] == self.account_name:
                    print(f'Получено сообщение от пользователя {msg["sender"]}: {msg["message_text"]}')
                    client_logger.info(f'Получено сообщение от пользователя {msg["sender"]}: {msg["message_text"]}')
                else:
                    client_logger.error(f'Получено некорректное сообщение с сервера: {msg}')
            except:
                client_logger.critical(f'Потеряно соединение с сервером.')
                break


class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, s):
        super().__init__()
        self.daemon = True
        self.account_name = account_name
        self.s = s

    def run(self):
        print('Отправить сообщение (send), выйти (exit)')
        while True:
            command = input('Введите команду: ')
            if command == 'send':
                try:
                    send_message(self.s, self.create_message())
                    client_logger.info(f'Сообщение  от пользователя {self.account_name} успешно отправлено')
                except:
                    client_logger.critical('Потеряно соединение с сервером.')
                    sys.exit(1)

            elif command == 'exit':
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
        dict_message = {
            'action': 'message',
            'time': time.time(),
            'sender': self.account_name,
            'destination': to_user,
            'message_text': message
        }
        return dict_message


def main():
    server_address, server_port, client_name = args_parser()
    if not client_name:
        client_name = input('Введите свое имя: ')

    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((server_address, server_port))
        msg = create_presence(client_name)
        send_message(s, msg)
        answer = process_ans(get_message(s))
        client_logger.info(f'Принят ответ от сервера {answer}')
    except ConnectionRefusedError:
        client_logger.error('Неудачная попытка подключения к серверу!')
        sys.exit(1)

    # 2 потока на прием и отправку сообщений
    reader = ClientReader(client_name, s)
    reader.start()

    sender = ClientSender(client_name, s)
    sender.start()

    while True:
        time.sleep(1)
        if reader.is_alive() and sender.is_alive():
            continue
        break


if __name__ == '__main__':
    main()
