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

    def vertices(self):                                             # Returns the number of verticies within the graph
        return list(self.graph.keys())

    def edges(self):                                                # Returns the edges of the graph
        return self.generate_edges()

    def add_node(self, node, x, y):                                 # Adds a node value if it not already in the graph
        if node not in self.graph:                                  # graph.add_node("b")
            self.graph[node] = []
        if node not in self.positions:                              # We have an associated dictionary with the coordinate values
            self.positions[node] = (x, y)

    def add_edge(self, edge):                                       # Adds an edge between two values in the form:
        edge = set(edge)                                            # graph.add_edge({"a", "z"})
        (vertex1, vertex2) = tuple(edge)
        if vertex1 in self.graph:
            self.graph[vertex1].append(vertex2)
        else:
            self.graph[vertex1] = [vertex2]

    def generate_edges(self):                                       # Returns a list of tuples of all the edges in the graph
        redges = []
        for vertex in self.graph:
            for neighbour in self.graph[vertex]:
                if {neighbour, vertex} not in redges:
                    redges.append({vertex, neighbour})
        return redges

    def find_path(self, start_vertex, end_vertex, path=None):       # Depth-first-search on the graph
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
        graph.add_node(BaseId, XPos, YPos)                          # Adds the id to the graph
        for i in edges:                                             # Adds all of the edges
            graph.add_edge({BaseId, i})

#
# readIn()
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
# run()
# See https://pymotw.com/2/select/#module-select
# Reads-in the commands from stdin whilst listening on the passed portnum using the select() call.
# STD input options
# SENDDATA [OriginID] [destinationID]
# QUIT
# Sensor input options
#
def run():
    listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        # Create a TCP socket

    listening_socket.bind(('', int(control_port)))                     # Set the socket to listen on any address, on the specified port
    listening_socket.listen(5)                                                  # bind takes a 2-tuple, not 2 arguments
    cond = True                                                                 # A condition to loop on, until the input from the terminal is QUIT
    inputs = [listening_socket, sys.stdin]                                      # Setting up the inputs for the select() call
    outputs = []

    while cond:                                                                   # Setting up the outputs for the select() call
        readable, writable, exceptional = select.select(inputs, outputs, inputs)    # Making the select call
        message_queues = {}
        for i in readable:                                                          # Looping over the readable array returned from the select call
            if i is listening_socket:                                               # A "readable"server socket is ready to accept a NEW connection
                client_socket, client_address = i.accept()
                print('new connection from ', client_address)
                client_socket.setblocking(0)
                inputs.append(client_socket)
                message_queues[client_socket] = queue.Queue()
            elif i is sys.stdin:                                                    # We recieved input fron the terminal
                input_message = sys.stdin.readline().strip()                        # Strip the ending of new line character
                input_array = input_message.split()                                 # Prepping for a send_data call
                if(input_message == 'QUIT'):                                        # If the input is quit, we exit the loop
                    cond = False
                elif(input_array[0] == 'SENDDATA'):                                 # If we recieved a send sata call... we have to
                    originID = input_array[1]
                    destinationID = input_array[2]
                    print('received send data call:', originID,'to', destinationID)
                else:
                    print('invalid command entered')
            else:
                data = i.recv(1024)                                                 # Otherwise ... we recieved input from an already established connection
                if data:                                                            # A readable client socket has data
                    print("Server received", data.decode())
                    message_queues[i].put(data)
                    if i not in outputs:                                            # Add output channel for response
                        outputs.append(i)
                    else:
                        print('closing', client_address, 'after reading no data')
                        # Stop listening for input on the connection
                        if i in outputs:
                            outputs.remove(i)
                        inputs.remove(i)
                        i.close()
                        del message_queues[i]
            for s in writable:                                                      # Sending output to the port if need be
                try:
                    next_msg = message_queues[s].get_nowait()
                except Queue.Empty:
                    # No messages waiting so stop checking for writability.
                    print('output queue for ', s.getpeername(), ' is empty')
                    outputs.remove(s)
                else:
                    print('sending {} to {}'.format(next_msg, s.getpeername()))
                    s.send(next_msg)

if __name__ == '__main__':
    readFromCommand()
    run()
