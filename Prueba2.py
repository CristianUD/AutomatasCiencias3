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

        state_btn = ttk.Button(toolbar, text="Add State", command=self.enable_state_mode)
        state_btn.pack(side='left', padx=5)

        transition_btn = ttk.Button(toolbar, text="Add Transition", command=self.enable_transition_mode)
        transition_btn.pack(side='left', padx=5)

        convert_dfa_btn = ttk.Button(toolbar, text="Convert to DFA", command=self.convert_to_dfa)
        convert_dfa_btn.pack(side='left', padx=5)

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

    def draw_transition(self, from_state, to_state, symbol):
        from_coords = self.canvas.coords(from_state)
        to_coords = self.canvas.coords(to_state)
        from_x = (from_coords[0] + from_coords[2]) / 2
        from_y = (from_coords[1] + from_coords[3]) / 2
        to_x = (to_coords[0] + to_coords[2]) / 2
        to_y = (to_coords[1] + to_coords[3]) / 2
        angle = math.atan2(to_y - from_y, to_x - from_x)
        from_edge_x = from_x + self.state_radius * math.cos(angle)
        from_edge_y = from_y + self.state_radius * math.sin(angle)
        to_edge_x = to_x - self.state_radius * math.cos(angle)
        to_edge_y = to_y - self.state_radius * math.sin(angle)
        self.canvas.create_line(
            from_edge_x, from_edge_y, to_edge_x, to_edge_y,
            arrow=tk.LAST, smooth=True
        )
        mid_x = (from_edge_x + to_edge_x) / 2
        mid_y = (from_edge_y + to_edge_y) / 2
        self.canvas.create_text(mid_x, mid_y, text=symbol, font=("Arial", 10))

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

def main():
    selector = AutomatonTypeSelector()
    if selector.selected_type:
        root = tk.Tk()
        app = AutomataGUI(root, selector.selected_type)
        root.mainloop()

if __name__ == "__main__":
    main()
