import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import math

class AutomatonTypeSelector:
    def __init__(self):
        self.selected_type = None

        self.dialog = tk.Tk()
        self.dialog.title("Seleccione el Automata a Convertir")

        window_width = 300
        window_height = 150
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.dialog.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        label = ttk.Label(self.dialog, text="Seleccione el autómata que quiere convertir:", padding=20)
        label.pack()

        btn_nfa = ttk.Button(self.dialog, text="AFN (sin transiciones λ)",
                             command=lambda: self.select_type("NFA"))
        btn_nfa.pack(pady=5)

        btn_enfa = ttk.Button(self.dialog, text="AFN con transiciones λ",
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

    def has_transition_with_symbol(self, target_state, symbol):

        if symbol in self.transitions:
            return target_state in self.transitions[symbol]
        return False

    def has_transition_to(self, target_state):

        # Check each list of destination states for all symbols
        for destinations in self.transitions.values():
            for dest in destinations:
                if dest.state_id == target_state:
                    return True
        return False

class Automaton:
    def __init__(self):
        self.states = {}  # {state_id: State}
        self.start_state = None

    def add_state(self, state_id, is_accepting=False):
        if state_id in self.states:
            raise ValueError(f"Estado {state_id} ya existe!")
        state = State(state_id, is_accepting)
        self.states[state_id] = state
        return state

    def set_start_state(self, state_id):
        if state_id not in self.states:
            raise ValueError(f"Estado {state_id} no existe!")
        self.start_state = self.states[state_id]

    def add_transition(self, from_state_id, symbol, to_state_id):
        if from_state_id not in self.states or to_state_id not in self.states:
            raise ValueError("Ambos estados deben existir para poder hacer una transición.")
        from_state = self.states[from_state_id]
        to_state = self.states[to_state_id]
        from_state.add_transition(symbol, to_state)

    def get_epsilon_closure(self, state_id):
        if state_id not in self.states:
            raise ValueError(f"State {state_id} does not exist!")
        return self.states[state_id].get_epsilon_closure()

    def to_dfa(self):
        if not self.start_state:
            raise ValueError("The automaton has no start state defined.")

        dfa = Automaton()
        start_closure = self.start_state.get_epsilon_closure()
        start_state_id = self._get_state_id(start_closure)
        dfa.add_state(start_state_id, any(s.is_accepting for s in start_closure))
        dfa.set_start_state(start_state_id)

        unprocessed = [start_closure]
        processed = {}

        while unprocessed:
            current_closure = unprocessed.pop()
            current_state_id = self._get_state_id(current_closure)
            processed[current_state_id] = current_closure

            transitions = self._get_combined_transitions(current_closure)
            for symbol, target_closure in transitions.items():
                target_state_id = self._get_state_id(target_closure)
                if target_state_id not in dfa.states:
                    dfa.add_state(target_state_id, any(s.is_accepting for s in target_closure))
                    unprocessed.append(target_closure)
                dfa.add_transition(current_state_id, symbol, target_state_id)

        return dfa

    def _get_state_id(self, closure):
        return "{" + ",".join(sorted(s.state_id for s in closure)) + "}"

    def _get_combined_transitions(self, closure):
        transitions = {}
        for state in closure:
            for symbol, targets in state.transitions.items():
                if symbol == "λ":
                    continue
                if symbol not in transitions:
                    transitions[symbol] = set()
                for target in targets:
                    transitions[symbol].update(target.get_epsilon_closure())
        return transitions
    def convert_to_nfa(self):
        """Convert the automaton to one without ε-transitions."""
        # Create a new automaton to store the result
        new_automaton = Automaton()

        # Copy states to the new automaton
        for state_id, state in self.states.items():
            new_automaton.add_state(state_id, is_accepting=state.is_accepting)

        # Copy start state
        if self.start_state:
            new_automaton.set_start_state(self.start_state.state_id)

        # Compute transitions for the new automaton
        for state_id, state in self.states.items():
            # Get the epsilon closure for the current state
            epsilon_closure = self.get_epsilon_closure(state_id)

            # For each symbol (other than ε), aggregate transitions
            for closure_state in epsilon_closure:
                for symbol, target_states in closure_state.transitions.items():
                    if symbol != "λ":  # Skip ε-transitions
                        for target_state in target_states:
                            new_automaton.add_transition(state_id, symbol, target_state.state_id)

            # Update accepting states
            if any(closure_state.is_accepting for closure_state in epsilon_closure):
                new_automaton.states[state_id].is_accepting = True

        return new_automaton

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

        self.state_counter = 1  # Start with q1 since q0 is reserved for the initial state
        self.state_radius = 30
        self.loop_radius = 20

        self.drawing_transition = False
        self.transition_start = None

        self.create_toolbar()
        self.bind_events()

        # Create the initial state q0
        self.create_initial_state()

    def create_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side='top', fill='x')

        state_btn = ttk.Button(toolbar, text="Agregar estado", command=self.enable_state_mode)
        state_btn.pack(side='left', padx=5)

        transition_btn = ttk.Button(toolbar, text="Agregar Transiciones", command=self.enable_transition_mode)
        transition_btn.pack(side='left', padx=5)
        if self.automaton_type== "NFA":

            convert_dfa_btn = ttk.Button(toolbar, text="Convertir a AFD", command=self.convert_to_dfa)
            convert_dfa_btn.pack(side='left', padx=5)
        else:
            convert_nfa_btn = ttk.Button(toolbar, text="Convertir a AFN", command=self.convert_to_nfa)
            convert_nfa_btn.pack(side='left', padx=5)
            closure_btn = ttk.Button(toolbar, text="Obtener λ-clausura", command=self.compute_epsilon_closure)
            closure_btn.pack(side='left', padx=5)

        clear_btn = ttk.Button(toolbar, text="Clear All", command=self.clear_canvas)
        clear_btn.pack(side='left', padx=5)



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

    def create_initial_state(self):
        self.automaton.add_state("q0")
        self.automaton.set_start_state("q0")
        self.draw_state(100, 100, "q0", False, is_initial=True)

    def create_state(self, event):
        x, y = event.x, event.y
        for state_id, state in self.automaton.states.items():
            coords = self.canvas.coords(state_id)
            if not coords:
                continue
            x1, y1, x2, y2 = coords
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            if math.hypot(x - center_x, y - center_y) <= self.state_radius:
                state.is_accepting = not state.is_accepting
                self.draw_state(center_x, center_y, state_id, state.is_accepting)
                return

        state_id = f"q{self.state_counter}"
        new_state = self.automaton.add_state(state_id)
        self.state_counter += 1
        self.draw_state(x, y, state_id, new_state.is_accepting)

    def draw_state(self, x, y, state_id, is_accepting, is_initial=False):
        self.canvas.delete(state_id)
        self.canvas.create_oval(
            x - self.state_radius, y - self.state_radius,
            x + self.state_radius, y + self.state_radius,
            tags=(state_id, "state"),
            width=2
        )
        if is_accepting:
            self.canvas.create_oval(
                x - self.state_radius + 5, y - self.state_radius + 5,
                x + self.state_radius - 5, y + self.state_radius - 5,
                tags=(state_id, "state"),
                width=2
            )
        if is_initial:
            self.canvas.create_line(
                x - self.state_radius - 20, y,
                x - self.state_radius, y,
                arrow=tk.LAST,
                width=2
            )
        self.canvas.create_text(
            x, y, text=state_id, tags=(state_id, "state"), font=("Arial", 12)
        )

    def handle_transition_click(self, event):
        x, y = event.x, event.y
        clicked_state = None
        for state_id, state in self.automaton.states.items():
            coords = self.canvas.coords(state_id)
            if not coords:
                continue
            x1, y1, x2, y2 = coords
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            if math.hypot(x - center_x, y - center_y) <= self.state_radius:
                clicked_state = state_id
                break

        if clicked_state:
            if not self.transition_start:
                self.transition_start = clicked_state
            else:
                self.prompt_transition_symbol(clicked_state)

    def prompt_transition_symbol(self, target_state):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Transition")

        label = ttk.Label(dialog, text="Enter the transition symbol:")
        label.pack(pady=5)

        entry = ttk.Entry(dialog)
        entry.pack(pady=5)

        def add_lambda():
            entry.delete(0, tk.END)
            entry.insert(0, "λ")

        lambda_btn = ttk.Button(dialog, text="λ", command=add_lambda)
        lambda_btn.pack(pady=5)

        def confirm():
            symbol = entry.get()
            if symbol:
                self.automaton.add_transition(self.transition_start, symbol, target_state)
                self.draw_transition(self.transition_start, target_state, symbol)
            self.transition_start = None
            dialog.destroy()

        def cancel():
            self.transition_start = None
            dialog.destroy()

        confirm_btn = ttk.Button(dialog, text="OK", command=confirm)
        confirm_btn.pack(side="left", padx=5)

        cancel_btn = ttk.Button(dialog, text="Cancel", command=cancel)
        cancel_btn.pack(side="right", padx=5)

        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

    def draw_transition(self, from_state, to_state, symbol, is_reverse=False):
        """
        Draw a transition arrow with a symbol between two states.
        is_reverse parameter is used to offset bidirectional transitions.
        """        # Get the bounding boxes of the states
        if self.automaton.states[to_state].has_transition_to(from_state):
            is_reverse = True
        from_coords = self.canvas.coords(from_state)  # [x1, y1, x2, y2]
        to_coords = self.canvas.coords(to_state)  # [x1, y1, x2, y2]


        # Calculate the centers of the states
        from_x = (from_coords[0] + from_coords[2]) / 2
        from_y = (from_coords[1] + from_coords[3]) / 2
        to_x = (to_coords[0] + to_coords[2]) / 2
        to_y = (to_coords[1] + to_coords[3]) / 2

        # Handle self-transition (same state)
        if from_state == to_state:
            # Create a circular arc above the state
            center_x = from_x
            center_y = from_y
            radius = self.state_radius * 1.5

            # Calculate points for a bezier curve to create the loop
            # Start point - slightly above and to the left of the state
            start_x = center_x - self.state_radius * 0.5
            start_y = center_y - self.state_radius

            # End point - slightly above and to the right of the state
            end_x = center_x + self.state_radius * 0.5
            end_y = center_y - self.state_radius

            # Control points - to create the curved loop
            ctrl1_x = start_x - radius
            ctrl1_y = start_y - radius
            ctrl2_x = end_x + radius
            ctrl2_y = end_y - radius

            # Draw the curved line with an arrow
            self.canvas.create_line(
                start_x, start_y,
                ctrl1_x, ctrl1_y,
                ctrl2_x, ctrl2_y,
                end_x, end_y,
                smooth=True,
                splinesteps=36,
                arrow=tk.LAST
            )

            # Place the symbol above the loop
            self.canvas.create_text(
                center_x,
                center_y - radius - self.state_radius,
                text=symbol,
                font=("Arial", 10)
            )
        else:
            # Calculate the angle of the line
            angle = math.atan2(to_y - from_y, to_x - from_x)

            # Offset for bidirectional transitions
            offset = 15 if is_reverse else 0
            perpendicular_angle = angle + math.pi / 2
            offset_x = offset * math.cos(perpendicular_angle)
            offset_y = offset * math.sin(perpendicular_angle)

            # Adjust the start and end points to be at the edge of the circles
            from_edge_x = from_x + self.state_radius * math.cos(angle)
            from_edge_y = from_y + self.state_radius * math.sin(angle)
            to_edge_x = to_x - self.state_radius * math.cos(angle)
            to_edge_y = to_y - self.state_radius * math.sin(angle)

            # Apply the offset
            from_edge_x += offset_x
            from_edge_y += offset_y
            to_edge_x += offset_x
            to_edge_y += offset_y

            # Draw the transition arrow
            self.canvas.create_line(
                from_edge_x, from_edge_y, to_edge_x, to_edge_y,
                arrow=tk.LAST, smooth=True
            )

            # Draw the symbol near the middle of the line
            mid_x = (from_edge_x + to_edge_x) / 2
            mid_y = (from_edge_y + to_edge_y) / 2
            self.canvas.create_text(
                mid_x + offset_x / 2,
                mid_y + offset_y / 2,
                text=symbol,
                font=("Arial", 10)
            )

    def clear_canvas(self):
        self.canvas.delete("all")
        self.automaton = Automaton()
        self.state_counter = 1  # Reset counter but keep q0 as the initial state
        self.create_initial_state()

    def compute_epsilon_closure(self):
        state_id = simpledialog.askstring("Epsilon Closure", "Enter the state ID:")
        if state_id in self.automaton.states:
            closure = self.automaton.get_epsilon_closure(state_id)
            closure_ids = {state.state_id for state in closure}
            messagebox.showinfo("Epsilon Closure", f"Epsilon closure of {state_id}: {', '.join(closure_ids)}")
        else:
            messagebox.showerror("Error", f"State {state_id} does not exist.")

    def convert_to_dfa(self):
        try:
            dfa = self.automaton.to_dfa()
            self.clear_canvas()
            for state_id, state in dfa.states.items():
                self.create_state_at_fixed_position(state_id, state.is_accepting)
            for state_id, state in dfa.states.items():
                for symbol, targets in state.transitions.items():
                    for target in targets:
                        self.draw_transition(state_id, target.state_id, symbol)
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def create_state_at_fixed_position(self, state_id, is_accepting):
        x = 100 + (self.state_counter % 5) * 150
        y = 100 + (self.state_counter // 5) * 150
        self.automaton.add_state(state_id, is_accepting)
        self.draw_state(x, y, state_id, is_accepting)
        self.state_counter += 1

    def convert_to_nfa(self):
        """Convert the automaton to an NFA and display it with a circular layout."""
        try:
            # Convert the automaton to an NFA
            nfa = self.automaton.convert_to_nfa()

            # Clear the canvas and reset the automaton
            self.clear_canvas()
            self.automaton = Automaton()


            # Get the canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Calculate the center and radius for the circular layout
            center_x = canvas_width / 2
            center_y = canvas_height / 2
            radius = min(canvas_width, canvas_height) / 3  # Adjust radius as needed

            # Calculate positions for the states
            num_states = len(nfa.states)
            angle_step = 2 * math.pi / num_states

            state_positions = {}
            for i, (state_id, state) in enumerate(nfa.states.items()):
                angle = i * angle_step
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                state_positions[state_id] = (x, y)

                # Create the state on the canvas
                self.create_state_at_fixed_position(state_id, state.is_accepting)

            # Draw the transitions
            for state_id, state in nfa.states.items():
                for symbol, targets in state.transitions.items():
                    for target in targets:
                        from_x, from_y = state_positions[state_id]
                        to_x, to_y = state_positions[target.state_id]
                        self.draw_transition(state_id, target.state_id, symbol)

            print("Conversion completed")

        except ValueError as e:
            messagebox.showerror("Error", str(e))





def main():
    selector = AutomatonTypeSelector()
    if selector.selected_type:
        root = tk.Tk()
        app = AutomataGUI(root, selector.selected_type)
        root.mainloop()




if __name__ == "__main__":
    main()
