import socket
import threading

HOST = "127.0.0.1"
PORT = 5050
FORMAT = "utf-8"
EOF_TOKEN = "!<EOF>"
ACK_TOKEN = "ACK"

# ANSI color codes
class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class FTP_Server:
    def __init__(self, host, port, format=FORMAT, eof_token=EOF_TOKEN, ack_token=ACK_TOKEN):
        self.HOST = host
        self.PORT = port
        self.FORMAT = format
        self.EOF = eof_token.encode(self.FORMAT)
        self.ACK = ack_token.encode(self.FORMAT)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"{Color.HEADER}[INFO] Starting server{Color.ENDC}")
        self.server.bind((self.HOST, self.PORT))
        self.server.listen()
        print(f"{Color.OKGREEN}[INFO] Server running. Listening on {self.HOST} at port {self.PORT}{Color.ENDC}")

    def start(self):
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target = self.handle_client, args = (conn, addr))
            thread.start()

    def handle_client(self, conn, addr):
        print(f"{Color.OKBLUE}[CONNECTION] {addr} connected to server{Color.ENDC}")
        print(f"{Color.WARNING}[INFO] Currently serving {threading.active_count() - 1} connections.{Color.ENDC}")
        conn.sendall(f"Greetings {addr}.".encode(self.FORMAT))
        
        while True:
            try:
                data = conn.recv(1024).decode(self.FORMAT).split()
                if not data:
                    continue
                print(f"{Color.OKBLUE}[CLIENT] Client sent {data[0]}{Color.ENDC}")
                if data[0] == "CLOSE":
                    conn.sendall("BYE".encode(self.FORMAT))
                    break
                elif data[0] == "GET":
                    if len(data) == 2:
                        self.get_file(conn, addr, data[1])
                    else:
                        conn.sendall("Invalid Command Format.")
                elif data[0] == "PUT":
                    if len(data) == 2:
                        self.put_file(conn, addr, data[1])
                    else:
                        conn.sendall("Invalid Command Format.")
                else:
                    conn.sendall("Invalid Command Format.")
            except Exception:
                conn.sendall("Server Error")
        conn.close()
        print(f"{Color.WARNING}[INFO] {addr} disconnected.{Color.ENDC}")


    def get_file(self, conn, addr, filename):
        try:
            with open(f"server/{filename}", "rb") as file:
                conn.sendall("FOUND".encode(self.FORMAT))
                print(f"{Color.OKGREEN}[GET] Sending {filename} to {addr}{Color.ENDC}")
                while True:
                    data = file.read(1024)
                    if not data:
                        conn.sendall(self.EOF)
                        break
                    conn.sendall(data)
                    acknowledgement = conn.recv(1024)
                    if acknowledgement == self.ACK:
                        continue

                print(f"{Color.WARNING}[INFO] File {filename} sent successfully to {addr}{Color.ENDC}")
        except FileNotFoundError:
            conn.sendall(f"File {filename} Not Found".encode(self.FORMAT))

    def put_file(self, conn, addr, filename):
        with open(f"server/{filename}", "wb") as file:
            conn.sendall(self.ACK)
            while True:
                data = conn.recv(1024)
                if data == self.EOF:
                    break
                file.write(data)
                conn.sendall(self.ACK)

        print(f"{Color.OKBLUE}[PUT] File {filename} received and saved in directory from {addr}.{Color.ENDC}")


server = FTP_Server(host=HOST,port=PORT)
server.start()