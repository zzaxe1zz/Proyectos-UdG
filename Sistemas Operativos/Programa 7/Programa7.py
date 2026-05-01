import time
import os
import random
import msvcrt

# ─────────────────────────────────────────────────────────────────────
#  CONSTANTES
# ─────────────────────────────────────────────────────────────────────
TIEMPO_ESPERA = 1
TIEMPO_BLOQUEADO = 8

MEMORIA_TOTAL = 240
TAM_MARCO = 5
NUM_MARCOS = MEMORIA_TOTAL // TAM_MARCO   # 48
MARCOS_SO = 4                            # marcos 44-47 → S.O.
MARCOS_USUARIO = NUM_MARCOS - MARCOS_SO       # 44 disponibles (0-43)
TAM_PAGINA = TAM_MARCO                    # 5

_id_counter = 0


def siguiente_id():
    global _id_counter
    _id_counter += 1
    return _id_counter


# ─────────────────────────────────────────────────────────────────────
#  PROCESO
# ─────────────────────────────────────────────────────────────────────
class Proceso:
    def __init__(self):
        self.id = siguiente_id()
        self.operacion, self.op1, self.op2 = self._generar_operacion()
        self.tme = random.randint(6, 20)
        self.tamano = random.randint(6, 30)
        self.num_paginas = (self.tamano + TAM_PAGINA - 1) // TAM_PAGINA
        self.marcos_asignados = []

        self.tiempo_transcurrido = 0
        self.tiempo_bloqueado = 0
        self.espera = 0
        self.servicio = 0
        self.llegada = None
        self.finalizacion = None
        self.retorno = None
        self.respuesta = None
        self.respondido = False
        self.resultado = None
        self.error = False
        self.estado = "NUEVO"

    def _generar_operacion(self):
        op = random.choice(['+', '-', '*', '/', '%', '^'])
        op1 = random.randint(1, 100)
        op2 = random.randint(1, 100)
        return op, op1, op2

    def tiempo_restante_cpu(self):
        return max(0, self.tme - self.tiempo_transcurrido)


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
#  GESTIÓN DE MEMORIA
# ─────────────────────────────────────────────────────────────────────
marcos = [None] * NUM_MARCOS   # None = libre | int = id del proceso


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
#  UTILIDADES DE TABLA
# ─────────────────────────────────────────────────────────────────────
def linea_h(anchos, tipo="mid"):
    mapa = {
        "top": ("╔", "╦", "╗", "═"),
        "mid": ("╠", "╬", "╣", "═"),
        "bot": ("╚", "╩", "╝", "═"),
        "sep": ("├", "┼", "┤", "─"),
    }
    l, m, r, c = mapa[tipo]
    partes = [c * (a + 2) for a in anchos]
    return l + m.join(partes) + r


def fila(valores, anchos):
    celdas = [f" {str(v):<{a}} " for v, a in zip(valores, anchos)]
    return "║" + "║".join(celdas) + "║"


def ancho_total(anchos):
    return sum(a + 3 for a in anchos) + 1


def fila_vacia(texto, anchos):
    w = ancho_total(anchos) - 2
    return "║" + texto.center(w) + "║"


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


# ─────────────────────────────────────────────────────────────────────
#  MAPA DE MEMORIA  (colores ANSI)
# ─────────────────────────────────────────────────────────────────────
C_LISTO = "\033[34m"   # azul
C_EJECUCION = "\033[31m"   # rojo
C_BLOQUEADO = "\033[35m"   # morado
C_SO = "\033[90m"   # gris oscuro (S.O.)
C_RESET = "\033[0m"


def color_marco(idx, ejecucion, bloqueados):
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


def mostrar_memoria(ejecucion, listos, bloqueados):
    print("  MAPA DE MEMORIA  (48 marcos, tamaño 5 c/u)")
    print(f"  {'Marco':<7}{'Contenido':<12}   {'Marco':<7}{'Contenido':<12}")
    print("  " + "─" * 46)
    for row in range(24):
        izq = row
        der = row + 24

        def celda(idx):
            color = color_marco(idx, ejecucion, bloqueados)
            pid = marcos[idx]
            if idx >= MARCOS_USUARIO:
                label = "S.O."
            elif pid is None:
                label = "libre"
            else:
                label = f"P{pid}"
            return f"{color}[{idx:>2}] {label:<7}{C_RESET}"

        print(f"  {celda(izq)}      {celda(der)}")
    print()


# ─────────────────────────────────────────────────────────────────────
#  PANTALLA PRINCIPAL
# ─────────────────────────────────────────────────────────────────────
def mostrar_estado(nuevos, listos, ejecucion, bloqueados, terminados, reloj, tiempo_quantum, quantum):
    limpiar()

    libres = len(marcos_libres_lista())
    print(
        f"  RELOJ: {reloj}   |   MARCOS LIBRES: {libres}/{MARCOS_USUARIO}"
        f"   |   NUEVOS EN ESPERA: {len(nuevos)}"
        f"   |   QUANTUM: {quantum}"
    )
    if nuevos:
        sig = nuevos[0]
        print(f"  Próximo a admitir → P{sig.id}  tamaño={sig.tamano}  "
              f"páginas={sig.num_paginas}  (necesita {sig.num_paginas} marcos libres)")
    print()

    mostrar_memoria(ejecucion, listos, bloqueados)

    # ── Cola de Listos ──────────────────────────────────────────────
    print("  COLA DE LISTOS  (Round-Robin)")
    cols_l = ["#", "ID", "Operación", "TME", "Tam", "Págs",
              "T.Trans", "T.Rest", "T.Espera", "Turno"]
    anchos_l = [3,   6,   12,          5,     5,    5,
                7,       6,      8,         6]
    print("  " + linea_h(anchos_l, "top"))
    print("  " + fila(cols_l, anchos_l))
    print("  " + linea_h(anchos_l, "mid"))
    if listos:
        for i, p in enumerate(listos):
            oper = f"{p.op1} {p.operacion} {p.op2}"
            carrusel = "◄ sig" if i == 0 else ""
            print("  " + fila([i+1, f"P{p.id}", oper, p.tme, p.tamano,
                               p.num_paginas, p.tiempo_transcurrido,
                               p.tiempo_restante_cpu(), p.espera, carrusel], anchos_l))
    else:
        print("  " + fila_vacia("(vacía)", anchos_l))
    print("  " + linea_h(anchos_l, "bot"))
    print()

    # ── En Ejecución ────────────────────────────────────────────────
    print("  EN EJECUCIÓN")
    cols_e = ["ID", "Operación", "TME", "Tam", "Marcos",
              "T.Trans", "T.Rest", "T.Llegada", "T.Resp", "T.Espera", "T.Quantum"]
    anchos_e = [6,   12,          5,     5,     20,
                7,       6,      9,          6,       8,         9]
    print("  " + linea_h(anchos_e, "top"))
    print("  " + fila(cols_e, anchos_e))
    print("  " + linea_h(anchos_e, "mid"))
    if ejecucion:
        e = ejecucion
        oper = f"{e.op1} {e.operacion} {e.op2}"
        resp = e.respuesta if e.respondido else "—"
        te_parcial = (reloj - e.llegada) - e.tiempo_transcurrido
        marc_str = str(e.marcos_asignados)[:18]
        print("  " + fila([f"P{e.id}", oper, e.tme, e.tamano, marc_str,
                           e.tiempo_transcurrido, e.tiempo_restante_cpu(),
                           e.llegada, resp, te_parcial, tiempo_quantum], anchos_e))
    else:
        print("  " + fila_vacia("(procesador libre)", anchos_e))
    print("  " + linea_h(anchos_e, "bot"))
    print()

    # ── Cola de Bloqueados ──────────────────────────────────────────
    print("  COLA DE BLOQUEADOS")
    cols_b = ["ID", "T.Bloqueado", "T.Rest.Bloqueo"]
    anchos_b = [6,   11,            14]
    print("  " + linea_h(anchos_b, "top"))
    print("  " + fila(cols_b, anchos_b))
    print("  " + linea_h(anchos_b, "mid"))
    if bloqueados:
        for p in bloqueados:
            restante = max(0, TIEMPO_BLOQUEADO - p.tiempo_bloqueado)
            print(
                "  " + fila([f"P{p.id}", p.tiempo_bloqueado, restante], anchos_b))
    else:
        print("  " + fila_vacia("(vacía)", anchos_b))
    print("  " + linea_h(anchos_b, "bot"))
    print()

    # ── Terminados ──────────────────────────────────────────────────
    print("  TERMINADOS")
    cols_t = ["ID", "Operación", "Resultado"]
    anchos_t = [6,   14,          14]
    print("  " + linea_h(anchos_t, "top"))
    print("  " + fila(cols_t, anchos_t))
    print("  " + linea_h(anchos_t, "mid"))
    if terminados:
        for p in terminados:
            res = "ERROR" if p.error else str(p.resultado)
            oper = f"{p.op1} {p.operacion} {p.op2}"
            print("  " + fila([f"P{p.id}", oper, res], anchos_t))
    else:
        print("  " + fila_vacia("(ninguno)", anchos_t))
    print("  " + linea_h(anchos_t, "bot"))
    print()
    print("  Teclas: I=Bloqueado  E=Error  P=Pausa  N=Nuevo  B=BCP  T=TabPáginas")


# ─────────────────────────────────────────────────────────────────────
#  TABLA BCP  (tecla B)
# ─────────────────────────────────────────────────────────────────────
def mostrar_bcp(nuevos, listos, ejecucion, bloqueados, terminados, reloj, quantum):
    limpiar()
    print(
        f"  TABLA DE PROCESOS (BCP)  —  RELOJ: {reloj}  |  QUANTUM: {quantum}")
    print()

    cols = ["ID", "Estado", "Operación", "TME", "Tam", "Págs",
            "T.Llegada", "T.Final", "T.Retorno", "T.Espera",
            "T.Servicio", "T.RestCPU", "T.Respuesta", "Resultado"]
    anchos = [6,    10,       12,          5,     5,    5,
              9,          7,        9,         8,
              10,          9,          11,           12]

    print("  " + linea_h(anchos, "top"))
    print("  " + fila(cols, anchos))
    print("  " + linea_h(anchos, "mid"))

    todos = []
    for p in nuevos:
        todos.append(('NUEVO',     p))
    for p in listos:
        todos.append(('LISTO',     p))
    if ejecucion:
        todos.append(('EJECUCION', ejecucion))
    for p in bloqueados:
        todos.append(('BLOQUEADO', p))
    for p in terminados:
        todos.append(('TERMINADO', p))
    todos.sort(key=lambda x: x[1].id)

    for i, (estado, p) in enumerate(todos):
        oper = f"{p.op1} {p.operacion} {p.op2}"

        if estado == 'NUEVO':
            vals = [f"P{p.id}", estado, oper, p.tme, p.tamano, p.num_paginas,
                    "—", "—", "—", "—", "—", "—", "—", "—"]

        elif estado in ('LISTO', 'EJECUCION', 'BLOQUEADO'):
            resp_d = str(p.respuesta) if p.respondido else "—"
            ts_parcial = p.tiempo_transcurrido
            tr_parcial = reloj - p.llegada
            te_parcial = tr_parcial - ts_parcial
            vals = [f"P{p.id}", estado, oper, p.tme, p.tamano, p.num_paginas,
                    str(p.llegada), "—", "—",
                    str(te_parcial), str(ts_parcial),
                    str(p.tiempo_restante_cpu()), resp_d, "—"]

        else:  # TERMINADO
            res = "ERROR" if p.error else str(p.resultado)
            est = "ERROR" if p.error else "Normal"
            vals = [f"P{p.id}", est, oper, p.tme, p.tamano, p.num_paginas,
                    str(p.llegada), str(p.finalizacion), str(p.retorno),
                    str(p.espera), str(p.servicio),
                    "0", str(p.respuesta), res]

        print("  " + fila(vals, anchos))
        if i < len(todos) - 1:
            print("  " + linea_h(anchos, "sep"))

    print("  " + linea_h(anchos, "bot"))
    print()
    print("  Presione C para continuar...")
    _esperar_c()


# ─────────────────────────────────────────────────────────────────────
#  TABLA DE PÁGINAS  (tecla T)
# ─────────────────────────────────────────────────────────────────────
def mostrar_tabla_paginas(nuevos, listos, ejecucion, bloqueados, terminados, reloj):
    limpiar()
    print(f"  TABLA DE PÁGINAS  —  RELOJ: {reloj}")
    print()

    activos = []
    if ejecucion:
        activos.append(ejecucion)
    activos += listos + bloqueados

    cols_p = ["ID", "Estado", "Tam", "Págs", "Página", "Marco"]
    anchos_p = [6,   10,       5,    5,      7,        6]

    if activos:
        print("  " + linea_h(anchos_p, "top"))
        print("  " + fila(cols_p, anchos_p))
        print("  " + linea_h(anchos_p, "mid"))

        for idx, p in enumerate(activos):
            for pag, marco in enumerate(p.marcos_asignados):
                if pag == 0:
                    id_str = f"P{p.id}"
                    est_str = p.estado
                    tam_str = str(p.tamano)
                    pag_cnt = str(p.num_paginas)
                else:
                    id_str = est_str = tam_str = pag_cnt = ""
                print("  " + fila([id_str, est_str, tam_str, pag_cnt,
                                   pag, marco], anchos_p))
            if idx < len(activos) - 1:
                print("  " + linea_h(anchos_p, "sep"))

        print("  " + linea_h(anchos_p, "bot"))
    else:
        print("  (ningún proceso activo en memoria)")

    print()
    libres = marcos_libres_lista()
    print(f"  Marcos libres ({len(libres)}): {libres}")
    print()
    print("  Presione C para continuar...")
    _esperar_c()


# ─────────────────────────────────────────────────────────────────────
#  HELPERS
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
    p.servicio = p.tiempo_transcurrido
    p.retorno = p.finalizacion - p.llegada
    p.espera = p.retorno - p.servicio
    p.estado = "TERMINADO"
    liberar_marcos(p)


# ─────────────────────────────────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────────────────────────────────
def main():
    os.system("")   # activa colores ANSI en Windows

    limpiar()
    n = int(input("Número inicial de procesos: "))
    quantum = int(input("Tamaño del Quantum: "))
    time.sleep(1)

    cola_nuevos = [Proceso() for _ in range(n)]
    cola_listos = []
    cola_bloqueados = []
    terminados = []
    proceso_actual = None
    reloj = 0
    tiempo_quantum = 0
    total_esperados = n

    while len(terminados) < total_esperados:

        # 1. Planificador a largo plazo — admitir en orden FIFO si hay marcos
        for p in cola_nuevos[:]:
            if asignar_marcos(p):
                cola_nuevos.remove(p)
                p.llegada = reloj
                p.estado = "LISTO"
                cola_listos.append(p)
            else:
                break  # no hay espacio; esperar al siguiente tick

        # 2. Avanzar bloqueados
        for p in cola_bloqueados[:]:
            p.tiempo_bloqueado += 1
            if p.tiempo_bloqueado >= TIEMPO_BLOQUEADO:
                p.tiempo_bloqueado = 0
                cola_bloqueados.remove(p)
                p.estado = "LISTO"
                cola_listos.append(p)

        # 3. Despachar (Round-Robin)
        if not proceso_actual and cola_listos:
            proceso_actual = cola_listos.pop(0)
            proceso_actual.estado = "EJECUCION"
            tiempo_quantum = 0
            if not proceso_actual.respondido:
                proceso_actual.respuesta = reloj - proceso_actual.llegada
                proceso_actual.respondido = True

        # 4. Acumular espera en cola listos
        for p in cola_listos:
            p.espera += 1

        # 5. Mostrar pantalla
        mostrar_estado(cola_nuevos, cola_listos, proceso_actual,
                       cola_bloqueados, terminados, reloj, tiempo_quantum, quantum)

        # 6. Polling de teclas (1 segundo con muestreo a 50 ms)
        inicio = time.time()
        while time.time() - inicio < TIEMPO_ESPERA:
            if msvcrt.kbhit():
                tecla = msvcrt.getch().decode('utf-8', errors='ignore').upper()

                if tecla == 'I' and proceso_actual:
                    proceso_actual.tiempo_bloqueado = 0
                    proceso_actual.estado = "BLOQUEADO"
                    cola_bloqueados.append(proceso_actual)
                    proceso_actual = None
                    tiempo_quantum = 0

                elif tecla == 'E' and proceso_actual:
                    terminar_proceso(proceso_actual, reloj, error=True)
                    terminados.append(proceso_actual)
                    proceso_actual = None
                    tiempo_quantum = 0

                elif tecla == 'P':
                    print("\n  PAUSADO — presione C para continuar")
                    _esperar_c()

                elif tecla == 'N':
                    nuevo = Proceso()
                    nuevo.estado = "NUEVO"
                    cola_nuevos.append(nuevo)
                    total_esperados += 1

                elif tecla == 'B':
                    mostrar_bcp(cola_nuevos, cola_listos, proceso_actual,
                                cola_bloqueados, terminados, reloj, quantum)

                elif tecla == 'T':
                    mostrar_tabla_paginas(cola_nuevos, cola_listos, proceso_actual,
                                          cola_bloqueados, terminados, reloj)

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

    # ── Tabla final ──────────────────────────────────────────────────
    limpiar()
    print("  SIMULACIÓN FINALIZADA")
    print()

    cols_f = ["ID", "Fin por", "Operación", "T.Llegada", "T.Final",
              "T.Retorno", "T.Respuesta", "T.Espera", "T.Servicio", "Resultado"]
    anchos_f = [6,   8,         12,          9,          7,
                9,          11,           8,         10,           12]

    print("  " + linea_h(anchos_f, "top"))
    print("  " + fila(cols_f, anchos_f))
    print("  " + linea_h(anchos_f, "mid"))

    lista_final = sorted(terminados, key=lambda x: x.id)
    for i, p in enumerate(lista_final):
        res = "ERROR" if p.error else str(p.resultado)
        est = "ERROR" if p.error else "Normal"
        oper = f"{p.op1} {p.operacion} {p.op2}"
        print("  " + fila([f"P{p.id}", est, oper, p.llegada, p.finalizacion,
                           p.retorno, p.respuesta, p.espera, p.servicio, res], anchos_f))
        if i < len(lista_final) - 1:
            print("  " + linea_h(anchos_f, "sep"))

    print("  " + linea_h(anchos_f, "bot"))
    print()
    print(f"  Tiempo total de simulación: {reloj}")
    print()
    input("  Presione ENTER para salir...")


if __name__ == "__main__":
    main()
