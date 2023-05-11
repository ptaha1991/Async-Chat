import logging
import sys
import time
from argparse import ArgumentParser
from select import select
from socket import socket, AF_INET, SOCK_STREAM

from decorator import logs
from utils import get_message, process_client_message, send_message
import log.server_log_config

server_logger = logging.getLogger('server')


@logs
def arg_parser():
    default_port = 7776
    parser = ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    if not 1023 < listen_port < 65536:
        server_logger.critical(
            f'Попытка запуска сервера с указанием неподходящего порта '
            f'{listen_port}. Допустимы адреса с 1024 до 65535.')
        sys.exit(1)

    return listen_address, listen_port


def main():
    listen_address, listen_port = arg_parser()

    server_logger.info(
        f'Запущен сервер, порт для подключений: {listen_port}, '
        f'адрес с которого принимаются подключения: {listen_address}. '
        f'Если адрес не указан, принимаются соединения с любых адресов.')
    clients_list = []
    messages_list = []

    s = socket(AF_INET, SOCK_STREAM)
    s.bind((listen_address, listen_port))
    s.settimeout(0.5)
    s.listen(5)

    while True:
        try:
            client, client_address = s.accept()
        except OSError as e:
            pass
        else:
            server_logger.info(f'Установлено соедение с ПК {client_address}')
            clients_list.append(client)

        r = []
        w = []
        try:
            if clients_list:
                r, w, e = select(clients_list, clients_list, [], 1)
        except OSError:
            pass

        if r:
            for client_with_message in r:
                try:
                    process_client_message(get_message(client_with_message),
                                           messages_list, client_with_message)
                except:
                    server_logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                    clients_list.remove(client_with_message)

        if messages_list and w:
            print(messages_list)
            message = {
                'action': 'message',
                'time': time.time(),
                'sender': messages_list[0][0],
                'message_text': messages_list[0][1]
            }
            del messages_list[0]
            for waiting_client in w:
                try:
                    send_message(waiting_client, message)
                except:
                    server_logger.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                    clients_list.remove(waiting_client)


if __name__ == '__main__':
    main()
