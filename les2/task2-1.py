#  Задание на закрепление знаний по модулю CSV.
#  Написать скрипт, осуществляющий выборку определенных данных из файлов info_1.txt, info_2.txt, info_3.txt
#  и формирующий новый «отчетный» файл в формате CSV. Для этого:

# a)Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с данными,
# их открытие и считывание данных. В этой функции из считанных данных необходимо с помощью регулярных выражений
# извлечь значения параметров «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
# Значения каждого параметра поместить в соответствующий список. Должно получиться четыре списка —
# например, os_prod_list, os_name_list, os_code_list, os_type_list.
# В этой же функции создать главный список для хранения данных отчета — например, main_data —
# и поместить в него названия столбцов отчета в виде списка: «Изготовитель системы», «Название ОС», «Код продукта»,
# «Тип системы». Значения для этих столбцов также оформить в виде списка и поместить в файл main_data
# (также для каждого файла);

# b) Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл.
# В этой функции реализовать получение данных через вызов функции get_data(),
# а также сохранение подготовленных данных в соответствующий CSV-файл;
#
# c)Проверить работу программы через вызов функции write_to_csv().

import re
import csv
from chardet.universaldetector import UniversalDetector

DETECTOR = UniversalDetector()

with open('info_1.txt', 'rb') as test:
    for i in test:
        DETECTOR.feed(i)
        if DETECTOR.done:
            break
    DETECTOR.close()


def get_data():
    os_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []
    main_data = [['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы']]

    for i in range(1, 4):
        with open(f'info_{i}.txt', 'r', encoding=DETECTOR.result['encoding']) as file:
            data = file.read()

            os_prod_r = re.compile(r'(Изготовитель системы:.+?)\n')
            os_prod_list.append(os_prod_r.findall(data)[0].split()[2])

            os_name_r = re.compile(r'(Название ОС:.+?)\n')
            os_name_list.append(os_name_r.findall(data)[0].split(None, 2)[2])

            os_code_r = re.compile(r'(Код продукта:.+?)\n')
            os_code_list.append(os_code_r.findall(data)[0].split()[2])

            os_type_r = re.compile(r'(Тип системы:.+?)\n')
            os_type_list.append(os_type_r.findall(data)[0].split()[2])

    for item in range(len(os_prod_list)):
        main_data.append([os_prod_list[item], os_name_list[item], os_code_list[item], os_type_list[item]])

    return main_data


def write_to_csv(file):
    data = get_data()
    with open(file, 'w', encoding='utf-8') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_NONNUMERIC)
        for row in data:
            writer.writerow(row)


write_to_csv('data_report.csv')
