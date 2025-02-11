import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import math
import graphviz
from PIL import Image, ImageTk  # Para mostrar los png en Tkinter

import ExpresionesRegulares

##############################################
#          Selector Principal de Módulo      #
##############################################

class AutomatonTypeSelector:
    def __init__(self):
        self.selected_type = None

        self.dialog = tk.Tk()
        self.dialog.title("Seleccione la Funcionalidad")
        self.dialog.configure(background="#f0f0f0")

        window_width = 350
        window_height = 200
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.dialog.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        label = ttk.Label(self.dialog, text="Seleccione la funcionalidad a utilizar:", padding=20, font=("Bahnschrift", 12))
        label.pack()

        btn_nfa = ttk.Button(self.dialog, text="AFN (sin transiciones λ)",
                             command=lambda: self.select_type("NFA"))
        btn_nfa.pack(pady=5, ipadx=10, ipady=5)

        btn_enfa = ttk.Button(self.dialog, text="AFN con transiciones λ",
                              command=lambda: self.select_type("eNFA"))
        btn_enfa.pack(pady=5, ipadx=10, ipady=5)

        btn_regex = ttk.Button(self.dialog, text="Conversor de Expresiones Regulares",
                               command=lambda: self.select_type("regex"))
        btn_regex.pack(pady=5, ipadx=10, ipady=5)

        self.dialog.mainloop()

    def select_type(self, automaton_type):
        self.selected_type = automaton_type
        self.dialog.destroy()


##############################################
#                Clases de Autómata          #
##############################################

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
        for destinos in self.transitions.values():
            for dest in destinos:
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

    def rename_states_sequentially(self):
        if not self.states:
            return  # No hay estados para renombrar
        estado_inicial = self.start_state
        ordered_states = [estado_inicial]
        for estado in self.states.values():
            if estado != estado_inicial:
                ordered_states.append(estado)
        new_states = {}
        for index, state in enumerate(ordered_states):
            new_name = f'q{index}'
            state.state_id = new_name
            new_states[new_name] = state
        self.states = new_states
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
        new_automaton = Automaton()
        for state_id, state in self.states.items():
            new_automaton.add_state(state_id, is_accepting=state.is_accepting)
        if self.start_state:
            new_automaton.set_start_state(self.start_state.state_id)
        for state_id, state in self.states.items():
            epsilon_closure = self.get_epsilon_closure(state_id)
            combined_transitions = {}
            for closure_state in epsilon_closure:
                for symbol, target_states in closure_state.transitions.items():
                    if symbol == "λ":
                        continue
                    if symbol not in combined_transitions:
                        combined_transitions[symbol] = set()
                    for target_state in target_states:
                        combined_transitions[symbol].update(target_state.get_epsilon_closure())
            for symbol, target_states in combined_transitions.items():
                for target_state in target_states:
                    new_automaton.add_transition(state_id, symbol, target_state.state_id)
            if any(closure_state.is_accepting for closure_state in epsilon_closure):
                new_automaton.states[state_id].is_accepting = True
        return new_automaton

    def construir_desde_postfix(self, postfix):
        pila = []
        contador_estados = 0
        for token in postfix:
            if token == '&':  # Concatenación
                nfa2 = pila.pop()
                nfa1 = pila.pop()
                cantidad_estados_nfa1 = len(nfa1.states)
                estados_renombrados_nfa2 = {}
                for estado_id, estado in nfa2.states.items():
                    nuevo_id = f"q{int(estado_id[1:]) + cantidad_estados_nfa1}b"
                    estado.state_id = nuevo_id
                    estados_renombrados_nfa2[nuevo_id] = estado
                for estado_id, estado in estados_renombrados_nfa2.items():
                    nfa1.add_state(estado_id, is_accepting=False)
                for estado_id, estado in estados_renombrados_nfa2.items():
                    for simbolo, destinos in estado.transitions.items():
                        for destino in destinos:
                            destino_id = destino.state_id
                            nfa1.add_transition(estado_id, simbolo, destino_id)
                for estado in nfa1.states.values():
                    if estado.is_accepting:
                        estado.is_accepting = False
                        nfa1.add_transition(estado.state_id, "λ", nfa2.start_state.state_id)
                for estado in nfa2.states.values():
                    if estado.is_accepting:
                        nfa1.states[estado.state_id].is_accepting = True
                nfa1.start_state = nfa1.start_state
                nfa1.rename_states_sequentially()
                pila.append(nfa1)
            elif token == '|':  # Unión
                nfa2 = pila.pop()
                nfa1 = pila.pop()
                cantidad_estados_nfa1 = len(nfa1.states)
                estados_renombrados_nfa2 = {}
                for estado_id, estado in nfa2.states.items():
                    nuevo_id = f"q{int(estado_id[1:]) + cantidad_estados_nfa1 -1 }a"
                    estado.state_id = nuevo_id
                    estados_renombrados_nfa2[nuevo_id] = estado
                automata = Automaton()
                for estado_id, estado in nfa1.states.items():
                    automata.add_state(estado_id, estado.is_accepting)
                for estado_id, estado in nfa1.states.items():
                    for simbolo, destinos in estado.transitions.items():
                        for destino in destinos:
                            automata.add_transition(estado_id, simbolo, destino.state_id)
                for estado_id, estado in estados_renombrados_nfa2.items():
                    automata.add_state(estado_id, estado.is_accepting)
                for estado_id, estado in estados_renombrados_nfa2.items():
                    for simbolo, destinos in estado.transitions.items():
                        for destino in destinos:
                            automata.add_transition(estado_id, simbolo, destino.state_id)
                nuevo_inicio = State(f"q{len(automata.states)+1}")
                automata.add_state(nuevo_inicio.state_id)
                automata.set_start_state(nuevo_inicio.state_id)
                automata.add_transition(nuevo_inicio.state_id, "λ", nfa1.start_state.state_id)
                automata.add_transition(nuevo_inicio.state_id, "λ", nfa2.start_state.state_id)
                automata.rename_states_sequentially()
                pila.append(automata)
            elif token == '*':  # Clausura de Kleene
                nfa = pila.pop()
                for estado in nfa.states.values():
                    if estado.is_accepting:
                        nfa.add_transition(estado.state_id, "λ", nfa.start_state.state_id)
                nfa.states.get(nfa.start_state.state_id).is_accepting = True
                pila.append(nfa)
            elif token == '+':  # Clausura positiva de Kleene
                nfa = pila.pop()
                for estado in nfa.states.values():
                    if estado.is_accepting:
                        nfa.add_transition(estado.state_id, "λ", nfa.start_state.state_id)
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
        nfa_final = pila.pop()
        nfa_final.rename_states_sequentially()
        return nfa_final

    def __repr__(self):
        return f"Automaton(States: {list(self.states.keys())})"


##############################################
#         Función para Renderizar y         #
#       Mostrar autómatas con Graphviz       #
##############################################

def render_automaton(automaton, filename="automaton"):
    dot = graphviz.Digraph(format="png")
    # Estados: doble círculo si es de aceptación
    for state_id, state in automaton.states.items():
        shape = "doublecircle" if state.is_accepting else "circle"
        dot.node(state_id, shape=shape, label=state_id)
    # Transiciones
    for state_id, state in automaton.states.items():
        for symbol, targets in state.transitions.items():
            for target in targets:
                label = "λ" if symbol == "λ" else symbol
                dot.edge(state_id, target.state_id, label=label)
    # Estado inicial
    if automaton.start_state:
        start_state_id = automaton.start_state.state_id
        dot.node("start", shape="none", label="")
        dot.edge("start", start_state_id)
    # Renderiza sin abrir el visor y retorna la ruta del archivo generado
    output_path = dot.render(filename, view=False, cleanup=True)
    return output_path

def mostrar_automata_images(imagenes):
    """
    Recibe un diccionario {título: ruta_imagen} y muestra todas las imágenes en una ventana
    con pestañas (Notebook) para evitar abrir múltiples ventanas.
    
    Esta versión utiliza, en cada pestaña, un canvas con scrollbars para visualizar
    imágenes de gran tamaño sin que se “pierda” contenido.
    """
    window = tk.Toplevel()
    window.title("Autómatas Generados")
    notebook = ttk.Notebook(window)
    notebook.pack(expand=True, fill='both', padx=10, pady=10)

    for title, path in imagenes.items():
        tab_frame = ttk.Frame(notebook)
        notebook.add(tab_frame, text=title)

        # Crear un canvas dentro del tab_frame
        canvas = tk.Canvas(tab_frame, bg='white')
        # Scrollbars horizontales y verticales
        hbar = tk.Scrollbar(tab_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        vbar = tk.Scrollbar(tab_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, expand=True, fill='both')

        try:
            pil_image = Image.open(path)
            # Se mantiene la imagen en su tamaño original para poder desplazarla
            photo = ImageTk.PhotoImage(pil_image)
        except Exception as e:
            photo = None

        if photo:
            canvas.create_image(0, 0, anchor="nw", image=photo)
            # Guardar referencia a la imagen
            canvas.image = photo
            canvas.config(scrollregion=canvas.bbox(tk.ALL))

    # No se llama a mainloop() aquí porque ya existe la principal


##############################################
#           Interfaz de Dibujo de            #
#               Autómatas                  #
##############################################

class AutomataGUI:
    def __init__(self, root, automaton_type):
        self.root = root
        self.root.title(f"Automata Designer - {automaton_type}")
        self.automaton = Automaton()
        self.automaton_type = automaton_type
        self.style_buttons()

        # Configuración del Canvas
        self.canvas = tk.Canvas(root, width=960, height=720, bg='white')
        self.canvas.pack(expand=True, fill='both')
        self.canvas.after(100, self.add_color_convention_legend)

        self.state_counter = 1  # q0 es el estado inicial
        self.state_radius = 30
        self.loop_radius = 20

        self.drawing_transition = False
        self.transition_start = None

        self.create_toolbar()
        self.bind_events()

        # Crear estado inicial q0
        self.create_initial_state()

    def style_buttons(self):
        style = ttk.Style()
        style.configure("TButton",
                        font=("Bahnschrift", 10, "bold"),
                        borderwidth=2,
                        foreground="black",  # Texto en negro
                        background="#b03737")
        style.map("TButton",
                  background=[("active", "#45a049")],
                  relief=[("pressed", "sunken")])

    def create_toolbar(self):
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(side='top', fill='x')

        state_btn = ttk.Button(toolbar, text="Agregar estado", command=self.enable_state_mode)
        state_btn.pack(side='left', padx=5)

        transition_btn = ttk.Button(toolbar, text="Agregar Transiciones", command=self.enable_transition_mode)
        transition_btn.pack(side='left', padx=5)

        if self.automaton_type == "NFA":
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

    def add_color_convention_legend(self):
        legend_x, legend_y = 10, self.canvas.winfo_height() - 90
        padding = 5
        spacing = 30
        self.canvas.create_rectangle(
            legend_x - padding, legend_y - padding,
            legend_x + 180, legend_y + 90,
            fill="white", outline="black", width=1
        )
        self.canvas.create_oval(legend_x, legend_y, legend_x + 20, legend_y + 20, fill="green", width=2)
        self.canvas.create_text(legend_x + 40, legend_y + 10, text="Inicial", font=("Bahnschrift", 10), anchor="w")
        legend_y += spacing
        self.canvas.create_oval(legend_x, legend_y, legend_x + 20, legend_y + 20, fill="blue", width=2)
        self.canvas.create_text(legend_x + 40, legend_y + 10, text="Normal", font=("Bahnschrift", 10), anchor="w")
        legend_y += spacing
        self.canvas.create_oval(legend_x, legend_y, legend_x + 20, legend_y + 20, fill="orange", width=2)
        self.canvas.create_text(legend_x + 40, legend_y + 10, text="Final", font=("Bahnschrift", 10), anchor="w")

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
        dialog.title("Agregar transición")
        label = ttk.Label(dialog, text="Ingrese el símbolo para la transición:", font=("Bahnschrift", 12))
        label.pack(pady=5)
        entry = ttk.Entry(dialog, font=("Bahnschrift", 12))
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
        if not hasattr(self, "transition_counts"):
            self.transition_counts = {}
        pair = (from_state, to_state)
        if pair not in self.transition_counts:
            self.transition_counts[pair] = 0
        self.transition_counts[pair] += 1
        count = self.transition_counts[pair]
        from_coords = self.canvas.coords(from_state)
        to_coords = self.canvas.coords(to_state)
        from_x = (from_coords[0] + from_coords[2]) / 2
        from_y = (from_coords[1] + from_coords[3]) / 2
        to_x = (to_coords[0] + to_coords[2]) / 2
        to_y = (to_coords[1] + to_coords[3]) / 2
        angle = math.atan2(to_y - from_y, to_x - from_x)
        offset_distance = 10 * count
        offset_x = offset_distance * math.cos(angle + math.pi / 2)
        offset_y = offset_distance * math.sin(angle + math.pi / 2)
        if from_state == to_state:
            center_x = from_x
            center_y = from_y
            radius = self.state_radius * 1.5
            start_x = center_x - self.state_radius * 0.5
            start_y = center_y - self.state_radius
            end_x = center_x + self.state_radius * 0.5
            end_y = center_y - self.state_radius
            ctrl1_x = start_x - radius
            ctrl1_y = start_y - radius
            ctrl2_x = end_x + radius
            ctrl2_y = end_y - radius
            self.canvas.create_line(
                start_x, start_y,
                ctrl1_x, ctrl1_y,
                ctrl2_x, ctrl2_y,
                end_x, end_y,
                smooth=True,
                splinesteps=36,
                arrow=tk.LAST
            )
            self.canvas.create_text(
                center_x,
                center_y - radius - self.state_radius,
                text=symbol,
                font=("Bahnschrift", 10, "bold")
            )
        else:
            from_edge_x = from_x + self.state_radius * math.cos(angle)
            from_edge_y = from_y + self.state_radius * math.sin(angle)
            to_edge_x = to_x - self.state_radius * math.cos(angle)
            to_edge_y = to_y - self.state_radius * math.sin(angle)
            from_edge_x += offset_x
            from_edge_y += offset_y
            to_edge_x += offset_x
            to_edge_y += offset_y
            self.canvas.create_line(
                from_edge_x, from_edge_y, to_edge_x, to_edge_y,
                arrow=tk.LAST, smooth=True, width=2
            )
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

    def go_back_to_main_menu(self):
        self.root.destroy()
        main()

    def compute_epsilon_closure(self):
        state_id = simpledialog.askstring("Lambda Clausura Individual", "Ingrese el ID del Estado:")
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
        radius = min(canvas_width, canvas_height) / 3
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
            output_path = render_automaton(dfa, "dfa")
            mostrar_automata_images({"AFD": output_path})
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def convert_to_nfa(self):
        try:
            nfa = self.automaton.convert_to_nfa()
            self.layout_states_circular(nfa)
            output_path = render_automaton(nfa, "nfa")
            mostrar_automata_images({"AFN (sin λ)": output_path})
        except ValueError as e:
            messagebox.showerror("Error", str(e))


##############################################
#     Interfaz Gráfica para Expresiones      #
#           Regulares a Autómatas            #
##############################################

class InterfazGraficaRegex:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Expresiones Regulares a Autómatas")
        self.root.configure(background="#f0f0f0")
        
        # Configurar estilo de botones para que tengan texto negro
        style = ttk.Style()
        style.configure("TButton",
                        font=("Bahnschrift", 10, "bold"),
                        foreground="black",  # Texto en negro
                        background="#b03737")
        style.map("TButton",
                  background=[("active", "#45a049")],
                  relief=[("pressed", "sunken")])
        
        frame = ttk.Frame(root, padding=20)
        frame.pack(expand=True, fill="both")
        
        title_label = ttk.Label(frame, text="Conversor de Expresiones Regulares a Autómatas", font=("Bahnschrift", 16, "bold"))
        title_label.pack(pady=10)
        
        instruction_label = ttk.Label(frame, text="1. a·b = ab    2. aUb = a|b", font=("Bahnschrift", 12))
        instruction_label.pack(pady=5)
        
        expr_label = ttk.Label(frame, text="Ingrese la expresión regular:", font=("Bahnschrift", 12))
        expr_label.pack(pady=10)
        
        self.entrada = ttk.Entry(frame, width=50, font=("Bahnschrift", 12))
        self.entrada.pack(pady=10)
        
        self.boton = ttk.Button(frame, text="Convertir a Autómata", command=self.convertir_a_automata, style="TButton")
        self.boton.pack(pady=20)
        
        # Botón para volver al menú principal
        volver_btn = ttk.Button(frame, text="Volver al Menú Principal", command=self.volver_menu_principal, style="TButton")
        volver_btn.pack(pady=10)

    def convertir_a_automata(self):
        expresion = self.entrada.get().strip()
        if not expresion:
            messagebox.showerror("Error", "Por favor, ingrese una expresión regular.")
            return
        try:
            expresion_regular = ExpresionesRegulares.ExpresionRegular(expresion)
            es_valida, mensaje = expresion_regular.validar_expresion()
            if not es_valida:
                messagebox.showerror("Error", f"Expresión inválida: {mensaje}")
                return
            postfix = expresion_regular.convertir_a_postfix()
            automata = Automaton()
            lambdanfa = automata.construir_desde_postfix(postfix)
            nfa = lambdanfa.convert_to_nfa()
            dfa = nfa.to_dfa()
            images = {}
            images["AFN (sin λ)"] = render_automaton(nfa, "nfa")
            images["AFD"] = render_automaton(dfa, "dfa")
            images["AFN con λ"] = render_automaton(lambdanfa, "enfa")
            mostrar_automata_images(images)
            messagebox.showinfo("Autómata Generado", "Autómata creado exitosamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")
    
    def volver_menu_principal(self):
        self.root.destroy()
        main()


##############################################
#                  main()                    #
##############################################

def main():
    selector = AutomatonTypeSelector()
    if selector.selected_type:
        root = tk.Tk()
        if selector.selected_type == "regex":
            app = InterfazGraficaRegex(root)
        else:
            app = AutomataGUI(root, selector.selected_type)
        root.mainloop()


if __name__ == "__main__":
    main()
