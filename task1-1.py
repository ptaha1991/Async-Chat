# 1. Каждое из слов «разработка», «сокет», «декоратор» представить в строковом формате
# и проверить тип и содержание соответствующих переменных.
# Затем с помощью онлайн-конвертера преобразовать строковые представление в формат Unicode
# и также проверить тип и содержимое переменных.

def get_type_and_print(var_list):
    for el in var_list:
        print(type(el))
        print(el)


var_list1 = ["разработка", "сокет", "декоратор"]
get_type_and_print(var_list1)
var_list2 = ["\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430", "\u0441\u043e\u043a\u0435\u0442",
             "\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440"]
get_type_and_print(var_list2)
