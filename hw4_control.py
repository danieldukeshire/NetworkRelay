#
# hw4_control.py
# Written by: Daniel Dukeshire, Thomas Durkin, Chris Pence, Chris Allen
# Date: 11.30.2020
# This is a control server used to relay TCP messages between sensors (clients)
# and manage messages that are moving between base stations .
#

import sys

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
def readIn():
    if len(sys.argv) != 3:                                          # Ensuring the proper number of command-line agrs
        print("Error, correct usage is {} [control port] [base station file]".format(sys.argv[0]))

    control_port = sys.argv[1]                                      # The port to be listening on (global)
    file = sys.argv[2]                                              # The file with the graph values
    try:
        with open(file) as fp:                                      # If the file is valid, we now need to read it into a graph class
            inputToGraph(fp)                                        # ^ This is that call, passes the file pointer to the function
            fp.close()                                              # Closes the file
    except IOError:
            print("Could not read file: ", file)                    # If we catch an error, we can not proceed. Therefore, we exit
            exit(1)


if __name__ == '__main__':
    readIn()
