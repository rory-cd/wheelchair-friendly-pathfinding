import math
import numpy as np
import heapq
import functools
from shapely import Point, Polygon
import time


#region PROBLEM
class Problem():

    """The abstract class for a formal problem. You should subclass
    this and implement the methods actions and result, and possibly
    __init__, goal_test, and path_cost. Then you will create instances
    of your subclass and solve them with the various search functions."""

    def __init__(self, initial, goal=None):
        """The constructor specifies the initial state, and possibly a goal
        state, if there is a unique goal. Your subclass's constructor can add
        other arguments. 'initial' might be a string like 'Melbourne', 'goal'
        might be another string like 'sunshine'."""
        self.initial = initial
        self.goal = goal
    def is_in(self,elt, seq):
        """Similar to (elt in seq), but compares with 'is', not '=='."""
        return any(x is elt for x in seq)

    def actions(self, state):
        """Return the actions that can be executed in the given
        state. The result would typically be a list, but if there are
        many actions, consider yielding them one at a time in an
        iterator, rather than building them all at once."""
        raise NotImplementedError

    def result(self, state, action):
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""
        raise NotImplementedError

    def goal_test(self, state):
        """Return True if the state is a goal. The default method compares the
        state to self.goal or checks for state in self.goal if it is a
        list, as specified in the constructor. Override this method if
        checking against a single self.goal is not enough."""
        if isinstance(self.goal, list):
            return self.is_in(state, self.goal)
        else:
            return state == self.goal

    def g(self, c, state1, action, state2):
        """Return the cost of a solution path that arrives at state2 from
        state1 via action, assuming cost c to get up to state1. If the problem
        is such that the path doesn't matter, this function will only look at
        state2.  If the path does matter, it will consider c and maybe state1
        and action. The default method costs 1 for every step in the path."""
        return c + 1

    def value(self, state):
        """For optimization problems, each state has a value.  Hill-climbing
        and related algorithms try to maximize this value."""
        raise NotImplementedError


class GraphProblem(Problem):

    """The problem of searching a graph from one node to another."""

    def __init__(self, initial, goal, graph):
        Problem.__init__(self, initial, goal)
        self.graph = graph
        self.infinity=math.inf
        
    def distance(self,a, b):
        """The distance between two (x, y) points."""
        xA, yA = a
        xB, yB = b
        return np.hypot((xA - xB), (yA - yB)) # Euclidean distance
        
    def actions(self, A):
        """The actions at a graph node are just its neighbors."""
        return list(self.graph.get(A).keys())

    def result(self, state, action):
        """The result of going to a neighbor is just that neighbor."""
        return action

    def g(self, cost_so_far, A, action, B):
        return cost_so_far + (self.graph.get(A, B) or self.infinity)

    def find_min_edge(self):
        """Find minimum value of edges."""
        m = self.infinity
        for d in self.graph.graph_dict.values():
            local_min = min(d.values())
            m = min(m, local_min)

        return m

#endregion

#region DATA STRUCTURES

class Node:

    """A node in a search tree. Contains a pointer to the parent (the node
    that this is a successor of) and to the actual state for this node. Note
    that if a state is arrived at by two paths, then there are two nodes with
    the same state.  Also includes the action that got us to this state, and
    the total path_cost (also known as g) to reach the node.  Other functions
    may add an f and h value; see best_first_graph_search and astar_search for
    an explanation of how the f and h values are handled. You will not need to
    subclass this class."""

    def __init__(self, state, parent=None, action=None, g=0):
        """Create a search tree Node, derived from a parent by an action."""
        self.state = state
        self.parent = parent
        self.action = action
        self.g = g
        self.depth = 0
        if parent:
            self.depth = parent.depth + 1

    def __repr__(self):
        return "<Node {}>".format(self.state)

    def __lt__(self, node):
        return self.state < node.state

    def expand(self, problem):
        """List the nodes reachable in one step from this node."""
        return [self.child_node(problem, action)
                for action in problem.actions(self.state)]

    def child_node(self, problem, action):
        next_state = problem.result(self.state, action)
        next_node = Node(next_state, self, action,
                    problem.g(self.g, self.state, action, next_state))
        return next_node

    def solution(self):
        """Return the sequence of actions to go from the root to this node."""
        return [node.action for node in self.path()[1:]]

    def path(self):
        """Return a list of nodes forming the path from the root to this node."""
        node, path_back = self, []
        while node:
            path_back.append(node)
            node = node.parent
        return list(reversed(path_back))

    def __eq__(self, other):
        return isinstance(other, Node) and self.state == other.state

    def __hash__(self):
        return hash(self.state)
    

class Graph:
    """A graph connects nodes (vertices) by edges (links). Each edge can also
    have a length associated with it. The constructor call is something like:
        g = Graph({'A': {'B': 1, 'C': 2})
    this makes a graph with 3 nodes, A, B, and C, with an edge of length 1 from
    A to B,  and an edge of length 2 from A to C. You can use g.nodes() to get
    a list of nodes, g.get('A') to get a dict of links out of A, and g.get('A', 'B')
    to get the length of the link from A to B. 'Lengths' can actually be any object at
    all, and nodes can be any hashable object."""

    def __init__(self, graph_dict=None, loc_data=None):
        self.graph_dict = graph_dict or {}
        self.loc_data = loc_data or {}
            
    def default_cost_function(self, distance, src_data, dst_data):
        """Default cost function (simply returns the distance)."""
        return distance

    def get(self, a, b=None):
        """Return a link distance or a dict of {node: distance} entries.
        .get(a,b) returns the distance or None;
        .get(a) returns a dict of {node: distance} entries, possibly {}."""
        links = self.graph_dict.setdefault(a, {})
        if b is None:
            return links
        else:
            return links.get(b)

    def nodes(self):
        """Return a list of nodes in the graph."""
        s1 = set([k for k in self.graph_dict.keys()])
        s2 = set([k2 for v in self.graph_dict.values() for k2, v2 in v.items()])
        nodes = s1.union(s2)
        return list(nodes)


class PriorityQueue:
    """A Queue in which the minimum (or maximum) element (as determined by f and
    order) is returned first.
    If order is 'min', the item with minimum f(x) is
    returned first; if order is 'max', then it is the item with maximum f(x).
    Also supports dict-like lookup."""

    def __init__(self, order='min', f=lambda x: x):
        self.heap = []
        if order == 'min':
            self.f = f
        elif order == 'max':  # now item with max f(x)
            self.f = lambda x: -f(x)  # will be popped first
        else:
            raise ValueError("Order must be either 'min' or 'max'.")

    def append(self, item):
        """Insert item at its correct position. single element"""
        heapq.heappush(self.heap, (self.f(item), item))

    def extend(self, items):
        """Insert each item in items at its correct position.multiple element"""
        for item in items:
            self.append(item)

    def pop(self):
        """Pop and return the item (with min or max f(x) value)
        depending on the order."""
        if self.heap:
            return heapq.heappop(self.heap)[1]
        else:
            raise Exception('Trying to pop from empty PriorityQueue.')

    def __len__(self):
        """Return current capacity of PriorityQueue."""
        return len(self.heap)

    def __contains__(self, key):
        """Return True if the key is in PriorityQueue."""
        return any([item == key for _, item in self.heap])

    def __getitem__(self, key):
        """Returns the first value associated with key in PriorityQueue.
        Raises KeyError if key is not present."""
        for value, item in self.heap:
            if item == key:
                return value
        raise KeyError(str(key) + " is not in the priority queue")

    def __delitem__(self, key):
        """Delete the first occurrence of key."""
        try:
            del self.heap[[item == key for _, item in self.heap].index(True)]
        except ValueError:
            raise KeyError(str(key) + " is not in the priority queue")
        heapq.heapify(self.heap)


#region ALGORITHM

def memoize(fn, slot=None, maxsize=32):
    """Memoize fn: make it remember the computed value for any argument list.
    If slot is specified, store result in that slot of first argument.
    If slot is false, use lru_cache for caching the values."""

    # Define the memoized function that will be returned
    if slot:
        def memoized_fn(obj, *args):
            # If the object has a slot with the specified name, return its value
            if hasattr(obj, slot):
                return getattr(obj, slot)
            # Otherwise, compute the value of fn and store it in the slot
            else:
                val = fn(obj, *args)
                setattr(obj, slot, val)
                return val
    else:
        # Use the lru_cache decorator to cache the values
        @functools.lru_cache(maxsize=maxsize)
        def memoized_fn(*args):
            return fn(*args)

    # Return the memoized function
    return memoized_fn


def best_first_graph_search(problem, f):
    """Search the nodes with the lowest f scores first.
    You specify the function f(node) that you want to minimize; for example,
    if f is a heuristic estimate to the goal, then we have greedy best
    first search; if f is node.depth then we have breadth-first search.
    There is a subtlety: the line "f = memoize(f, 'f')" means that the f
    values will be cached on the nodes as they are computed. So after doing
    a best first search you can examine the f values of the path returned."""

    f = memoize(f, 'f')
    explored = set()
    node = Node(problem.initial)

    if problem.goal_test(node.state): # Already at goal
        explored.add(node)
        return [node], explored

    frontier = PriorityQueue('min', f)
    frontier.append(node)

    while frontier:
        node = frontier.pop()

        #goal test before the expansion of child nodes
        if problem.goal_test(node.state):
            if node in explored: explored.remove(node)
            explored.add(node)
            return node.path(), explored

        if node in explored: explored.remove(node)
        explored.add(node)
        for child in node.expand(problem):
            if child.state not in explored and child not in frontier:
                frontier.append(child)
            elif child in frontier:
              # Check if this child is a better path
                incumbent = frontier[child]
                if f(child) < incumbent:
                    del frontier[child]
                    frontier.append(child)

    return None, explored

#endregion


#region UTILITIES

def get_slope(distance, src_data, dst_data):
    """Calculates the slope between two points (src and dst) using 
    formula slope = rise / run"""
    rise = (src_data['elevation'] - dst_data['elevation'])
    # Calculate slope
    return rise / distance


def get_slope_penalty(slope):
    """Calculates and returns the slope penalty for a given slope value.
    Increases exponentially, penalising uphill slopes more than downhill.
    Larger multipliers applied beyond maximum standard slope grade."""
    # Maximum standard grade for Australian ramps
    max_grade = 1 / 14
    
    # Increase exponentially
    result = math.exp((abs(slope) * 10) -1)
    
    # Uphill
    if slope > 0:
        # Steep
        if slope > max_grade: return 1200 * result
        else: return 80 * result
    # Downhill or flat
    else:
        # Steep
        if slope < -max_grade: return 1000 * result
        else: return 20 * result
        

def haversine(lat1, lon1, lat2, lon2):
    """The haversine formula determines the great-circle distance between two points
    on a sphere given their longitudes and latitudes. This is necessary to obtain
    the Euclidean distance between given coordinates."""
    
    R = 6371000  # Earth radius in metres
    
    # Get latitude in radians
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    # Get differences in radians
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)

    # Apply formula
    a = math.sin(Δφ / 2) ** 2 + math.sin(Δλ / 2) ** 2 * math.cos(φ1) * math.cos(φ2)
    c = 2 * math.asin(math.sqrt(a))

    return R * c  # Distance in metres


def generate_costs(edge_dists, loc_data, cost_function, surface_data):
    """Uses the provided cost function to generate an adjusted cost, using
    the edge distances, location data, and surface data. Returns a dictionary
    with the same structure as edge_dists, but with adjusted costs."""
    result = {}
    
    # Iterate through each source node
    for src, src_connections in edge_dists.items():
        result[src] = {}
        
        # Set each neighbour's edge cost
        for neighbour, distance in src_connections.items():
            # Compute the cost using the provided cost function
            result[src][neighbour] = cost_function(distance, loc_data[src], loc_data[neighbour], surface_data[src][neighbour])
            
    return result


def clear_path():
    """Clears global variables, ready for a new search."""
    global source, dest, path, explored_nodes
    source = dest = explored_nodes = path = None
    
    
def check_admissibility():
    """Checks whether the selected heuristic is admissible.
    A heuristic h is admissible if h(n) ≤ h*(n) , where h*(n) is the true cost from n.
    Returns a boolean representing whether the heuristic is admissible,
    along with the first inadmissible node found (or None)."""
    
    if problem == None:
        print("Problem not set.")
        return
    
    if path == None:
        print("Path not finalised.")
        return
    
    # Get all costs for problem
    costs = problem.graph.graph_dict
    # Reverse the final path
    rev_path = list(reversed(path))
    
    # Iterate through the reversed path
    for i, node in enumerate(rev_path):
        
        # If it's the last node in the path (first in reversed path), cost is 0
        if i == 0: cost_to_goal = 0
        # Else add the cost between this node and the last to cumulative total
        else: cost_to_goal += costs[node.state][rev_path[i - 1].state]
        
        # Does the node overestimate the true cost to the goal?
        if node.h > cost_to_goal:
            return False, node.state
        
    return True, None


def check_consistency():
    """Checks whether the selected heuristic is consistent (monotonic).
    A heuristic h is consistent if for every edge (n, n'): h(n) <= cost(n, n') + h(n').
    Returns a boolean representing whether the heuristic is consistent,
    along with the first inconsistent node found (or None)."""
    
    if problem == None:
        print("Problem not set.")
        return
    
    if path == None:
        print("Path not finalised.")
        return
    
    # Get all costs for problem
    costs = problem.graph.graph_dict
    
    # Iterate through the final path
    for i in range(len(path) - 1):
        node = path[i]
        next_node = path[i + 1]
        next_edge_cost = costs[node.state][next_node.state]

        # If there's a node whose h value exceeds the next edge cost
        # plus the next heuristic, the heuristic is not consistent
        if node.h > next_edge_cost + next_node.h:
            return False, node.state
        
    return True, None

#endregion

#region SEARCH TYPES

def uniform_cost_search_graph(problem, h=None):
    """Uniform Cost Search uses Best First Search algorithm with f(n) = g(n)"""
    path, explored = best_first_graph_search(problem, lambda node: node.g)
    return path, explored

def greedy_best_first_search(problem, h=None):
    """Greedy Best-first graph search is an informative searching algorithm with f(n) = h(n).
    You need to specify the h function when you call best_first_search"""
    h = memoize(h or problem.h, 'h')
    path, explored = best_first_graph_search(problem, lambda n: h(n))
    return path, explored

def astar_search(problem, h=None):
    """A* search is best-first graph search with f(n) = g(n)+h(n).
    You need to specify the h function when you call astar_search"""
    h = memoize(h, 'h')
    path, explored = best_first_graph_search(problem, lambda node: node.g + h(node))
    return path, explored

#endregion

#region COST FUNCTIONS

def cost_standard(distance, src_data, dst_data, surface = None):
    """Calculates the cost of a path edge starting with the distance,
    adding a slope penalty, and an additional penalty based on the elevation
    difference between the two nodes."""
    if distance == 0: return 0

    # Calculate slope using rise / run
    elevation_diff = dst_data['elevation'] - src_data['elevation']
    slope = elevation_diff / distance
    
    # Set the slope penalty (exponential)
    slope_penalty = get_slope_penalty(slope)

    # Assign a weight to the elevation difference
    if elevation_diff < 0: weight = 15  # Downhill
    else: weight = 35                   # Uphill
    elevation_penalty = abs(elevation_diff) * weight
    
    return int(distance + slope_penalty + elevation_penalty)


def cost_extended(distance, src_data, dst_data, surface):
    """Calculates the cost of a path edge starting with the standard
    cost evaluation (distance + slope penalty + elevation penalty)
    and adding a penalty for the surface of the path."""
    result = cost_standard(distance, src_data, dst_data)
    if result == 0: return 0
    
    # If no surface data has been provided, use the standard cost function
    if surface == None: return result
    
    # Surface will be 0, 1, or 2 here
    surface_penalty = surface * 10
    
    return int(result + surface_penalty)

#endregion

#region HEURISTICS

def h_euclidean(problem, node):
    """A heuristic function based on the Euclidean (straight-line) distance 
    from a node's coordinates to the goal. The distance between coordinates 
    in metres is calculated using the haversine formula."""
    
    # Get location data
    locs = problem.graph.loc_data
    if locs == None: return problem.infinity
    
    # Get coordinates of given node
    if type(node) is str: lat1, lon1 = locs[node]['coords']
    else: lat1, lon1 = locs[node.state]['coords']
    # Get coordinates of goal
    lat2, lon2 = locs[problem.goal]['coords']
    
    # Return distance in metres
    return int(haversine(lat1, lon1, lat2, lon2))


def h_standard(problem, node):
    """A heuristic function based on the Euclidean distance from a node
    to the goal, plus a slope penalty based on the estimated slope, and
    an additional penalty based on the elevation difference between the
    node and the goal."""
    
    # Get location data
    locs = problem.graph.loc_data
    if locs == None: return problem.infinity
    
    # Get Euclidean distance
    euclidean = h_euclidean(problem, node)
    if euclidean == 0: return 0  # Arrived at goal
    
    # Calculate elevation difference and estimated grade
    node_elev = locs[node.state]['elevation']
    goal_elev = locs[problem.goal]['elevation']
    elevation_diff = goal_elev - node_elev

    # Estimate the slope based on rise / run
    estimated_slope = elevation_diff / euclidean
    # Calculate the slope penalty, with dampening
    slope_penalty = get_slope_penalty(estimated_slope) * 0.15   # Dampening to ensure admissibility
    
    # Assign a weight to the elevation difference
    if elevation_diff < 0: weight = 15  # Downhill
    else: weight = 35                   # Uphill
    elevation_penalty = abs(elevation_diff) * weight

    result = int(euclidean + slope_penalty + elevation_penalty)
    
    return result


def h_extended(problem, node):
    """A heuristic function based on the standard heuristic
    (Euclidean distance + slope penalty + elevation penalty)
    Applies an additional cost if the path ahead is likely to
    be unmade. This penalty is dampened closer to the goal"""
    
    # Start with the standard heuristic
    result = h_standard(problem, node)
    if result == 0: return 0
    
    # Get location data
    locs = problem.graph.loc_data
    
    # Set a Shapely point based on the current node
    point = Point(locs[node.state]['coords'])
    # Set a Shapely polygon denoting the risk zone
    polygon = Polygon(risk_zone)
    # Get the euclidean distance, for dampening
    euclidean = h_euclidean(problem, node)
    # Penalty grows exponentially as distance from goal increases, with a maximum of 20
    penalty = min(20, math.exp(0.05 * euclidean) - 1)

    # If the node is in the risk zone, apply the penalty
    if polygon.contains(point): result += penalty
        
    return int(result)

#endregion

#region DATA

# Defines the distance along each edge between nodes
edge_dists = dict(
    A=dict(B=25, C=82),
    B=dict(A=25, C=45),
    C=dict(A=82, B=45, D=87, E=44),
    D=dict(C=87, F=40),
    E=dict(C=44, F=78, H=159),
    F=dict(D=40, E=78, G=86),
    G=dict(F=86, I=185, J=102),
    H=dict(E=159, I=96, L=347),
    I=dict(G=185, H=96, K=113),
    J=dict(G=102, K=220, M=97),
    K=dict(I=113, J=220, N=101),
    L=dict(H=347, O=154),
    M=dict(J=97, N=250),
    N=dict(K=101, M=250, P=100, Q=240),
    O=dict(L=154, R=149, V=259),
    P=dict(N=100, S=103, U=265),
    Q=dict(N=240, R=56, T=92),
    R=dict(O=149, Q=56, T=66, X=269),
    S=dict(P=103, W=239),
    T=dict(Q=92, R=66, U=29),
    U=dict(P=265, T=29, W=97, Y=264),
    V=dict(O=259, X=103),
    W=dict(S=239, U=97, Z=254),
    X=dict(R=269, V=103, Y=93),
    Y=dict(U=264, X=93, Z=98),
    Z=dict(W=254, Y=98)
)

# Define the cost
edge_surfaces = dict(
    A=dict(B=0, C=0),
    B=dict(A=0, C=0),
    C=dict(A=0, B=0, D=0, E=0),
    D=dict(C=0, F=0),
    E=dict(C=0, F=0, H=0),
    F=dict(D=0, E=0, G=0),
    G=dict(F=0, I=0, J=0),
    H=dict(E=0, I=0, L=1),
    I=dict(G=0, H=0, K=0),
    J=dict(G=0, K=0, M=2),
    K=dict(I=0, J=0, N=0),
    L=dict(H=1, O=0),
    M=dict(J=2, N=2),
    N=dict(K=0, M=2, P=0, Q=0),
    O=dict(L=0, R=0, V=1),
    P=dict(N=0, S=0, U=0),
    Q=dict(N=0, R=0, T=0),
    R=dict(O=0, Q=0, T=0, X=0),
    S=dict(P=0, W=0),
    T=dict(Q=0, R=0, U=0),
    U=dict(P=0, T=0, W=0, Y=0),
    V=dict(O=1, X=1),
    W=dict(S=0, U=0, Z=0),
    X=dict(R=0, V=1, Y=0),
    Y=dict(U=0, X=0, Z=0),
    Z=dict(W=0, Y=0)
)

# Defines the coordinates and elevation of each node on the map
location_data = dict(
    A=dict(coords=(-38.27255, 144.51679), elevation=7),
    B=dict(coords=(-38.27233, 144.51676), elevation=9),
    C=dict(coords=(-38.27225, 144.51726), elevation=10),
    D=dict(coords=(-38.2715, 144.51724), elevation=11),
    E=dict(coords=(-38.27216, 144.51774), elevation=11),
    F=dict(coords=(-38.27147, 144.51769), elevation=11),
    G=dict(coords=(-38.27084, 144.51807), elevation=9),
    H=dict(coords=(-38.27177, 144.51946), elevation=8),
    I=dict(coords=(-38.2713, 144.52006), elevation=15),
    J=dict(coords=(-38.26993, 144.51825), elevation=8),
    K=dict(coords=(-38.27046, 144.52067), elevation=25),
    L=dict(coords=(-38.27132, 144.52324), elevation=20),
    M=dict(coords=(-38.26907, 144.51843), elevation=7),
    N=dict(coords=(-38.26965, 144.5212), elevation=24),
    O=dict(coords=(-38.27092, 144.52482), elevation=12),
    P=dict(coords=(-38.2688, 144.52156), elevation=19),
    Q=dict(coords=(-38.26966, 144.52395), elevation=27),
    R=dict(coords=(-38.26966, 144.52458), elevation=26),
    S=dict(coords=(-38.26789, 144.52189), elevation=34),
    T=dict(coords=(-38.26905, 144.5246), elevation=31),
    U=dict(coords=(-38.26879, 144.5246), elevation=32),
    V=dict(coords=(-38.27054, 144.52772), elevation=14),
    W=dict(coords=(-38.26792, 144.52462), elevation=35),
    X=dict(coords=(-38.26968, 144.52767), elevation=18),
    Y=dict(coords=(-38.26884, 144.52761), elevation=32),
    Z=dict(coords=(-38.26796, 144.52752), elevation=35)
)

# Polygon vertices denoting an area near the beach, with increased risk of unmade paths
risk_zone = [
    (-38.26993, 144.52816),
    (-38.2702, 144.524),
    (-38.27054, 144.52089),
    (-38.27134, 144.51584),
    (-38.27474, 144.51583),
    (-38.27436, 144.52984),
    (-38.26993, 144.52816)
]

#endregion

#region SET SELECTIONS

def set_problem(from_node, to_node):
    """Sets the problem (including global "source" and "destination") based on provided start and end nodes"""
    global selected_cost_function, source, dest, problem
    
    # Cost function required to set costs for the problem
    if selected_cost_function == None:
        print("Cost function not selected")
        return
    
    source = from_node
    dest = to_node
    costs = generate_costs(edge_dists, location_data, selected_cost_function, edge_surfaces)
    graph = Graph(costs, location_data)
    problem = GraphProblem(source, dest, graph)


def set_search_type(index):
    """Sets the global search type based on a passed index (ideally from a GUI)."""
    global selected_search_type
    if index == 0: selected_search_type = astar_search
    elif index == 1: selected_search_type = uniform_cost_search_graph
    else: selected_search_type = None
    
    
def set_heuristic(index):
    """Sets the global heuristic function based on a passed index (ideally from a GUI)."""
    global selected_heuristic
    if index == 0: selected_heuristic = h_standard
    elif index == 1: selected_heuristic = h_extended
    else: selected_heuristic = h_euclidean
    
    
def set_cost_function(index):
    """Sets the global cost function based on a passed index (ideally from a GUI)."""
    global selected_cost_function
    if index == 0: selected_cost_function = cost_standard
    else: selected_cost_function = cost_extended

#endregion


def run_search():
    """Run the currently selected search type with the currently selected heuristic.
    Returns the best cost path, along with a list of explored nodes,
    then assigns them to global variables."""
    if selected_search_type == None:
        print("Algorithm not selected.")
        return
    
    if problem == None:
        print("Problem not set.")
        return
    
    if selected_heuristic == None:
        print("Heuristic not selected.")
        return
    
    global path, explored_nodes
    path, explored_nodes = selected_search_type(problem, lambda node: selected_heuristic(problem, node))
    

# Search options
selected_search_type = None
selected_heuristic = None
selected_cost_function = None
problem = None

# Selected path
source = None
dest = None
path = None
explored_nodes = None

if __name__ == '__main__':
    set_cost_function(0)
    set_problem('A', 'Z')
    set_search_type(0)
    set_heuristic(0)
    start = time.time()
    run_search()
    end = time.time()
    print(f"PATH: {path}")
    
    # Check efficiency and runtime
    runtime = math.floor((end - start) * 10000) / 10000
    efficiency = int((len(path) / len(explored_nodes)) * 100)
    print(f"Efficiency: {efficiency}%   Runtime: {runtime}s")
    
    # Check admissibility
    admissible, node1 = check_admissibility()
    if admissible: print("Admissible")
    else: print(f"Inadmissible at: {node1}")
    
    # Check consistency
    consistent, node2 = check_consistency()
    if consistent: print("Consistent")
    else: print(f"Inconsistent at: {node2}")
