Common package
=================================================

Пакет общих утилит, использующихся в разных модулях проекта.

Скрипт decorators.py
---------------

.. automodule:: common.decorators
    :members:

Скрипт descriptors.py
---------------------

.. autoclass:: common.descriptors.WrongPort
    :members:

.. autoclass:: common.descriptors.WrongAddress
    :members:


Скрипт metaclasses.py
-----------------------

.. autoclass:: common.metaclasses.ServerVerifier
   :members:

.. autoclass:: common.metaclasses.ClientVerifier
   :members:

Скрипт utils.py
---------------------

common.utils. **get_message** (client)


    Функция приёма сообщений от удалённых компьютеров. Принимает сообщения JSON,
    декодирует полученное сообщение и проверяет что получен словарь.

common.utils. **send_message** (sock, message)


    Функция отправки словарей через сокет. Кодирует словарь в формат JSON и отправляет через сокет.
