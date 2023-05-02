# Задание на закрепление знаний по модулю json.
# Есть файл orders в формате JSON с информацией о заказах. Написать скрипт, автоматизирующий его заполнение данными.
# Для этого:

# a) Создать функцию write_order_to_json(), в которую передается 5 параметров — товар (item), количество (quantity),
# цена (price), покупатель (buyer), дата (date). Функция должна предусматривать запись данных в виде словаря в файл
# orders.json. При записи данных указать величину отступа в 4 пробельных символа;

# b)Проверить работу программы через вызов функции write_order_to_json() с передачей в нее значений каждого параметра.

import json


def write_order_to_json(item, quantity, price, buyer, date):

    with open('orders.json', 'r', encoding='utf-8') as f_r:
        data = json.load(f_r)

    with open('orders.json', 'w', encoding='utf-8', ) as f_w:
        data['orders'].append({'item': item, 'quantity': quantity, 'price': price, 'buyer': buyer, 'date': date})
        json.dump(data, f_w, indent=4, ensure_ascii=False)


write_order_to_json('Телефон', '11', '345', 'Иванов', '12.12.2012')
write_order_to_json('Айпад', '14', '500', 'Уткин', '15.09.2023')

