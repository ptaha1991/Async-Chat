import logging
import sys

server_logger = logging.getLogger('server')


class WrongPort:
    def __set__(self, instance, listen_port):
        if not 1023 < listen_port < 65536:
            server_logger.critical(
                f'Попытка запуска сервера с указанием неподходящего порта '
                f'{listen_port}. Допустимы адреса с 1024 до 65535.')
            sys.exit(1)
        instance.__dict__[self.my_attr] = listen_port

    def __set_name__(self, owner, my_attr):
        self.my_attr = my_attr
