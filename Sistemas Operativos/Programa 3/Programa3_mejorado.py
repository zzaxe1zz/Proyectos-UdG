import time
import os
import random
import msvcrt


TIEMPO_ESPERA = 1
MAX_MEMORIA = 5
TIEMPO_BLOQUEADO = 8


class Proceso:
    def __init__(self, id):
        self.id = id
        self.operacion, self.op1, self.op2 = self.generar_operacion()
        self.tme = random.randint(6, 20)
        self.tiempo_transcurrido = 0
        self.tiempo_bloqueado = 0

        # Tiempos requeridos
        self.llegada = None
        self.finalizacion = None
        self.retorno = None
        self.respuesta = None
        self.espera = 0
        self.servicio = 0

        self.respondido = False
        self.resultado = None
        self.error = False

    def generar_operacion(self):
        operaciones = ['+', '-', '*', '/', '%', '^']
        op = random.choice(operaciones)
        op1 = random.randint(1, 100)
        op2 = random.randint(1, 100)

        if op in ['/', '%']:
            op2 = random.randint(1, 100)

        return op, op1, op2


def ejecutar_operacion(p):
    try:
        if p.operacion == '+':
            return p.op1 + p.op2
        elif p.operacion == '-':
            return p.op1 - p.op2
        elif p.operacion == '*':
            return p.op1 * p.op2
        elif p.operacion == '/':
            return round(p.op1 / p.op2, 4)
        elif p.operacion == '%':
            return p.op1 % p.op2
        elif p.operacion == '^':
            return p.op1 ** p.op2
    except:
        return "ERROR"


def limpiar():
    os.system("cls")


def mostrar_estado(nuevos, listos, ejecucion, bloqueados, terminados, reloj):
    limpiar()

    print("NUEVOS:", len(nuevos))
    print("=" * 50)

    print("LISTOS:")
    for p in listos:
        print(f"ID:{p.id} | TME:{p.tme} | TT:{p.tiempo_transcurrido}")
    print("-" * 50)

    print("EJECUCIÓN:")
    if ejecucion:
        print(f"ID:{ejecucion.id}")
        print(f"{ejecucion.op1} {ejecucion.operacion} {ejecucion.op2}")
        print(f"TME:{ejecucion.tme}")
        print(f"TT:{ejecucion.tiempo_transcurrido}")
        print(f"TR:{ejecucion.tme - ejecucion.tiempo_transcurrido}")
    else:
        print("PROCESO NULO")

    print("-" * 50)
    print("BLOQUEADOS:")
    for p in bloqueados:
        print(f"ID:{p.id} | TB:{p.tiempo_bloqueado}")
    print("-" * 50)

    print("TERMINADOS:")
    for p in terminados:
        estado = "ERROR" if p.error else p.resultado
        print(f"ID:{p.id} | {p.op1}{p.operacion}{p.op2} = {estado}")
    print("=" * 50)

    print("RELOJ:", reloj)


def main():
    limpiar()
    n = int(input("Número de procesos: "))

    cola_nuevos = [Proceso(i + 1) for i in range(n)]
    cola_listos = []
    cola_bloqueados = []
    terminados = []
    proceso_actual = None

    reloj = 0

    while len(terminados) < n:

        # Admitir procesos si hay espacio
        while len(cola_listos) + len(cola_bloqueados) + (1 if proceso_actual else 0) < MAX_MEMORIA and cola_nuevos:
            p = cola_nuevos.pop(0)
            p.llegada = reloj
            cola_listos.append(p)

        # Pasar de bloqueado a listo
        for p in cola_bloqueados[:]:
            p.tiempo_bloqueado += 1
            if p.tiempo_bloqueado >= TIEMPO_BLOQUEADO:
                p.tiempo_bloqueado = 0
                cola_bloqueados.remove(p)
                cola_listos.append(p)

        # Tomar proceso FCFS
        if not proceso_actual and cola_listos:
            proceso_actual = cola_listos.pop(0)
            if not proceso_actual.respondido:
                proceso_actual.respuesta = reloj - proceso_actual.llegada
                proceso_actual.respondido = True

        mostrar_estado(cola_nuevos, cola_listos, proceso_actual,
                       cola_bloqueados, terminados, reloj)

        # Teclas
        if msvcrt.kbhit():
            tecla = msvcrt.getch().decode().upper()

            if tecla == 'I' and proceso_actual:
                cola_bloqueados.append(proceso_actual)
                proceso_actual = None

            elif tecla == 'E' and proceso_actual:
                proceso_actual.error = True
                proceso_actual.finalizacion = reloj
                proceso_actual.servicio = proceso_actual.tiempo_transcurrido
                proceso_actual.retorno = proceso_actual.finalizacion - proceso_actual.llegada
                terminados.append(proceso_actual)
                proceso_actual = None

            elif tecla == 'P':
                print("\n--- SISTEMA PAUSADO --- (C para continuar)")
                while True:
                    if msvcrt.kbhit():
                        if msvcrt.getch().decode().upper() == 'C':
                            break

        time.sleep(TIEMPO_ESPERA)

        # Ejecutar
        if proceso_actual:
            proceso_actual.tiempo_transcurrido += 1
            proceso_actual.servicio += 1

            if proceso_actual.tiempo_transcurrido >= proceso_actual.tme:
                proceso_actual.resultado = ejecutar_operacion(proceso_actual)
                proceso_actual.finalizacion = reloj + 1
                proceso_actual.retorno = proceso_actual.finalizacion - proceso_actual.llegada
                terminados.append(proceso_actual)
                proceso_actual = None

        # Tiempo de espera
        for p in cola_listos:
            p.espera += 1

        reloj += 1

    # Mostrar resumen final
    limpiar()
    print("SIMULACIÓN FINALIZADA\n")

    print("TABLA BCP\n")
    print("ID | Lleg | Fin | Ret | Resp | Esp | Serv | Resultado")
    print("-" * 65)

    for p in terminados:
        resultado = "ERROR" if p.error else p.resultado
        print(f"{p.id:<3}| "
              f"{p.llegada:<5}| "
              f"{p.finalizacion:<4}| "
              f"{p.retorno:<4}| "
              f"{p.respuesta:<5}| "
              f"{p.espera:<4}| "
              f"{p.servicio:<5}| "
              f"{resultado}")

    print("Tiempo total:", reloj)
    input("Presione ENTER para salir")


if __name__ == "__main__":
    main()
