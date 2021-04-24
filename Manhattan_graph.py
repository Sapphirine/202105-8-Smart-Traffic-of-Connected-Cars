from collections import defaultdict
import pandas as pd
import math

class Graph:
    def __init__(self):
        self.zones = set()
        self.edges = defaultdict(list)
        self.distances = {}
        self.congestion = {}

    def add_zones(self, value):
        self.zones.add(value)

    def add_edge(self, puZone, doZone, time, conges_level = 1):
        self.edges[puZone].append(doZone)
#         self.edges[doZone].append(puZone)
        self.distances[(puZone, doZone)] = time
        self.congestion[(puZone, doZone)] = conges_level
    
    def update_edge(self, puZone, doZone, time, conges_level = 1):
        t = {(puZone, doZone): time}
        c = {(puZone, doZone): conges_level}
        self.distances.update(t)
        self.congestion.update(c)
        
def dijkstra(graph, initial):
    visited = {initial: 0}
    path = {}

    nodes = set(graph.zones)

    while nodes: 
        min_node = None
        for node in nodes:
            if node in visited:
                if min_node is None:
                    min_node = node
                elif visited[node] < visited[min_node]:
                    min_node = node

        if min_node is None:
            break

        nodes.remove(min_node)
        current_weight = visited[min_node]

        for edge in graph.edges[min_node]:
            try:
                weight = current_weight + graph.distances[(min_node, edge)]
            except:
                weight = current_weight + math.inf

            if edge not in visited or weight < visited[edge]:
                visited[edge] = weight
                path[edge] = min_node

    return visited, path

def get_path(graph, src, dest, path = [], updated = False):
    if updated != True:
        time, path = dijkstra(graph, src)
        updated = True
    # route contains the complete steps from puZone to doZone
    route = [dest]
    while path[dest] != src:
        dest = path[dest]
        route.insert(0, dest)
    route.insert(0, src)
    route = [str(i) for i in route]
    
    return time, " ".join(route), path

def get_gas_path(graph, src, dest, path = [], updated = False):
    if updated != True:
        time, path = dijkstra(graph, src)
        updated = True

    gas_loc = None
    gas_zones = [42, 50, 68, 74, 75, 116, 127, 152, 166, 224, 238, 243, 244, 249, 263]
    gas_time = math.inf

    for gas in gas_zones:
        if time[gas] < gas_time:
            gas_loc = gas
            gas_time = time[gas]

    time_g, path_g = dijkstra(graph, gas_loc)
    # print(gas_loc)
    route = [dest]
    while path_g[dest] != gas_loc:
        dest = path_g[dest]
        route.insert(0, dest)
    route.insert(0, gas_loc)
    while path[dest] != src:
        dest = path[dest]
        route.insert(0, dest)
    route.insert(0, src)
    route = [str(i) for i in route]

    return time, " ".join(route), path

# Valid Zone IDs
# [4, 12, 13, 24, 41, 42, 43, 45, 48, 50,
#  68, 74, 75, 79, 87, 88, 90, 100, 107, 113,
#  114, 116, 120, 125, 127, 128, 137, 140, 141, 142,
#  143, 144, 148, 151, 152, 153, 158, 161, 162, 163,
#  164, 166, 170, 186, 194, 202, 209, 211, 224, 229,
#  230, 231, 232, 233, 234, 236, 237, 238, 239, 243,
#  244, 246, 249, 261, 262, 263]
def graph_init():
    
    g = Graph()
    
    valid_zones = [4, 12, 13, 24, 41, 42, 43, 45, 48, 50,
                   68, 74, 75, 79, 87, 88, 90, 100, 107, 113,
                   114, 116, 120, 125, 127, 128, 137, 140, 141, 142,
                   143, 144, 148, 151, 152, 153, 158, 161, 162, 163,
                   164, 166, 170, 186, 194, 202, 209, 211, 224, 229,
                   230, 231, 232, 233, 234, 236, 237, 238, 239, 243,
                   244, 246, 249, 261, 262, 263]
    for z in valid_zones:
        g.add_zones(z)
    
    df = pd.read_excel('graph_weight.xlsx')
    [g.add_edge(row[0], row[1], row[2]) for row in zip(df['puZone'], df['doZone'], df['time'])]
    
    return g
