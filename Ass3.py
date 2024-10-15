import os
import socket
import re
from datetime import datetime

class SocketServer:
    
    def __init__(self):
        self.bufsize = 1024 
        with open('./response.bin', 'rb') as file:
            self.RESPONSE = file.read()
        self.DIR_PATH = './request'
        self.IMAGE_DIR = './images'
        self.createDir(self.DIR_PATH)
        self.createDir(self.IMAGE_DIR)
                
    def createDir(self, path):
        """디렉토리 생성"""
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError:
            print(f"Error: Failed to create the directory '{path}'.")
    
    def receive_all(self, clnt_sock):
        """클라이언트로부터 모든 데이터를 수신"""
        data = b""
        while True:
            try:
                part = clnt_sock.recv(self.bufsize)
                if not part:
                    break
                data += part
            except socket.timeout:
                break
            except Exception as e:
                print(f"Error receiving data: {e}")
                break
        return data

    def save_request(self, data):
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        request_filename = f"{timestamp}.bin"
        request_path = os.path.join(self.DIR_PATH, request_filename)
        with open(request_path, 'wb') as f:
            f.write(data)
        print(f"Request saved to '{request_path}'")
        return request_path

    def parse_multipart(self, headers, body):
        content_type = headers.get('Content-Type', '')
        boundary_match = re.search(r'boundary=(.+)', content_type)
        if not boundary_match:
            print("No boundary found in Content-Type header.")
            return None, None
        boundary = boundary_match.group(1)
        boundary_bytes = boundary.encode()
        parts = body.split(b'--' + boundary_bytes)
        for part in parts:
            if b'Content-Disposition' in part and b'filename=' in part:
                filename_match = re.search(b'filename="([^"]+)"', part)
                if filename_match:
                    filename = filename_match.group(1).decode()
                else:
                    filename = 'uploaded_image'
                try:
                    header_end = part.find(b'\r\n\r\n') + 4
                    file_content = part[header_end:]
                    file_content = file_content.rstrip(b'\r\n')
                except Exception as e:
                    print(f"Error extracting file content: {e}")
                    continue
                return filename, file_content
        print("No file part found in the request.")
        return None, None

    def parse_headers(self, header_bytes):
        headers = {}
        header_text = header_bytes.decode('utf-8', errors='ignore')
        header_lines = header_text.split('\r\n')
        for line in header_lines:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key] = value
        return headers

    def save_image(self, filename, content):
        image_path = os.path.join(self.IMAGE_DIR, filename)
        with open(image_path, 'wb') as img_file:
            img_file.write(content)
        print(f"Image saved to '{image_path}'")
        return image_path

    
    def run(self, ip, port):
        """서버 실행"""
        # 소켓 생성
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen(10)
        print("Socket server started...")
        print("Press \"Ctrl+C\" to stop the server.\n")
        try:
            while True:
                # 클라이언트의 요청 대기
                clnt_sock, req_addr = self.sock.accept()
                clnt_sock.settimeout(5.0)  # 타임아웃 설정 (5초)
                print(f"Connection from {req_addr}")
                print("Receiving request data...")
                data = self.receive_all(clnt_sock)

                if not data:
                    print("No data received.")
                    clnt_sock.close()
                    continue

                # 실습1
                self.save_request(data)

                header_end = data.find(b'\r\n\r\n')
                if header_end == -1:
                    print("Invalid HTTP request: No header-body separator found.")
                    clnt_sock.sendall(self.RESPONSE)
                    clnt_sock.close()
                    continue

                header_bytes = data[:header_end]
                body = data[header_end+4:]
                headers = self.parse_headers(header_bytes)

                # 실습2
                filename, file_content = self.parse_multipart(headers, body)
                if filename and file_content:
                    self.save_image(filename, file_content)
                else:
                    print("No image data to save.")

                clnt_sock.sendall(self.RESPONSE)
                print("Response sent to the client.\n")
                clnt_sock.close()
        except KeyboardInterrupt:
            print("\nStopping the server...")
            self.sock.close()

if __name__ == "__main__":
    server = SocketServer()
    server.run("127.0.0.1", 8000)