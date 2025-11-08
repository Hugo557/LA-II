# ================================================================
# ANALIZADOR SINTÁCTICO - Lenguajes y Autómatas II
# Lee el archivo "tabla_tokens.txt" generado por el analizador léxico
# y valida la estructura del lenguaje (parser recursivo descendente)
# ================================================================

import re
from dataclasses import dataclass

# ================================================================
# Mapa de equivalencias (TOKEN numérico → tipo lógico)
# ================================================================
TOKEN_MAP = {
    # Palabras reservadas
    -1: "CLASE", -2: "LEER", -3: "SWITCH", -4: "POSXY", -5: "ENTERO", -6: "VAR",
    -7: "ESCRIBIR", -8: "ENCASO", -9: "LIMPIAR", -10: "REAL", -11: "VACIO",
    -12: "SI", -13: "REPITE", -14: "EJECUTAR", -15: "REGRESAR",
    -16: "METODO", -17: "SINO", -18: "MIENTRAS", -19: "CADENA", -20: "SALIR",

    # Operadores aritméticos
    -101: "MAS", -102: "MENOS", -103: "MULT", -104: "DIV", -105: "MOD",
    -106: "IGUAL", -107: "INCR", -108: "DECR", -109: "MAS_IGUAL",
    -110: "MENOS_IGUAL", -111: "DIV_IGUAL", -112: "MULT_IGUAL",

    # Relacionales
    -120: "MENOR", -121: "MENOR_IGUAL", -122: "DISTINTO",
    -123: "MAYOR", -124: "MAYOR_IGUAL", -125: "IGUALDAD",

    # Lógicos
    -130: "NOT", -131: "AND", -132: "OR",

    # Delimitadores
    -140: "PUNTOYCOMA", -141: "COR_AP", -142: "COR_CI", -143: "COMA",
    -144: "DOS_PUNTOS", -145: "PAR_AP", -146: "PAR_CI", -147: "LLAVE_AP", -148: "LLAVE_CI",

    # Identificadores
    -300: "ID_ARROBA", -301: "ID_DOLAR", -302: "ID_AMP", -303: "ID_PORC",

    # Constantes
    -400: "CTE_CADENA", -401: "CTE_ENT", -402: "CTE_REAL",
}

# ================================================================
# Clase Token
# ================================================================
@dataclass
class Token:
    type: str
    lexeme: str
    line: int

# ================================================================
# Función para leer "tabla_tokens.txt"
# ================================================================
def cargar_tokens_desde_tabla(ruta):
    tokens = []
    with open(ruta, encoding="utf-8") as f:
        for line in f:
            # Ignorar encabezado y separadores
            if not line.strip() or line.startswith('-') or line.startswith('LEXEMA'):
                continue

            # Leer por columnas fijas según formato del léxico
            lexema = line[0:20].strip()
            token_str = line[20:30].strip()
            pts_str = line[30:40].strip()
            linea_str = line[40:50].strip()

            if not token_str or not linea_str:
                continue

            try:
                codigo = int(token_str)
                linea = int(linea_str)
            except ValueError:
                continue

            tipo = TOKEN_MAP.get(codigo, f"DESCONOCIDO_{codigo}")
            tokens.append(Token(type=tipo, lexeme=lexema, line=linea))
    print(f"📄 {len(tokens)} tokens cargados correctamente desde {ruta}\n")
    return tokens

# ================================================================
# Clase del Analizador Sintáctico (versión resumida)
# ================================================================
class ParserError(Exception):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens + [Token("EOF", "EOF", -1)]
        self.pos = 0
        self.current = self.tokens[0]

    def advance(self):
        self.pos += 1
        self.current = self.tokens[self.pos]

    def check(self, lex=None, type_=None):
        if lex is not None:
            return self.current.lexeme == lex
        if type_ is not None:
            return self.current.type == type_
        return False

    def consume(self, lex=None, type_=None, msg="Error de sintaxis"):
        if (lex and self.current.lexeme == lex) or (type_ and self.current.type == type_):
            self.advance()
        else:
            raise ParserError(f"[L{self.current.line}] {msg} — encontrado '{self.current.lexeme}'")

    # ==============================================
    # Reglas sintácticas (simplificadas)
    # ==============================================

    def parse(self):
        self.PROG()
        if self.current.type != "EOF":
            raise ParserError(f"Tokens extra después del final del programa ({self.current.lexeme})")
        print("Análisis sintáctico correcto")

    def PROG(self):
        self.consume(lex="clase", msg="Se esperaba 'clase'")
        self.consume(type_="ID_ARROBA", msg="Se esperaba nombre de clase (@id)")
        self.consume(lex="{", msg="Se esperaba '{'")
        while self.current.lexeme in ("var", "metodo", "vacio"):
            if self.current.lexeme == "var":
                self.VAR()
            else:
                self.METODO()
        self.consume(lex="}", msg="Se esperaba '}' al final de la clase")

        # ============================================================
    # <VAR> -> "var" <TIPO> <ID> ("," <ID>)* ";"
    # Acepta identificadores con prefijo @, $, %, &
    # ============================================================
    def VAR(self):
        # Palabra reservada var
        self.consume(lex="var")

        # Validar tipo de variable
        if self.current.lexeme not in ("entero", "real", "cadena"):
            raise ParserError(
                f"[L{self.current.line}] Se esperaba tipo de dato (entero, real o cadena)"
            )
        self.advance()  # consumir el tipo

        if self.current.type not in ("ID_ARROBA", "ID_DOLAR", "ID_AMP", "ID_PORC"):
            raise ParserError(
                f"[L{self.current.line}] Se esperaba identificador de variable (@id, $id, &id o %id)"
            )
        self.advance()

        while self.current.lexeme == ",":
            self.advance()
            if self.current.type not in ("ID_ARROBA", "ID_DOLAR", "ID_AMP", "ID_PORC"):
                raise ParserError(
                    f"[L{self.current.line}] Se esperaba identificador de variable después de ','"
                )
            self.advance()

        self.consume(lex=";", msg="Se esperaba ';' al final de la declaración de variable")

    def METODO(self):
        if self.current.lexeme in ("metodo", "vacio"):
            self.advance()
        else:
            raise ParserError(f"[L{self.current.line}] Se esperaba 'metodo' o 'vacio'")
        self.consume(type_="ID_ARROBA", msg="Se esperaba nombre de método (@id)")
        self.consume(lex="(", msg="Falta '(' en definición de método")
        self.consume(lex=")", msg="Falta ')' en definición de método")
        self.consume(lex="{", msg="Falta '{' en cuerpo de método")
        if self.current.lexeme == "escribir":
            self.ESCRIBIR()
        self.consume(lex="}", msg="Falta '}' al final del método")

    def ESCRIBIR(self):
        self.consume(lex="escribir")
        self.consume(lex="(", msg="Falta '(' en escribir")
        if self.check(type_="ID_ARROBA"):
            self.advance()
        elif self.check(type_="CTE_ENT") or self.check(type_="CTE_CADENA"):
            self.advance()
        else:
            raise ParserError(f"[L{self.current.line}] Argumento inválido en escribir()")
        self.consume(lex=")", msg="Falta ')' en escribir")
        self.consume(lex=";", msg="Falta ';' al final de escribir")

# ================================================================
# Punto de entrada principal
# ================================================================
if __name__ == "__main__":
    print("=== ANALIZADOR SINTÁCTICO ===")
    ruta = input("Ruta del archivo tabla_tokens.txt: ").strip()
    try:
        tokens = cargar_tokens_desde_tabla(ruta)
        parser = Parser(tokens)
        parser.parse()
    except FileNotFoundError:
        print("No se encontró el archivo especificado.")
    except ParserError as e:
        print("Error sintáctico:", e)
    except Exception as e:
        print("Error inesperado:", e)
