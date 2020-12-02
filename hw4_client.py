#
# hw4_client.py
# Written by: Daniel Dukeshire, Thomas Durkin, Chris Pence, Chris Allen
# Date: 11.30.2020
# The sensors running (a running client) process commands given via standard input,
# and react to messages received from the control server.
#

import sys
import socket
import queue
import select

control_address = None      # The address to connect to
control_port = None         # The port to connect to
sensor_id = None            # This client's sensor ID
sensor_range = None         # The range of this clint
x_coordinate = None         # The current x_coordinate of this client
y_coordinate = None         # The current y_coordinate of this client

#
# sendUpdatePosition
# Takes a client object, and sends an updte position message to the server in the form of:
# UPDATEPOSITION [SensorID] [SensorRange] [CurrentXPosition] [CurrentYPosition]
#
def sendUpdatePosition(client):
    send_string = "UPDATEPOSITION {} {} {} {}".format(sensor_id, sensor_range, x_coordinate, y_coordinate)
    client.send(send_string.encode('utf-8'))

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

#
# runCLient()
# Reads-in commands from stdin whilst listening on the client-server port via select()
#
def runClient():
    # First, we connect to the server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)          # Create the TCP socket, connect to the server
    client.connect((control_address, control_port))                     # Bind takes a 2-tuple, not 2 arguments
    inputs = [client, sys.stdin]                                        # Inputs for the select call
    outputs = []
    cond = True

    # Before we read input in from the server, we send an UPDATEPOSITION message
    # in the form UPDATEPOSITION [SensorID] [SensorRange] [CurrentXPosition] [CurrentYPosition]
    sendUpdatePosition(client)

    # Now we actively listen on stdin and the client port to
    while cond:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        for i in readable:
            if i is client:
                buf = client.recv(1024)
                if(len(buf.decode()) != 0):
                    print("Recieved a message from server:",buf.decode())
            elif i is sys.stdin:
                input_message = sys.stdin.readline().strip()                        # Strip the ending of new line character
                input_array = input_message.split()                                 # Prepping for multi-input stdin values
                print("Recieved a message from stdin:", input_message)
                if(input_message == 'QUIT'):
                    cond = False
                    client.close()
                elif(input_array[0] == 'MOVE'):
                    print("Implement Move")
                elif(input_array[0] == 'SENDDATA'):
                    print("Implement Send Data")
                elif(input_array[0] == 'WHERE'):
                    print("Implenent Send Data")



    #recv_string = client.recv(1024)                                     # Get the response from the server

    # Disconnect from the server
    #print("Closing connection to server")
    #client.close()

    # Print the response to standard output, both as byte stream and decoded text
    #print(f"Received {recv_string} from the server")
    #print(f"Decoding, received {recv_string.decode('utf-8')} from the server")

if __name__ == '__main__':
    readFromCommand()
    runClient()
