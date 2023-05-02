# 3. Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в байтовом типе.

var_list = ["attribute", "класс", "функция", "type"]

for el in var_list:
    try:
        print(bytes(el, 'ascii'))
    except UnicodeEncodeError:
        print(f"Слово '{el}' невозможно записать в байтовом типе")
