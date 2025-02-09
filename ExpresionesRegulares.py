class ExpresionRegular:
    def __init__(self, expresion):
        self.expresion = expresion
    def validar_expresion(self):
        """
        Valida que la expresión regular esté balanceada en términos de paréntesis
        y que los operadores estén correctamente colocados.

        Retorna:
        - True si la expresión es válida.
        - False si la expresión es inválida.
        """
        pila = []  # Pila para verificar paréntesis balanceados
        caracteres_validos = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789()|*&")

        for i, char in enumerate(self.expresion):
            # Verificar si el carácter es válido
            if char not in caracteres_validos:
                return False, f"Carácter no válido: '{char}' en la posición {i}"

            # Verificar paréntesis balanceados
            if char == '(':
                pila.append(char)
            elif char == ')':
                if not pila or pila[-1] != '(':
                    return False, f"Paréntesis de cierre ')' sin apertura en la posición {i}"
                pila.pop()

            # Verificar operadores
            if char in {'|', '&'}:
                # Un operador no puede estar al inicio o al final de la expresión
                if i == 0 or i == len(self.expresion) - 1:
                    return False, f"Operador '{char}' en posición inválida: {i}"
                # Un operador no puede estar seguido de otro operador
                siguiente_char = self.expresion[i + 1] if i + 1 < len(self.expresion) else None
                if siguiente_char in {'|', '&', '*'}:
                    return False, f"Operador '{char}' seguido de otro operador en la posición {i}"

            # Verificar clausura de Kleene (*)
            if char == '*':
                # El operador * no puede estar al inicio de la expresión
                if i == 0:
                    return False, f"Operador '*' en posición inválida: {i}"
                # El operador * no puede estar seguido de otro operador
                siguiente_char = self.expresion[i + 1] if i + 1 < len(self.expresion) else None
                if siguiente_char in {'|', '&', '*'}:
                    return False, f"Operador '*' seguido de otro operador en la posición {i}"

        # Verificar si hay paréntesis sin cerrar
        if pila:
            return False, "Paréntesis de apertura '(' sin cierre"

        return True, "Expresión válida"
    def preprocesar(self):
        """
        Preprocesa la expresión regular para insertar operadores de concatenación explícitos (&).

        Retorna:
        - La expresión regular preprocesada.
        """
        procesada = []
        prev_char = None
        for char in self.expresion:
            if prev_char is not None:
                prev_is_symbol = prev_char not in {'*', '|', '(', ')', '&'}
                curr_is_symbol = char not in {'*', '|', '(', ')', '&'}
                if (prev_char in {'*', ')', '&'} or prev_is_symbol) and (char == '(' or curr_is_symbol):
                    procesada.append('&')  # Usamos & para concatenación
            procesada.append(char)
            prev_char = char
        return ''.join(procesada)

    def convertir_a_postfix(self):
        """
        Convierte la expresión regular preprocesada a notación postfix (RPN).

        Retorna:
        - La expresión regular en notación postfix.
        """
        expresion_preprocesada = self.preprocesar()
        tokens = list(expresion_preprocesada)

        precedencia = {'|': 1, '&': 2, '*': 3}  # Usamos & para concatenación
        salida = []
        pila = []

        for token in tokens:
            if token == '(':
                pila.append(token)
            elif token == ')':
                while pila and pila[-1] != '(':
                    salida.append(pila.pop())
                pila.pop()  # Eliminar el '(' de la pila
            elif token in precedencia:
                while pila and pila[-1] != '(' and precedencia[pila[-1]] >= precedencia[token]:
                    salida.append(pila.pop())
                pila.append(token)
            else:
                salida.append(token)

        while pila:
            salida.append(pila.pop())

        return ''.join(salida)
