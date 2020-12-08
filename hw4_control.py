#
# hw4_control.py
# Written by: Daniel Dukeshire, Thomas Durkin, Chris Pence, Chris Allen
# Date: 11.30.2020
# This is a control server used to relay TCP messages between sensors (clients)
# and manage messages that are moving between base stations .
#
# The graph class is implemented from: https://www.python-course.eu/graphs_python.php
#

import sys
import socket
import select
import queue
import math

control_port = None                     # The port the server should listen on for sensors to connect to
graph = None
all_connections = {}

#
# class Graph
# Used to represent the graph of base stations. Contains two dictionary values:
# Graph: with a key value pair of NodeId: [List of edges]
# Positions: with a key value pair of NodeId: (x_coordinate, y_coordinate)
#
class Graph(object):
    def __init__(self, graph_dict=None):                            # Used to initialize the graph
        if graph_dict == None:                                      # Allows for the option to pass a dictionary
            graph_dict = {}
        self.graph = graph_dict
        self.positions = {}                                         # An associated dictionary with the coordinates
        self.type = {}                                              # An associated dictionary with the type of object
                                                                    # i.e. if the object is a sensor (Range Value), or a base station (-1)

    def vertices(self):                                             # Returns the number of verticies within the graph
        return list(self.graph.keys())

    def edges(self):                                                # Returns the edges of the graph
        return self.generate_edges()

    def add_node(self, node, x, y, range):                          # Adds a node value if it not already in the graph
        if node not in self.graph:                                  # graph.add_node("b")
            self.graph[node] = []
        if node not in self.positions:                              # We have an associated dictionary with the coordinate values
            self.positions[node] = (int(x), int(y))
        if node not in self.type:
            self.type[node] = float(range)                          # assigns the boolean value, TRUE if it is a base station, FALSE otherwise

    def add_edge(self, id, edge):                                   # Adds an edge between two locations in the form:
        if id in self.graph:
            self.graph[id].append(edge)

    def find_edges(self, node, range):                              # Called by SENSORS ONLY, calculates all the connected values with EUCLEAN DISTANCE
        range = float(range)
        if self.type[node] == -1:                                   # Returns nothing if a base-station calls it
            return
        else:                                                       # Otherwise, I loop through all the positions and calculate the edges
            a = self.positions[node]                                # Gathering the current location of the node
            for vertex in self.graph:
                if vertex != node:
                    b = self.positions[vertex]                          # Getting each vertex's location (x and y values) to calculate the distance
                    dst = math.sqrt( (a[0]-b[0])**2 + (a[1]-b[1])**2 )
                    if(self.type[vertex] == -1):                        # If it is a base station, all we need to check for an edge is the sensor's distance
                        if(range >= dst):                               # If the point is within range ... we can add an edge to the base station and sensor
                            self.add_edge(node, vertex)
                            self.add_edge(vertex, node)
                    else:                                               # Otherwise, if it is a sensor, they both have to be in range of one another
                        range2 = self.type[vertex]
                        if(float(range)>=dst and float(range2)>=dst):   # Here, we check to see if the ranges are compatable
                            self.add_edge(node, vertex)             # and we add the edges accordingly
                            self.add_edge(vertex, node)

    def removeEdgesId(self, node):                                  # Removes all edge values with the same id value as "node"
        for vertex in self.graph:
            try:
                self.graph[vertex].remove(node)                     # Deletes the value .... as i dont loop through to check...
            except ValueError:                                      # I might get an error
                pass                                                # do nothing in the case of getting the value error

#
# inputToGraph()
# Takes a file pointer as input, and converts the text file to a graph object
#
def inputToGraph(fp):
    global graph
    graph = Graph()                                                 # Initialize the graph object
    for line in fp:                                                 # We need to parse the input
        inputs = line.split()                                       # Creates an array of the values split on whitespace
        BaseId = inputs[0]                                          # The Base id value
        XPos = int(inputs[1])                                       # Y coordinate value
        YPos = int(inputs[2])                                       # X coordinate value
        NumLinks = int(inputs[3])                                   # The number of edges
        edges = inputs[4:]                                          # All of the edges is what is left over
        graph.add_node(BaseId, XPos, YPos, -1)                      # Adds the id to the graph
        for i in edges:                                             # Adds all of the edges
            graph.add_edge(BaseId, i)
#
# readFromCommand()
# Reads-in the values from the command-line: control port and text file
#
def readFromCommand():
    if len(sys.argv) != 3:                                          # Ensuring the proper number of command-line agrs
        print("Error, correct usage is {} [control port] [base station file]".format(sys.argv[0]))

    global control_port
    control_port = sys.argv[1]                                      # The port to be listening on (global)
    file = sys.argv[2]                                              # The file with the graph values
    try:
        with open(file) as fp:                                      # If the file is valid, we now need to read it into a graph class
            inputToGraph(fp)                                        # ^ This is that call, passes the file pointer to the function
            fp.close()                                              # Closes the file
    except IOError:
            print("Could not read file: ", file)                    # If we catch an error, we can not proceed. Therefore, we exit
            exit(1)

#
# handleSendData()
# Takes the originId and the destinationID, and outputs to the terminal after a few checks.
# This is called in run() upon a senddata request.
#
def handleSendData(originID, destinationID, nextID):
    client = all_connections[nextID]
    send_string = "DATAMESSAGE {} {} {} {} {}".format(originID, nextID, destinationID, 0, '[]')
    client.send(send_string.encode('utf-8'))        # Send the message


def distances(destinationID, originID):
    global graph
    distances_for_originID = {}
    a = graph.positions[destinationID]                          # We choose the next node to traverse to by the shortest distance
    for edge in graph.graph[originID]:
        b = graph.positions[edge]
        dst = math.sqrt( (a[0]-b[0])**2 + (a[1]-b[1])**2 )
        distances_for_originID[edge] =  dst                     # A dictionary with all keys being edges of the origin id, values being distances

    sort = sorted(distances_for_originID.items(), key=lambda item: (item[1], item[0])) # The sorted list
    return sort


def dfs(start_node, visited, end_node):
    global graph
    visited.append(start_node)
    if start_node == end_node:
        return visited
    dist = distances(end_node, start_node)
    for neighbour in dist:
        if neighbour[0] not in visited:
            return dfs(neighbour[0], visited, end_node)

#
# handleDataMessage()
# Takes the data message send to the server, and attempts to deliver
# The data message to the point of interest. The data message is sent in the form of
# DATAMESSAGE [OriginID] [NextID] [DestinationID] [HopListLength] [HopList]
#
def handleDataMessage(str_list, server):
    originID = str_list[1]
    temp_o_ID = originID
    nextID = str_list[2]
    destinationID = str_list[3]
    global graph
    cond = True
    path = dfs(originID, [], destinationID)

    # Handle the case where there isn't a path.
    # Even though we know there isn't a path, we still need to play it out until it can't anymore
    if path == None:
        # Send to the node nearest to DEST reachable from client
        nodes = distances(destinationID, originID)                     # Get reachable nodes sorted by increasing distance from dest
        visited = [originID]
        # While there are nodes to visit, visit them
        # This loops through the "path" until there are no more moves
        while len(nodes) > 0:
            found_next = False
            for i in nodes:
                if i[0] not in visited:
                    nextID = i[0]
                    visited.append(nextID)
                    print_string = "{}: Message from {} to {} being forwarded through {}".format(nextID, originID, destinationID, nextID)
                    print(print_string)
                    nodes = distances(destinationID, nextID)
                    found_next = True
                    break
            # Onces there are no more moves, this runs
            if found_next == False:
                print_string = "{}: Message from {} to {} could not be delivered.".format(visited[-1], originID, destinationID)
                print(print_string)
                break
    # Handle the case where the is a path
    # In this case we do one move and hand off to the next client
    else:
        i = 1
        while i < len(path):
            if(i == len(path)-1): #and graph.type[path[-1]] == '-1'):
                if(graph.type[path[i]] == -1):
                    print_string = "{}: Message from {} to {} successfully received.".format(destinationID, originID, destinationID)
                    print(print_string)
                else:
                    handleSendData(originID, path[i], path[i])
            else:
                if(graph.type[path[i]] == -1):
                    print_string = "{}: Message from {} to {} being forwarded through {}".format(path[i], originID, destinationID, path[i])
                    print(print_string)
                else:
                    handleSendData(originID, destinationID, path[i])
            i += 1

#
# handleWhere()
# On request from the client, returns a formatted message with the location of the
# passed id
#
def handleWhere(id, server):
    global graph
    x = -1
    y = -1
    if(id in graph.positions):
        x = graph.positions[id][0]
        y = graph.positions[id][1]
    send_string = "THERE {} {} {}".format(id, x, y)
    server.send(send_string.encode('utf-8'))

#
# handleUpdatePosition()
# Takes the server and list of values passed by the UPDATEPOSITION. Checks to see if the node is in the graph.
# If it isnt, it is added properly. If it is there, it updates the location of the node, and ALL of the edges
# In the graph related to that node
#
def handleUpdatePosition(value_list, server):
    global graph
    sensor_id = value_list[1]                                       # Assigning all the variables from the graph accordingly
    sensor_range = value_list[2]
    new_x = value_list[3]
    new_y = value_list[4]

    if(sensor_id in graph.graph.keys()):                            # Check to see if the node is in the graph. If it is we update
        graph.graph[sensor_id] = []                                 # Clear all of the edges
        graph.removeEdgesId(sensor_id)                              # Removes all the edges with the passed sensor_id
        graph.positions[sensor_id] = (int(new_x), int(new_y))       # Update the position
        graph.type[sensor_id] = sensor_range                        # Update the range
        graph.find_edges(sensor_id, sensor_range)                   # Finding all of the edges for the added node
    else:                                                           # If its not in the graph, we need to add it to the graph
        graph.add_node(sensor_id, new_x, new_y, sensor_range)       # Adding it to the graph
        graph.find_edges(sensor_id, sensor_range)                   # Finding all of the edges for the added node

    num_reachable = len(graph.graph[sensor_id])                     # The number of reachable nodes
    reachable_list = []                                             # Initializing the reachable list

    for i in graph.graph[sensor_id]:
        x = graph.positions[i][0]
        y = graph.positions[i][1]
        temp_string = "{} {} {}".format(i, x, y)                    # "Each entry in ReachableList is actually 3 strings: [ID] [XPosition] [YPosition].
        reachable_list.append(temp_string)                          # Entries are separated by a space."

    send_string = "REACHABLE {} {}".format(num_reachable, reachable_list)
    server.send(send_string.encode('utf-8'))                        # Sends the string to the client
    #print(graph.graph)

#
# run()
# See https://pymotw.com/2/select/#module-select
# Reads-in the commands from stdin whilst listening on the passed portnum using the select() call.
# STD input options
# SENDDATA [OriginID] [destinationID]
# QUIT
# Sensor input options
#
def runServer():
    global all_connections                                              # A global dictionary with the client_name, and the socket as value
    global graph
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)          # Create a TCP socket

    server.bind(('', int(control_port)))                                # Set the socket to listen on any address, on the specified port
    server.listen(5)                                                    # bind takes a 2-tuple, not 2 arguments
    #server.setblocking(0)
    cond = True                                                         # A condition to loop on, until the input from the terminal is QUIT
    inputs = [server, sys.stdin]                                        # Setting up the inputs for the select() call
    outputs = []
    cond = True

    while cond:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)    # Call to select, selects a queue of input possibilities
        for i in readable:
            if i is server:                                                         # We now loop over possible read-in sets
                connection, client_address = i.accept()                             # If it is a new connection on listen(), we add it to inputs
                connection.setblocking(0)
                inputs.append(connection)
            elif i is sys.stdin:                                                    # Otherwise, it is a message from the terminal
                input_message = sys.stdin.readline().strip()                        # Strip the ending of new line character
                input_array = input_message.split()                                 # Prepping for a send_data call
                if(input_message == 'QUIT'):                                        # If the input is quit, we exit the loop
                    cond = False
                    server.close()
                elif(input_array[0] == 'SENDDATA'):                                 # If we received a send sata call... we have to
                    originID = input_array[1]
                    destinationID = input_array[2]
                    handleSendData(originID, destinationID)                         # Handle the send data accordingly in a call
                else:
                    print('invalid command entered')                                # If the input is incorrect ...
            else:                                                                   # Otherwise, data was sent from existing client
                data = i.recv(1024)                                                 # Open the data and read it into an array
                if data:
                    str = data.decode().strip()
                    str_list = str.split()                                          # Array of string inputs
                    if(str_list[0] == 'UPDATEPOSITION'):                            # Checks if the input is Update Position
                        handleUpdatePosition(str_list, i)
                        all_connections[str_list[1]] = i                            # Stores the address to send to
                    elif(str_list[0] == 'WHERE'):                                   # Checks if the input is where
                        handleWhere(str_list[1], i)
                    elif(str_list[0] == 'DATAMESSAGE'):
                        handleDataMessage(str_list, i)
                    if i not in outputs:                                            # We add the readable to outputs if necessary
                        outputs.append(i)

#
# main()
# Gets the server going, calls read-in functions
#
if __name__ == '__main__':
    readFromCommand()
    runServer()
