# 2. Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования в последовательность кодов
# (не используя методы encode и decode) и определить тип, содержимое и длину соответствующих переменных.

var_list = [b"class", b"function", b"method"]

for el in var_list:
    print(type(el), el, len(el), sep='-->')

