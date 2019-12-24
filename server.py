from urllib import parse
import socket, sys, email
import pprint

class HTTPServer:

    def __init__(self, host, port):
        self.host = host #Host name
        self.port = port #Port number
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    '''
    Input - req: (string) raw string of GET request
    The function parses the raw request to a readable & manageable json
    '''
    def parse_request(self, req):
            request_line, headers_alone = req.split('\r\n', 1)
            message = email.message_from_string(headers_alone)
            headers = dict(message.items())
            requested_file = request_line.split(" ")[1]
            return requested_file, headers
    '''
    Input - file: (string) name of the file
    Function returns the requested file content, if file is (.jpg or .ico) returns the binary content of the file
    If file doesn't exist returns false
    '''
    def get_file_content(self, file_path):
        if(file_path == '/'):
            file_path += 'index.html'
        if(file_path == '/redirect'):
            file_path = "/result.html"
        file_path = "files" + file_path
        file_ext = file_path[-3:]
        try: #If error then file doesn't exist
            if(file_ext == 'jpg' or file_ext == 'ico'): #If jpg or ico read as binary
                with open(file_path, 'rb') as f:
                    bytes_to_send = f.read()
                return bytes_to_send

            else:
                with open(file_path, 'r') as f:
                    bytes_to_send = f.read()
                return bytes(bytes_to_send,encoding='utf-8')
        except:
            return False
    '''
    Input - status_code (string), content_length (int), 

    '''
    def build_http_response(self, status_code, connection, content_length):
        if('404' in status_code):
            http_response = 'HTTP/1.1 404 Not Found\r\nConnection: %s'%(connection)

        elif('301' in status_code):
            http_response = 'HTTP/1.1 301 Moved Permanently\r\nConnection: %s\r\nLocation: /result.html\r\n' %(connection)

        else:
            http_response = 'HTTP/1.1 200 OK\r\nConnection: %s\r\nContent-length: %s\r\n\r\n' %(connection, str(content_length))

        return bytes(http_response, encoding='utf-8') #Convert to bytes

    def set_timeout(self, connection, client_socket):
        if(connection == 'keep-alive'): #set timeout to 1 sec
            client_socket.settimeout(3.0)
            return False

        elif(connection == 'close'): #Close immediatly connection and accept a new one
            client_socket.close()
            return True

    def start_server(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        stop = False
        while True:
            client_connection, client_address = self.socket.accept()
            while stop != True:
                received_data = client_connection.recv(10000)
                received_data = received_data.decode('utf-8')
                while(received_data[-4:] != '\r\n\r\n'): #Continue recv if not finished
                    next_data = client_connection.recv(10000).decode('utf-8')
                    received_data += next_data

                print(received_data)
                requested_file, header = self.parse_request(received_data)
                file_content = self.get_file_content(requested_file)

                connection = header['Connection']
                if(file_content == False): #File not found
                    resp = self.build_http_response("404", "close", None)
                    client_connection.send(resp)
                    client_connection.close()
                    break
                elif(requested_file == '/redirect'):
                    resp = self.build_http_response("301", connection, None)
                    client_connection.send(resp)
                    client_connection.close()
                    break
                else:
                    content_length = len(file_content)
                    resp = self.build_http_response("200", connection, content_length)
                    client_connection.send(resp)
                    client_connection.send(file_content)

                    stop = self.set_timeout(connection,client_connection)
                    if(not stop):
                        break

if __name__ == '__main__':
    if(len(sys.argv) != 2):
        print("Please specify port")
        sys.exit()
    port = int(sys.argv[1])
    server = HTTPServer('localhost',port)
    server.start_server()
