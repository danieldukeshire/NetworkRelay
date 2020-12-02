#
# hw4_client.py
# Written by: Daniel Dukeshire, Thomas Durkin, Chris Pence, Chris Allen
# Date: 11.30.2020
# This

import sys
import socket
import queue

control_address = None      # The address to connect to
control_port = None         # The port to connect to
sensor_id = None            # This client's sensor ID
sensor_range = None         # The range of this clint
x_coordinate = None         # The current x_coordinate of this client
y_coordinate = None         # The current y_coordinate of this client

#
# readFromCommand()
# Reads-in the values from the command-line: control address, control port, sensor ID, sensor range
# initial X position, and initial Y position. Stores in global variables for refrence
#
def readFromCommand():
    if len(sys.argv) != 7:                                          # Ensuring the proper number of command-line agrs
        print("Error, correct usage is {} [control address] [control port] [SensorID] [SensorRange] [InitalXPosition] [InitialYPosition]".format(sys.argv[0]))

    # Reading values from the command line and declaring them as global variables
    global control_address
    control_address = sys.argv[1]
    global control_port
    control_port = int(sys.argv[2])
    global sensor_id
    sensor_id = sys.argv[3]
    global sensor_range
    sensor_range = sys.argv[4]
    global x_coordinate
    x_coordinate = sys.argv[5]
    global y_coordinate
    y_coortdinate = sys.argv[6]


def runClient():

    # Create the TCP socket, connect to the server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bind takes a 2-tuple, not 2 arguments
    client.connect((control_address, control_port))

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
    readFromCommand()
    runClient()
