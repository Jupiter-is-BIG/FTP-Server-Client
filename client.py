import socket

HOST = "127.0.0.1"
PORT = 5050
FORMAT = "utf-8"
EOF_TOKEN = "!<EOF>"
ACK_TOKEN = "ACK"

# ANSI color codes
COLOR_INFO = '\033[36m'  # Cyan
COLOR_CONNECTION = '\033[32m'  # Green
COLOR_ERROR = '\033[31m'  # Red
COLOR_WARNING = '\033[33m'  # Yellow
COLOR_RESET = '\033[0m'  # Reset color

class FTP_Client:
    def __init__(self, host=HOST, format=FORMAT, eof_token=EOF_TOKEN,  ack_token=ACK_TOKEN):
        self.HOST = host
        self.FORMAT = format
        self.client = None
        self.EOF = eof_token.encode(self.FORMAT)
        self.ACK = ack_token.encode(self.FORMAT)

    def help(self):
        print("""
        Available commands:
        - OPEN <port>: Open a connection to the server on the specified port.
        - CLOSE: Close the current connection to the server.
        - GET <filename>: Download a file from the server.
        - PUT <filename>: Upload a file to the server.
        - QUIT: Quit the FTP client shutting any open connection.
        - HELP: Display this help message.
        """)

    def close(self):
        if self.client is None:
            print(COLOR_WARNING + "[INFO] No active connection found to close." + COLOR_RESET)
            return True
        
        self.client.sendall("CLOSE".encode(self.FORMAT))
        response = self.client.recv(1024).decode(self.FORMAT)
        if response == "BYE":
            self.client.close()
            self.client = None
            print(COLOR_INFO + "[INFO] Successfully closed connection." + COLOR_RESET)
            return True
        else:
            print(COLOR_ERROR + "[ERROR] Unexpected error from server." + COLOR_RESET)
            return False
        
    def quit(self):
        if self.client:
            self.close()
        print(COLOR_WARNING + "========\nQuitting the interface. Bye.\n========" + COLOR_RESET)

    def open(self, port):
        if self.client:
            print(COLOR_ERROR + "[ERROR] Please close the current connection to open a new one" + COLOR_RESET)
            return
        try:
            port = int(port)
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.HOST, port))
            greetings = self.client.recv(1024).decode(self.FORMAT)
            print(COLOR_INFO + f"[MESSAGE] {greetings}" + COLOR_RESET)
            print(COLOR_WARNING + f"[INFO] Connected to {self.HOST} at port {port}." + COLOR_RESET)
        except Exception:
            print(COLOR_ERROR + f"[ERROR] Couldn't connect to {self.HOST}. Please check the port and try again." + COLOR_RESET)
            if self.client:
                self.client.close()
                self.client = None
    
    def get(self, filename):
        if self.client is None:
            print(COLOR_ERROR + "[ERROR] Not connected to the server." + COLOR_RESET)
            return
        
        self.client.sendall(f"GET {filename}".encode(self.FORMAT))
        response = self.client.recv(1024).decode(self.FORMAT)

        if response != "FOUND":
            print(COLOR_INFO + f"[MESSAGE] {response}" + COLOR_RESET)
            return
        
        with open(f"client/{filename}", "wb") as file:
            while True:
                data = self.client.recv(1024)
                if data == self.EOF:
                    break
                file.write(data)
                self.client.sendall(self.ACK)

        print(COLOR_WARNING + f"[INFO] File {filename} received and saved in client directory." + COLOR_RESET)

    def put(self, filename):
        if self.client is None:
            print(COLOR_ERROR + "[ERROR] Not connected to the server." + COLOR_RESET)
            return
        
        try:
            with open(f"client/{filename}", "rb") as file:
                self.client.sendall(f"PUT {filename}".encode(self.FORMAT))
                response = self.client.recv(1024)

                if response != self.ACK:
                    print(COLOR_INFO + f"[MESSAGE] {response.decode(self.FORMAT)}" + COLOR_RESET)
                    return

                print(COLOR_WARNING + f"[INFO] Sending {filename} to {self.HOST}" + COLOR_RESET)
                while True:
                    data = file.read(1024)
                    if not data:
                        self.client.sendall(self.EOF)
                        break
                    self.client.sendall(data)
                    acknowledgement = self.client.recv(1024)
                    if acknowledgement == self.ACK:
                        continue

                print(COLOR_WARNING + f"[INFO] File {filename} sent successfully to {self.HOST}" + COLOR_RESET)
        except FileNotFoundError:
            print(COLOR_ERROR + f"[ERROR] File {filename} Not Found" + COLOR_RESET)

    def start(self):
        print(COLOR_WARNING + "========\nWelcome to FTP\n========" + COLOR_RESET)
        while True:
            command = input("< FTP > ").split()
            if len(command) > 2 or len(command) == 0:
                print(COLOR_ERROR + f"[ERROR] Our protocol enforces using commands of length at most 2 and at least 1. Make sure your filename doesn't have spaces." + COLOR_RESET)
                continue
            if command[0] == "QUIT":
                self.quit()
                break
            elif command[0] == "CLOSE":
                self.close()
            elif command[0] == "OPEN":
                if len(command) == 1:
                    print(COLOR_ERROR + "[ERROR] No port specified." + COLOR_RESET)
                    continue
                self.open(port=command[1])
            elif command[0] == "GET":
                if len(command) == 1:
                    print(COLOR_ERROR + "[ERROR] No filename specified." + COLOR_RESET)
                    continue
                self.get(command[1])
            elif command[0] == "PUT":
                if len(command) == 1:
                    print(COLOR_ERROR + "[ERROR] No filename specified." + COLOR_RESET)
                    continue
                self.put(command[1])
            elif command[0] == "HELP":
                self.help()
            else:
                print(COLOR_ERROR + "[ERROR] No such command found. Use HELP to get list of commands." + COLOR_RESET)
                
user = FTP_Client()
user.start()