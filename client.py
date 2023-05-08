import json
import logging
import sys
from socket import AF_INET, SOCK_STREAM, socket

from utils import create_presence, send_message, process_ans, get_message
import log.client_log_config

client_logger = logging.getLogger('client')


def main():
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        print((server_address, server_port))
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        server_address = '127.0.0.1'
        server_port = 7777
    except ValueError:
        client_logger.critical('Порт может быть в диапазоне от 1024 до 65535.')
        sys.exit(1)

    s = socket(AF_INET, SOCK_STREAM)
    s.connect((server_address, server_port))
    msg = create_presence()
    send_message(s, msg)

    try:
        answer = process_ans(get_message(s))
        client_logger.info(f'Принят ответ от сервера {answer}')
    except (ValueError, json.JSONDecodeError):
        client_logger.error('Не удалось декодировать сообщение сервера.')


if __name__ == '__main__':
    main()
