# 2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
# Меняться должен только последний октет каждого адреса.
# По результатам проверки должно выводиться соответствующее сообщение.
from ipaddress import ip_address

from les9.task1 import host_ping


def find_last_oct(ip):
    return int(ip.split('.')[3])


def host_range_ping():
    while True:
        start_ip = input('Введите начальный адрес: ')
        try:
            last_oct_start_ip = find_last_oct(start_ip)
            break
        except Exception as e:
            print(e)
    while True:
        end_ip = input('Введите конечный адрес: ')
        try:
            last_oct_end_ip = find_last_oct(end_ip)
            break
        except Exception as e:
            print(e)

    result_list = []
    for x in range(last_oct_end_ip - last_oct_start_ip + 1):
        result_list.append(str(ip_address(start_ip) + x))

    return host_ping(result_list)


if __name__ == "__main__":
    host_range_ping()
