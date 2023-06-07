from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, \
    create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class ServerDatabase:
    """
    Класс - оболочка для работы с базой данных сервера.
    Использует SQLite базу данных, реализован с помощью
    SQLAlchemy ORM и используется декларативный подход.
    """

    class Clients(Base):
        """Класс - отображение таблицы всех пользователей."""
        __tablename__ = 'clients'
        id = Column(Integer, primary_key=True)
        name = Column(String(30), unique=True)
        passwd_hash = Column(String)
        pubkey = Column(Text)
        info = Column(String(255), nullable=True)
        last_login = Column(DateTime)

        def __init__(self, name, passwd_hash, info=None):
            self.name = name
            self.passwd_hash = passwd_hash
            self.pubkey = None
            self.info = info
            self.last_login = datetime.now()

    class ClientsHistory(Base):
        """Класс - отображение таблицы истории входов."""
        __tablename__ = 'clients_history'
        id = Column(Integer, primary_key=True)
        client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
        login_time = Column(DateTime)
        login_ip = Column(Integer)

        def __init__(self, client_id, login_time, login_ip):
            self.client_id = client_id
            self.login_time = login_time
            self.login_ip = login_ip

    class ClientsContacts(Base):
        """Класс - отображение таблицы контактов пользователей."""
        __tablename__ = 'clients_contacts'
        id = Column(Integer, primary_key=True)
        owner_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
        contact_id = Column(Integer, ForeignKey('clients.id'), nullable=False)

        def __init__(self, owner_id, contact_id):
            self.owner_id = owner_id
            self.contact_id = contact_id

    class OnlineClients(Base):
        """Класс - отображение таблицы онлайн пользователей."""
        __tablename__ = 'online_clients'
        id = Column(Integer, primary_key=True)
        client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
        client_ip = Column(Integer)

        def __init__(self, client_id, client_ip):
            self.client_id = client_id
            self.client_ip = client_ip

    def __init__(self, path):
        print(path)
        self.database_engine = create_engine(
            'sqlite:///server_base.db3', echo=False, pool_recycle=7200)
        Base.metadata.create_all(self.database_engine)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        self.session.query(self.OnlineClients).delete()
        self.session.commit()

    def client_login(self, account_name, ip_address, key):
        """
        Метод выполняющийся при входе пользователя, записывает в базу
        факт входа. Обновляет открытый ключ пользователя при его изменении.
        """
        rez = self.session.query(self.Clients).filter_by(name=account_name)
        if rez.count():
            user = rez.first()
            user.last_login = datetime.now()
            if user.pubkey != key:
                user.pubkey = key
        else:
            raise ValueError('Пользователь не зарегистрирован.')

        new_online_client = self.OnlineClients(user.id, ip_address)
        self.session.add(new_online_client)

        history = self.ClientsHistory(user.id, datetime.now(), ip_address)
        self.session.add(history)
        self.session.commit()

    def add_user(self, name, passwd_hash):
        """Метод регистрации пользователя. Принимает имя и хэш пароля."""
        user_row = self.Clients(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()

    def remove_user(self, name):
        """Метод удаляющий пользователя из базы."""
        user = self.session.query(self.Clients).filter_by(name=name).first()
        self.session.query(self.OnlineClients).filter_by(
            client_id=user.id).delete()
        self.session.query(self.ClientsHistory).filter_by(
            client_id=user.id).delete()
        self.session.query(self.ClientsContacts).filter_by(
            owner_id=user.id).delete()
        self.session.query(self.ClientsContacts).filter_by(
            contact_id=user.id).delete()
        self.session.query(self.Clients).filter_by(name=name).delete()
        self.session.commit()

    def get_hash(self, name):
        """Метод получения хэша пароля пользователя."""
        user = self.session.query(self.Clients).filter_by(name=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        """Метод получения публичного ключа пользователя."""
        user = self.session.query(self.Clients).filter_by(name=name).first()
        return user.pubkey

    def check_user(self, name):
        """Метод проверяющий существование пользователя."""
        if self.session.query(self.Clients).filter_by(name=name).count():
            return True
        else:
            return False

    def client_logout(self, account_name):
        """Метод фиксирующий отключения пользователя."""
        user = self.session.query(self.Clients).filter_by(
            name=account_name).first()
        self.session.query(self.OnlineClients).filter_by(
            client_id=user.id).delete()
        self.session.commit()

    def add_contact_to_client(self, account_name, contact):
        """Метод добавления контакта для пользователя."""
        user = self.session.query(self.Clients).filter_by(
            name=account_name).first()
        contact = self.session.query(self.Clients).filter_by(
            name=contact).first()

        if not contact or self.session.query(self.ClientsContacts).filter_by(
                owner_id=user.id, contact_id=contact.id).count():
            return

        contact_new = self.ClientsContacts(user.id, contact.id)
        self.session.add(contact_new)
        self.session.commit()

    def delete_contact_from_client(self, account_name, contact):
        """Метод удаления контакта пользователя."""
        user = self.session.query(self.Clients).filter_by(
            name=account_name).first()
        contact = self.session.query(self.Clients).filter_by(
            name=contact).first()

        if not contact:
            return

        self.session.query(self.ClientsContacts).filter(
            self.ClientsContacts.owner_id == user.id,
            self.ClientsContacts.contact_id == contact.id
        ).delete()
        self.session.commit()

    def get_clients_history(self, account_name=None):
        """Метод возвращающий историю входов."""
        query = self.session.query(self.Clients.name,
                                   self.ClientsHistory.login_time,
                                   self.ClientsHistory.login_ip
                                   ).join(self.Clients)
        if account_name:
            query = query.filter(self.Clients.name == account_name)
        return query.all()

    def get_contacts(self, account_name):
        """Метод возвращающий список контактов пользователя."""
        user = self.session.query(self.Clients).filter_by(
            name=account_name).one()
        query = self.session.query(self.ClientsContacts, self.Clients.name).\
            filter_by(owner_id=user.id). \
            join(self.Clients,
                 self.ClientsContacts.contact_id == self.Clients.id)
        return [contact[1] for contact in query.all()]

    def get_online_clients(self):
        """Метод возвращающий список онлайн пользователей."""
        query = self.session.query(
            self.Clients.name,
            self.OnlineClients.client_ip,
        ).join(self.Clients)
        return query.all()

    def get_clients_list(self):
        """
        Метод возвращающий список пользователей со временем последнего входа.
        """
        query = self.session.query(self.Clients.name, self.Clients.last_login)
        return query.all()
