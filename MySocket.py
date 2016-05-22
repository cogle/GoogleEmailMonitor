import socket


HOST = '127.0.0.1';
PORT =  '1337';

class MySocket:

    sock = None

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST,PORT))

    def send_message(self, message):
        s.sendall(message.encode())

    def shutdown(self):
        sock.close()
