import time
import math
import os
import random
import msvcrt

# Configuración inicial
CAPACIDAD_LOTE = 5
TIEMPO_ESPERA = 1  # Segundos por cada tick de reloj


class Proceso:
    def __init__(self, operacion, operando_uno, operando_dos, tiempo_maximo, numero_programa, num_lote):
        self.operacion = operacion
        self.operandoUno = operando_uno
        self.operandoDos = operando_dos
        self.tiempoMaximo = tiempo_maximo
        self.numeroPrograma = numero_programa
        self.numLote = num_lote
        self.tiempoTranscurrido = 0


def ejecutar_operacion(proceso):
    try:
        if proceso.operacion == '+':
            res = proceso.operandoUno + proceso.operandoDos
        elif proceso.operacion == '-':
            res = proceso.operandoUno - proceso.operandoDos
        elif proceso.operacion == '*':
            res = proceso.operandoUno * proceso.operandoDos
        elif proceso.operacion == '/':
            res = proceso.operandoUno / proceso.operandoDos
        elif proceso.operacion == '%':
            res = proceso.operandoUno % proceso.operandoDos
        elif proceso.operacion == '^':
            res = proceso.operandoUno ** proceso.operandoDos

        if isinstance(res, float):
            return round(res, 4)
        return res
    except ZeroDivisionError:
        return "ERROR (Div/0)"
    except:
        return "ERROR"


def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")


def generar_proceso(numero_programa, num_lote):
    operaciones = ['+', '-', '*', '/', '%', '^']
    operacion = random.choice(operaciones)
    operando_uno = random.randint(1, 100)
    operando_dos = random.randint(1, 100)

    if operacion in ['/', '%'] and operando_dos == 0:
        operando_dos = random.randint(1, 100)

    tiempo_maximo = random.randint(5, 15)
    return Proceso(operacion, operando_uno, operando_dos, tiempo_maximo, numero_programa, num_lote)


def main():
    procesos_iniciales = []
    procesos_terminados = []
    contador_global = 0

    limpiar_pantalla()
    try:
        entrada = input("Ingrese la cantidad de procesos a realizar: ")
        cantidad_procesos = int(entrada)
    except ValueError:
        print("Error: Debe ingresar un número entero.")
        return

    for i in range(cantidad_procesos):
        num_lote = (i // CAPACIDAD_LOTE) + 1
        procesos_iniciales.append(generar_proceso(i + 1, num_lote))

    total_lotes = (len(procesos_iniciales) +
                   CAPACIDAD_LOTE - 1) // CAPACIDAD_LOTE
    indice_proceso = 0

    for num_lote in range(1, total_lotes + 1):
        fin_lote = min(indice_proceso + CAPACIDAD_LOTE,
                       len(procesos_iniciales))
        cola_lote = procesos_iniciales[indice_proceso:fin_lote]
        indice_proceso = fin_lote

        while cola_lote:
            proceso_actual = cola_lote.pop(0)
            interrumpido = False
            error_tecla = False

            while proceso_actual.tiempoTranscurrido < proceso_actual.tiempoMaximo:
                limpiar_pantalla()

                print(f"Lotes pendientes: {total_lotes - num_lote}")
                print("=" * 45)

                print(
                    f"--- PROCESO EN EJECUCIÓN (Lote: {proceso_actual.numLote}) ---")
                print(f"ID: {proceso_actual.numeroPrograma}")
                print(
                    f"Operación: {proceso_actual.operandoUno} {proceso_actual.operacion} {proceso_actual.operandoDos}")
                print(f"TME: {proceso_actual.tiempoMaximo}s | TT: {proceso_actual.tiempoTranscurrido}s | "
                      f"TR: {proceso_actual.tiempoMaximo - proceso_actual.tiempoTranscurrido}s")
                print("-" * 45)

                print(f"--- PROCESOS EN ESPERA (LOTE {num_lote}) ---")
                for p in cola_lote:
                    print(
                        f"[ID: {p.numeroPrograma} | TME: {p.tiempoMaximo} | TT: {p.tiempoTranscurrido}]")
                print("-" * 45)

                print("--- PROCESOS TERMINADOS ---")

                for t in procesos_terminados:
                    print(t)

                print("=" * 45)
                print(f"CONTADOR GLOBAL: {contador_global}")

                if msvcrt.kbhit():
                    try:
                        tecla_bytes = msvcrt.getch()

                        if tecla_bytes in (b'\x00', b'\xe0'):
                            msvcrt.getch()
                            continue

                        tecla = tecla_bytes.decode(errors="ignore").upper()

                        if tecla not in ['I', 'E', 'P']:
                            continue

                        if tecla == 'I':
                            interrumpido = True
                            cola_lote.append(proceso_actual)
                            break

                        elif tecla == 'E':
                            error_tecla = True
                            procesos_terminados.append(
                                f"ID {proceso_actual.numeroPrograma} | ERROR | Lote: {proceso_actual.numLote}"
                            )
                            break

                        elif tecla == 'P':
                            print("\n--- SISTEMA PAUSADO --- (C para continuar)")
                            while True:
                                if msvcrt.kbhit():
                                    try:
                                        tecla_bytes = msvcrt.getch()

                                        if tecla_bytes in (b'\x00', b'\xe0'):
                                            msvcrt.getch()
                                            continue

                                        tecla = tecla_bytes.decode(
                                            errors="ignore").upper()

                                        if tecla == 'C':
                                            break
                                    except:
                                        continue

                    except:
                        continue

                time.sleep(TIEMPO_ESPERA)
                proceso_actual.tiempoTranscurrido += 1
                contador_global += 1

            if interrumpido or error_tecla:
                continue

            resultado = ejecutar_operacion(proceso_actual)
            procesos_terminados.append(
                f"ID {proceso_actual.numeroPrograma} | "
                f"{proceso_actual.operandoUno}{proceso_actual.operacion}"
                f"{proceso_actual.operandoDos} = {resultado} | "
                f"Lote: {proceso_actual.numLote}"
            )
        procesos_terminados.append("---- FIN DE LOTE ----")
    limpiar_pantalla()
    print("--- SIMULACIÓN FINALIZADA ---")
    print("\nRESULTADOS FINALES:")
    for t in procesos_terminados:
        print(t)

    print(f"\nTIEMPO TOTAL DE EJECUCIÓN: {contador_global}")
    input("\nPresione ENTER para salir...")


if __name__ == "__main__":
    main()
