# ================================================================
# ANALIZADOR SINTÁCTICO - Basado en Diagramas de Sintaxis (Agosto 2025)
# ================================================================

import re
from dataclasses import dataclass

# ================================================================
# MAPA DE TOKENS DEL ANALIZADOR LÉXICO OFICIAL
# ================================================================
TOKEN_MAP = {
    # Palabras reservadas
    -1: "CLASE", -2: "LEER", -3: "SWITCH", -4: "POSXY", -5: "ENTERO", -6: "VAR",
    -7: "ESCRIBIR", -8: "ENCASO", -9: "LIMPIAR", -10: "REAL", -11: "VACIO",
    -12: "SI", -13: "REPITE", -14: "EJECUTAR", -15: "REGRESAR",
    -16: "METODO", -17: "SINO", -18: "MIENTRAS", -19: "CADENA", -20: "SALIR",

    # Operadores
    -101: "MAS", -102: "MENOS", -103: "MULT", -104: "DIV", -105: "MOD",
    -106: "IGUAL", -107: "INCR", -108: "DECR", -109: "MAS_IGUAL",
    -110: "MENOS_IGUAL", -111: "DIV_IGUAL", -112: "MULT_IGUAL",

    # Relacionales y lógicos
    -120: "MENOR", -121: "MENOR_IGUAL", -122: "DISTINTO",
    -123: "MAYOR", -124: "MAYOR_IGUAL", -125: "IGUALDAD",
    -130: "NOT", -131: "AND", -132: "OR",

    # Delimitadores
    -140: "PUNTOYCOMA", -141: "COR_AP", -142: "COR_CI", -143: "COMA",
    -144: "DOS_PUNTOS", -145: "PAR_AP", -146: "PAR_CI",
    -147: "LLAVE_AP", -148: "LLAVE_CI",

    # Identificadores
    -300: "ID_ARROBA", -301: "ID_DOLAR", -302: "ID_AMP", -303: "ID_PORC",

    # Constantes
    -400: "CTE_CADENA", -401: "CTE_ENT", -402: "CTE_REAL",
}

# ================================================================
# CLASE TOKEN
# ================================================================
@dataclass
class Token:
    type: str
    lexeme: str
    line: int

# ================================================================
# LECTOR DE TABLA DE TOKENS
# ================================================================
def cargar_tokens_desde_tabla(ruta):
    tokens = []
    with open(ruta, encoding="utf-8") as f:
        for line in f:
            if not line.strip() or line.startswith('-') or line.startswith('LEXEMA'):
                continue

            partes = line.strip().split("\t")
            if len(partes) != 4:
                continue

            lexema, token_str, pts_str, linea_str = partes

            try:
                codigo = int(token_str)
                linea = int(linea_str)
            except ValueError:
                continue

            tipo = TOKEN_MAP.get(codigo, f"DESCONOCIDO_{codigo}")
            tokens.append(Token(type=tipo, lexeme=lexema, line=linea))

    print(f"{len(tokens)} tokens cargados correctamente desde {ruta}\n")
    return tokens


# ================================================================
# ANALIZADOR SINTÁCTICO CON RECUPERACIÓN DE ERRORES
# ================================================================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens + [Token("EOF", "EOF", -1)]
        self.pos = 0
        self.current = self.tokens[0]
        self.errores = []

    def advance(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.current = self.tokens[self.pos]

    def consume(self, lex=None, type_=None, msg="Error de sintaxis"):
        if (lex and self.current.lexeme == lex) or (type_ and self.current.type == type_):
            self.advance()
        else:
            self.reportar_error(msg)

    def reportar_error(self, msg):
        texto = f"[L{self.current.line}] {msg} — encontrado '{self.current.lexeme}'"
        self.errores.append(texto)
        while self.current.lexeme not in (";", "}", "EOF"):
            self.advance()
        if self.current.lexeme != "EOF":
            self.advance()

    # ============================================================
    # PROGRAMA PRINCIPAL
    # ============================================================
    def parse(self):
        self.PROG()
        self.mostrar_reporte()

    def PROG(self):
        self.consume(lex="clase", msg="Se esperaba 'clase'")
        self.consume(type_="ID_ARROBA", msg="Se esperaba identificador de clase (@id)")
        self.consume(lex="{", msg="Falta '{' después de clase")

        while self.current.lexeme in ("var", "metodo", "vacio"):
            if self.current.lexeme == "var":
                self.VAR()
            else:
                self.METODO()

        self.consume(lex="}", msg="Falta '}' al final de la clase")

    # ============================================================
    # VARIABLES
    # ============================================================
    def VAR(self):
        self.consume(lex="var")
        if self.current.lexeme not in ("entero", "real", "cadena"):
            self.reportar_error("Tipo de dato inválido en declaración")
        else:
            self.advance()
        if self.current.type not in ("ID_ARROBA", "ID_DOLAR", "ID_AMP", "ID_PORC"):
            self.reportar_error("Identificador inválido en variable")
        else:
            self.advance()
        while self.current.lexeme == ",":
            self.advance()
            if self.current.type not in ("ID_ARROBA", "ID_DOLAR", "ID_AMP", "ID_PORC"):
                self.reportar_error("Falta identificador después de ','")
            else:
                self.advance()
        self.consume(lex=";", msg="Falta ';' al final de la declaración")

    # ============================================================
    # METODOS
    # ============================================================
    def METODO(self):
        if self.current.lexeme in ("metodo", "vacio"):
            self.advance()
        else:
            self.reportar_error("Se esperaba 'metodo' o 'vacio'")
        self.consume(type_="ID_ARROBA", msg="Falta nombre del método (@id)")
        self.consume(lex="(", msg="Falta '(' en definición de método")
        self.consume(lex=")", msg="Falta ')' en definición de método")
        self.consume(lex="{", msg="Falta '{' en cuerpo del método")
        while self.current.lexeme not in ("}", "EOF"):
            self.ESTATUTO()
        self.consume(lex="}", msg="Falta '}' al final del método")

    # ============================================================
    # ESTATUTOS GENERALES
    # ============================================================
    def ESTATUTO(self):
        if self.current.lexeme == "leer":
            self.LEER()
        elif self.current.lexeme == "escribir":
            self.ESCRIBIR()
        elif self.current.lexeme == "si":
            self.SI()
        elif self.current.lexeme == "mientras":
            self.MIENTRAS()
        elif self.current.lexeme == "repite":
            self.REPETIR()
        elif self.current.lexeme == "switch":
            self.SWITCH()
        elif self.current.lexeme == "ejecutar":
            self.EJECUTAR()
        elif self.current.lexeme == "salir":
            self.SALIR()
        elif self.current.lexeme == "regresar":
            self.REGRESAR()
        else:
            self.reportar_error("Estatuto no reconocido")

    # ============================================================
    # ESTATUTOS INDIVIDUALES
    # ============================================================
    def LEER(self):
        self.consume(lex="leer")
        if self.current.type not in ("ID_ARROBA", "ID_DOLAR", "ID_AMP", "ID_PORC"):
            self.reportar_error("Falta identificador válido en 'leer'")
        else:
            self.advance()
        self.consume(lex=";", msg="Falta ';' al final de 'leer'")

    def ESCRIBIR(self):
        self.consume(lex="escribir")
        self.consume(lex="(", msg="Falta '(' en 'escribir'")
        while self.current.lexeme not in (")", "EOF"):
            self.advance()
        self.consume(lex=")", msg="Falta ')' en 'escribir'")
        self.consume(lex=";", msg="Falta ';' al final de 'escribir'")

    def SI(self):
        self.consume(lex="si")
        self.consume(lex="(", msg="Falta '(' en condición de 'si'")
        while self.current.lexeme not in (")", "EOF"):
            self.advance()
        self.consume(lex=")", msg="Falta ')' en condición de 'si'")
        self.consume(lex="{", msg="Falta '{' en bloque 'si'")
        while self.current.lexeme not in ("}", "EOF"):
            self.ESTATUTO()
        self.consume(lex="}", msg="Falta '}' al final del bloque 'si'")
        if self.current.lexeme == "sino":
            self.advance()
            self.consume(lex="{", msg="Falta '{' en bloque 'sino'")
            while self.current.lexeme not in ("}", "EOF"):
                self.ESTATUTO()
            self.consume(lex="}", msg="Falta '}' al final de bloque 'sino'")

    def MIENTRAS(self):
        self.consume(lex="mientras")
        self.consume(lex="(", msg="Falta '(' en 'mientras'")
        while self.current.lexeme not in (")", "EOF"):
            self.advance()
        self.consume(lex=")", msg="Falta ')' en 'mientras'")
        self.consume(lex="{", msg="Falta '{' en bloque 'mientras'")
        while self.current.lexeme not in ("}", "EOF"):
            self.ESTATUTO()
        self.consume(lex="}", msg="Falta '}' al final de 'mientras'")

    def REPETIR(self):
        self.consume(lex="repite")
        self.consume(lex="{", msg="Falta '{' en bloque 'repite'")
        while self.current.lexeme not in ("}", "EOF"):
            self.ESTATUTO()
        self.consume(lex="}", msg="Falta '}' al final de 'repite'")
        self.consume(lex="mientras", msg="Falta 'mientras' en 'repite'")
        self.consume(lex="(", msg="Falta '(' en condición de 'mientras'")
        while self.current.lexeme not in (")", "EOF"):
            self.advance()
        self.consume(lex=")", msg="Falta ')' en 'repite ... mientras'")
        self.consume(lex=";", msg="Falta ';' al final de 'repite ... mientras'")

    def SWITCH(self):
        self.consume(lex="switch")
        self.consume(lex="(", msg="Falta '(' en 'switch'")
        while self.current.lexeme not in (")", "EOF"):
            self.advance()
        self.consume(lex=")", msg="Falta ')' en 'switch'")
        self.consume(lex="{", msg="Falta '{' en bloque 'switch'")
        while self.current.lexeme not in ("}", "EOF"):
            self.advance()
        self.consume(lex="}", msg="Falta '}' al final de 'switch'")

    def EJECUTAR(self):
        self.consume(lex="ejecutar")
        if self.current.type != "ID_ARROBA":
            self.reportar_error("Falta identificador de método en 'ejecutar'")
        else:
            self.advance()
        self.consume(lex=";", msg="Falta ';' al final de 'ejecutar'")

    def SALIR(self):
        self.consume(lex="salir")
        self.consume(lex=";", msg="Falta ';' al final de 'salir'")

    def REGRESAR(self):
        self.consume(lex="regresar")
        self.consume(lex=";", msg="Falta ';' al final de 'regresar'")

    # ============================================================
    # REPORTE FINAL
    # ============================================================
    def mostrar_reporte(self):
        if not self.errores:
            print("Analisis sintactico correcto (sin errores)\n")
        else:
            print("Se encontraron errores sintacticos:\n")
            for e in self.errores:
                print("   -", e)
            print(f"\nTotal de errores: {len(self.errores)}")
            with open("errores_sintacticos.txt", "w", encoding="utf-8") as f:
                f.write("ERRORES SINTACTICOS ENCONTRADOS\n")
                f.write("-" * 50 + "\n")
                for e in self.errores:
                    f.write(e + "\n")
                f.write(f"\nTotal de errores: {len(self.errores)}\n")
            print("\nArchivo generado: errores_sintacticos.txt")

# ================================================================
# PUNTO DE ENTRADA
# ================================================================
if __name__ == "__main__":
    print("=== ANALIZADOR SINTACTICO ===")
    ruta = input("Ruta del archivo tabla_tokens.txt: ").strip().strip('"')
    try:
        tokens = cargar_tokens_desde_tabla(ruta)
        parser = Parser(tokens)
        parser.parse()
    except FileNotFoundError:
        print("No se encontro el archivo especificado.")
    except Exception as e:
        print("Error inesperado:", e)
