import sqlite3
from sqlite3 import OperationalError
from DBErrors import UserExistError

# def _get_by_id(dict_list, _id):
#     result = None
#     ids = [d["id"] for d in dict_list]
#     if _id in ids:
#         pos = ids.index(_id)
#         result = dict_list[pos]
#     return result


class DB:

    def __init__(self, urn):
        self.urn = urn
        self.conn = None

    def get_cursor(self):

        self.conn = sqlite3.connect(self.urn)
        return self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
        self.conn = None

    def execute(self, query, params):

        try:
            curs = self.get_cursor()
            exc = curs.execute(query, params)
            self.close()
            return exc
        except OperationalError as oe:
            print(oe.args[0])
        finally:
            self.close()

    def get_data_dicts(self, query, params=None):

        curs = self.get_cursor()
        if params:
            curs.execute(query, params)
        else:
            curs.execute(query)

        colnames = [desc[0] for desc in curs.description]

        rowdicts = [dict(zip(colnames, row)) for row in curs.fetchall()]
        self.close()
        return rowdicts

    def drop_table(self, name):

        try:
            curs = self.get_cursor()
            curs.execute(f"DROP TABLE {name}")

        except OperationalError as oe:
            print(oe.args[0].upper())
        finally:
            self.close()

    def create_table(self, name: str, fields: dict, foreign_keys=None):

        try:

            params = ', '.join([nfield + " " + tfield for nfield, tfield in fields.items()])
            query = f"CREATE TABLE {name} ({params}"
            if foreign_keys:

                query += DB.__fields_to_foreign_key_format(foreign_keys)

            query += ")"
            curs = self.get_cursor()
            curs.execute(query)

        except OperationalError as oe:
            print(f"TABLE {name}:", oe.args[0])


        finally:
            self.close()

    def __get_id_by_field(self, table, id_name, name_field, field):

        exc = self.get_data_dicts(f"SELECT * FROM {table} WHERE {name_field}=?", (field,))

        if exc:
            return exc[0][id_name]
        #  return exc[id_name]

    @staticmethod
    def __fields_to_foreign_key_format(foreign_keys:dict):

        fk_str = ""
        for field, table in foreign_keys.items():
            fk_str += f", FOREIGN KEY ({field}) REFERENCES {table['table_name']}({table['reference_field']})"
        return fk_str

class ChessDB:

    def __init__(self, db_name):
        self.__db = DB(db_name)
       # self.db.drop_table("users")
        self.db.create_table(name="users", fields={"user_id": "INTEGER PRIMARY KEY",
                                                   "login": "TEXT",
                                                   "password": "TEXT"})

        #self.db.drop_table("matches")
        self.db.create_table(name="matches",

                             fields={"match_id": "INTEGER PRIMARY KEY",
                                     "white_chess_gamer_id": "INTEGER",
                                     "black_chess_gamer_id": "INTEGER",
                                     "steps": "TEXT",
                                     "datetime_begin": "DATETIME",
                                     "datetime_end": "DATETIME",
                                     "is_draw": "BIT",
                                     "winner_id":"INTEGER"},

                             foreign_keys={"white_chess_gamer_id": {"table_name": "users",
                                                                    "reference_field": "user_id"},
                                           "black_chess_gamer_id": {"table_name": "users",
                                                                    "reference_field": "user_id"}}
                             )

    @property
    def db(self):
        return self.__db

    @db.setter
    def db(self, value):
        raise PermissionError

    def is_user_with_such_login_exist(self, login):

        if self.db.get_data_dicts("SELECT * FROM users WHERE login=?", (login,)):
            return True
        return False

    def is_user_in_database(self, login):
        if self.db.get_data_dicts("SELECT * FROM users WHERE login=?", (login,)):
            return True
        return False
        # self.db.create_table(name="ga")

    def add_user(self, login):
        if not self.is_user_with_such_login_exist(login):
            self.db.execute("INSERT INTO users(login) VALUES (?)", (login,))
        else:
            raise UserExistError

    def add_match(self, white_chess_gamer_id, black_chess_gamer_id, steps, datetime_begin_match=None, datetime_end_match=None, is_draw=None, winner_id=None):

        query = "INSERT INTO matches(white_chess_gamer_id, black_chess_gamer_id, steps, datetime_begin, datetime_end, is_draw, winner_id) VALUES (?,?,?,?,?,?, ?)"

        self.db.execute(query,
                        (white_chess_gamer_id, black_chess_gamer_id, steps, datetime_begin_match, datetime_end_match, is_draw, winner_id))

    def get_matches_by_user_id(self, user_id):
        query = "SELECT * FROM matches WHERE white_chess_gamer_id=? OR black_chess_gamer_id=?"
        params = (user_id, user_id)
        return self.db.get_data_dicts(query, params)

    def get_match_by_id(self, match_id):
        query = "SELECT * FROM matches WHERE match_id=?"
        params = (match_id, )
        return self.db.get_data_dicts(query, params)[0]

    def get_id_by_login(self, login):
        query = "SELECT * FROM users WHERE login=?"
        params = (login,)
        return self.db.get_data_dicts(query, params)[0]["user_id"]

    def is_record_in_table(self, table_name, field_names, values):
        fields = ""
        for field in field_names:
            fields += f"{field}=?,"
        fields = field[:-2:] #REMOVE LAST ","
        query = f"SELECT * FROM {table_name} WHERE {fields}"
        records = self.db.get_data_dicts(query, values)
        if records:
            return True
        else:
            return False

if __name__=="__main__":
    chess_db = ChessDB("chess.db")
    print(chess_db.get_match_by_id(1))