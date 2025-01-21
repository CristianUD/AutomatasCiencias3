import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import math

class AutomatonTypeSelector:
    def __init__(self):
        self.selected_type = None

        self.dialog = tk.Tk()
        self.dialog.title("Select Automaton Type")

        window_width = 300
        window_height = 150
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.dialog.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        label = ttk.Label(self.dialog, text="Choose the type of automaton:", padding=20)
        label.pack()

        btn_nfa = ttk.Button(self.dialog, text="NFA (No ε-transitions)",
                             command=lambda: self.select_type("NFA"))
        btn_nfa.pack(pady=5)

        btn_enfa = ttk.Button(self.dialog, text="ε-NFA",
                              command=lambda: self.select_type("eNFA"))
        btn_enfa.pack(pady=5)

        self.dialog.mainloop()

    def select_type(self, automaton_type):
        self.selected_type = automaton_type
        self.dialog.destroy()

class State:
    def __init__(self, state_id, is_accepting=False):
        self.state_id = state_id
        self.is_accepting = is_accepting
        self.transitions = {}  # {symbol: [State, State, ...]}

    def add_transition(self, symbol, target_state):
        if symbol not in self.transitions:
            self.transitions[symbol] = []
        self.transitions[symbol].append(target_state)

    def get_epsilon_closure(self):
        closure = set()
        stack = [self]
        while stack:
            current = stack.pop()
            if current not in closure:
                closure.add(current)
                for next_state in current.transitions.get("λ", []):
                    stack.append(next_state)
        return closure

    def __repr__(self):
        return f"State({self.state_id}, accepting={self.is_accepting})"


class Automaton:
    def __init__(self):
        self.states = {}  # {state_id: State}
        self.start_state = None

    def add_state(self, state_id, is_accepting=False):
        if state_id in self.states:
            raise ValueError(f"State {state_id} already exists!")
        state = State(state_id, is_accepting)
        self.states[state_id] = state
        return state

    def set_start_state(self, state_id):
        if state_id not in self.states:
            raise ValueError(f"State {state_id} does not exist!")
        self.start_state = self.states[state_id]

    def add_transition(self, from_state_id, symbol, to_state_id):
        if from_state_id not in self.states or to_state_id not in self.states:
            raise ValueError("Both states must exist to add a transition.")
        from_state = self.states[from_state_id]
        to_state = self.states[to_state_id]
        from_state.add_transition(symbol, to_state)

    def get_epsilon_closure(self, state_id):
        if state_id not in self.states:
            raise ValueError(f"State {state_id} does not exist!")
        return self.states[state_id].get_epsilon_closure()

    def __repr__(self):
        return f"Automaton(States: {list(self.states.keys())})"


class AutomataGUI:
    def __init__(self, root, automaton_type):
        self.root = root
        self.root.title(f"Automata Designer - {automaton_type}")
        self.automaton = Automaton()
        self.automaton_type = automaton_type

        # Canvas setup
        self.canvas = tk.Canvas(root, width=800, height=600, bg='white')
        self.canvas.pack(expand=True, fill='both')

        self.state_counter = 0
        self.state_radius = 30
        self.loop_radius = 20

        self.drawing_transition = False
        self.transition_start = None

        self.create_toolbar()
        self.bind_events()

    def create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side='top', fill='x')

        state_btn = ttk.Button(toolbar, text="Add State", command=self.enable_state_mode)
        state_btn.pack(side='left', padx=5)

        transition_btn = ttk.Button(toolbar, text="Add Transition", command=self.enable_transition_mode)
        transition_btn.pack(side='left', padx=5)

        clear_btn = ttk.Button(toolbar, text="Clear All", command=self.clear_canvas)
        clear_btn.pack(side='left', padx=5)

        closure_btn = ttk.Button(toolbar, text="Compute ε-Closure", command=self.compute_epsilon_closure)
        closure_btn.pack(side='left', padx=5)

    def bind_events(self):
        self.canvas.bind("<Button-1>", self.handle_click)

    def enable_state_mode(self):
        self.drawing_transition = False
        self.transition_start = None

    def enable_transition_mode(self):
        self.drawing_transition = True

    def handle_click(self, event):
        if not self.drawing_transition:
            self.create_state(event)
        else:
            self.handle_transition_click(event)

    def create_state(self, event):
        """Create a new state or toggle the acceptance status of an existing state."""
        x, y = event.x, event.y

        # Check if clicking on an existing state
        for state_id, state in self.automaton.states.items():
            coords = self.canvas.coords(state_id)  # [x1, y1, x2, y2]
            if not coords:
                continue
            x1, y1, x2, y2 = coords

            # Calculate the center of the state
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            # Check if the click is within the state radius
            if math.hypot(x - center_x, y - center_y) <= self.state_radius:
                # Toggle acceptance status
                state.is_accepting = not state.is_accepting
                self.draw_state(center_x, center_y, state_id, state.is_accepting)
                return

        # If no state was clicked, create a new state
        state_id = f"q{self.state_counter}"
        new_state = self.automaton.add_state(state_id)
        self.state_counter += 1
        self.draw_state(x, y, state_id, new_state.is_accepting)

    def draw_state(self, x, y, state_id, is_accepting):
        """Draw a state circle with its label."""
        # Delete any existing drawing for this state
        self.canvas.delete(state_id)

        # Draw the outer circle
        self.canvas.create_oval(
            x - self.state_radius, y - self.state_radius,
            x + self.state_radius, y + self.state_radius,
            tags=(state_id, "state"),
            width=2
        )

        # Draw an inner circle for accepting states
        if is_accepting:
            self.canvas.create_oval(
                x - self.state_radius + 5, y - self.state_radius + 5,
                x + self.state_radius - 5, y + self.state_radius - 5,
                tags=(state_id, "state"),
                width=2
            )

        # Add state label
        self.canvas.create_text(
            x, y, text=state_id, tags=(state_id, "state"), font=("Arial", 12)
        )

    def handle_transition_click(self, event):
        x, y = event.x, event.y  # Click position
        clicked_state = None

        # Iterate through states to detect which one was clicked
        for state_id, state in self.automaton.states.items():
            # Get bounding box of the state
            coords = self.canvas.coords(state_id)  # [x1, y1, x2, y2]
            if not coords:  # Skip if the state has no drawn representation
                continue
            x1, y1, x2, y2 = coords

            # Calculate the center of the state
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            # Check if the click is within the state radius
            if math.hypot(x - center_x, y - center_y) <= self.state_radius:
                clicked_state = state_id
                break

        if clicked_state:
            if not self.transition_start:
                # Start transition from the clicked state
                self.transition_start = clicked_state
            else:
                # Finish transition by connecting the start state to the clicked state
                symbol = simpledialog.askstring("Transition Symbol", "Enter the transition symbol:")
                if symbol:
                    self.automaton.add_transition(self.transition_start, symbol, clicked_state)
                    self.draw_transition(self.transition_start, clicked_state, symbol)
                self.transition_start = None  # Reset for the next transition

    def draw_transition(self, from_state, to_state, symbol):
        """Draw a transition arrow with a symbol between two states."""
        # Get the bounding boxes of the states
        from_coords = self.canvas.coords(from_state)  # [x1, y1, x2, y2]
        to_coords = self.canvas.coords(to_state)  # [x1, y1, x2, y2]

        # Calculate the centers of the states
        from_x = (from_coords[0] + from_coords[2]) / 2
        from_y = (from_coords[1] + from_coords[3]) / 2
        to_x = (to_coords[0] + to_coords[2]) / 2
        to_y = (to_coords[1] + to_coords[3]) / 2

        # Calculate the angle of the line
        angle = math.atan2(to_y - from_y, to_x - from_x)

        # Adjust the start and end points to be at the edge of the circles
        from_edge_x = from_x + self.state_radius * math.cos(angle)
        from_edge_y = from_y + self.state_radius * math.sin(angle)
        to_edge_x = to_x - self.state_radius * math.cos(angle)
        to_edge_y = to_y - self.state_radius * math.sin(angle)

        # Draw the transition arrow
        self.canvas.create_line(
            from_edge_x, from_edge_y, to_edge_x, to_edge_y,
            arrow=tk.LAST, smooth=True
        )

        # Draw the symbol near the middle of the line
        mid_x = (from_edge_x + to_edge_x) / 2
        mid_y = (from_edge_y + to_edge_y) / 2
        self.canvas.create_text(mid_x, mid_y, text=symbol, font=("Arial", 10))
    def clear_canvas(self):
        self.canvas.delete("all")
        self.automaton = Automaton()
        self.state_counter = 0

    def compute_epsilon_closure(self):
        """Compute and display the epsilon closure of a state."""
        state_id = simpledialog.askstring("Epsilon Closure", "Enter the state ID:")

        if state_id in self.automaton.states:
            # Get the epsilon closure as a set of states
            closure = self.automaton.get_epsilon_closure(state_id)

            # Extract the state IDs from the closure set
            closure_ids = {state.state_id for state in closure}

            # Display the state IDs in a messagebox
            messagebox.showinfo("Epsilon Closure", f"Epsilon closure of {state_id}: {', '.join(closure_ids)}")
        else:
            messagebox.showerror("Error", f"State {state_id} does not exist.")
def main():
    # First show the type selector
    selector = AutomatonTypeSelector()

    # If user selected a type (didn't just close the window)
    if selector.selected_type:
        root = tk.Tk()
        app = AutomataGUI(root, selector.selected_type)
        root.mainloop()


if __name__ == "__main__":
    main()