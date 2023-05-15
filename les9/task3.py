# Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2.
# Но в данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном формате
# (использовать модуль tabulate).

from tabulate import tabulate
from les9.task2 import host_range_ping


def host_range_ping_tab():
    result_dict = host_range_ping()
    print(tabulate([result_dict], headers='keys', tablefmt="grid"))


if __name__ == "__main__":
    host_range_ping_tab()
