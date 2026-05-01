import time
import random
import os
import threading
import msvcrt

# ── Configuración ──────────────────────────────────────────
CAPACIDAD = 18
MIN_PRODUCE = 3
MAX_PRODUCE = 6
MIN_SLEEP = 1
MAX_SLEEP = 4

PRODUCTOS = list(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    "0123456789!@#$%&*?"
)

# ── Estado compartido ──────────────────────────────────────
buffer = [None] * CAPACIDAD
ptr_prod = 0
ptr_cons = 0
count = 0

lock = threading.Lock()         # protege buffer, punteros y count
display_lock = threading.Lock()         # protege el refresco de pantalla
sem_espacio = threading.Semaphore(CAPACIDAD)
sem_lleno = threading.Semaphore(0)

estado_prod = "Iniciando..."
estado_cons = "Iniciando..."
log_msgs = []
MAX_LOG = 8
running = True


def agregar_log(msg):
    log_msgs.append(msg)
    if len(log_msgs) > MAX_LOG:
        log_msgs.pop(0)


# ── Tabla helpers ──────────────────────────────────────────
def linea_h(anchos, tipo="mid"):
    mapa = {
        "top": ("╔", "╦", "╗", "═"),
        "mid": ("╠", "╬", "╣", "═"),
        "bot": ("╚", "╩", "╝", "═"),
    }
    l, m, r, c = mapa[tipo]
    return l + m.join(c * (a + 2) for a in anchos) + r


def fila_tabla(valores, anchos, alin=None):
    celdas = []
    for i, (v, a) in enumerate(zip(valores, anchos)):
        s = str(v)
        al = alin[i] if alin else "l"
        s = s.center(a) if al == "c" else s.ljust(a)
        celdas.append(f" {s} ")
    return "║" + "║".join(celdas) + "║"


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


# ── Render ─────────────────────────────────────────────────
def mostrar():
    with display_lock:
        limpiar()
        print("  PRODUCTOR - CONSUMIDOR  |  Buffer circular acotado  |  Capacidad: 18")
        print()

        MITAD = 9   # 2 filas de 9 casillas
        AW = 5   # ancho de cada casilla

        for fila_idx in range(2):
            ini = fila_idx * MITAD
            fin = ini + MITAD

            nums = [str(i + 1) for i in range(ini, fin)]
            anch_buf = [AW] * MITAD

            print("  " + linea_h(anch_buf, "top"))
            print("  " + fila_tabla(nums, anch_buf, ["c"] * MITAD))
            print("  " + linea_h(anch_buf, "mid"))

            contenidos = []
            for i in range(ini, fin):
                val = buffer[i] if buffer[i] is not None else "·"
                if i == ptr_prod and i == ptr_cons:
                    indicador = "P+C"
                elif i == ptr_prod:
                    indicador = " P "
                elif i == ptr_cons:
                    indicador = " C "
                else:
                    indicador = "   "
                celda = f"{val}{indicador}"[:AW].ljust(AW)
                contenidos.append(celda)

            print("  " + fila_tabla(contenidos, anch_buf, ["c"] * MITAD))
            print("  " + linea_h(anch_buf, "bot"))
            if fila_idx == 0:
                print()

        print()
        print(f"  Ocupado: {count}/{CAPACIDAD}   "
              f"|  Productor → casilla {ptr_prod + 1}   "
              f"|  Consumidor → casilla {ptr_cons + 1}")
        print()

        # Estado P / C
        anch_e = [12, 55]
        print("  " + linea_h(anch_e, "top"))
        print("  " + fila_tabla(["PRODUCTOR", estado_prod], anch_e))
        print("  " + linea_h(anch_e, "mid"))
        print("  " + fila_tabla(["CONSUMIDOR", estado_cons], anch_e))
        print("  " + linea_h(anch_e, "bot"))
        print()

        # Log
        anch_l = [71]
        print("  " + linea_h(anch_l, "top"))
        print("  " + fila_tabla(["REGISTRO DE ACTIVIDAD"], anch_l, ["c"]))
        print("  " + linea_h(anch_l, "mid"))
        for msg in log_msgs:
            print("  " + fila_tabla([msg[:71]], anch_l))
        for _ in range(MAX_LOG - len(log_msgs)):
            print("  " + fila_tabla([""], anch_l))
        print("  " + linea_h(anch_l, "bot"))
        print()
        print("  Presione ESC para terminar.")


# ── Productor ──────────────────────────────────────────────
def productor():
    global ptr_prod, count, estado_prod, running

    while running:
        t = random.randint(MIN_SLEEP, MAX_SLEEP)
        estado_prod = f"Durmiendo {t}s..."
        agregar_log(f"[PRODUCTOR] Se duerme durante {t} segundo(s).")
        mostrar()
        for _ in range(t):
            if not running:
                return
            time.sleep(1)
        if not running:
            return

        n = random.randint(MIN_PRODUCE, MAX_PRODUCE)
        estado_prod = f"Despertó. Intentará producir {n} elemento(s)."
        agregar_log(f"[PRODUCTOR] Despertó, quiere producir {n} elemento(s).")
        mostrar()
        time.sleep(0.4)

        producidos = 0
        for _ in range(n):
            if not running:
                return
            if count >= CAPACIDAD:
                estado_prod = f"Buffer lleno ({count}/{CAPACIDAD}). Esperando espacio..."
                agregar_log("[PRODUCTOR] Buffer lleno — esperando espacio.")
                mostrar()
            sem_espacio.acquire()
            if not running:
                return

            producto = random.choice(PRODUCTOS)
            with lock:
                buffer[ptr_prod] = producto
                ptr_prod = (ptr_prod + 1) % CAPACIDAD
                count += 1
                producidos += 1
            sem_lleno.release()

            estado_prod = f"Produjo '{producto}'. Siguiente → casilla {ptr_prod + 1}. ({producidos}/{n})"
            agregar_log(
                f"[PRODUCTOR] Colocó '{producto}'. Buffer: {count}/{CAPACIDAD}. Siguiente casilla: {ptr_prod + 1}")
            mostrar()
            time.sleep(0.35)

        estado_prod = f"Terminó: produjo {producidos} elemento(s). Vuelve a trabajar."
        agregar_log(
            f"[PRODUCTOR] Ciclo completo: {producidos} elemento(s) producido(s).")
        mostrar()
        time.sleep(0.4)


# ── Consumidor ─────────────────────────────────────────────
def consumidor():
    global ptr_cons, count, estado_cons, running

    while running:
        t = random.randint(MIN_SLEEP, MAX_SLEEP)
        estado_cons = f"Durmiendo {t}s..."
        agregar_log(f"[CONSUMIDOR] Se duerme durante {t} segundo(s).")
        mostrar()
        for _ in range(t):
            if not running:
                return
            time.sleep(1)
        if not running:
            return

        n = random.randint(MIN_PRODUCE, MAX_PRODUCE)
        estado_cons = f"Despertó. Intentará consumir {n} elemento(s)."
        agregar_log(f"[CONSUMIDOR] Despertó, quiere consumir {n} elemento(s).")
        mostrar()
        time.sleep(0.4)

        consumidos = 0
        for _ in range(n):
            if not running:
                return
            if count <= 0:
                estado_cons = "Buffer vacío. Esperando producto..."
                agregar_log("[CONSUMIDOR] Buffer vacío — esperando producto.")
                mostrar()
            sem_lleno.acquire()
            if not running:
                return

            with lock:
                producto = buffer[ptr_cons]
                buffer[ptr_cons] = None
                ptr_cons = (ptr_cons + 1) % CAPACIDAD
                count -= 1
                consumidos += 1
            sem_espacio.release()

            estado_cons = f"Consumió '{producto}'. Siguiente → casilla {ptr_cons + 1}. ({consumidos}/{n})"
            agregar_log(
                f"[CONSUMIDOR] Retiró '{producto}'. Buffer: {count}/{CAPACIDAD}. Siguiente casilla: {ptr_cons + 1}")
            mostrar()
            time.sleep(0.35)

        estado_cons = f"Terminó: consumió {consumidos} elemento(s). Vuelve a trabajar."
        agregar_log(
            f"[CONSUMIDOR] Ciclo completo: {consumidos} elemento(s) consumido(s).")
        mostrar()
        time.sleep(0.4)


# ── Hilo teclado ───────────────────────────────────────────
def escuchar_teclado():
    """Hilo dedicado exclusivamente a detectar ESC."""
    global running
    while running:
        # getch() es bloqueante: espera hasta que se presione una tecla
        tecla = msvcrt.getch()
        if tecla == b'\x1b':          # ESC
            running = False
            # Liberar varias veces para desbloquear hilos que puedan estar
            # bloqueados en sem_espacio.acquire() o sem_lleno.acquire()
            for _ in range(CAPACIDAD + 5):
                sem_espacio.release()
                sem_lleno.release()
            break
        # Si es tecla especial (flechas, F-keys) viene en dos bytes
        if tecla in (b'\x00', b'\xe0'):
            msvcrt.getch()   # descartar segundo byte


# ── Main ───────────────────────────────────────────────────
def main():
    global running
    limpiar()
    mostrar()

    t_teclado = threading.Thread(target=escuchar_teclado, daemon=True)
    t_prod = threading.Thread(target=productor,        daemon=True)
    t_cons = threading.Thread(target=consumidor,       daemon=True)

    t_teclado.start()
    t_prod.start()
    t_cons.start()

    # El main solo espera a que running se vuelva False
    while running:
        time.sleep(0.1)

    t_prod.join(timeout=3)
    t_cons.join(timeout=3)

    limpiar()
    print("\n  Simulacion finalizada.\n")
    print(f"  Elementos restantes en buffer : {count}")
    print(f"  Puntero productor en casilla  : {ptr_prod + 1}")
    print(f"  Puntero consumidor en casilla : {ptr_cons + 1}")
    print()
    input("  Presione ENTER para salir...")


if __name__ == "__main__":
    main()
