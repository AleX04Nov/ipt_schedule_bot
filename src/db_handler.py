from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import exc

# Подключиться к базе данных.
##################################
# TO CHANGE DB URL!

class dbHandler():
    def __init__(self, url):
        metadata = MetaData()
        self.engine = create_engine(url)
        metadata.bind = self.engine

        Base = automap_base()
        Base.prepare(self.engine, reflect = True)

        self.chat_ids_orm = Base.classes.chat_ids

        self.name_table_orm = Base.classes.name_table

        self.Session = sessionmaker(bind = self.engine)

        self._session = self.Session()

        print("Connection Established!")

    def update_sql(
        self,
        const_chat_id,
        new_rozklad_group,
        new_admin,
        new_username
    ):
        while True:
            try:
                quer = self._session.query(
                    self.chat_ids_orm
                ).filter(
                    self.chat_ids_orm.chat_id == str(const_chat_id)
                ).one()
                quer.rozklad_group = new_rozklad_group
                quer.admin = new_admin
                quer.username = new_username
                self._session.commit()
                break
            except exc.OperationalError as e:
                print(e, "\nReconnection")
                self._session = self.Session()
            except exc.SQLAlchemyError as e:
                print("update_sql() exc.SQLAlchemyError \t", e)
                break
            except Exception as e:
                print("update_sql() ", e)
                break

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
            try:
                s_rows1 = self._session.query(
                    self.name_table_orm.name,
                    self.name_table_orm.username
                ).filter(
                    self.name_table_orm.id == user_id
                ).all()

                s_rows2 = self._session.query(
                    self.chat_ids_orm.username,
                    self.chat_ids_orm.rozklad_group,
                    self.chat_ids_orm.admin
                ).filter(
                    self.chat_ids_orm.chat_id == chat_id
                ).all()
                break
            except exc.OperationalError as e:
                print(e, "\nReconnection")
                self._session = self.Session()
            except exc.SQLAlchemyError as e:
                print("ERRR in GET_INFO_MSG!! exc.SQLAlchemyError \t", e)
                return [None, False]
            except Exception as e:
                print("ERRR in GET_INFO_MSG!!\t", e)
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
            try:
                self._session.add(
                    self.chat_ids_orm(
                        chat_id = str(new_chat_id),
                        admin = new_admin,
                        username = new_username
                    )
                )
                self._session.commit()
                break
            except exc.OperationalError as e:
                print(e, "\nReconnection")
                self._session = self.Session()
            except exc.SQLAlchemyError as e:
                print("insert_sql() exc.SQLAlchemyError \t", e)
                break
            except Exception as e:
                print("insert_sql()\t", e)
                break

    def upd_chat_rozklad(self, chat_id, group):
        while True:
            try:
                quer = self._session.query(
                    self.chat_ids_orm
                ).filter(
                    self.chat_ids_orm.chat_id == str(chat_id)
                ).one()
                quer.rozklad_group = group
                self._session.commit()
                break
            except exc.OperationalError as e:
                print(e, "\nReconnection")
                self._session = self.Session()
            except exc.SQLAlchemyError as e:
                print("upd_chat_rozklad() exc.SQLAlchemyError \t", e)
                break
            except Exception as e:
                print("upd_chat_rozklad()\t", e)
                break

    def get_info_sql(self, const_chat_id):
        while True:
            try:
                s_rows = self._session.query(
                    self.chat_ids_orm
                ).filter(
                    self.chat_ids_orm.chat_id == const_chat_id
                ).all()
                break
            except exc.OperationalError as e:
                print(e, "\nReconnection")
                self._session = self.Session()
            except exc.SQLAlchemyError as e:
                print("get_info_sql() exc.SQLAlchemyError \t", e)
                return []
            except Exception as e:
                print("get_info_sql()\t", e)
                return []
        return s_rows[0]

    def new_name_table(self, ids, username, name):
        while True:
            try:
                self._session.add(
                    self.name_table_orm(
                        id = ids,
                        username = username,
                        name = str(name)
                    )
                )
                self._session.commit()
                break
            except exc.OperationalError as e:
                print(e, "\nReconnection")
                self._session = self.Session()
            except exc.SQLAlchemyError as e:
                print("new_name_table() exc.SQLAlchemyError\t", e)
                break
            except Exception as e:
                print("new_name_table()\t", e)
                break

    def update_name_table(self, ids, username, name):
        while True:
            try:
                quer = self._session.query(
                    self.name_table_orm
                ).filter(
                    self.name_table_orm.id == str(ids)
                ).one()
                quer.username = str(username)
                quer.name = str(name)
                self._session.commit()
                break
            except exc.OperationalError as e:
                print(e, "\nReconnection")
                self._session = self.Session()
            except exc.SQLAlchemyError as e:
                print("update_name_table() exc.SQLAlchemyError\t", e)
                break
            except Exception as e:
                print("update_name_table()\t", e)
                break

    def get_chatIds(self):
        while True:
            try:
                s_rows = self._session.query(
                    self.chat_ids_orm.chat_id
                ).all()
                break
            except exc.OperationalError as e:
                print(e, "\nReconnection")
                self._session = self.Session()
            except exc.SQLAlchemyError as e:
                print("get_chatIds() exc.SQLAlchemyError\t", e)
                return []
            except Exception as e:
                print("get_chatIds()\t", e)
                return []
        return s_rows

    # NEEDS FURTHER TESTING!!!!
    def delete_chats(self, deleted_chats):
        while True:
            try:
                self._session.query(
                    self.chat_ids_orm
                ).filter(
                    self.chat_ids_orm.chat_id.in_(deleted_chats),
                    self.chat_ids_orm.rozklad_group == None
                ).delete()
                self._session.commit()
                break
            except exc.OperationalError as e:
                print(e, "\nReconnection")
                self._session = self.Session()
            except exc.SQLAlchemyError as e:
                print("delete_chats() exc.SQLAlchemyError\t", e)
                break
            except Exception as e:
                print("delete_chats()\t", e)
                break
    ##############

    def close(self):
        while True:
            try:
                self._session.close()
                self.engine.dispose()
                break
            except Exception as err:
                print("close(): \t", err)
