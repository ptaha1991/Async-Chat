import dis


class ServerVerifier(type):
    """
    Метакласс проверяющий, что в результирующем классе нет клиентских
    вызовов таких как: connect. Также проверяется, что серверный
    сокет является TCP и работает по IPv4 протоколу.
    """

    def __init__(self, clsname, bases, clsdict):
        # clsname - экземпляр метакласса - Server
        # bases - кортеж базовых классов - ()
        # clsdict - словарь атрибутов и методов экземпляра метакласса
        methods = []
        for func in clsdict:
            try:
                # Возвращает итератор по инструкциям в предоставленной функции
                ret = dis.get_instructions(clsdict[func])
                # Если не функция, то ловим исключение (если порт)
            except TypeError:
                pass
            else:
                for i in ret:
                    # i - Instruction(opname='LOAD_GLOBAL', opcode=116,
                    # arg=9, argval='send_message',
                    # argrepr='send_message', offset=308,
                    # starts_line=201, is_jump_target=False)
                    # opname - имя для операции
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо '
                            'в серверном классе')
        if not ('SOCK_STREAM' in methods and 'AF_INET' in methods):
            raise TypeError('Некорректная инициализация сокета.')

        super().__init__(clsname, bases, clsdict)


class ClientVerifier(type):
    """
    Метакласс проверяющий, что в результирующем классе нет серверных
    вызовов таких как: accept, listen. Также проверяется, что сокет не
    создаётся внутри конструктора класса.
    """

    def __init__(self, clsname, bases, clsdict):
        methods = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)

        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError(f'Использование {command} '
                                f'недопустимо в клиентском классе')

        # Вызов get_message или send_message из utils
        # считаем корректным использованием сокетов
        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError(
                'Отсутствуют вызовы функций, работающих с сокетами.')

        super().__init__(clsname, bases, clsdict)
