#!/usr/bin/env python3

import sys  # For arg parsing
import socket  # For sockets

def run_client():
    if len(sys.argv) != 3:
        print(f"Proper usage is {sys.argv[0]} [server name/address] [server port]")
        sys.exit(0)

    # Create the TCP socket, connect to the server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bind takes a 2-tuple, not 2 arguments
    server_socket.connect((sys.argv[1], int(sys.argv[2])))

    # Read a string from standard input
    send_string = 'hello'#input("Enter a string to send: ")
    print('send: ', send_string)
    # Send the message to the server, even if it takes multiple send() calls
    # Could just use send(), for small messages that should be fine
    # We need to "encode" to make this bytes, technically a string str() is NOT
    server_socket.sendall(send_string.encode('utf-8'))

    # Get the response from the server
    recv_string = server_socket.recv(1024)

    # Disconnect from the server
    print("Closing connection to server")
    server_socket.close()

    # Print the response to standard output, both as byte stream and decoded text
    print(f"Received {recv_string} from the server")
    print(f"Decoding, received {recv_string.decode('utf-8')} from the server")

if __name__ == '__main__':
    run_client()
