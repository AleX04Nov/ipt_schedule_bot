from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import exc
import logging
from logging.handlers import RotatingFileHandler


class dbHandler():
    def __init__(self, url, path):
        self.logger = logging.getLogger('db_handler')
        hdlr = logging.handlers.RotatingFileHandler(
            path + '..\\data\\db_handler.log',
            mode='a',
            maxBytes=12 * 1024 * 1024,
            backupCount=2,
        )
        format = logging.Formatter(
            '%(asctime)s | %(levelname)-5s | %(message)s',
            datefmt='%d.%m.%Y | %H:%M:%S'
        )
        hdlr.setFormatter(format)
        self.logger.addHandler(hdlr)

        metadata = MetaData()
        self.engine = create_engine(url)
        metadata.bind = self.engine

        Base = automap_base()
        Base.prepare(self.engine, reflect=True)

        self.chat_ids_orm = Base.classes.chat_ids
        self.name_table_orm = Base.classes.name_table
        self.Session = sessionmaker(bind=self.engine)

        print("Connection Established!")

    def update_sql(
        self,
        const_chat_id,
        new_rozklad_group,
        new_admin,
        new_username
    ):
        while True:
            session = self.Session()
            try:
                quer = session.query(
                    self.chat_ids_orm
                ).filter(
                    self.chat_ids_orm.chat_id == str(const_chat_id)
                ).one()
                quer.rozklad_group = new_rozklad_group
                quer.admin = new_admin
                quer.username = new_username
                session.commit()
                break
            except exc.OperationalError as e:
                self.logger.error("update_sql()", e, "\nReconnection")
                session.close()
            except exc.IntegrityError as e:
                self.logger.error("update_sql() exc.IntegrityError \t", e)
                session.rollback()
                session.close()
            except exc.SQLAlchemyError as e:
                self.logger.error("update_sql() exc.SQLAlchemyError \t", e)
                break
            except Exception as e:
                self.logger.error("update_sql() ", e)
                break
        session.close()

    def get_info_msgNEW(
        self,
        user_id,
        username,
        nameofuser,
        group_bool,
        chat_id,
        chat_title
    ):
        while True:
            session = self.Session()
            try:
                s_rows1 = session.query(
                    self.name_table_orm.name,
                    self.name_table_orm.username
                ).filter(
                    self.name_table_orm.id == user_id
                ).all()

                s_rows2 = session.query(
                    self.chat_ids_orm.username,
                    self.chat_ids_orm.rozklad_group,
                    self.chat_ids_orm.admin
                ).filter(
                    self.chat_ids_orm.chat_id == chat_id
                ).all()
                break
            except exc.OperationalError as e:
                self.logger.error(f"GET_INFO_MSG() {e} | Reconnection")
                session.close()
            except exc.IntegrityError as e:
                self.logger.error(f"GET_INFO_MSG() exc.IntegrityError \t{e}")
                session.rollback()
                session.close()
            except exc.SQLAlchemyError as e:
                self.logger.error(f"GET_INFO_MSG!! "
                                  f"exc.SQLAlchemyError \t{e}")
                return [None, False]
            except Exception as e:
                self.logger.error(f"GET_INFO_MSG \t{e}")
                return [None, False]

        if len(s_rows1) == 0:
            self.new_name_table(user_id, username, nameofuser)
        elif s_rows1[0][0] != nameofuser or s_rows1[0][1] != username:
            self.update_name_table(user_id, username, nameofuser)

        chat_payload = chat_title if group_bool is True else username
        if len(s_rows2) == 0:
            self.insert_sql(chat_id, False, chat_payload)
            return [None, False]
        elif s_rows2[0][0] != chat_payload:
            self.update_sql(
                chat_id,
                s_rows2[0][1],
                s_rows2[0][2],
                chat_payload
            )

        return [s_rows2[0][1], s_rows2[0][2]]

    def insert_sql(self, new_chat_id, new_admin, new_username):
        while True:
            session = self.Session()
            try:
                session.add(
                    self.chat_ids_orm(
                        chat_id=str(new_chat_id),
                        admin=new_admin,
                        username=new_username
                    )
                )
                session.commit()
                break
            except exc.OperationalError as e:
                self.logger.error(f"insert_sql() {e} | Reconnection")
                session.close()
            except exc.IntegrityError as e:
                self.logger.error(f"insert_sql() exc.IntegrityError \t{e}")
                session.rollback()
                session.close()
            except exc.SQLAlchemyError as e:
                self.logger.error(f"insert_sql() exc.SQLAlchemyError \t{e}")
                break
            except Exception as e:
                self.logger.error(f"insert_sql() \t{e}")
                break

    def upd_chat_rozklad(self, chat_id, group):
        while True:
            session = self.Session()
            try:
                quer = session.query(
                    self.chat_ids_orm
                ).filter(
                    self.chat_ids_orm.chat_id == str(chat_id)
                ).one()
                quer.rozklad_group = group
                session.commit()
                break
            except exc.OperationalError as e:
                self.logger.error(f"upd_chat_rozklad() {e} | Reconnection")
                session.close()
            except exc.IntegrityError as e:
                self.logger.error(f"upd_chat_rozklad() "
                                  f"exc.IntegrityError \t{e}")
                session.rollback()
                session.close()
            except exc.SQLAlchemyError as e:
                self.logger.error(f"upd_chat_rozklad() "
                                  f"exc.SQLAlchemyError \t{e}")
                break
            except Exception as e:
                self.logger.error(f"upd_chat_rozklad() \t{e}")
                break

    def get_info_sql(self, const_chat_id):
        while True:
            session = self.Session()
            try:
                s_rows = session.query(
                    self.chat_ids_orm
                ).filter(
                    self.chat_ids_orm.chat_id == const_chat_id
                ).all()
                break
            except exc.OperationalError as e:
                self.logger.error(f"get_info_sql() {e} | Reconnection")
                session.close()
            except exc.IntegrityError as e:
                self.logger.error(f"get_info_sql() exc.IntegrityError \t{e}")
                session.rollback()
                session.close()
            except exc.SQLAlchemyError as e:
                self.logger.error(f"get_info_sql() exc.SQLAlchemyError \t{e}")
                return []
            except Exception as e:
                self.logger.error(f"get_info_sql() \t{e}")
                return []
        return s_rows[0]

    def new_name_table(self, ids, username, name):
        while True:
            session = self.Session()
            try:
                session.add(
                    self.name_table_orm(
                        id=ids,
                        username=username,
                        name=str(name)
                    )
                )
                session.commit()
                break
            except exc.OperationalError as e:
                self.logger.error(f"new_name_table() {e} | Reconnection")
                session.close()
            except exc.IntegrityError as e:
                self.logger.error(f"new_name_table() exc.IntegrityError \t{e}")
                session.rollback()
                session.close()
            except exc.SQLAlchemyError as e:
                self.logger.error(f"new_name_table() "
                                  f"exc.SQLAlchemyError \t{e}")
                break
            except Exception as e:
                self.logger.error(f"new_name_table() \t {e}")
                break

    def update_name_table(self, ids, username, name):
        while True:
            session = self.Session()
            try:
                quer = session.query(
                    self.name_table_orm
                ).filter(
                    self.name_table_orm.id == str(ids)
                ).one()
                quer.username = str(username)
                quer.name = str(name)
                session.commit()
                break
            except exc.OperationalError as e:
                self.logger.error(f"update_name_table() {e} | Reconnection")
                session.close()
            except exc.IntegrityError as e:
                self.logger.error(f"update_name_table() "
                                  f"exc.IntegrityError \t{e}")
                session.rollback()
                session.close()
            except exc.SQLAlchemyError as e:
                self.logger.error(f"update_name_table() "
                                  f"exc.SQLAlchemyError \t{e}")
                break
            except Exception as e:
                self.logger.error(f"update_name_table() \t{e}")
                break

    def get_chatIds(self):
        while True:
            session = self.Session()
            try:
                s_rows = session.query(
                    self.chat_ids_orm.chat_id
                ).all()
                break
            except exc.OperationalError as e:
                self.logger.error(f"get_chatIds() {e} | Reconnection")
                session.close()
            except exc.IntegrityError as e:
                self.logger.error(f"get_chatIds() exc.IntegrityError \t{e}")
                session.rollback()
                session.close()
            except exc.SQLAlchemyError as e:
                self.logger.error(f"get_chatIds() exc.SQLAlchemyError \t{e}")
                return []
            except Exception as e:
                self.logger.error(f"get_chatIds() \t{e}")
                return []
        return s_rows

    # NEEDS FURTHER TESTING!!!!
    def delete_chats(self, deleted_chats):
        while True:
            session = self.Session()
            try:
                session.query(
                    self.chat_ids_orm
                ).filter(
                    self.chat_ids_orm.chat_id.in_(deleted_chats),
                    self.chat_ids_orm.rozklad_group == None
                ).delete()
                session.commit()
                break
            except exc.OperationalError as e:
                self.logger.error(f"delete_chats() {e} | Reconnection")
                session.close()
            except exc.IntegrityError as e:
                self.logger.error(f"delete_chats() exc.IntegrityError \t{e}")
                session.rollback()
                session.close()
            except exc.SQLAlchemyError as e:
                self.logger.error(f"delete_chats() exc.SQLAlchemyError \t{e}")
                break
            except Exception as e:
                self.logger.error(f"delete_chats() \t{e}")
                break

    ##############

    def close(self):
        while True:
            try:
                self.Session.close_all()
                self.engine.dispose()
                break
            except Exception as err:
                self.logger.error(f"close(): \t{err}")
