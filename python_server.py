#!/usr/bin/env python3
import socket
import threading
import time

# Server configuration
HOST = '127.0.0.1'  # localhost
PORT = 8888
MAX_CLIENTS = 100
BUFFER_SIZE = 2048

# Connected clients and their usernames
clients_lock = threading.Lock()
clients = {}  # socket -> username

def broadcast(message, sender_socket=None):
    """Send a message to all connected clients except the sender."""
    with clients_lock:
        for client_socket, username in clients.items():
            # Don't send the message back to the sender
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode('utf-8'))
                except:
                    # Client probably disconnected
                    continue

def handle_client(client_socket, addr):
    """Handle a client connection."""
    print(f"New connection from {addr}")
    
    # Ask for username
    try:
        client_socket.send("Please enter your username: ".encode('utf-8'))
        username_bytes = client_socket.recv(BUFFER_SIZE)
        if not username_bytes:
            return
        
        username = username_bytes.decode('utf-8').strip()
        if not username:
            username = f"User-{addr[0]}"
        
        # Register the client
        with clients_lock:
            clients[client_socket] = username
        
        # Welcome message
        welcome_msg = f"Welcome {username}! You are now connected to the chat server.\n"
        client_socket.send(welcome_msg.encode('utf-8'))
        
        # Notify others
        broadcast(f"SERVER: {username} has joined the chat.\n", client_socket)
        print(f"{username} has joined the chat")
        
        # Main loop
        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:  # Client disconnected
                    break
                
                message = data.decode('utf-8').strip()
                if message == "/exit":
                    break
                
                # Format message with timestamp and username
                timestamp = time.strftime("%H:%M", time.localtime())
                formatted_message = f"[{timestamp}] {username}: {message}\n"
                
                # Broadcast to everyone
                broadcast(formatted_message, client_socket)
                print(formatted_message.strip())
                
            except Exception as e:
                print(f"Error handling client {username}: {e}")
                break
        
        # Client is disconnecting
        with clients_lock:
            if client_socket in clients:
                del clients[client_socket]
        
        broadcast(f"SERVER: {username} has left the chat.\n")
        print(f"{username} has left the chat")
        client_socket.close()
        
    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()

def start_server():
    """Start the chat server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"Server started on {HOST}:{PORT}")
        print("Waiting for connections...")
        
        while True:
            client_socket, addr = server.accept()
            
            # Check if server is full
            with clients_lock:
                if len(clients) >= MAX_CLIENTS:
                    client_socket.send("Server is full. Try again later.".encode('utf-8'))
                    client_socket.close()
                    continue
            
            # Create a new thread to handle the client
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        print("\nShutting down server...")
        broadcast("SERVER: Server is shutting down. Goodbye!")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        # Close all connections
        with clients_lock:
            for client in clients:
                try:
                    client.close()
                except:
                    pass
        server.close()
        print("Server closed")

if __name__ == "__main__":
    start_server() 