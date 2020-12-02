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

    def add_edge(self, id, edge):                                       # Adds an edge between two locations in the form:
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
                        if(range>=dst and range2>=dst):                 # Here, we check to see if the ranges are compatable
                            self.add_edge(node, vertex)                 # and we add the edges accordingly
                            self.add_edge(vertex, node)

    def find_path(self, start_vertex, end_vertex, path=None):           # Depth-first-search on the graph
        if path == None:
            path = []
        graph = self.graph
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return path
        if start_vertex not in graph:
            return None
        for vertex in graph[start_vertex]:
            if vertex not in path:
                extended_path = self.find_path(vertex,
                                               end_vertex,
                                               path)
                if extended_path:
                    return extended_path
        return None

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
# This is called in run() upon a senddata request
#
def handleSendData(originID, destinationID):
    print('This is where we handle the send data call from terminal')

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
        print("Its  here!")
        # Update position, range, and all node edges as the position has changed
    else:                                                           # If its not in the graph, we need to add it to the graph
        graph.add_node(sensor_id, new_x, new_y, sensor_range)       # Adding it to the graph
        graph.find_edges(sensor_id, sensor_range)                   # Finding all of the edges for the added node

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
    global graph
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        # Create a TCP socket

    server.bind(('', int(control_port)))                              # Set the socket to listen on any address, on the specified port
    server.listen(5)                                                  # bind takes a 2-tuple, not 2 arguments
    #server.setblocking(0)
    cond = True                                                       # A condition to loop on, until the input from the terminal is QUIT
    inputs = [server, sys.stdin]                                      # Setting up the inputs for the select() call
    outputs = []
    cond = True

    while inputs and cond:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        for i in readable:
            if i is server:
                connection, client_address = i.accept()
                connection.setblocking(0)
                inputs.append(connection)
            elif i is sys.stdin:
                input_message = sys.stdin.readline().strip()                        # Strip the ending of new line character
                input_array = input_message.split()                                 # Prepping for a send_data call
                if(input_message == 'QUIT'):                                        # If the input is quit, we exit the loop
                    cond = False
                    server.close()
                elif(input_array[0] == 'SENDDATA'):                                 # If we recieved a send sata call... we have to
                    originID = input_array[1]
                    destinationID = input_array[2]
                    handleSendData(originID, destinationID)
                else:
                    print('invalid command entered')
            else:
                data = i.recv(1024)
                if data:
                    str = data.decode().strip()
                    str_list = str.split()
                    print(str)
                    if(str_list[0] == 'UPDATEPOSITION'):
                        handleUpdatePosition(str_list, server)
                        i.send("REACHABLE".encode('utf-8'))
                        print(graph.graph)
                    elif(str_list[0] == 'WHERE'):
                        print("Handle where")
                        i.send("Some list of values".encode('utf-8'))
                    if i not in outputs:
                        outputs.append(i)

#
# main()
# Gets the server going, calls read-in functions
#
if __name__ == '__main__':
    readFromCommand()
    runServer()
