import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
import sys
import time
import math

try:
    import algorithms as alg
except ImportError:
    sys.exit("Exiting early because algorithms.py was not found.")


class UI_State:

    def __init__(self, state = 0, source = None, dest = None):
        """Create a UI State"""
        self.state = state
        self.source = source
        self.dest = dest

    def next_state(self):
        """Go to the next UI state"""
        self.state += 1
        
    def reset_state(self):
        """Reset the state to 0."""
        self.state = 0


#region CREATE_ELEMENTS

def create_ui(root):
    # Check necessary data
    if alg.location_data is None: sys.exit("Exiting early because alg.location_data was not found.")
    if alg.edge_dists is None: sys.exit("Exiting early because alg.edge_dists was not found.")
    location_data = alg.location_data
    edge_dists = alg.edge_dists
    
    # Set the left column
    left_frame = tk.Frame(root, width=300)
    left_frame.pack(side=tk.LEFT, fill=tk.Y)
    left_frame.pack_propagate(False)
    frame_bg = left_frame["background"]
    
    # Set canvas
    canvas = tk.Canvas(root, width=1500, height=800, bg='black')
    canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    # Display the image on the canvas (this will be the background)
    bg_image_file = PhotoImage(file="Map-BG.png")
    bg_image = canvas.create_image(0, 0, anchor=tk.NW, image=bg_image_file, tags='bg')
    
    # Cost
    c_label = tk.Label(left_frame, text="Cost function:", font=("Arial", 11, "bold"))
    c_label.pack(padx=20, pady=(20, 0), anchor="w")
    c_combobox = ttk.Combobox(left_frame, values=["Standard", "Extended"], width='50')
    c_combobox.pack(padx=20, anchor="w")
    c_combobox.current(0)

    # Search
    s_label = tk.Label(left_frame, text="Search:", font=("Arial", 11, "bold"))
    s_label.pack(padx=20, pady=(10, 0), anchor="w")
    s_combobox = ttk.Combobox(left_frame, values=["A*", "Dijikstra's algorithm"], width='50')
    s_combobox.pack(padx=20, anchor="w")
    s_combobox.current(0)
    
    # Heuristic
    h_label = tk.Label(left_frame, text="Heuristic:", font=("Arial", 11, "bold"))
    h_label.pack(padx=20, pady=(10, 0), anchor="w")
    h_combobox = ttk.Combobox(left_frame, values=["Standard", "Extended", "Euclidean dist. only"], width='50')
    h_combobox.pack(padx=20, anchor="w")
    h_combobox.current(0)
    
    # Efficiency
    efficiency_label = tk.Label(left_frame, text="Efficiency: N/A", font=("Arial", 10, "bold"))
    efficiency_label.pack(padx=20, pady=(5, 0), anchor="w")
    
    # Admissibility
    admissibility_label = tk.Label(left_frame, text="", font=("Arial", 10))
    admissibility_label.pack(padx=20, pady=(5, 0), anchor="w")

    # Cost toggle
    show_costs_ticked = tk.BooleanVar(value=True)
    cost_checkbox = tk.Checkbutton(left_frame, text="Show costs on map", relief="flat", font=("Arial", 10),
                                   variable=show_costs_ticked, command=lambda: on_cost_toggle(canvas, show_costs_ticked))
    cost_checkbox.pack(padx=20, pady=(10, 5), anchor="w")
    
    # Create a textbox
    path_summary_label = tk.Label(left_frame, text="", font=("Arial", 11, "bold"), fg=frame_bg)
    path_summary_label.pack(padx=20, pady=(0, 5), anchor="w")
    text_box = tk.Text(left_frame, width=50, height=300, relief="flat", bg=frame_bg)
    text_box.pack(padx=20, pady=(0, 10), anchor="w")
    # Define the tags (styling)
    text_box.tag_config("path", foreground="white", background="dodgerblue4", font=("Arial", 10, "bold"))
    text_box.tag_config("exp", foreground="white", background="cadetblue", font=("Arial", 10, "bold"))
    text_box.tag_config("bold", font=("Arial", 10, "bold"))
    text_box.tag_config("body", font=("Arial", 10))
    text_box.tag_config("italic", font=("Arial", 10, "italic"))
    text_box.tag_config("red_under", foreground="red")
    text_box.config(state="disabled") # Read only

    node_objects, node_positions = draw_nodes(canvas, location_data)
    edge_colours = set_edge_colours(location_data, edge_dists)
    edge_objects = draw_edges(canvas, edge_colours, node_positions)
    costboxes = draw_costs(canvas)

    ui_elements = { 'left_frame': left_frame,
                'frame_bg' : frame_bg,
                's_label': s_label,
                's_combobox': s_combobox,
                'h_label': h_label,
                'h_combobox': h_combobox,
                'c_label': c_label,
                'c_combobox': c_combobox,
                'efficiency_label': efficiency_label,
                'admissibility_label': admissibility_label,
                'show_costs_ticked': show_costs_ticked,
                'cost_checkbox': cost_checkbox,
                'path_summary_label': path_summary_label,
                'text_box': text_box,
                'canvas': canvas,
                'bg_image': bg_image,
                'bg_image_file': bg_image_file,
                'node_objects': node_objects,
                'node_positions': node_positions,
                'edge_colours': edge_colours,
                'edge_objects': edge_objects,
                'costboxes': costboxes
            }

    # Bind nodes
    for node, data in location_data.items():
        # Bind the node
        canvas.tag_bind(node, '<Button-1>', lambda event, node=node: on_node_click(node, ui_elements))
        
    s_combobox.bind("<<ComboboxSelected>>",  lambda event: on_search_change(s_combobox, h_combobox))
        
    canvas.tag_bind(bg_image, '<Button-1>', lambda event: clear_map(ui_elements))

    canvas.tag_lower("edge")  # Push all items tagged 'edge' to the back
    canvas.tag_lower("bg")


def draw_nodes(canvas, location_data):
    """Draws nodes and corresponding labels on the canvas, storing them in a dictionary for reference"""
    node_objects = {}
    node_positions = {}
    
    # Find the min and max values for latitude and longitude
    latitudes = [data["coords"][0] for data in location_data.values()]
    longitudes = [data["coords"][1] for data in location_data.values()]

    min_lat, max_lat = min(latitudes), max(latitudes)
    min_lon, max_lon = min(longitudes), max(longitudes)
    
    for node, data in location_data.items():
        coords = data['coords']
        scaled_coords = scale_coordinates(coords, min_lat, max_lat, min_lon, max_lon)
        fill_colour = 'gray30'
        # Store positions for later use
        node_positions[node] = scaled_coords
        
        # Draw an outline circle
        canvas.create_oval(scaled_coords[0] - 12, scaled_coords[1] - 12,
                        scaled_coords[0] + 12, scaled_coords[1] + 12,
                        fill='white', outline='', width=15, tags = node)
                
        # Draw a circle for each node
        node_obj = canvas.create_oval(scaled_coords[0] - 11, scaled_coords[1] - 11,
                        scaled_coords[0] + 11, scaled_coords[1] + 11,
                        fill=fill_colour, outline='', width=15, tags = node)
        
        # Store the canvas object in the dictionary for later access
        node_objects[node] = node_obj

        # Label the node
        canvas.create_text(scaled_coords[0], scaled_coords[1] + 1, text=node, font=("Arial Bold", 11), fill='white', tags=node)
    return node_objects, node_positions


def set_edge_colours(location_data, edge_costs):
    seen = set()
    result = {}
    for node, neighbours in edge_costs.items():
        for neighbour in neighbours:
            edge = tuple(sorted((node, neighbour)))  # Sort to make ('A', 'B') == ('B', 'A')
            if edge not in seen:
                seen.add(edge)
                grade = alg.get_slope(edge_costs[node][neighbour], location_data[node], location_data[neighbour])
                edge_colour = 'grey'
                if abs(grade) > 1/14: edge_colour = 'firebrick'
                elif abs(grade) > 1/20: edge_colour = 'sandybrown'
                result[edge] = edge_colour
    return result


def draw_edges(canvas, edge_colours, node_positions):
    # Draw edges on the canvas
    result = {}
    for n1, n2 in edge_colours:
        x1, y1 = node_positions[n1]
        x2, y2 = node_positions[n2]
        
        canvas.create_line(x1, y1, x2, y2, fill='white', width=6, tags='edge')
        edge_obj = canvas.create_line(x1, y1, x2, y2, fill=edge_colours[(n1, n2)], width=4, tags='edge')
        
        # Store the canvas object in the dictionary for later access
        result[(n1, n2)] = edge_obj
    return result


def draw_costs(canvas):
    costboxes = {}
    box_positions = {('A', 'B'): (25, 630), ('A', 'C'): (105, 645), ('B', 'C'): (70, 580), ('C', 'E'): (147, 615),
                    ('C', 'D'): (108, 545), ('E', 'F'): (180, 540), ('E', 'H'): (260, 580), ('D', 'F'): (125, 475),
                    ('F', 'G'): (182, 460), ('H', 'L'): (525, 520), ('H', 'I'): (340, 505), ('L', 'O'): (768, 470),
                    ('O', 'V'): (980, 425), ('G', 'J'): (187, 370), ('G', 'I'): (290, 442), ('J', 'K'): (325, 335),
                    ('K', 'N'): (485, 335), ('K', 'I'): (424, 434), ('J', 'M'): (205, 255), ('M', 'N'): (357, 228),
                    ('O', 'R'): (814, 365), ('V', 'X'): (1138, 330), ('X', 'Y'): (1132, 225), ('Y', 'Z'): (1126, 115),
                    ('N', 'Q'): (630, 286), ('Q', 'R'): (780, 305), ('R', 'T'): (841, 237), ('Q', 'T'): (765, 230),
                    ('T', 'U'): (848, 190), ('N', 'P'): (498, 220), ('R', 'X'): (960, 290), ('P', 'U'): (680, 180),
                    ('U', 'Y'): (960, 185), ('P', 'S'): (535, 110), ('U', 'W'): (810, 110), ('S', 'W'): (695, 50),
                    ('W', 'Z'): (950, 55)}
    
    for edge, position in box_positions.items():
        costboxes[edge] = draw_costbox(canvas, position)
    return costboxes


def draw_costbox(canvas, coords):
    pos_x, pos_y = coords
    w = 50
    h = 30
    canvas.create_rectangle(pos_x, pos_y, pos_x + w, pos_y + h, fill="", outline='', tags='cb_bg')
    text_object = canvas.create_text((pos_x + (pos_x + w)) / 2, (pos_y + (pos_y + h)) / 2, text='', font=("Arial Bold", 8), fill='', tags='cb_txt')
    return text_object

#endregion


#region SHOW/HIDE

def show_costs(canvas):
    cost_boxes = canvas.find_withtag("cb_bg")
    cost_texts = canvas.find_withtag("cb_txt")
    for box in cost_boxes:
        canvas.itemconfig(box, fill='black')
    for text in cost_texts:
        canvas.itemconfig(text, fill='white')
    
    
def hide_costs(canvas):
    cost_boxes = canvas.find_withtag("cb_bg")
    cost_texts = canvas.find_withtag("cb_txt")
    for box in cost_boxes:
        canvas.itemconfig(box, fill='')
    for text in cost_texts:
        canvas.itemconfig(text, fill='')
        
        
def show_path_description(path_summary_label, text_box, show_h_values):
    path_summary_label.config(fg="black", text=f"Path summary: {alg.source} > {alg.dest}")
    # Insert text with tags
    text_box.config(state="normal")
    text_box.insert("end", f"Total cost: {alg.path[-1].g}\n\n", "bold")
    for path_node in alg.path:
        # Add path node
        text_box.insert("end", f"Node {path_node.state}\n", "path")
        if show_h_values:
            text_box.insert("end", f"g({path_node.state}): {path_node.g}    h({path_node.state}): {path_node.h}\n\n", "body")
        else:
            text_box.insert("end", f"g({path_node.state}): {path_node.g}\n\n", "body")
        
    # List explored nodes
    if len(alg.explored_nodes) > 0:
        text_box.insert("end", "\nOther explored nodes\n\n", "bold")
    for exp_node in alg.explored_nodes:
        if exp_node not in alg.path:
            text_box.insert("end", f"Node {exp_node.state}\n", "exp")
            if show_h_values:
                text_box.insert("end", f"g({exp_node.state}): {exp_node.g}    h({exp_node.state}): {exp_node.h}\n\n", "body")
            else:
                text_box.insert("end", f"g({exp_node.state}): {exp_node.g}\n\n", "body")
                    
    # Explored but not used 
    text_box.config(state="disabled") # Read only
    
    
def hide_path_description(path_summary_label, text_box, frame_bg):
    path_summary_label.config(fg=frame_bg, text='')
    # Clear the textbox
    text_box.config(state="normal")
    text_box.delete(1.0, "end")
    text_box.config(state="disabled") # Read only
    

def show_efficiency(efficiency_label, runtime):
    efficiency = int((len(alg.path) / len(alg.explored_nodes)) * 100)
    colour = "red" if efficiency < 50 else ("black" if efficiency < 75 else "green")
    efficiency_label.config(text=f"Efficiency: {efficiency}%  Runtime: {runtime}s", fg=colour)
    

def show_admissibility(admissibiity_label):
    admissible, node1 = alg.check_admissibility()
    consistent, node2 = alg.check_consistency()
    if not admissible and not consistent:
        admissibiity_label.config(text=f"Inadmissable at {node1}. Inconsistent at {node2}.", fg="red")
    elif admissible and consistent:
        admissibiity_label.config(text=f"Admissible and consistent", fg="green")
    else:
        admissibiity_label.config(text=f"Admissible. Inconsistent at {node2}.", fg="orange")

#endregion


#region UTILITIES

# Function to scale coordinates to fit the canvas
def scale_coordinates(coords, min_lat, max_lat, min_lon, max_lon):
    latitude, longitude = coords
    # Scale the coordinates to fit on the canvas
    scaled_x = (longitude - min_lon) / (max_lon - min_lon) * 1050  # Width of the canvas
    scaled_y = (max_lat - latitude) / (max_lat - min_lat) * 580  # Height of the canvas

    return scaled_x + 85, scaled_y + 70

#endregion


#region INPUT

def on_node_click(node, ui_elements):
    """Called when node object is clicked"""
    canvas = ui_elements['canvas']
    edge_colours = ui_elements['edge_colours']
    node_objects = ui_elements['node_objects']
    # Set start point
    if ui_state.state == 0:
        ui_state.source = node
        canvas.itemconfig(node_objects[node], fill='dodgerblue4')
        ui_state.next_state()
    # Set end point
    elif ui_state.state == 1:
        ui_state.dest = node
        canvas.itemconfig(node_objects[node], fill='dodgerblue4')
    
        # Find the path
        selected_s = ui_elements['s_combobox'].current()
        selected_h = ui_elements['h_combobox'].current()
        selected_c = ui_elements['c_combobox'].current()
        alg.set_search_type(selected_s)
        alg.set_heuristic(selected_h)
        alg.set_cost_function(selected_c)
        alg.set_problem(ui_state.source, ui_state.dest)
        problem = alg.problem
        start = time.time()
        alg.run_search()
        explored = alg.explored_nodes
        end = time.time()
        if selected_s == 0:
            print(f"Admissible: {alg.check_admissibility()}")
            print(f"Consistency: {alg.check_consistency()}")
        runtime = math.floor((end - start) * 10000) / 10000
        path = alg.path
        
        for edge, costbox in ui_elements['costboxes'].items():
            a, b = edge
            ab_cost = problem.graph.graph_dict[a][b]
            ba_cost = problem.graph.graph_dict[b][a]
            canvas.itemconfig(costbox, text=f"{a}{b}: {ab_cost}\n{b}{a}: {ba_cost}")
        
        # Mark explored nodes
        for exp_node in explored:
            canvas.itemconfig(node_objects[exp_node.state], fill='cadetblue')
        
        for trail_node in path:
            canvas.itemconfig(node_objects[trail_node.state], fill='dodgerblue4')
            
        path_node_values = [node.state for node in alg.path] 
        
        adjusted_path = [(min(a, b), max(a, b)) for a, b in zip(path_node_values, path_node_values[1:])]
        for n1, n2 in edge_colours.keys():
            if (n1, n2) in adjusted_path:
                canvas.itemconfig(ui_elements['edge_objects'][(n1, n2)], fill='dodgerblue4')
        
        # Show path description
        if selected_s == 0: show_h_values = True
        else: show_h_values = False 
        show_path_description(ui_elements['path_summary_label'], ui_elements['text_box'], show_h_values)
        
        # Show costs
        if ui_elements['show_costs_ticked'].get(): show_costs(canvas)
        
        # Show efficiency
        show_efficiency(ui_elements['efficiency_label'], runtime)
        
        # Show admissibility
        if selected_s == 0:
            show_admissibility(ui_elements['admissibility_label'])
        
        ui_state.next_state()
    # Start again
    elif ui_state.state == 2:
        clear_map(ui_elements)


def on_cost_toggle(canvas, show_costs_ticked):
    show = show_costs_ticked.get()
    if show: show_costs(canvas)
    else: hide_costs(canvas)
    

def on_search_change(s_combobox, h_combobox):
    value = s_combobox.current()
    print(value)
    if value == 1:
        h_combobox.config(state='disabled')
    else:
        h_combobox.config(state='readonly')


def clear_map(ui_elements):
    if ui_state.state != 2: return
    canvas = ui_elements['canvas']
    edge_objects = ui_elements['edge_objects']
    edge_colours = ui_elements['edge_colours']
    node_objects = ui_elements['node_objects']
    hide_costs(canvas)
    hide_path_description(ui_elements['path_summary_label'], ui_elements['text_box'], ui_elements['frame_bg'])
    for trail_node in alg.path:
        canvas.itemconfig(node_objects[trail_node.state], fill='gray30')
    for exp_node in alg.explored_nodes:
        canvas.itemconfig(node_objects[exp_node.state], fill='gray30')
    for edge in edge_objects:
        canvas.itemconfig(edge_objects[edge], fill=edge_colours[(edge)])
    ui_elements['efficiency_label'].config(text="Efficiency: N/A", fg="black")
    ui_elements['admissibility_label'].config(text=" ", fg="black")
    ui_state.reset_state()
    alg.clear_path()

#endregion


if __name__ == '__main__':
    # Set up the window
    root = tk.Tk()
    root.title("Pathfinding Problem")
    root.geometry('1500x800')
    root.resizable(False, False)
    create_ui(root)
    ui_state = UI_State()
    root.mainloop()