from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class ClientDatabase:
    """
    Класс - оболочка для работы с базой данных клиента.
    Использует SQLite базу данных, реализован с помощью
    SQLAlchemy ORM и используется декларативный подход.
    """
    class MessageHistory(Base):
        """Класс - отображение для таблицы истории сообщений."""
        __tablename__ = 'message_history'
        id = Column(Integer, primary_key=True)
        from_user = Column(String(30))
        to_user = Column(String(30))
        message = Column(Text)
        date = Column(DateTime)

        def __init__(self, from_user, to_user, message):
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = datetime.now()

    class Contacts(Base):
        """Класс - отображение для таблицы контактов."""
        __tablename__ = 'contacts'
        id = Column(Integer, primary_key=True)
        contact = Column(String(30), unique=True)

        def __init__(self, contact):
            self.contact = contact

    class KnownClients(Base):
        """Класс - отображение для таблицы всех пользователей."""
        __tablename__ = 'known_clients'
        id = Column(Integer, primary_key=True)
        username = Column(String)

        def __init__(self, user):
            self.username = user

    def __init__(self, name):
        self.database_engine = create_engine(
            f'sqlite:///client_{name}.db3', echo=False, pool_recycle=7200)
        Base.metadata.create_all(self.database_engine)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        """Метод добавляющий контакт в базу данных."""
        if not self.session.query(
                self.Contacts).filter_by(contact=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact):
        """Метод удаляющий определённый контакт."""
        self.session.query(self.Contacts).filter_by(contact=contact).delete()
        self.session.commit()

    def contacts_clear(self):
        """Метод очищающий таблицу со списком контактов."""
        self.session.query(self.Contacts).delete()

    def save_message(self, from_user, to_user, message):
        """Метод сохраняющий сообщение в базе данных."""
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        """Метод возвращающий список всех контактов."""
        return [contact[0] for contact in self.session.query(
            self.Contacts.contact).all()]

    def get_clients(self):
        """Метод возвращающий список всех пользователей."""
        return [client[0] for client in self.session.query(
            self.KnownClients.username).all()]

    def add_users(self, users_list):
        """Метод заполняющий таблицу известных пользователей."""
        self.session.query(self.KnownClients).delete()
        for user in users_list:
            user_row = self.KnownClients(user)
            self.session.add(user_row)
        self.session.commit()

    def check_user(self, user):
        """Метод проверяющий существует ли пользователь."""
        if self.session.query(
                self.KnownClients).filter_by(username=user).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        """Метод проверяющий существует ли контакт."""
        if self.session.query(
                self.Contacts).filter_by(contact=contact).count():
            return True
        else:
            return False

    def get_history(self, from_who=None, to_who=None):
        """Метод возвращающий историю сообщений с пользователем."""
        query = self.session.query(self.MessageHistory)
        if from_who:
            query = query.filter_by(from_user=from_who)
        if to_who:
            query = query.filter_by(to_user=to_who)
        return [(history_row.from_user,
                 history_row.to_user,
                 history_row.message,
                 history_row.date)
                for history_row in query.all()]
