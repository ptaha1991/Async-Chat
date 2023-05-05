import json
import logging
import sys
from socket import socket, AF_INET, SOCK_STREAM

from utils import get_message, process_client_message, send_message
import log.server_log_config

server_logger = logging.getLogger('server')


def main():
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = 7777
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        server_logger.critical(f'Неподходящий порт {listen_port}. В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)
    except ValueError:
        server_logger.critical(
            'ValueError. В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)


    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''

    except IndexError:
        server_logger.error('После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
        sys.exit(1)

    s = socket(AF_INET, SOCK_STREAM)
    s.bind((listen_address, listen_port))
    s.listen(5)

    while True:
        client, client_address = s.accept()
        server_logger.info(f'Установлено соедение с ПК {client_address}')
        try:
            message_from_client = get_message(client)
            server_logger.info(f'Получено сообщение {message_from_client}')
            response = process_client_message(message_from_client)
            send_message(client, response)
            client.close()
        except (ValueError, json.JSONDecodeError):
            server_logger.error('Принято некорретное сообщение от клиента.')
            client.close()


if __name__ == '__main__':
    main()
