# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'client_module.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainClientWindow(object):
    def setupUi(self, MainClientWindow):
        MainClientWindow.setObjectName("MainClientWindow")
        MainClientWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainClientWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label_message_history = QtWidgets.QLabel(self.centralwidget)
        self.label_message_history.setGeometry(QtCore.QRect(10, 10, 401, 21))
        self.label_message_history.setFrameShape(QtWidgets.QFrame.Box)
        self.label_message_history.setObjectName("label_message_history")
        self.label_contacts = QtWidgets.QLabel(self.centralwidget)
        self.label_contacts.setGeometry(QtCore.QRect(430, 10, 171, 21))
        self.label_contacts.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.label_contacts.setAlignment(QtCore.Qt.AlignCenter)
        self.label_contacts.setObjectName("label_contacts")
        self.btn_delete_contact = QtWidgets.QPushButton(self.centralwidget)
        self.btn_delete_contact.setGeometry(QtCore.QRect(430, 400, 171, 31))
        self.btn_delete_contact.setObjectName("btn_delete_contact")
        self.btn_add_contact = QtWidgets.QPushButton(self.centralwidget)
        self.btn_add_contact.setGeometry(QtCore.QRect(620, 400, 171, 31))
        self.btn_add_contact.setObjectName("btn_add_contact")
        self.btn_send_message = QtWidgets.QPushButton(self.centralwidget)
        self.btn_send_message.setGeometry(QtCore.QRect(130, 520, 131, 31))
        self.btn_send_message.setObjectName("btn_send_message")
        self.list_message_history = QtWidgets.QListView(self.centralwidget)
        self.list_message_history.setGeometry(QtCore.QRect(10, 40, 401, 351))
        self.list_message_history.setObjectName("list_message_history")
        self.list_contacts = QtWidgets.QListView(self.centralwidget)
        self.list_contacts.setGeometry(QtCore.QRect(430, 40, 171, 351))
        self.list_contacts.setObjectName("list_contacts")
        self.text_message = QtWidgets.QTextEdit(self.centralwidget)
        self.text_message.setGeometry(QtCore.QRect(10, 433, 401, 71))
        self.text_message.setObjectName("text_message")
        self.label_known_clients = QtWidgets.QLabel(self.centralwidget)
        self.label_known_clients.setGeometry(QtCore.QRect(620, 10, 171, 21))
        self.label_known_clients.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.label_known_clients.setAlignment(QtCore.Qt.AlignCenter)
        self.label_known_clients.setObjectName("label_known_clients")
        self.label_new_message = QtWidgets.QLabel(self.centralwidget)
        self.label_new_message.setGeometry(QtCore.QRect(10, 400, 401, 21))
        self.label_new_message.setFrameShape(QtWidgets.QFrame.Box)
        self.label_new_message.setTextFormat(QtCore.Qt.AutoText)
        self.label_new_message.setObjectName("label_new_message")
        self.list_known_clients = QtWidgets.QListView(self.centralwidget)
        self.list_known_clients.setGeometry(QtCore.QRect(620, 40, 171, 351))
        self.list_known_clients.setObjectName("list_known_clients")
        MainClientWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainClientWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        MainClientWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainClientWindow)
        self.statusbar.setObjectName("statusbar")
        MainClientWindow.setStatusBar(self.statusbar)
        self.menubar.addAction(self.menu.menuAction())

        self.retranslateUi(MainClientWindow)
        QtCore.QMetaObject.connectSlotsByName(MainClientWindow)

    def retranslateUi(self, MainClientWindow):
        _translate = QtCore.QCoreApplication.translate
        MainClientWindow.setWindowTitle(_translate("MainClientWindow", "Чат Клиента"))
        self.label_message_history.setText(_translate("MainClientWindow", "История сообщений"))
        self.label_contacts.setText(_translate("MainClientWindow", "Мои Контакты"))
        self.btn_delete_contact.setText(_translate("MainClientWindow", "Удалить контакт"))
        self.btn_add_contact.setText(_translate("MainClientWindow", "Добавить контакт"))
        self.btn_send_message.setText(_translate("MainClientWindow", "Отправить"))
        self.label_known_clients.setText(_translate("MainClientWindow", "Возможные контакты"))
        self.label_new_message.setText(_translate("MainClientWindow", "Введите сообщение"))
        self.menu.setTitle(_translate("MainClientWindow", "Выйти"))
