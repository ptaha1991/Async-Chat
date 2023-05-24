from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class ServerDatabase:
    class Clients(Base):
        __tablename__ = 'clients'
        id = Column(Integer, primary_key=True)
        name = Column(String(30), unique=True)
        info = Column(String(255), nullable=True)
        last_login = Column(DateTime)

        def __init__(self, name, info=None):
            self.name = name
            self.info = info
            self.last_login = datetime.now()

    class ClientsHistory(Base):
        __tablename__ = 'clients_history'
        id = Column(Integer, primary_key=True)
        client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
        login_time = Column(DateTime)
        login_ip = Column(Integer)

        def __init__(self, client_id, login_time, login_ip):
            self.client_id = client_id
            self.login_time = login_time
            self.login_ip = login_ip

    class ClientsContacts(Base):
        __tablename__ = 'clients_contacts'
        id = Column(Integer, primary_key=True)
        owner_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
        contact_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

        def __init__(self, owner_id, contact_id):
            self.owner_id = owner_id
            self.contact_id = contact_id

    def __init__(self):
        self.database_engine = create_engine('sqlite:///server_base.db3', echo=False, pool_recycle=7200)
        Base.metadata.create_all(self.database_engine)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

    def client_login(self, account_name, ip_address):
        rez = self.session.query(self.Clients).filter_by(name=account_name)
        if rez.count():
            user = rez.first()
            user.last_login = datetime.now()
        else:
            user = self.Clients(account_name)
            self.session.add(user)
            self.session.commit()

        history = self.ClientsHistory(user.id, datetime.now(), ip_address)
        self.session.add(history)
        self.session.commit()

    def add_contact_to_client(self, account_name, contact):
        user = self.session.query(self.Clients).filter_by(name=account_name).first()
        contact = self.session.query(self.Clients).filter_by(name=contact).first()

        if not contact or self.session.query(self.ClientsContacts) \
                .filter_by(owner_id=user.id, contact_id=contact.id).count():
            return

        contact_new = self.ClientsContacts(user.id, contact.id)
        self.session.add(contact_new)
        self.session.commit()

    def get_clients_history(self, account_name=None):
        query = self.session.query(self.Clients.name,
                                   self.ClientsHistory.login_time,
                                   self.ClientsHistory.login_ip
                                   ).join(self.Clients)

        if account_name:
            query = query.filter(self.Clients.name == account_name)
        return query.all()

    def get_contacts(self, account_name):
        user = self.session.query(self.Clients).filter_by(name=account_name).first()
        if not user:
            return
        query = self.session.query(self.ClientsContacts, self.Clients.name). \
            filter_by(owner_id=user.id). \
            join(self.Clients, self.ClientsContacts.contact_id == self.Clients.id)
        return [contact[1] for contact in query.all()]
