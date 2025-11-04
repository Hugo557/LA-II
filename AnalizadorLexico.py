import re
import os

class AnalizadorLexico:
    """
    Analizador Léxico 

    Este analizador procesa un archivo fuente, identifica los lexemas válidos y
    genera una tabla de tokens con su tipo, PTS y número de línea.  
    Además, detecta y reporta errores léxicos según las reglas especificadas:

    - Identificadores:
        * Deben iniciar con uno de los prefijos: @, $, &, %
        * Solo pueden contener letras (sin dígitos, guiones ni símbolos)
        * Longitud mínima: 2 y máxima: 8 (incluyendo el prefijo)
    - Constantes enteras y reales según rango
    - Constantes cadena encerradas entre comillas
    - Soporta comentarios de línea iniciados con //
    - Palabras reservadas, operadores y delimitadores predefinidos
    """

    def __init__(self):
        """Constructor: inicializa las estructuras de tokens y errores."""
        self.token_map = {}           # Diccionario de lexemas conocidos → token numérico
        self.tokens = []              # Lista de tokens válidos (diccionarios con lexema, token, pts, línea)
        self.errores_lexicos = []     # Lista de errores léxicos detectados
        self._inicializar_tokens()    # Carga el mapa de palabras reservadas y operadores

    # Inicialización del mapa de tokens

    def _inicializar_tokens(self):
        """
        Define las palabras reservadas, operadores y caracteres especiales del lenguaje,
        asignándoles un valor de token negativo (convención interna).
        """
        # Palabras reservadas
        reservadas = [
            "clase", "leer", "switch", "posxy", "entero", "var", "escribir", "encaso",
            "limpiar", "real", "vacio", "si", "repite", "ejecutar", "regresar",
            "metodo", "sino", "mientras", "cadena", "salir"
        ]
        for i, palabra in enumerate(reservadas, start=1):
            self.token_map[palabra] = -i

        # Operadores aritméticos
        self.token_map.update({
            "+": -101, "-": -102, "*": -103, "/": -104, "%": -105, "=": -106,
            "++": -107, "--": -108, "+=": -109, "-=": -110, "/=": -111, "*=": -112
        })

        # Operadores relacionales
        self.token_map.update({
            "<": -120, "<=": -121, "!=": -122, ">": -123, ">=": -124, "==": -125
        })

        # Operadores lógicos
        self.token_map.update({
            "!": -130, "&&": -131, "||": -132
        })

        # Caracteres especiales (sí generan token)
        self.token_map.update({
            ";": -140, "[": -141, "]": -142, ",": -143, ":": -144,
            "(": -145, ")": -146, "{": -147, "}": -148
        })

    # Procesamiento del archivo fuente

    def procesar_archivo(self, ruta):
        """
        Lee y procesa el archivo fuente línea por línea.
        Genera la tabla de tokens y los archivos de salida:
            - tabla_tokens.txt
            - errores_lexicos.txt
        """
        try:
            carpeta = os.path.dirname(ruta)
            tabla_path = os.path.join(carpeta, "tabla_tokens.txt")
            errores_path = os.path.join(carpeta, "errores_lexicos.txt")

            # Procesa cada línea del archivo
            with open(ruta, "r", encoding="utf-8") as f:
                for num_linea, linea in enumerate(f, start=1):
                    self._procesar_linea(linea.rstrip("\n"), num_linea)

            # Clasifica cada lexema en su tipo de token
            self._clasificar_tokens()
            # Escribe resultados
            self._escribir_tabla(tabla_path)
            self._mostrar_errores(errores_path)

            # Mensaje de resumen
            print(f"\nAnálisis completado.")
            print(f"Tabla: {tabla_path}")
            print(f"Errores: {errores_path}")
            print(f"Resumen: {len(self.tokens)} tokens válidos, {len(self.errores_lexicos)} errores léxicos.\n")

        except FileNotFoundError:
            print("No se encontró el archivo:", ruta)


    # Procesamiento de cada línea del archivo

    def _procesar_linea(self, linea, num_linea):
        """
        Tokeniza una línea del archivo fuente:
        - Elimina comentarios (// ...)
        - Usa expresiones regulares para separar lexemas válidos
        """
        # Eliminar comentarios simples
        if "//" in linea:
            linea = linea.split("//", 1)[0]

        # Expresión regular que captura todos los posibles lexemas
        patron = re.compile(
            r'"[^"]*"|'                                   # Cadenas entre comillas
            r'==|!=|<=|>=|\+\+|--|\+=|-=|/=|\*=|&&|\|\||'  # Operadores compuestos
            r'[@$%&][A-Za-z0-9_]*|'                       # Identificadores o posibles errores
            r'-?\d+\.\d+|-?\.\d+|-?\d+|'                  # Números reales y enteros
            r'[A-Za-z]+|'                                 # Palabras reservadas
            r'[+\-*/%=<>!{}\[\],:;()]|'                   # Operadores simples
            r'\s+'                                        # Espacios
        )

        # Agregar cada lexema encontrado a la lista general de tokens
        for match in patron.finditer(linea):
            lex = match.group().strip()
            if lex:
                self.tokens.append({"lexema": lex, "token": 0, "pts": 0, "linea": num_linea})

    # Clasificación de tokens

    def _clasificar_tokens(self):
        """
        Determina el tipo de cada token detectado:
        - Identificadores (con validación de prefijo, letras y longitud)
        - Constantes (enteras, reales, cadenas)
        - Palabras reservadas, operadores, delimitadores
        - Registra los errores léxicos encontrados
        """
        tokens_finales = []

        for t in self.tokens:
            lex = t["lexema"]
            if not lex or re.match(r"^\s+$", lex):
                continue

            # Caracteres que no generan token
            if lex in ['“', '.', '\t', ' ']:
                continue

            # Palabras reservadas u operadores conocidos
            if lex in self.token_map:
                t["token"] = self.token_map[lex]
                t["pts"] = -1
                tokens_finales.append(t)
                continue

            # Prefijos sin letras posteriores → error
            if lex in ['@', '$', '&', '%']:
                self.errores_lexicos.append((t["linea"], lex))
                continue

            # -Identificadores 
            if re.match(r"^[@$%&][A-Za-z]+$", lex):
                cuerpo = lex[1:]
                # Longitud entre 2 y 8 caracteres (incluyendo prefijo)
                if 1 <= len(cuerpo) <= 7:
                    if lex[0] == "@":
                        t["token"], t["pts"] = -300, -2
                    elif lex[0] == "$":
                        t["token"], t["pts"] = -301, -2
                    elif lex[0] == "&":
                        t["token"], t["pts"] = -302, -2
                    elif lex[0] == "%":
                        t["token"], t["pts"] = -303, -2
                    tokens_finales.append(t)
                else:
                    self.errores_lexicos.append((t["linea"], lex))
                continue

            # Constantes
            elif re.match(r'^"[^"]*"$', lex):  # Constante string
                t["token"], t["pts"] = -400, -1

            elif re.match(r"^-?\d+$", lex):  # Constante entera
                try:
                    val = int(lex)
                    t["token"] = -401 if -32768 <= val <= 32767 else -402  # fuera de rango → real
                except ValueError:
                    t["token"] = -402
                t["pts"] = -1

            elif re.match(r"^-?(\d+\.\d+|\.\d+)$", lex):  # Constante real válida
                t["token"], t["pts"] = -402, -1

            elif re.match(r"^-?\d+\.$", lex):  # Error: real terminado en punto
                self.errores_lexicos.append((t["linea"], lex))
                continue

            else:
                # Todo lo no reconocido es error léxico
                self.errores_lexicos.append((t["linea"], lex))
                continue

            tokens_finales.append(t)

        self.tokens = tokens_finales

    # Generar tabla de tokens

    def _escribir_tabla(self, ruta):
        """
        Escribe la tabla de tokens válidos en formato de columnas:
        LEXEMA | TOKEN | PTS | LÍNEA
        """
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(f"{'LEXEMA':<20}{'TOKEN':<10}{'PTS':<10}{'LÍNEA':<10}\n")
            f.write("-" * 50 + "\n")
            for t in self.tokens:
                f.write(f"{t['lexema']:<20}{t['token']:<10}{t['pts']:<10}{t['linea']:<10}\n")


    # Mostrar y guardar errores

    def _mostrar_errores(self, ruta):
        """
        Muestra en consola los errores léxicos encontrados y los guarda
        en un archivo de texto (errores_lexicos.txt).
        """
        if not self.errores_lexicos:
            print("Sin errores léxicos.")
            return

        print("\n Errores léxicos encontrados:")
        with open(ruta, "w", encoding="utf-8") as f:
            for linea, lex in self.errores_lexicos:
                msg = f"Línea {linea}: '{lex}' no es un token válido."
                print(msg)
                f.write(msg + "\n")


# Ejecución principal del analizador

if __name__ == "__main__":
    print("=== ANALIZADOR LÉXICO ===")
    ruta = input("Ingrese la ruta del archivo fuente (.txt): ").strip()
    analizador = AnalizadorLexico()
    analizador.procesar_archivo(ruta)
