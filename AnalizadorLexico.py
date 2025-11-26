import re
import os

class AnalizadorLexico:
    """
    Analizador Léxico final
    ----------------------------------------
    - Respeta reglas oficiales del lenguaje 2025
    - Soporta identificadores @ $ & %
    - Valida longitud 2–8
    - Constantes enteras y reales
    - Cadenas entre comillas
    - Palabras reservadas, operadores, delimitadores
    - Comentarios //
    """

    def __init__(self):
        self.token_map = {}           # Diccionario lexema → token numérico
        self.tokens = []              # Tokens válidos detectados
        self.errores_lexicos = []     # Lista de errores
        self._inicializar_tokens()

    # ---------------------------------------------------------------
    # MAPA DE TOKENS PREDEFINIDOS
    # ---------------------------------------------------------------
    def _inicializar_tokens(self):
        reservadas = [
            "clase", "leer", "switch", "posxy", "entero", "var", "escribir", "encaso",
            "limpiar", "real", "vacio", "si", "repite", "ejecutar", "regresar",
            "metodo", "sino", "mientras", "cadena", "salir"
        ]

        for i, palabra in enumerate(reservadas, start=1):
            self.token_map[palabra] = -i

        self.token_map.update({
            "+": -101, "-": -102, "*": -103, "/": -104, "%": -105, "=": -106,
            "++": -107, "--": -108, "+=": -109, "-=": -110, "/=": -111, "*=": -112
        })

        self.token_map.update({
            "<": -120, "<=": -121, "!=": -122, ">": -123, ">=": -124, "==": -125
        })

        self.token_map.update({
            "!": -130, "&&": -131, "||": -132
        })

        self.token_map.update({
            ";": -140, "[": -141, "]": -142, ",": -143, ":": -144,
            "(": -145, ")": -146, "{": -147, "}": -148
        })

    # ---------------------------------------------------------------
    # PROCESAR ARCHIVO FUENTE
    # ---------------------------------------------------------------
    def procesar_archivo(self, ruta):
        try:
            carpeta = os.path.dirname(ruta)
            tabla_path = os.path.join(carpeta, "tabla_tokens.txt")
            errores_path = os.path.join(carpeta, "errores_lexicos.txt")

            # Leer líneas del archivo
            with open(ruta, "r", encoding="utf-8") as f:
                for num_linea, linea in enumerate(f, start=1):
                    self._procesar_linea(linea.rstrip("\n"), num_linea)

            # Clasificar tokens detectados
            self._clasificar_tokens()

            # Generar tabla
            self._escribir_tabla(tabla_path)

            # Mostrar errores
            self._mostrar_errores(errores_path)

            print("\nAnálisis completado.")
            print(f"Tabla: {tabla_path}")
            print(f"Errores: {errores_path}")
            print(f"Resumen: {len(self.tokens)} tokens válidos, {len(self.errores_lexicos)} errores léxicos.\n")

        except FileNotFoundError:
            print("No se encontró el archivo:", ruta)

    # ---------------------------------------------------------------
    # TOKENIZACIÓN DE UNA LÍNEA
    # ---------------------------------------------------------------
    def _procesar_linea(self, linea, num_linea):

        if "//" in linea:
            linea = linea.split("//", 1)[0]

        patron = re.compile(
            r'"[^"]*"|'                                   # Cadenas
            r'==|!=|<=|>=|\+\+|--|\+=|-=|/=|\*=|&&|\|\||'  # Operadores dobles
            r'[@$%&][A-Za-z0-9_]*|'                       # Identificadores
            r'-?\d+\.\d+|-?\.\d+|-?\d+|'                  # Números
            r'[A-Za-z]+|'                                 # Palabras
            r'[+\-*/%=<>!{}\[\],:;()]|'                   # Simbolos
            r'\s+'                                        # Espacios
        )

        for match in patron.finditer(linea):
            lex = match.group().strip()
            if lex:
                self.tokens.append({"lexema": lex, "token": 0, "pts": 0, "linea": num_linea})

    # ---------------------------------------------------------------
    # CLASIFICACIÓN DE TOKENS
    # ---------------------------------------------------------------
    def _clasificar_tokens(self):
        tokens_finales = []

        for t in self.tokens:
            lex = t["lexema"]

            if not lex or re.match(r"^\s+$", lex):
                continue

            if lex in ['“', '.', '\t', ' ']:
                continue

            # Si es palabra reservada u operador ya conocido
            if lex in self.token_map:
                t["token"] = self.token_map[lex]
                t["pts"] = -1
                tokens_finales.append(t)
                continue

            # Prefijos sin nombre -> error
            if lex in ['@', '$', '&', '%']:
                self.errores_lexicos.append((t["linea"], lex))
                continue

            # Identificadores válidos
            if re.match(r"^[@$%&][A-Za-z]+$", lex):
                cuerpo = lex[1:]
                if 1 <= len(cuerpo) <= 7:
                    if lex.startswith("@"): t["token"] = -300
                    if lex.startswith("$"): t["token"] = -301
                    if lex.startswith("&"): t["token"] = -302
                    if lex.startswith("%"): t["token"] = -303
                    t["pts"] = -2
                    tokens_finales.append(t)
                else:
                    self.errores_lexicos.append((t["linea"], lex))
                continue

            # String
            if re.match(r'^"[^"]*"$', lex):
                t["token"], t["pts"] = -400, -1

            # Entero
            elif re.match(r"^-?\d+$", lex):
                try:
                    val = int(lex)
                    t["token"] = -401 if -32768 <= val <= 32767 else -402
                except:
                    t["token"] = -402
                t["pts"] = -1

            # Real
            elif re.match(r"^-?(\d+\.\d+|\.\d+)$", lex):
                t["token"], t["pts"] = -402, -1

            else:
                self.errores_lexicos.append((t["linea"], lex))
                continue

            tokens_finales.append(t)

        self.tokens = tokens_finales

    # ---------------------------------------------------------------
    # ESCRIBIR TABLA SIN CORTAR LEXEMAS
    # ---------------------------------------------------------------
    def _escribir_tabla(self, ruta):
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("LEXEMA\tTOKEN\tPTS\tLINEA\n")
            for t in self.tokens:
                f.write(f"{t['lexema']}\t{t['token']}\t{t['pts']}\t{t['linea']}\n")

    # ---------------------------------------------------------------
    # MOSTRAR ERRORES
    # ---------------------------------------------------------------
    def _mostrar_errores(self, ruta):
        if not self.errores_lexicos:
            print("Sin errores léxicos.")
            return

        print("\nErrores léxicos encontrados:")
        with open(ruta, "w", encoding="utf-8") as f:
            for linea, lex in self.errores_lexicos:
                msg = f"Línea {linea}: '{lex}' no es un token válido."
                print(msg)
                f.write(msg + "\n")


if __name__ == "__main__":
    print("=== ANALIZADOR LÉXICO ===")
    ruta = input("Ingrese la ruta del archivo fuente (.txt): ").strip()
    analizador = AnalizadorLexico()
    analizador.procesar_archivo(ruta)
