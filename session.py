import socketserver
import pickle
import format_data
import json
from typing import Any
from dataclasses import dataclass
from Chess_Engine import GameState, Move
from DBcontoller import ChessDB
from constants import DATABASE_NAME
from datetime import datetime
from time import sleep

@dataclass
class Gamer:
    id: int
    login: str
    is_white: bool
    wfile: Any
    address: tuple


    def __str__(self):
        return f"{self.name}[{self.address[1]}]"

    def __ne__(self, other):
        return self.address != other.address

    def __eq__(self, other):
        return self.address == other.address

class ClientException(Exception):
    pass

class SessionServer(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, RequestHandlerClass):

        super().__init__(server_address, RequestHandlerClass)

        self.chess_db = ChessDB(DATABASE_NAME)

        self.clients = []
        self.trying_connect_clients = []
        self.gamers = []

        self.game_statement = GameState()
        self.is_game_began = False
        self.is_white_move = True

    def is_game(self):
        return len(self.gamers) == 2

    def begin_game(self):
        self.begin_time_game = datetime.today()
        self.is_game_began = True

    def end_game(self):
        if self.gamers:
            gamers = self.gamers
            white_player = gamers[0]
            black_player = gamers[1]
            self.end_time_game = datetime.today()

            steps = json.dumps(self.game_statement.steps)
            winner_id = self.winner_game().id if self.winner_game() else None
            is_draw = None if winner_id else True

            self.chess_db.add_match(white_chess_gamer_id=white_player.id, black_chess_gamer_id=black_player.id, steps=steps, datetime_begin_match=self.begin_time_game,
                          datetime_end_match=self.end_time_game, is_draw=None, winner_id=winner_id)


            sleep(1)
            self.game_statement = GameState()
            self.gamers = []
            self.is_game_began == False

    def winner_game(self):
        is_white_win = self.game_statement.is_white_win()

        if is_white_win:
            return self.gamers[0]
        elif is_white_win==False:
            return self.gamers[1]

    def is_finish_game(self):
        return self.game_statement.is_finish_game()

    def is_enough_player_for_game(self):
        return len(self.gamers)==2


class GameRequestHandler(socketserver.StreamRequestHandler):

    def handle(self):

        print('connected from', self.client_address)
        self.user = None

        while True:
            if not self.user:
                self.add_to_session()
            else:

                if self.user not in self.server.gamers:

                    req = self.read_json()

                    if req.get("command") == "exit":
                        self.del_self_from_server()
                        break

                    elif req.get("type") == "GET":
                        self.handle_get_request(req)

                    elif req.get("type") == "POST":

                        if req.get("command") == "start":

                            self.server.gamers.append(self.user)

                            break
        while len(self.server.gamers) != 2:
            pass

        if self.server.is_enough_player_for_game():
            self.server.begin_game()

            while self.server.is_enough_player_for_game() and not self.server.is_finish_game(): #and not self.is_finish_game():

                try:
                    if self.is_my_step():
                        self.send({"is_my_step": True}, "json")
                        req = self.read_json()

                        step = None
                        if req.get("type") == "POST":
                            step = req.get("step")
                        if not step:
                            continue

                        move = Move(step[0], step[1], self.server.game_statement.board)
                        if self.server.game_statement.is_valid_move(move):

                            self.server.game_statement.makeMove(move)

                            self.send_all_without_me({"is_my_step": not self.is_my_step(),
                                                         "step": step}, "json")
                            self.server.is_white_move = not self.server.is_white_move
                    else:
                        pass

                except Exception as e:
                    print(e.args)
                    self.server.end_game()

            else:
               # self.end_time_game = datetime.today()
                self.server.end_game()

    def is_my_step(self):

        return self.user.is_white == self.server.is_white_move #and self.is_enough_player_for_game()

    def add_to_session(self):
        req = self.read_json()

        if req.get("type") == "POST":
            if req.get("login"):

                login = req.get("login")

                if self.server.chess_db.is_user_in_database(login):

                    id = self.server.chess_db.get_id_by_login(login)

                    self.user = Gamer(id, login, len(self.server.clients)%2, self.wfile, self.client_address)

                    self.server.clients.append(self.user)

                else:
                    self.server.chess_db.add_user(login)
                    id = self.server.chess_db.get_id_by_login(login)
                    self.user = Gamer(id, login, len(self.server.clients) % 2, self.wfile, self.client_address)
                    self.server.clients.append(self.user)

                print(f"User {self.user.login} added to session")


    def del_self_from_server(self):

        print('disconnected', self.client_address)
        self.send_all_gamers(f"!!! User {self.user.login} disconnected from server !!!", "text")
        self.server.clients.remove(self.user)


    def send(self, data, data_type):

        self.send_user(data, data_type, self.user)

    def send_user(self, data, data_type, user):

        try:

            #

            headers, bytes_data = format_data.data_for_send(data, data_type)

            bytes_headers = format_data.data_to_bytes(headers, "json")

            user.wfile.write(bytes_headers+b'\n')
            user.wfile.write(bytes_data)

        except Exception as ex:
            print(ex.args[0], "except")
            raise Exception
            self.server.clients.remove(user)

    def send_all_gamers(self, data, data_type):
        for gamer in self.server.gamers:

            self.send_user(data, data_type, gamer)

    def send_all_without_me(self, data, data_type):
        for gamer in self.server.gamers:
            if self.user != gamer:
                self.send_user(data, data_type, gamer)

    def send_text(self, text: str, user: Gamer):
        try:
            user.wfile.write(bytes(text+'\r\n', encoding='utf-8'))
        except Exception as ex:
            print(ex.args[0])
            self.server.clients.remove(user)

    def send_obj(self, obj, user):

        try:
            user.wfile.write(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL))
        except:
            self.server.clients.remove(user)

    def _read(self, n):
        res = str(self.rfile.read(n), encoding="utf-8")
        return res

    def _readline_str(self):
        res = str(self.rfile.readline().strip(), encoding='utf-8')
        return res
    def _readline_bytes(self):
        return self.rfile.readline().strip()

    def read_json(self):
        try:
            req = self._readline_bytes()

            return format_data.data_from_bytes(req, "json")
        except:
            pass

    def _write(self, msg):
        self.wfile.write(bytes(msg, encoding='utf-8'))

    def sendall_msg_without_sender(self, text):
        res = bytes(text, encoding='utf-8')
        for user in self.server.clients:
            if user != self.user:
                self.send_text(text, user)

    def sendall_obj(self, obj):
        serialized_obj = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        for user in self.server.clients:
            self.send_obj(serialized_obj, user)

    def send_matches_played_user(self):

        matches = self.server.chess_db.get_matches_by_user_id(self.user.id)
        self.send(matches, "json")

    def read_json(self):
        req = self._readline_bytes()
        if req:
            req = format_data.data_from_bytes(req, "json")
        else:
            req = {}

        return req

    def handle_get_request(self, request: dict):


        if request.get("table") == "matches":
            self.send_matches_played_user()

        if request.get("command") == "exit":
            self.del_self_from_game()

        if request.get("step") == "is_my_step":#"is_my_step"):
            self.send({"is_my_step": self.is_my_step()}, "json")

    def handle_request(self, request: dict):
        if request.get("type") == "GET":
            self.handle_get_request(request)
        if request.get("type") == "POST":
            return request

HOST = ''
PORT = 2002

if __name__ == '__main__':
    print('=== Chess server ===')
    SessionServer((HOST, PORT), GameRequestHandler).serve_forever()
