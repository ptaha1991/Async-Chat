# Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
# Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
# В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения
# («Узел доступен», «Узел недоступен»).
# При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
import socket
from ipaddress import ip_address
from subprocess import Popen, PIPE


def host_ping(list_addresses):
    result_dict = {'Reachable': '', 'Unreachable': ''}
    for address in list_addresses:
        try:
            ip_address(address)
        except ValueError:
            pass
        except Exception as e:
            print(e)
            break
        proc = Popen(['ping', '-c', '2', address], stdout=PIPE)
        proc.wait()
        if proc.returncode == 0:
            print(f'Узел доступен: {address}')
            result_dict['Reachable'] += f"{address}\n"
        else:
            print(f'Узел недоступен: {address}')
            result_dict['Unreachable'] += f"{address}\n"
    return result_dict


if __name__ == '__main__':
    ip_addresses = ['yandex.ru', '2.2.2.2', 'google.com', '192.168.178.63']
    host_ping(ip_addresses)
