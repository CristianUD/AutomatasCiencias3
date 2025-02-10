import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import ExpresionesRegulares
import math
import graphviz



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
    """
    def rename_states_sequentially(self):
        if not self.states:
            return  # No states to rename

        # Get the order of states as per insertion order
        ordered_states = list(self.states.values())

        # Generate new names and update each state's ID
        new_states = {}
        for index, state in enumerate(ordered_states):
            new_name = f'q{index}'
            state.state_id = new_name
            new_states[new_name] = state

        # Update the automaton's states dictionary
        self.states = new_states
        """

    def rename_states_sequentially(self):
        if not self.states:
            return  # No hay estados para renombrar

        # Obtener el estado inicial
        estado_inicial = self.start_state

        # Crear una lista de estados, asegurando que el estado inicial esté primero
        ordered_states = [estado_inicial]  # El estado inicial va primero
        for estado in self.states.values():
            if estado != estado_inicial:  # Evitar duplicar el estado inicial
                ordered_states.append(estado)

        # Generar nuevos nombres y actualizar cada estado
        new_states = {}
        for index, state in enumerate(ordered_states):
            new_name = f'q{index}'  # q0, q1, q2, ...
            state.state_id = new_name
            new_states[new_name] = state

        # Actualizar el diccionario de estados del autómata
        self.states = new_states

        # Asegurarse de que el estado inicial sea q0
        self.start_state = self.states['q0']
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
        dfa.rename_states_sequentially()
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
        new_automaton = Automaton()

        # Copy all states to the new automaton
        for state_id, state in self.states.items():
            new_automaton.add_state(state_id, is_accepting=state.is_accepting)

        # Set the start state
        if self.start_state:
            new_automaton.set_start_state(self.start_state.state_id)

        # For each state in the original automaton
        for state_id, state in self.states.items():
            # Compute the ε-closure of the current state
            epsilon_closure = self.get_epsilon_closure(state_id)

            # Aggregate transitions for all states in the ε-closure
            combined_transitions = {}
            for closure_state in epsilon_closure:
                for symbol, target_states in closure_state.transitions.items():
                    if symbol == "λ":
                        continue  # Skip ε-transitions
                    if symbol not in combined_transitions:
                        combined_transitions[symbol] = set()
                    # Add all states reachable from the ε-closure of target states
                    for target_state in target_states:
                        combined_transitions[symbol].update(target_state.get_epsilon_closure())

            # Add the aggregated transitions to the new automaton
            for symbol, target_states in combined_transitions.items():
                for target_state in target_states:
                    new_automaton.add_transition(state_id, symbol, target_state.state_id)

            # Update the accepting status of the state
            if any(closure_state.is_accepting for closure_state in epsilon_closure):
                new_automaton.states[state_id].is_accepting = True

        return new_automaton

    def construir_desde_postfix(self, postfix):
        """
        Construye un autómata finito no determinista (NFA) a partir de una expresión en postfix.

        Parámetros:
        - postfix: La expresión regular en notación postfix.

        Retorna:
        - El autómata construido.
        """
        pila = []
        contador_estados = 0

        for token in postfix:
            if token == '&':  # Concatenación
                nfa2 = pila.pop()  # Segundo autómata
                nfa1 = pila.pop()  # Primer autómata

                # Contar la cantidad de estados en nfa1



                # Fusionar los estados de nfa1 y nfa2 en el nuevo autómata
                for estado_id, estado in nfa2.states.items():
                    nfa1.add_state(estado_id,is_accepting=False)
                for estado_id, estado in nfa2.states.items():
                    for simbolo, destinos in estado.transitions.items():
                        for destino in destinos:
                            # Asegurarse de que el estado destino también esté renombrado
                            destino_id = destino.state_id
                            nfa1.add_transition(estado_id, simbolo, destino_id)

                # Conectar los estados finales de nfa1 al estado inicial de nfa2 usando transiciones lambda
                for estado in nfa1.states.values():
                    if estado.is_accepting:  # Si es un estado final de nfa1
                        estado.is_accepting = False  # Desmarcar como no aceptación
                        nfa1.add_transition(estado.state_id, "λ", nfa2.start_state.state_id)  # Transición lambda a nfa2
                for estado in nfa2.states.values():
                    if estado.is_accepting:
                        nfa1.states[estado.state_id].is_accepting = True
                # Actualizar el estado inicial y final del nuevo autómata
                nfa1.start_state = nfa1.start_state  # El estado inicial sigue siendo el de nfa1

                # Agregar el nuevo autómata a la pila
                pila.append(nfa1)

            elif token == '|':  # Unión
                nfa2 = pila.pop()
                nfa1 = pila.pop()
                # Contar la cantidad de estados en nfa1
                cantidad_estados_nfa1 = len(nfa1.states)+1

                # Renombrar los estados de nfa2 sumando la cantidad de estados de nfa1
                estados_renombrados_nfa2 = {}
                for estado_id, estado in nfa2.states.items():
                    nuevo_id = f"q{int(estado_id[1:]) + cantidad_estados_nfa1}"  # Renombrar el estado
                    estado.state_id = nuevo_id
                    estados_renombrados_nfa2[nuevo_id] = estado

                # Crear un nuevo autómata para la unión
                automata = Automaton()

                # 1. Copiar todos los estados de nfa1 al nuevo autómata
                for estado_id, estado in nfa1.states.items():
                    automata.add_state(estado_id, estado.is_accepting)

                # 2. Copiar todas las transiciones de nfa1 al nuevo autómata
                for estado_id, estado in nfa1.states.items():
                    for simbolo, destinos in estado.transitions.items():
                        for destino in destinos:
                            automata.add_transition(estado_id, simbolo, destino.state_id)

                # 3. Copiar todos los estados de nfa2 al nuevo autómata
                for estado_id, estado in estados_renombrados_nfa2.items():
                    automata.add_state(estado_id, estado.is_accepting)

                # 4. Copiar todas las transiciones de nfa2 al nuevo autómata
                for estado_id, estado in estados_renombrados_nfa2.items():
                    for simbolo, destinos in estado.transitions.items():
                        for destino in destinos:
                            automata.add_transition(estado_id, simbolo, destino.state_id)

                # Crear un nuevo estado inicial y final para la unión
                nuevo_inicio = State(f"q{len(automata.states)}")  # Nuevo estado inicial
               # nuevo_final = State(f"q{len(automata.states) + 1}", is_accepting=True)  # Nuevo estado final

                # Agregar los nuevos estados al autómata
                automata.add_state(nuevo_inicio.state_id)
                #automata.add_state(nuevo_final.state_id, is_accepting=True)

                # Establecer el nuevo estado inicial
                automata.set_start_state(nuevo_inicio.state_id)

                # Conectar el nuevo estado inicial a los estados iniciales de nfa1 y nfa2
                automata.add_transition(nuevo_inicio.state_id, "λ", nfa1.start_state.state_id)
                automata.add_transition(nuevo_inicio.state_id, "λ", nfa2.start_state.state_id)

                # Agregar el nuevo autómata a la pila
                pila.append(automata)

            elif token == '*':  # Clausura de Kleene
                nfa = pila.pop()
                for estado in nfa.states.values():
                    if estado.is_accepting:  # Si es un estado final
                        nfa.add_transition(estado.state_id, "λ", nfa.start_state.state_id)  # Transición lambda a inicio
                nfa.states.get(nfa.start_state.state_id).is_accepting = True
                # Agregar el nuevo autómata a la pila
                pila.append(nfa)

            else:  # Símbolo básico
                inicio = State(f"q{contador_estados}")
                contador_estados += 1
                final = State(f"q{contador_estados}", is_accepting=True)
                contador_estados += 1

                automata = Automaton()
                automata.add_state(inicio.state_id)
                automata.add_state(final.state_id, is_accepting=True)
                automata.set_start_state(inicio.state_id)
                automata.add_transition(inicio.state_id, token, final.state_id)

                pila.append(automata)

        # El NFA final es el último en la pila
        nfa_final = pila.pop()
        nfa_final.rename_states_sequentially()
        return nfa_final

    def __repr__(self):
        return f"Automaton(States: {list(self.states.keys())})"

class AutomataGUI:
    def __init__(self, root, automaton_type):
        self.root = root
        self.root.title(f"Automata Designer - {automaton_type}")
        self.automaton = Automaton()
        self.automaton_type = automaton_type
        self.style_buttons()

        # Canvas setup
        self.canvas = tk.Canvas(root, width=960, height=720, bg='white')
        self.canvas.pack(expand=True, fill='both')
        self.canvas.after(100, self.add_color_convention_legend)


        self.state_counter = 1  # Start with q1 since q0 is reserved for the initial state
        self.state_radius = 30
        self.loop_radius = 20

        self.drawing_transition = False
        self.transition_start = None

        self.create_toolbar()
        self.bind_events()

        # Create the initial state q0
        self.create_initial_state()

    def add_color_convention_legend(self):
        legend_x, legend_y = 10, self.canvas.winfo_height() - 90  # Bottom left
        padding = 5
        spacing = 30

        # Background box for better visibility
        self.canvas.create_rectangle(
            legend_x - padding, legend_y - padding,
            legend_x + 180, legend_y + 90,
            fill="white", outline="black", width=1
        )

        # Initial State
        self.canvas.create_oval(legend_x, legend_y, legend_x + 20, legend_y + 20, fill="green", width=2)
        self.canvas.create_text(legend_x + 40, legend_y + 10, text="Inicial", font=("Arial", 10), anchor="w")

        # Normal State
        legend_y += spacing
        self.canvas.create_oval(legend_x, legend_y, legend_x + 20, legend_y + 20, fill="blue", width=2)
        self.canvas.create_text(legend_x + 40, legend_y + 10, text="Normal", font=("Arial", 10), anchor="w")

        # Final State
        legend_y += spacing
        self.canvas.create_oval(legend_x, legend_y, legend_x + 20, legend_y + 20, fill="orange", width=2)
        self.canvas.create_text(legend_x + 40, legend_y + 10, text="Final", font=("Arial", 10), anchor="w")

    def style_buttons(self):
        style = ttk.Style()
        style.configure("TButton",
                        font=("Bahnschrift", 10, "bold"),
                        borderwidth=2,
                        foreground="black",
                        background="#b03737")  # Light green background
        style.map("TButton",
                  background=[("active", "#45a049")],  # Darker green when hovered
                  relief=[("pressed", "sunken")])  # Sunken effect when clicked

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

        clear_btn = ttk.Button(toolbar, text="Borrar todo", command=self.clear_canvas)
        clear_btn.pack(side='left', padx=5)
        
        back_btn = ttk.Button(toolbar, text="Volver al Menú Principal", command=self.go_back_to_main_menu)
        back_btn.pack(side='left', padx=5)




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
        fill_color = "light green" if is_initial else "#f9c989" if is_accepting else "light blue"
        self.canvas.create_oval(
            x - self.state_radius, y - self.state_radius,
            x + self.state_radius, y + self.state_radius,
            tags=(state_id, "state"),
            width=2, fill=fill_color
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
        font_style = ("Bahnschrift", 12, "italic") if is_accepting else ("Bahnschrift", 12)
        self.canvas.create_text(
            x, y, text=state_id, tags=(state_id, "state"), font=font_style
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
        dialog.title("agregar transición")

        label = ttk.Label(dialog, text="Ingrese el simbolo para transición:")
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

        cancel_btn = ttk.Button(dialog, text="Cancelar", command=cancel)
        cancel_btn.pack(side="right", padx=5)

        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

    def draw_transition(self, from_state, to_state, symbol):
        # Registro de transiciones entre pares de estados
        if not hasattr(self, "transition_counts"):
            self.transition_counts = {}

        pair = (from_state, to_state)
        if pair not in self.transition_counts:
            self.transition_counts[pair] = 0

        self.transition_counts[pair] += 1
        count = self.transition_counts[pair]

        from_coords = self.canvas.coords(from_state)  # [x1, y1, x2, y2]
        to_coords = self.canvas.coords(to_state)  # [x1, y1, x2, y2]
        from_x = (from_coords[0] + from_coords[2]) / 2
        from_y = (from_coords[1] + from_coords[3]) / 2
        to_x = (to_coords[0] + to_coords[2]) / 2
        to_y = (to_coords[1] + to_coords[3]) / 2

        # Calcula el ángulo de la línea y ajusta la posición
        angle = math.atan2(to_y - from_y, to_x - from_x)
        offset_distance = 10 * count  # Ajusta el desplazamiento según la cantidad de transiciones
        offset_x = offset_distance * math.cos(angle + math.pi / 2)
        offset_y = offset_distance * math.sin(angle + math.pi / 2)
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
                font=("Bahnschrift", 10, "bold")
            )
        else:

            # Calcula los centros de los estados


            from_edge_x = from_x + self.state_radius * math.cos(angle)
            from_edge_y = from_y + self.state_radius * math.sin(angle)
            to_edge_x = to_x - self.state_radius * math.cos(angle)
            to_edge_y = to_y - self.state_radius * math.sin(angle)

            # Aplica el desplazamiento
            from_edge_x += offset_x
            from_edge_y += offset_y
            to_edge_x += offset_x
            to_edge_y += offset_y

            # Dibuja la flecha de transición
            self.canvas.create_line(
                from_edge_x, from_edge_y, to_edge_x, to_edge_y,
                arrow=tk.LAST, smooth=True, width=2
            )

            # Dibuja el símbolo cerca del medio de la línea
            mid_x = (from_edge_x + to_edge_x) / 2
            mid_y = (from_edge_y + to_edge_y) / 2
            self.canvas.create_text(
                mid_x + offset_x / 2,
                mid_y + offset_y / 2,
                text=symbol,
                font=("Bahnschrift", 10, "bold")
            )



    def clear_canvas(self):
        self.canvas.delete("all")
        self.automaton = Automaton()
        self.state_counter = 1
        self.create_initial_state()
        self.add_color_convention_legend()

    def clear_canvas_dfa(self):
        self.canvas.delete("all")
        self.automaton = Automaton()
        self.state_counter = 1
        self.add_color_convention_legend()
    """    
    def go_back_to_main_menu(self):
        self.root.destroy()
        main()
"""

    def compute_epsilon_closure(self):
        state_id = simpledialog.askstring("Lambda Clausura Individual", "Ingrese el ID del Estado :")
        if state_id in self.automaton.states:
            closure = self.automaton.get_epsilon_closure(state_id)
            closure_ids = {state.state_id for state in closure}
            messagebox.showinfo("Lambda Clausura", f"Lambda clausura de {state_id}: {', '.join(closure_ids)}")
        else:
            messagebox.showerror("Error", f"State {state_id} no existe.")

    def layout_states_circular(self, automaton):
        self.clear_canvas_dfa()
        self.automaton = automaton

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        center_x = canvas_width / 2
        center_y = canvas_height / 2
        radius = min(canvas_width, canvas_height) / 3  # Radio ajustable

        num_states = len(automaton.states)
        angle_step = 2 * math.pi / num_states

        state_positions = {}
        for i, (state_id, state) in enumerate(automaton.states.items()):
            angle = i * angle_step
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            state_positions[state_id] = (x, y)

            self.draw_state(x, y, state_id, state.is_accepting, is_initial=(state_id == automaton.start_state.state_id))

        for state_id, state in automaton.states.items():
            for symbol, targets in state.transitions.items():
                for target in targets:
                    from_x, from_y = state_positions[state_id]
                    to_x, to_y = state_positions[target.state_id]
                    self.draw_transition(state_id, target.state_id, symbol)

    def create_state_at_fixed_position(self, state_id, is_accepting):
        x = 100 + (self.state_counter % 5) * 150
        y = 100 + (self.state_counter // 5) * 150
        self.automaton.add_state(state_id, is_accepting)
        self.draw_state(x, y, state_id, is_accepting)
        self.state_counter += 1

    def convert_to_dfa(self):
        try:
            dfa = self.automaton.to_dfa()
            self.layout_states_circular(dfa)
            render_automaton(dfa)
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def convert_to_nfa(self):
        try:
            nfa = self.automaton.convert_to_nfa()
            self.layout_states_circular(nfa)
            render_automaton(nfa)
            print ("completado")
        except ValueError as e:
            messagebox.showerror("Error", str(e))





def render_automaton(automaton, filename="automaton"):
    dot = graphviz.Digraph(format="png")

    # Mark accepting states with a double circle
    for state_id, state in automaton.states.items():
        shape = "doublecircle" if state.is_accepting else "circle"
        dot.node(state_id, shape=shape, label=state_id)

    # Add transitions
    for state_id, state in automaton.states.items():
        for symbol, targets in state.transitions.items():
            for target in targets:
                label = "λ" if symbol == "λ" else symbol
                dot.edge(state_id, target.state_id, label=label)

    # Highlight start state with an arrow from a blank node
    if automaton.start_state:
        start_state_id = automaton.start_state.state_id
        dot.node("start", shape="none", label="")
        dot.edge("start", start_state_id)

    # Render the automaton to file
    dot.render(filename, view=True)


class InterfazGrafica:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Expresiones Regulares a Autómatas")

        # Etiqueta y campo de entrada para la expresión regular
        self.label = tk.Label(root, text="Ingrese la expresión regular:")
        self.label.pack(pady=10)

        self.entrada = tk.Entry(root, width=50)
        self.entrada.pack(pady=10)

        # Botón para convertir la expresión a un autómata
        self.boton = tk.Button(root, text="Convertir a Autómata", command=self.convertir_a_automata)
        self.boton.pack(pady=20)

    def convertir_a_automata(self):
        """
        Obtiene la expresión regular ingresada por el usuario, la valida y la convierte a un autómata.
        Si la expresión no es válida, muestra un mensaje de error.
        """
        expresion = self.entrada.get().strip()
        if not expresion:
            messagebox.showerror("Error", "Por favor, ingrese una expresión regular.")
            return

        try:
            # Crear una instancia de ExpresionRegular
            expresion_regular = ExpresionesRegulares.ExpresionRegular(expresion)

            # Validar la expresión
            es_valida, mensaje = expresion_regular.validar_expresion()
            if not es_valida:
                messagebox.showerror("Error", f"Expresión inválida: {mensaje}")
                return

            # Convertir a postfix y construir el autómata
            postfix = expresion_regular.convertir_a_postfix()
            automata = Automaton()
            lambdanfa = automata.construir_desde_postfix(postfix)
            #lambdanfa.rename_states_sequentially()
            nfa = lambdanfa.convert_to_nfa()
            #nfa.set_start_state(lambdanfa.start_state)
            dfa =nfa.to_dfa()
            render_automaton(dfa)


            # Mostrar el resultado
            messagebox.showinfo("Autómata Generado", f"Autómata creado:")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")






def main():
    selector = AutomatonTypeSelector()
    if selector.selected_type:
        root = tk.Tk()
       # app = AutomataGUI(root, selector.selected_type)
        app = InterfazGrafica(root)
        root.mainloop()



if __name__ == "__main__":
    main()

