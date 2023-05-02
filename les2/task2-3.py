# Задание на закрепление знаний по модулю yaml.
# Написать скрипт, автоматизирующий сохранение данных в файле YAML-формата. Для этого:

# a) Подготовить данные для записи в виде словаря, в котором первому ключу соответствует список, второму — целое число,
# третьему — вложенный словарь, где значение каждого ключа — это целое число с юникод-символом,
# отсутствующим в кодировке ASCII (например, €);

# b) Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml.
# При этом обеспечить стилизацию файла с помощью параметра default_flow_style, а также установить возможность работы
# с юникодом: allow_unicode = True;

# c) Реализовать считывание данных из созданного файла и проверить, совпадают ли они с исходными.


import yaml

data = {'items': ['phone', 'ipad'],
        'quantity': 2,
        'price': {'phone': '500€',
                  'ipad': '1000€'}
        }

with open('file.yaml', 'w', encoding='utf-8') as f_w:
    yaml.dump(data, f_w, default_flow_style=False, allow_unicode=True, sort_keys=False)

with open("file.yaml", 'r', encoding='utf-8') as f_r:
    f_r_content = yaml.safe_load(f_r)
    print(f_r_content)
    print(f_r_content == data)
