import socket


import format_data

import json

class Client:

    def __init__(self, login, host="localhost", port=2002):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.input = self.socket.makefile('rb', 0)
        self.output = self.socket.makefile('wb', 0)
        self.login = login
        self.post({"login": self.login})

    def read(self):

        headers_bytes = self.input.readline().strip()
        headers = format_data.data_from_bytes(headers_bytes, "json")
    #    print(f"{headers=}")
        data_bytes = self.socket.recv(headers["len"])  # self.input.read(headers["len"])
      #  print(data_bytes)
        data = format_data.data_from_bytes(data_bytes, headers["type"])
        return headers, data

    def get_req(self, data:dict):

        req_data = {"type": "GET"}
        req_data = {**req_data, **data}
        req_data = format_data.data_to_bytes(req_data, "json")

        self.send(req_data)
        headers, new_data = self.read()
        return new_data

    def post(self, data:dict):

        req_data = {"type": "POST"}
        req_data = {**req_data, **data}
        req_data = format_data.data_to_bytes(req_data, "json")
        self.send(req_data)

    def send(self, msg):
        self.output.write(msg+b'\r\n')

if __name__ == '__main__':

    HOST = 'localhost'
    PORT = 2002
    login = input("Input login>> ")
    client = Client(login, HOST, PORT)

    print(client.get_req({"table": "matches"}))
    client.post({"command":"start"})
    while True:
        headers, data = client.read()
        is_my_step = data.get("is_my_step")
        if is_my_step:
            step = json.loads(input("Input step ([[6, 1], [4, 1]])>> "))
            print(step, type(step))
            client.post({"step": step})
        else:
            print(is_my_step)
#