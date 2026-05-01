import time
import os
import random
import msvcrt

TIEMPO_ESPERA = 1
MAX_MEMORIA = 5
TIEMPO_BLOQUEADO = 8

_id_counter = 0


def siguiente_id():
    global _id_counter
    _id_counter += 1
    return _id_counter


class Proceso:
    def __init__(self):
        self.id = siguiente_id()
        self.operacion, self.op1, self.op2 = self._generar_operacion()
        self.tme = random.randint(6, 20)
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


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


# ── Utilidades de tabla ──────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────────────
#  PANTALLA PRINCIPAL
# ─────────────────────────────────────────────────────────────────────
def mostrar_estado(nuevos, listos, ejecucion, bloqueados, terminados, reloj, tiempo_quantum, quantum):
    limpiar()

    en_mem = len(listos) + len(bloqueados) + (1 if ejecucion else 0)
    print(
        f"  RELOJ: {reloj}   |   EN MEMORIA: {en_mem}/{MAX_MEMORIA}"
        f"   |   NUEVOS EN ESPERA: {len(nuevos)}"
        f"   |   QUANTUM: {quantum}"
    )
    print()

    # ── Cola de Listos ──────────────────────────────────────────────
    print("  COLA DE LISTOS  (carrusel Round-Robin)")
    cols_l = ["#",  "ID",    "Operación",  "TME",
              "T.Transcurrido",  "T.Restante",  "T.Espera",  "Turno"]
    anchos_l = [3,   6,       12,           5,
                14,                10,            8,           6]
    print("  " + linea_h(anchos_l, "top"))
    print("  " + fila(cols_l, anchos_l))
    print("  " + linea_h(anchos_l, "mid"))
    if listos:
        for i, p in enumerate(listos):
            oper = f"{p.op1} {p.operacion} {p.op2}"
            # El primero en la cola es el siguiente en ejecutar → carrusel
            carrusel = "◄ sig" if i == 0 else ""
            print("  " + fila([i + 1, f"P{p.id}", oper, p.tme,
                               p.tiempo_transcurrido, p.tiempo_restante_cpu(),
                               p.espera, carrusel], anchos_l))
    else:
        print("  " + fila_vacia("(vacía)", anchos_l))
    print("  " + linea_h(anchos_l, "bot"))
    print()

    # ── En Ejecución ────────────────────────────────────────────────
    print("  EN EJECUCIÓN")
    cols_e = ["ID",  "Operación",  "TME",  "T.Transcurrido",  "T.Restante",
              "T.Llegada",  "T.Respuesta",  "T.Espera",  "T.Quantum"]
    anchos_e = [6,    12,           5,      14,               10,
                9,            11,            8,           9]
    print("  " + linea_h(anchos_e, "top"))
    print("  " + fila(cols_e, anchos_e))
    print("  " + linea_h(anchos_e, "mid"))
    if ejecucion:
        e = ejecucion
        oper = f"{e.op1} {e.operacion} {e.op2}"
        resp = e.respuesta if e.respondido else "—"
        te_parcial = (reloj - e.llegada) - e.tiempo_transcurrido
        print("  " + fila([f"P{e.id}", oper, e.tme, e.tiempo_transcurrido,
                           e.tiempo_restante_cpu(), e.llegada, resp,
                           te_parcial, tiempo_quantum], anchos_e))
    else:
        print("  " + fila_vacia("(procesador libre)", anchos_e))
    print("  " + linea_h(anchos_e, "bot"))
    print()

    # ── Cola de Bloqueados ──────────────────────────────────────────
    print("  COLA DE BLOQUEADOS")
    cols_b = ["ID",  "T.Transcurrido en Bloqueado"]
    anchos_b = [6,     28]
    print("  " + linea_h(anchos_b, "top"))
    print("  " + fila(cols_b, anchos_b))
    print("  " + linea_h(anchos_b, "mid"))
    if bloqueados:
        for p in bloqueados:
            print("  " + fila([f"P{p.id}", p.tiempo_bloqueado], anchos_b))
    else:
        print("  " + fila_vacia("(vacía)", anchos_b))
    print("  " + linea_h(anchos_b, "bot"))
    print()

    # ── Terminados ──────────────────────────────────────────────────
    print("  TERMINADOS")
    cols_t = ["ID",  "Operación",  "Resultado"]
    anchos_t = [6,    14,           14]
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
    print("  Teclas: I=Interrupción  E=Error  P=Pausa  N=Nuevo  B=BCP")


# ─────────────────────────────────────────────────────────────────────
#  TABLA BCP (tecla B)
# ─────────────────────────────────────────────────────────────────────
def mostrar_bcp(nuevos, listos, ejecucion, bloqueados, terminados, reloj, quantum):
    limpiar()
    print(
        f"  TABLA DE PROCESOS (BCP)   —   RELOJ: {reloj}   |   QUANTUM: {quantum}")
    print()

    cols = ["ID",  "Estado",  "Operación",  "TME",  "T.Llegada",  "T.Final",
            "T.Retorno",  "T.Espera",  "T.Servicio",  "T.RestCPU",  "T.Respuesta",  "Resultado"]
    anchos = [6,    10,        12,           5,       9,            7,
              9,           8,          10,           9,            11,           12]

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
            vals = [f"P{p.id}", estado, oper, p.tme,
                    "—", "—", "—", "—", "—", "—", "—", "—"]

        elif estado in ('LISTO', 'EJECUCION', 'BLOQUEADO'):
            resp_d = str(p.respuesta) if p.respondido else "—"
            ts_parcial = p.tiempo_transcurrido
            tr_parcial = reloj - p.llegada
            te_parcial = tr_parcial - ts_parcial
            vals = [f"P{p.id}", estado, oper, p.tme,
                    str(p.llegada), "—", "—",
                    str(te_parcial), str(ts_parcial),
                    str(p.tiempo_restante_cpu()), resp_d, "—"]

        else:  # TERMINADO
            res = "ERROR" if p.error else str(p.resultado)
            est = "ERROR" if p.error else "Normal"
            vals = [f"P{p.id}", est, oper, p.tme,
                    str(p.llegada), str(p.finalizacion), str(p.retorno),
                    str(p.espera), str(p.servicio),
                    "0", str(p.respuesta), res]

        print("  " + fila(vals, anchos))
        if i < len(todos) - 1:
            print("  " + linea_h(anchos, "sep"))

    print("  " + linea_h(anchos, "bot"))
    print()
    print("  Presione C para continuar la simulacion...")


# ─────────────────────────────────────────────────────────────────────
#  Terminar proceso
# ─────────────────────────────────────────────────────────────────────
def terminar_proceso(p, reloj, error=False):
    p.error = error
    if not error:
        p.resultado = ejecutar_operacion(p)
    p.finalizacion = reloj
    p.servicio = p.tiempo_transcurrido
    p.retorno = p.finalizacion - p.llegada
    p.espera = p.retorno - p.servicio
    p.estado = "TERMINADO"


# ─────────────────────────────────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────────────────────────────────
def main():
    limpiar()
    n = int(input("Numero inicial de procesos: "))
    quantum = int(input("Tamaño del Quantum: "))
    time.sleep(1)

    cola_nuevos = [Proceso() for _ in range(n)]
    cola_listos = []
    cola_bloqueados = []
    terminados = []
    proceso_actual = None
    reloj = 0
    tiempo_quantum = 0          # ← ticks acumulados del quantum actual
    total_esperados = n

    while len(terminados) < total_esperados:

        # 1. Admitir procesos (planificador largo plazo)
        en_memoria = len(cola_listos) + len(cola_bloqueados) + \
            (1 if proceso_actual else 0)
        while en_memoria < MAX_MEMORIA and cola_nuevos:
            p = cola_nuevos.pop(0)
            p.llegada = reloj
            p.estado = "LISTO"
            cola_listos.append(p)
            en_memoria += 1

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
            proceso_actual = cola_listos.pop(0)
            proceso_actual.estado = "EJECUCION"
            tiempo_quantum = 0          # ← resetear quantum al entrar al CPU
            if not proceso_actual.respondido:
                proceso_actual.respuesta = reloj - proceso_actual.llegada
                proceso_actual.respondido = True

        # 4. Acumular espera en cola listos
        for p in cola_listos:
            p.espera += 1

        # 5. Mostrar
        mostrar_estado(cola_nuevos, cola_listos, proceso_actual,
                       cola_bloqueados, terminados, reloj, tiempo_quantum, quantum)

        # 6. Esperar 1 segundo con polling de teclas cada 50ms
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
                    print("\n  SIMULACION PAUSADA  (C para continuar)")
                    while True:
                        if msvcrt.kbhit():
                            if msvcrt.getch().decode('utf-8', errors='ignore').upper() == 'C':
                                break
                        time.sleep(0.05)

                elif tecla == 'N':
                    nuevo = Proceso()
                    nuevo.estado = "NUEVO"
                    cola_nuevos.append(nuevo)
                    total_esperados += 1

                elif tecla == 'B':
                    mostrar_bcp(cola_nuevos, cola_listos, proceso_actual,
                                cola_bloqueados, terminados, reloj, quantum)
                    while True:
                        if msvcrt.kbhit():
                            if msvcrt.getch().decode('utf-8', errors='ignore').upper() == 'C':
                                break
                        time.sleep(0.05)

            time.sleep(0.05)

        if proceso_actual:
            proceso_actual.tiempo_transcurrido += 1
            tiempo_quantum += 1

            # ── Termina normalmente (agotó su TME) ──────────────────
            if proceso_actual.tiempo_transcurrido >= proceso_actual.tme:
                terminar_proceso(proceso_actual, reloj + 1)
                terminados.append(proceso_actual)
                proceso_actual = None
                tiempo_quantum = 0

            # ── Expulsión por quantum (RR) ───────────────────────────
            elif tiempo_quantum >= quantum:
                proceso_actual.estado = "LISTO"
                cola_listos.append(proceso_actual)   # va al FINAL de la cola
                proceso_actual = None
                tiempo_quantum = 0

        reloj += 1

    # ── Tabla final ──────────────────────────────────────────────────
    limpiar()
    print("  SIMULACION FINALIZADA")
    print()

    cols_f = ["ID",  "Fin por",  "Operacion",  "T.Llegada",  "T.Final",
              "T.Retorno",  "T.Respuesta",  "T.Espera",  "T.Servicio",  "Resultado"]
    anchos_f = [6,    8,          12,           9,            7,
                9,           11,           8,           10,           12]

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
    print(f"  Tiempo total de simulacion: {reloj}")
    print()
    input("  Presione ENTER para salir...")


if __name__ == "__main__":
    main()
