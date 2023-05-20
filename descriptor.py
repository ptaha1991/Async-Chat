import logging
import sys
from ipaddress import ip_address

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


class WrongAddress:
    def __set__(self, instance, listen_address):
        if not listen_address:
            pass
        else:
            try:
                ip_address(listen_address)
            # except ValueError:
            #     pass
            except Exception as e:
                print(e)
                server_logger.critical(
                    f'Попытка запуска сервера с указанием неподходящего адреса {listen_address}.')
                sys.exit(1)
        instance.__dict__[self.my_attr] = listen_address

    def __set_name__(self, owner, my_attr):
        self.my_attr = my_attr
