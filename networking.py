import socket
import threading

class Server:
    def __init__(self):
        self.running = True
        self.thread = threading.Thread(target=self.start)
        self.thread.start()

    def start(self):
        TCP_IP = '127.0.0.1'
        TCP_PORT = 5005
        BUFFER_SIZE = 1024
       
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((TCP_IP, TCP_PORT))
        s.listen(1)
        conn, addr = s.accept()
        print 'Connection address:', addr
        while self.running:
            data = conn.recv(BUFFER_SIZE)
            if not data: break
            print "server received data:", data
            conn.send(data)  # echo
        conn.close()

    def stop(self):
        self.running = False


class Client:
    def __init__(self):
        TCP_IP = '127.0.0.1'
        TCP_PORT = 5005
        BUFFER_SIZE = 1024
       
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TCP_IP, TCP_PORT))
        for i in [1,2,4,5,5]:
            s.send(str(i))
        data = s.recv(BUFFER_SIZE)
        s.close()
        print "server sent data back:", data

if __name__ == '__main__':
    server = Server()
    client = Client()
    server.stop()
