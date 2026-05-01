import time
import math
import os

CAPACIDAD_LOTE = 5
TIEMPO_ESPERA = 1


class Proceso:
    def __init__(self, nombre_programador, operacion, operando_uno,
                 operando_dos, tiempo_maximo, numero_programa):
        self.nombreProgramador = nombre_programador
        self.operacion = operacion
        self.operandoUno = operando_uno
        self.operandoDos = operando_dos
        self.tiempoMaximo = tiempo_maximo
        self.numeroPrograma = numero_programa


def ejecutar_operacion(proceso):
    if proceso.operacion == '+':
        return proceso.operandoUno + proceso.operandoDos
    elif proceso.operacion == '-':
        return proceso.operandoUno - proceso.operandoDos
    elif proceso.operacion == '*':
        return proceso.operandoUno * proceso.operandoDos
    elif proceso.operacion == '/':
        return proceso.operandoUno / proceso.operandoDos if proceso.operandoDos != 0 else 0
    elif proceso.operacion == '%':
        return int(proceso.operandoUno) % int(proceso.operandoDos)
    elif proceso.operacion == '^':
        return math.pow(proceso.operandoUno, proceso.operandoDos)
    return 0


def numero_unico(numero_programa, procesos):
    for proceso in procesos:
        if proceso.numeroPrograma == numero_programa:
            return False
    return True


def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")


def main():
    procesos = []
    procesos_terminados = []
    contador_global = 0

    cantidad_procesos = int(input("Cantidad de procesos: "))

    for i in range(cantidad_procesos):
        print(f"\nProceso {i + 1}")
        nombre_programador = input("Nombre del programador: ")

        while True:
            operacion = input("Operacion (+,-,*,/,%,^): ")
            if operacion in ['+', '-', '*', '/', '%', '^']:
                break

        operando_uno = float(input("Operando 1: "))

        while True:
            operando_dos = float(input("Operando 2: "))
            if not ((operacion in ['/', '%']) and operando_dos == 0):
                break

        while True:
            tiempo_maximo = int(input("Tiempo Maximo Estimado (>0): "))
            if tiempo_maximo > 0:
                break

        while True:
            numero_programa = int(input("Numero de Programa (ID unico): "))
            if numero_unico(numero_programa, procesos):
                break

        procesos.append(
            Proceso(nombre_programador, operacion, operando_uno,
                    operando_dos, tiempo_maximo, numero_programa)
        )

    total_lotes = (len(procesos) + CAPACIDAD_LOTE - 1) // CAPACIDAD_LOTE
    indice_proceso = 0

    for lote_actual in range(total_lotes):

        procesos_en_lote = min(
            CAPACIDAD_LOTE, len(procesos) - indice_proceso
        )

        inicio_lote = indice_proceso
        fin_lote = indice_proceso + procesos_en_lote

        for posicion in range(inicio_lote, fin_lote):

            proceso_actual = procesos[posicion]

            for tiempo in range(1, proceso_actual.tiempoMaximo + 1):

                limpiar_pantalla()

                lotes_pendientes = total_lotes - lote_actual - 1
                print("Lotes pendientes:", lotes_pendientes)

                print("\nProceso en Ejecucion")
                print("ID:", proceso_actual.numeroPrograma)
                print("Nombre:", proceso_actual.nombreProgramador)
                print("Operacion:",
                      proceso_actual.operacion,
                      proceso_actual.operandoUno,
                      proceso_actual.operandoDos)
                print("Tiempo Transcurrido:", tiempo)
                print("Tiempo Restante:",
                      proceso_actual.tiempoMaximo - tiempo)

                print("\nProcesos pendientes en este lote:")
                for p in procesos[posicion + 1:fin_lote]:
                    print("ID:", p.numeroPrograma)

                print("\nProcesos Terminados")
                for terminado in procesos_terminados:
                    print(terminado)

                print("\nContador Global:", contador_global)

                time.sleep(TIEMPO_ESPERA)
                contador_global += 1

            resultado = ejecutar_operacion(proceso_actual)

            procesos_terminados.append(
                f"ID {proceso_actual.numeroPrograma} | "
                f"{int(proceso_actual.operandoUno)}"
                f"{proceso_actual.operacion}"
                f"{int(proceso_actual.operandoDos)} | "
                f"{resultado} | Lote: {lote_actual + 1}"
            )

            indice_proceso += 1

        procesos_terminados.append("---- FIN DE LOTE ----")

    limpiar_pantalla()

    print("Procesos Terminados")
    for terminado in procesos_terminados:
        print(terminado)

    print("\nContador Global:", contador_global)
    print("\nTodos los procesos han terminado.")
    input("Presiona ENTER para salir...")


if __name__ == "__main__":
    main()
