#!/usr/bin/env python3
import socket
import threading
import sys
import argparse

# Client configuration
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8888
BUFFER_SIZE = 2048

class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
    
    def connect(self):
        """Connect to the chat server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.running = True
            
            print(f"Connected to server at {self.host}:{self.port}")
            
            # Start the receiving thread
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            # Main loop to send messages
            self.send_messages()
            
        except Exception as e:
            print(f"Connection error: {e}")
            self.cleanup()
    
    def receive_messages(self):
        """Receive and display messages from the server."""
        while self.running:
            try:
                data = self.socket.recv(BUFFER_SIZE)
                if not data:
                    print("Disconnected from server")
                    self.running = False
                    break
                
                message = data.decode('utf-8')
                print(message, end='')
                
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.running = False
                break
    
    def send_messages(self):
        """Send messages to the server."""
        try:
            while self.running:
                message = input()
                
                if message == "/exit":
                    self.running = False
                    self.socket.send(message.encode('utf-8'))
                    break
                
                self.socket.send(message.encode('utf-8'))
                
        except Exception as e:
            print(f"Error sending message: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Close the connection and cleanup."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print("Disconnected from server")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Chat Client')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Server IP address')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Server port')
    args = parser.parse_args()
    
    # Create and run the client
    client = ChatClient(args.host, args.port)
    client.connect()

if __name__ == "__main__":
    main() 