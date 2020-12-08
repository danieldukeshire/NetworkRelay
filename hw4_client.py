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


def handleDataMessage(str_list, i):
    destinationID = str_list[3]
    originID = str_list[1]
    if(destinationID == sensor_id):
        print_string = "{}: Message from {} to {} successfully received.".format(sensor_id, originID, sensor_id)
        print(print_string)
    else:
        print_string = "{}: Message from {} to {} being forwarded through {}".format(sensor_id, originID, destinationID, sensor_id)
        print(print_string)



#
# sendUpdatePosition
# Takes a client object, and sends an updte position message to the server in the form of:
# UPDATEPOSITION [SensorID] [SensorRange] [CurrentXPosition] [CurrentYPosition]
#
def sendUpdatePosition(client):
    send_string = "UPDATEPOSITION {} {} {} {}".format(sensor_id, sensor_range, x_coordinate, y_coordinate)
    client.send(send_string.encode('utf-8'))
    buf = client.recv(1024)
    return buf

#
# interpretPositionString()
# takes as input the result from UPDATEPOSITION and returns a proper dictionary of reachable items.
# Input in format: REACHABLE [NumReachable] [ReachableList]
# Where ReachableList in space delimited format: [ID] [XPOS] [YPOS]
# returns dictionary in format: {Key = station_name, Value = coord_tuple (x,y)}
#
def interpretPositionString(msg):
	output = {}
	delim_str = msg.decode("utf-8").split()
	numReachable = int(delim_str[1])

	# Get the list and loop through the items
	i = 0
	lis = delim_str[2:]
	while i < (3 * numReachable):
		name = lis[i].strip('[],\'\"')
		xpos = int(lis[i+1].strip('[],\'\"'))
		ypos = int(lis[i+2].strip('[],\'\"'))
		output[name] = (xpos,ypos)
		i += 3
	return output

#
# handleSendData()
# Handles the send data call from stdin. Sends a data message to the server in the form:
# DATAMESSAGE [OriginID] [NextID] [DestinationID] [HopListLength] [HopList]
#
def handleSendData(destinationID, client):
    msg = sendUpdatePosition(client)                # Starts by updating the current position
    reachable = interpretPositionString(msg)		# Converts reachable string to dict object
    nextID = "-1"
    hopListLength = 1
    hopList = [sensor_id]							# Start off with the current sensor in hop list

    # Check for case where no reachable nodes
    if(len(reachable) == 0):
    	print_str = "{}: Message from {} to {} could not be delivered.".format(sensor_id, sensor_id, destinationID)
    	print(print_str)
    	return # No data should be sent to control in this case

    #print(reachable)
    # Check if element in list matches dest name
    dest_reachable = False							# Variable to track if destination immediately reachable
    for key,(x,y) in reachable.items():
    	if key == destinationID:
    		nextID = destinationID 					# destID becomes our nextID
    		dest_reachable = True
    		break

    # Find the next closest node to send if dest isn't reachable
    if dest_reachable == False:
    	print_str = "{}: Sent a new message bound for {}.".format(sensor_id, destinationID)
    else:
        print_str = "{}: Sent a new message directly to {}.".format(sensor_id, nextID)
    print(print_str)

    # Format the string
    send_string = "DATAMESSAGE {} {} {} {} {}".format(sensor_id, nextID, destinationID, hopListLength, hopList)
    client.send(send_string.encode('utf-8'))        # Send the message

#
# handleMove()
# Handles the move call from stdin. Takes the new coordinates and the client
# to send an updateposition call
#
def handleMove(new_x, new_y, client):
    global x_coordinate, y_coordinate               # Must first recognize scope
    x_coordinate = new_x                            # Assigns the new variables to the global ones
    y_coordinate = new_y
    sendUpdatePosition(client)                      # Updates the server with the new coordinates

#
# handleWhere()
# Handles the where clause from stdin.
#
def handleWhere(send_string, client):
    client.send(send_string.encode('utf-8'))        # Sends the WHERE to the server
    buf = client.recv(1024)                         # We block on this recv call
    print(buf.decode())                             # print it to the terminal

#
# internalWhere()
# handles where calls needed by the code
#
def internalWhere(nodeID, client):
	send_string = "WHERE {}".format(nodeID)
	client.send(send_string.encode('utf-8'))
	buf = client.recv(1024)
	there = buf.decode('utf-8').split()

	return {there[1]: ( int(there[2]),int(there[3]) )}


#
# readFromCommand()
# Reads-in the values from the command-line: control address, control port, sensor ID, sensor range
# initial X position, and initial Y position. Stores in global variables for refrence
#
def readFromCommand():
    if len(sys.argv) != 7:                                          # Ensuring the proper number of command-line agrs
        print("Error, correct usage is {} [control address] [control port] [SensorID] [SensorRange] [InitalXPosition] [InitialYPosition]".format(sys.argv[0]))

    # Reading values from the command line and declaring them as global variables
    global control_address, control_port, sensor_id, sensor_range, x_coordinate, y_coordinate
    control_address = sys.argv[1]
    control_port = int(sys.argv[2])
    sensor_id = sys.argv[3]
    sensor_range = sys.argv[4]
    x_coordinate = sys.argv[5]
    y_coordinate = sys.argv[6]

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
                data = i.recv(1024)
                if data:
                    str = data.decode().strip()
                    str_list = str.split()                                          # Array of string inputs
                    if(str_list[0] == 'DATAMESSAGE'):
                        handleDataMessage(str_list, i)
                    if i not in outputs:                                            # We add the readable to outputs if necessary
                        outputs.append(i)
            elif i is sys.stdin:                                                    # RECIEVING DATA FROM STDIN
                input_message = sys.stdin.readline().strip()                        # Strip the ending of new line character
                input_array = input_message.split()                                 # Prepping for multi-input stdin values
                if(input_message == 'QUIT'):                                        # RECIEVE QUIT MESSAGE
                    cond = False
                    client.close()
                elif(input_array[0] == 'MOVE'):                                     # RECIEVE MOVE MESSAGE
                    new_x = input_array[1]                                          # Read in the new values from stdin
                    new_y = input_array[2]
                    handleMove(new_x, new_y, client)                                # Pass them to the handler function
                elif(input_array[0] == 'SENDDATA'):                                 # RECIEVE SENDDATE MESSAGE
                    destinationID = input_array[1]
                    handleSendData(destinationID, client)
                elif(input_array[0] == 'WHERE'):                                    # RECIEVE WHERE MESSAGE
                    handleWhere(input_message, client)
                else:
                    print('Command not supported. Try again')
            else:
                print("CONNECTED2")
                                                                # Open the data and read it into an array


#
# main()
# Gets the client going, calls read-in functions
#
if __name__ == '__main__':
    readFromCommand()
    runClient()
