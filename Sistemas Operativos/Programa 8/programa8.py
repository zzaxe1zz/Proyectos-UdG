import time
import os
import random
import msvcrt
import json

# ─────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────
TIEMPO_ESPERA    = 1
TIEMPO_BLOQUEADO = 8
MEMORIA_TOTAL    = 240
TAM_MARCO        = 5
NUM_MARCOS       = MEMORIA_TOTAL // TAM_MARCO   # 48
MARCOS_SO        = 4                            # marcos 44-47 → S.O.
MARCOS_USUARIO   = NUM_MARCOS - MARCOS_SO       # 44 disponibles (0-43)
TAM_PAGINA       = TAM_MARCO                    # 5
ARCHIVO_SUSP     = "suspendidos.json"

_id_counter = 0

def siguiente_id():
    global _id_counter
    _id_counter += 1
    return _id_counter

# ─────────────────────────────────────────────────────────────────────
# PROCESO
# ─────────────────────────────────────────────────────────────────────
class Proceso:
    def __init__(self, desde_dict=None):
        if desde_dict:
            self.__dict__.update(desde_dict)
        else:
            self.id                  = siguiente_id()
            self.operacion, self.op1, self.op2 = self._generar_operacion()
            self.tme                 = random.randint(6, 20)
            self.tamano              = random.randint(6, 30)
            self.num_paginas         = (self.tamano + TAM_PAGINA - 1) // TAM_PAGINA
            self.marcos_asignados    = []
            self.tiempo_transcurrido = 0
            self.tiempo_bloqueado    = 0
            self.espera              = 0
            self.servicio            = 0
            self.llegada             = None
            self.finalizacion        = None
            self.retorno             = None
            self.respuesta           = None
            self.respondido          = False
            self.resultado           = None
            self.error               = False
            self.estado              = "NUEVO"

    def _generar_operacion(self):
        op  = random.choice(['+', '-', '*', '/', '%', '^'])
        op1 = random.randint(1, 100)
        op2 = random.randint(1, 100)
        return op, op1, op2

    def tiempo_restante_cpu(self):
        return max(0, self.tme - self.tiempo_transcurrido)

    def to_dict(self):
        return self.__dict__.copy()

def proceso_from_dict(d):
    p = Proceso(desde_dict=d)
    return p

# ─────────────────────────────────────────────────────────────────────
# OPERACIÓN ARITMÉTICA
# ─────────────────────────────────────────────────────────────────────
def ejecutar_operacion(p):
    try:
        ops = {
            '+': p.op1 + p.op2,
            '-': p.op1 - p.op2,
            '*': p.op1 * p.op2,
            '/': round(p.op1 / p.op2, 4),
            '%': p.op1 % p.op2,
            '^': p.op1 ** p.op2,
        }
        return ops[p.operacion]
    except Exception:
        return "ERROR"

# ─────────────────────────────────────────────────────────────────────
# GESTIÓN DE MEMORIA
# ─────────────────────────────────────────────────────────────────────
marcos = [None] * NUM_MARCOS

def marcos_libres_lista():
    return [i for i in range(MARCOS_USUARIO) if marcos[i] is None]

def asignar_marcos(proceso):
    libres = marcos_libres_lista()
    if len(libres) < proceso.num_paginas:
        return False
    seleccionados = libres[:proceso.num_paginas]
    for m in seleccionados:
        marcos[m] = proceso.id
    proceso.marcos_asignados = seleccionados
    return True

def liberar_marcos(proceso):
    for m in proceso.marcos_asignados:
        marcos[m] = None
    proceso.marcos_asignados = []

# ─────────────────────────────────────────────────────────────────────
# ARCHIVO DE SUSPENDIDOS
# ─────────────────────────────────────────────────────────────────────
def guardar_suspendidos(cola_suspendidos):
    data = [p.to_dict() for p in cola_suspendidos]
    with open(ARCHIVO_SUSP, 'w') as f:
        json.dump(data, f, indent=2)

def cargar_suspendidos():
    try:
        with open(ARCHIVO_SUSP, 'r') as f:
            data = json.load(f)
        return [proceso_from_dict(d) for d in data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# ─────────────────────────────────────────────────────────────────────
# UTILIDADES DE TABLA (box-drawing compacto)
# ─────────────────────────────────────────────────────────────────────
def linea_h(anchos, tipo="mid"):
    mapa = {
        "top": ("╔", "╦", "╗", "═"),
        "mid": ("╠", "╬", "╣", "═"),
        "bot": ("╚", "╩", "╝", "═"),
        "sep": ("├", "┼", "┤", "─"),
    }
    l, m, r, c = mapa[tipo]
    return l + m.join(c * (a + 2) for a in anchos) + r

def fila(valores, anchos):
    celdas = [f" {str(v):<{a}} " for v, a in zip(valores, anchos)]
    return "║" + "║".join(celdas) + "║"

def fila_vacia(texto, anchos):
    w = sum(a + 3 for a in anchos) + 1 - 2
    return "║" + texto.center(w) + "║"

def limpiar():
    os.system("cls" if os.name == "nt" else "clear")

# ─────────────────────────────────────────────────────────────────────
# MAPA DE MEMORIA COMPACTO (2 columnas, una línea por marco)
# ─────────────────────────────────────────────────────────────────────
C_LISTO     = "\033[34m"
C_EJECUCION = "\033[32m"
C_BLOQUEADO = "\033[35m"
C_SUSPENDIDO= "\033[33m"
C_SO        = "\033[90m"
C_RESET     = "\033[0m"

def color_marco(idx, ejecucion, bloqueados, suspendidos):
    if idx >= MARCOS_USUARIO:
        return C_SO
    pid = marcos[idx]
    if pid is None:
        return C_RESET
    if ejecucion and pid == ejecucion.id:
        return C_EJECUCION
    for p in bloqueados:
        if p.id == pid:
            return C_BLOQUEADO
    return C_LISTO

def mapa_memoria_compacto(ejecucion, bloqueados, suspendidos):
    """Devuelve el mapa en dos columnas de 22 marcos, con etiquetas de SO corregidas."""
    lineas = []
    lineas.append(
        f" MEM(48 marcos×5) Libres:{len(marcos_libres_lista())}/{MARCOS_USUARIO}")

    for row in range(24):
        izq = row
        der = row + 24

        def celda(idx):
            if idx >= MARCOS_USUARIO:
                color = C_SO
            else:
                pid = marcos[idx]
                if pid is None:
                    color = C_RESET
                elif ejecucion and pid == ejecucion.id:
                    color = C_EJECUCION
                elif any(p.id == pid for p in bloqueados):
                    color = C_BLOQUEADO
                else:
                    color = C_LISTO

            pid = marcos[idx]
            if idx >= MARCOS_USUARIO:
                lbl = "SO"
            elif pid is None:
                lbl = "--"
            else:
                lbl = f"P{pid}"

            return f"{color}[{idx:>2}]{lbl:<4}{C_RESET}"

        lineas.append(f" {celda(izq)} {celda(der)}")
    return lineas

# ─────────────────────────────────────────────────────────────────────
# PANTALLA PRINCIPAL COMPACTA (dos columnas: mem | colas)
# ─────────────────────────────────────────────────────────────────────
def mostrar_estado(nuevos, listos, ejecucion, bloqueados, suspendidos,
                   terminados, reloj, tiempo_quantum, quantum):
    limpiar()

    libres = len(marcos_libres_lista())
    print(f" RELOJ:{reloj}  MARCOS LIBRES:{libres}/{MARCOS_USUARIO}"
          f"  NUEVOS:{len(nuevos)}  QUANTUM:{quantum}"
          f"  SUSPENDIDOS:{len(suspendidos)}")

    # Próximo suspendido que podría regresar
    if suspendidos:
        ps = suspendidos[0]
        print(f" Suspendido→regresar: P{ps.id}  tam={ps.tamano}  "
              f"necesita {ps.num_paginas} marcos")
    print()

    # ── Construcción de columnas ────────────────────────────────────
    mem_lines = mapa_memoria_compacto(ejecucion, bloqueados, suspendidos)

    # Cola listos
    cola_str = [" COLA DE LISTOS (Round-Robin)"]
    ah = [4, 5, 10, 4, 4, 4, 6, 5, 6]
    cola_str.append(" " + linea_h(ah, "top"))
    cola_str.append(" " + fila(["#", "ID", "Op", "TME", "Tam", "Pgs", "T.Tr", "T.Rt", "Esp"], ah))
    cola_str.append(" " + linea_h(ah, "mid"))
    if listos:
        for i, p in enumerate(listos):
            op = f"{p.op1}{p.operacion}{p.op2}"[:10]
            marca = "►" if i == 0 else " "
            cola_str.append(" " + fila([marca, f"P{p.id}", op, p.tme,
                                        p.tamano, p.num_paginas,
                                        p.tiempo_transcurrido,
                                        p.tiempo_restante_cpu(),
                                        p.espera], ah))
    else:
        cola_str.append(" " + fila_vacia("(vacía)", ah))
    cola_str.append(" " + linea_h(ah, "bot"))

    # Ejecución
    cola_str.append("")
    cola_str.append(" EN EJECUCIÓN")
    ae = [5, 10, 4, 4, 14, 5, 5, 6, 5, 7]
    cola_str.append(" " + linea_h(ae, "top"))
    cola_str.append(" " + fila(["ID", "Op", "TME", "Tam", "Marcos",
                                 "T.Tr", "T.Rt", "T.Ll", "T.Rp", "Quant"], ae))
    cola_str.append(" " + linea_h(ae, "mid"))
    if ejecucion:
        e   = ejecucion
        op  = f"{e.op1}{e.operacion}{e.op2}"[:10]
        rp  = e.respuesta if e.respondido else "—"
        marc= str(e.marcos_asignados)[:14]
        cola_str.append(" " + fila([f"P{e.id}", op, e.tme, e.tamano,
                                     marc, e.tiempo_transcurrido,
                                     e.tiempo_restante_cpu(),
                                     e.llegada, rp, tiempo_quantum], ae))
    else:
        cola_str.append(" " + fila_vacia("(libre)", ae))
    cola_str.append(" " + linea_h(ae, "bot"))

    # Bloqueados
    cola_str.append("")
    cola_str.append(" BLOQUEADOS")
    ab = [5, 8, 10]
    cola_str.append(" " + linea_h(ab, "top"))
    cola_str.append(" " + fila(["ID", "T.Bloq", "T.Rest.B"], ab))
    cola_str.append(" " + linea_h(ab, "mid"))
    if bloqueados:
        for p in bloqueados:
            rest = max(0, TIEMPO_BLOQUEADO - p.tiempo_bloqueado)
            cola_str.append(" " + fila([f"P{p.id}", p.tiempo_bloqueado, rest], ab))
    else:
        cola_str.append(" " + fila_vacia("(vacía)", ab))
    cola_str.append(" " + linea_h(ab, "bot"))

    # Suspendidos
    cola_str.append("")
    cola_str.append(" SUSPENDIDOS (en disco)")
    as_ = [5, 5, 5, 8]
    cola_str.append(" " + linea_h(as_, "top"))
    cola_str.append(" " + fila(["ID", "Tam", "Pgs", "T.Trans"], as_))
    cola_str.append(" " + linea_h(as_, "mid"))
    if suspendidos:
        for p in suspendidos:
            cola_str.append(" " + fila([f"P{p.id}", p.tamano,
                                         p.num_paginas,
                                         p.tiempo_transcurrido], as_))
    else:
        cola_str.append(" " + fila_vacia("(ninguno)", as_))
    cola_str.append(" " + linea_h(as_, "bot"))

    # Terminados
    cola_str.append("")
    cola_str.append(" TERMINADOS")
    at = [5, 10, 8]
    cola_str.append(" " + linea_h(at, "top"))
    cola_str.append(" " + fila(["ID", "Op", "Result."], at))
    cola_str.append(" " + linea_h(at, "mid"))
    if terminados:
        for p in terminados:
            res = "ERROR" if p.error else str(p.resultado)[:8]
            op  = f"{p.op1}{p.operacion}{p.op2}"[:10]
            cola_str.append(" " + fila([f"P{p.id}", op, res], at))
    else:
        cola_str.append(" " + fila_vacia("(ninguno)", at))
    cola_str.append(" " + linea_h(at, "bot"))

    # ── Imprimir lado a lado: memoria (izq) | colas (der) ──────────
    max_rows = max(len(mem_lines), len(cola_str))
    for i in range(max_rows):
        izq = mem_lines[i] if i < len(mem_lines) else ""
        der = cola_str[i]  if i < len(cola_str)  else ""
        # mem_lines tienen ~18 chars, ajustamos a 22
        print(f"{izq:<22}  {der}")

    print()
    print(" I=Bloq  E=Error  P=Pausa  N=Nuevo  B=BCP  T=TabPags  S=Suspender  R=Regresar")

# ─────────────────────────────────────────────────────────────────────
# TABLA BCP (tecla B)
# ─────────────────────────────────────────────────────────────────────
def mostrar_bcp(nuevos, listos, ejecucion, bloqueados, suspendidos,
                terminados, reloj, quantum):
    limpiar()
    print(f" TABLA BCP — RELOJ:{reloj}  QUANTUM:{quantum}")
    print()

    cols   = ["ID", "Estado", "Op", "TME", "Tam", "Pgs",
              "T.Ll", "T.Fin", "T.Ret", "T.Esp",
              "T.Serv", "T.RstCPU", "T.Resp", "Result."]
    anchos = [5, 9, 10, 4, 4, 4,
              5, 5, 5, 5,
              6, 8, 6, 10]

    print(" " + linea_h(anchos, "top"))
    print(" " + fila(cols, anchos))
    print(" " + linea_h(anchos, "mid"))

    todos = []
    for p in nuevos:      todos.append(('NUEVO',    p))
    for p in listos:      todos.append(('LISTO',    p))
    if ejecucion:         todos.append(('EJEC',     ejecucion))
    for p in bloqueados:  todos.append(('BLOQ',     p))
    for p in suspendidos: todos.append(('SUSP',     p))
    for p in terminados:  todos.append(('TERM',     p))
    todos.sort(key=lambda x: x[1].id)

    for i, (estado, p) in enumerate(todos):
        op = f"{p.op1}{p.operacion}{p.op2}"[:10]
        if estado == 'NUEVO':
            vals = [f"P{p.id}", estado, op, p.tme, p.tamano, p.num_paginas,
                    "—","—","—","—","—","—","—","—"]
        elif estado in ('LISTO', 'EJEC', 'BLOQ', 'SUSP'):
            resp_d  = str(p.respuesta) if p.respondido else "—"
            tr_p    = (reloj - p.llegada) if p.llegada is not None else 0
            te_p    = tr_p - p.tiempo_transcurrido
            vals = [f"P{p.id}", estado, op, p.tme, p.tamano, p.num_paginas,
                    str(p.llegada) if p.llegada is not None else "—",
                    "—","—", str(te_p), str(p.tiempo_transcurrido),
                    str(p.tiempo_restante_cpu()), resp_d, "—"]
        else:  # TERM
            res = "ERROR" if p.error else str(p.resultado)[:10]
            est = "ERROR" if p.error else "Normal"
            vals = [f"P{p.id}", est, op, p.tme, p.tamano, p.num_paginas,
                    str(p.llegada), str(p.finalizacion), str(p.retorno),
                    str(p.espera), str(p.servicio),
                    "0", str(p.respuesta), res]

        print(" " + fila(vals, anchos))
        if i < len(todos) - 1:
            print(" " + linea_h(anchos, "sep"))

    print(" " + linea_h(anchos, "bot"))
    print()
    print(" Presione C para continuar...")
    _esperar_c()

# ─────────────────────────────────────────────────────────────────────
# TABLA DE PÁGINAS (tecla T) — incluye bloqueados
# ─────────────────────────────────────────────────────────────────────
def mostrar_tabla_paginas(listos, ejecucion, bloqueados, reloj):
    limpiar()
    print(f" TABLA DE PÁGINAS — RELOJ:{reloj}")
    print()

    activos = []
    if ejecucion:
        activos.append(ejecucion)
    activos += listos + bloqueados   # req 4: incluir bloqueados

    cols_p  = ["ID", "Estado", "Tam", "Pgs", "Página", "Marco"]
    anchos_p = [6, 9, 5, 4, 7, 6]

    if activos:
        print(" " + linea_h(anchos_p, "top"))
        print(" " + fila(cols_p, anchos_p))
        print(" " + linea_h(anchos_p, "mid"))
        for idx, p in enumerate(activos):
            for pag, marco in enumerate(p.marcos_asignados):
                id_s  = f"P{p.id}" if pag == 0 else ""
                est_s = p.estado   if pag == 0 else ""
                tam_s = str(p.tamano)      if pag == 0 else ""
                pgs_s = str(p.num_paginas) if pag == 0 else ""
                print(" " + fila([id_s, est_s, tam_s, pgs_s, pag, marco], anchos_p))
            if idx < len(activos) - 1:
                print(" " + linea_h(anchos_p, "sep"))
        print(" " + linea_h(anchos_p, "bot"))
    else:
        print(" (ningún proceso activo en memoria)")

    libres = marcos_libres_lista()
    print()
    print(f" Marcos libres ({len(libres)}): {libres}")
    print()
    print(" Presione C para continuar...")
    _esperar_c()

# ─────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────
def _esperar_c():
    while True:
        if msvcrt.kbhit():
            if msvcrt.getch().decode('utf-8', errors='ignore').upper() == 'C':
                break
        time.sleep(0.05)

def terminar_proceso(p, reloj, error=False):
    p.error = error
    if not error:
        p.resultado = ejecutar_operacion(p)
    p.finalizacion = reloj
    p.servicio     = p.tiempo_transcurrido
    p.retorno      = p.finalizacion - p.llegada
    p.espera       = p.retorno - p.servicio
    p.estado       = "TERMINADO"
    liberar_marcos(p)

# ─────────────────────────────────────────────────────────────────────
# LOOP PRINCIPAL
# ─────────────────────────────────────────────────────────────────────
def main():
    os.system("")   # activa ANSI en Windows
    limpiar()

    n       = int(input("Número inicial de procesos: "))
    quantum = int(input("Tamaño del Quantum: "))
    time.sleep(0.5)

    cola_nuevos     = [Proceso() for _ in range(n)]
    cola_listos     = []
    cola_bloqueados = []
    cola_suspendidos= cargar_suspendidos()   # carga si hay archivo previo
    terminados      = []
    proceso_actual  = None
    reloj           = 0
    tiempo_quantum  = 0
    total_esperados = n + len(cola_suspendidos)

    # Limpiar marcos de procesos que venían suspendidos (no están en RAM)
    for p in cola_suspendidos:
        p.marcos_asignados = []
        p.estado = "SUSPENDIDO"

    while len(terminados) < total_esperados:

        # 1. Planificador a largo plazo
        for p in cola_nuevos[:]:
            if asignar_marcos(p):
                cola_nuevos.remove(p)
                p.llegada = reloj
                p.estado  = "LISTO"
                cola_listos.append(p)
            else:
                break

        # 2. Avanzar bloqueados
        for p in cola_bloqueados[:]:
            p.tiempo_bloqueado += 1
            if p.tiempo_bloqueado >= TIEMPO_BLOQUEADO:
                p.tiempo_bloqueado = 0
                cola_bloqueados.remove(p)
                p.estado = "LISTO"
                cola_listos.append(p)

        # 3. Despachar Round-Robin
        if not proceso_actual and cola_listos:
            proceso_actual        = cola_listos.pop(0)
            proceso_actual.estado = "EJECUCION"
            tiempo_quantum        = 0
            if not proceso_actual.respondido:
                proceso_actual.respuesta  = reloj - proceso_actual.llegada
                proceso_actual.respondido = True

        # 4. Acumular espera en listos
        for p in cola_listos:
            p.espera += 1

        # 5. Mostrar
        mostrar_estado(cola_nuevos, cola_listos, proceso_actual,
                       cola_bloqueados, cola_suspendidos,
                       terminados, reloj, tiempo_quantum, quantum)

        # 6. Polling de teclas
        inicio = time.time()
        while time.time() - inicio < TIEMPO_ESPERA:
            if msvcrt.kbhit():
                tecla = msvcrt.getch().decode('utf-8', errors='ignore').upper()

                # ── I: Bloquear ────────────────────────────────────
                if tecla == 'I' and proceso_actual:
                    proceso_actual.tiempo_bloqueado = 0
                    proceso_actual.estado = "BLOQUEADO"
                    cola_bloqueados.append(proceso_actual)
                    proceso_actual = None
                    tiempo_quantum = 0

                # ── E: Error ───────────────────────────────────────
                elif tecla == 'E' and proceso_actual:
                    terminar_proceso(proceso_actual, reloj, error=True)
                    terminados.append(proceso_actual)
                    proceso_actual = None
                    tiempo_quantum = 0

                # ── P: Pausa ───────────────────────────────────────
                elif tecla == 'P':
                    print("\n PAUSADO — presione C para continuar")
                    _esperar_c()

                # ── N: Nuevo proceso ───────────────────────────────
                elif tecla == 'N':
                    nuevo = Proceso()
                    nuevo.estado = "NUEVO"
                    cola_nuevos.append(nuevo)
                    total_esperados += 1

                # ── B: Tabla BCP ───────────────────────────────────
                elif tecla == 'B':
                    mostrar_bcp(cola_nuevos, cola_listos, proceso_actual,
                                cola_bloqueados, cola_suspendidos,
                                terminados, reloj, quantum)

                # ── T: Tabla de páginas ────────────────────────────
                elif tecla == 'T':
                    mostrar_tabla_paginas(cola_listos, proceso_actual,
                                         cola_bloqueados, reloj)

                # ── S: Suspender (primero de bloqueados → disco) ───
                elif tecla == 'S':
                    if cola_bloqueados:
                        p_susp = cola_bloqueados.pop(0)
                        liberar_marcos(p_susp)
                        p_susp.estado = "SUSPENDIDO"
                        cola_suspendidos.append(p_susp)
                        guardar_suspendidos(cola_suspendidos)

                # ── R: Regresar (primero de suspendidos → listos) ──
                elif tecla == 'R':
                    if cola_suspendidos:
                        p_reg = cola_suspendidos[0]
                        if asignar_marcos(p_reg):
                            cola_suspendidos.pop(0)
                            p_reg.estado           = "LISTO"
                            p_reg.tiempo_bloqueado = 0
                            cola_listos.append(p_reg)
                            guardar_suspendidos(cola_suspendidos)

            time.sleep(0.05)

        # 7. Tick de CPU
        if proceso_actual:
            proceso_actual.tiempo_transcurrido += 1
            tiempo_quantum += 1

            if proceso_actual.tiempo_transcurrido >= proceso_actual.tme:
                terminar_proceso(proceso_actual, reloj + 1)
                terminados.append(proceso_actual)
                proceso_actual = None
                tiempo_quantum = 0
            elif tiempo_quantum >= quantum:
                proceso_actual.estado = "LISTO"
                cola_listos.append(proceso_actual)
                proceso_actual = None
                tiempo_quantum = 0

        reloj += 1

    # ── Limpiar archivo de suspendidos al terminar ──────────────────
    try:
        os.remove(ARCHIVO_SUSP)
    except FileNotFoundError:
        pass

    # ── Tabla final ─────────────────────────────────────────────────
    limpiar()
    print(" SIMULACIÓN FINALIZADA")
    print()

    cols_f  = ["ID", "Fin", "Op", "T.Ll", "T.Fin",
               "T.Ret", "T.Resp", "T.Esp", "T.Serv", "Result."]
    anchos_f = [5, 6, 12, 5, 6,
                6, 6, 5, 6, 12]

    print(" " + linea_h(anchos_f, "top"))
    print(" " + fila(cols_f, anchos_f))
    print(" " + linea_h(anchos_f, "mid"))

    lista_final = sorted(terminados, key=lambda x: x.id)
    for i, p in enumerate(lista_final):
        res  = "ERROR" if p.error else str(p.resultado)
        est  = "ERROR" if p.error else "Normal"
        oper = f"{p.op1}{p.operacion}{p.op2}"
        print(" " + fila([f"P{p.id}", est, oper, p.llegada, p.finalizacion,
                           p.retorno, p.respuesta, p.espera, p.servicio, res],
                          anchos_f))
        if i < len(lista_final) - 1:
            print(" " + linea_h(anchos_f, "sep"))

    print(" " + linea_h(anchos_f, "bot"))
    print()
    print(f" Tiempo total de simulación: {reloj}")
    print()
    input(" Presione ENTER para salir...")

if __name__ == "__main__":
    main()
