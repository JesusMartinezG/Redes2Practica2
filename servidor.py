import time
import socket
import sys
import random
import threading
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-2s) %(message)s')

class Gato:

    def __init__(self, num_jugadores): # Crea un objeto base, sin valores en sus atributos
        self.tiempoInicio = None
        self.tiempoFin = None
        self.tam = None
        self.numJugadores = num_jugadores
        self.tablero = None
        self.turno = None
        self.numTiros = None
        self.tiros_maximos = None
        self.simbolos = []
        self.lista_conexiones = []  # Lista vacía donde se guardará los sockets para la conexión con los 
        self.barrera = threading.Barrier(num_jugadores) # Barrera para esperar a la conexion de todos los clientes


    def inicializar(self, siz):                          # Crea el tablero con el tamaño indicado
        self.tiempoInicio = time.time()                                 # Registra el tiempo de creación del juego
        self.tiempoFin = None
        self.tam = siz
        self.tablero = [[' ' for x in range(siz)] for y in range(siz)]  # Crea un tablero de tam x tam lleno de espacios
        self.turno = 0                                                  # Jugador 1 siempre tira primero
        self.numTiros = 0                                               # Cuenta los tiros realizados, sirve para detectar un empate
        self.tiros_maximos = siz*siz                                    # Numero de casillas = numero de tiros posibles
        #self.simbolos = None                                            # Simbolos de los jugadores en orden según su turno
        #self.numJugadores = num_jugadores
        #self.lista_conexiones = lista_conexiones

    def cambiarTurno(self):  # Cambia entre los turnos
        if self.turno < self.numJugadores-1:
            self.turno+=1
        else:
            self.turno = 0

    def agregarSimbolo(self, simbolo):
        self.simbolos.append(simbolo)


    def tirar(self, jg, coord):                             # Plasma el simbolo del jugador indicado en las coordeneadas ingresadas
        self.tablero[coord[0]][coord[1]] = jg               # Pone el simbolo en el tablero
        self.numTiros += 1                                  # Cuenta el tiro realizado
        pog = self.win(jg)                                  # Revisa la condición ganar
        if pog:                                             # Se forma una linea -> Gana el juego
            return '1'+jg                                   # Retorna el simbolo del jugador ganador y el digito de control que lo indica
        else:
            if self.numTiros == self.tiros_maximos:         # Si ya no hay más casillas que llenar
                return '1/'                                 # Empate
            else:                                           # Solo si el juego continua y no hubo errores
                self.cambiarTurno()
                return '0'+self.simbolos[self.turno]        # Sigue jugando

    def imprimir(self):
        for x in range(self.tam):
            for y in range(self.tam):
                print("%i \t" % self.tablero[x][y], end="", flush=True)
            print("\n")

    def win(self, jg):  # Evalúa si el jugador indicado ha ganado
        winner = False

        for x in range(self.tam):
            aux = True
            for y in range(self.tam):
                aux = aux and (self.tablero[x][y] == jg)  # Es linea vertical
            winner = winner or aux

        if winner:
            self.tiempoFin = time.time()
            return True

        for y in range(self.tam):
            aux = True
            for x in range(self.tam):
                aux = aux and (self.tablero[x][y] == jg)  # Es linea horizontal
            winner = winner or aux

        if winner:
            self.tiempoFin = time.time()
            return True

        aux = True
        for x in range(self.tam):
            aux = aux and (self.tablero[x][x] == jg)  # Es Diagonal \

        if aux:
            self.tiempoFin = time.time()
            return True

        aux = True
        for x in range(self.tam):
            aux = aux and (self.tablero[x][self.tam - 1 - x] == jg)  # es diagonal /

        if aux:
            self.tiempoFin = time.time()
            return True

        return False # No forma ninguna linea

    def validar(self, arr):
        try:
            return (not (arr[0] < 0 or arr[1] < 0 or
                   arr[0] >= self.tam or arr[1] >= self.tam)) and\
                   (self.tablero[arr[0]][arr[1]] == ' ')   # coordenadas validas y casilla vacía
        except Exception as e:
            print(e)
            return False

    def cpu(self):
        coord = (random.randint(0, self.tam - 1), random.randint(0, self.tam - 1))      # Genera un par de coordenadas aleatorio
        while not self.validar(coord):                                                  # Revisa que las casilla esté vacía
            coord = (random.randint(0, self.tam - 1), random.randint(0, self.tam - 1))  # Si no está vacía vuelve a generar
        print('CPU tira: ', coord)
        c = self.tirar('o', coord)                                                  # Realiza el tiro y retorna la cadena de control
        return c

    def enviarTablero(self, sock, control):
        s = ''.join([''.join(i) for i in self.tablero])    # Convierte la matriz en una cadena de caracteres consegutivos
        s = str(control) + s                    # Agrega la porcion de control a la cadena
        print('Cadena enviada: ', s)
        s = s.encode()                          # Codifica la cadena
        sock.sendall(s)                         # Envío por el socket

    def enviarTableroaTodos(self, sock, control):           # Envia el resultado del ultimo tiro recibido a todos los clientes
        s = ''.join([''.join(i) for i in self.tablero])     # Convierte la matriz en una cadena de caracteres consegutivos
        s = str(control) + s                                # Agrega la porcion de control a la cadena
        print('Cadena enviada: ', s)
        s = s.encode()                                      # Codifica la cadena
        print("hay %i clientes" % len(self.listaConexiones))

        for conec in self.listaConexiones:                  # Para cada cliente conectado
            conec.sendall(s)                                # Envía la cadena de bytes

def recibirTiro(sock, juego):
    print('Esperando tiro')
    s = sock.recv(512).decode("utf-8")     # Recibe el tiro del cliente
    s = s.split(',')
    print(s)
    try:
        coords = ( int(s[1]), int(s[2]) )       # Convierte la cadena en una tupla
        if juego.validar(coords):               # La cadena recibida es valida
            return juego.tirar(s[0], coords)    # Coordenadas registradas y comprueba la condición de ganar
        else:                                   # La cadena recibida no es valida
            return '2'+ s[0]                    # Mensaje de error
    except Exception as e:
        print(e)
        return '2'+ s[0]                        # Error en la cadena

    # Valores de retorno:
    #   0 : Sigue jugando, no hay errores y nadie ha ganado
    #   1 : Termina el juego, empata o gana alguien
    #   2 : Error, rxiste un error en la cadena recibida


def enviar(sock, cadena):
    logging.debug("No hay espacio para mangas")
    cadena = str(cadena).encode()
    sock.sendall(cadena)


def funcion_cliente(client_conn, juego, num_cliente): # Ejecuta la instancia que atiende a un cliente
    # Recibe el socket de comunicación con el cliente,
    # el objeto Gato que contiene los datos del juego,
    # el numero de conexión correspondiente al cliente

    with client_conn:
        client_conn.sendall('3{}'.format(num_cliente).encode())# Enviar turno al cliente

        if num_cliente == 0:                                    # Si es el primer cliente
            logging.debug('El  primer cliente se ha conectado')
            client_conn.sendall('5'.encode())                   # Pide la dificultad
            tam = int(client_conn.recv(512).decode('utf-8'))    # Recibe la dificultad
            juego.inicializar(tam)                              # inicializa el objeto de la partida

        logging.debug('Pidiendo simbolo al cliente')
        client_conn.sendall('4'.encode())                       # Pide simbolo al cliente
        misimbolo = client_conn.recv(64).decode('utf-8')[0]     # Recibe el simbolo del cliente
        logging.debug('El cliente eligio el simbolo: {}'.format(misimbolo))
        # ¿Adquiere candado?
        juego.agregarSimbolo(misimbolo)                         # Registra el simbolo en el objeto del juego
        logging.debug('Simbolo guadado {}'.format(juego.simbolos))
        # ¿Libera candado?

        logging.debug('Esperando la conexión de los clientes restantes')
        juego.barrera.wait()                                    # Espera a que todos los clientes estén listos
        juego.enviarTablero(client_conn, '0' + juego.simbolos[juego.turno]) # Envía el primer tablero a todos
        
        juego_continua = True # Comienza el juego

        while juego_continua: # while juego_continua

            # ¿Adquiere el candado?
            control = recibirTiro(client_conn, juego) # procesa lo recibido, bloqueante hasta que reciba algo
            juego.enviarTableroaTodos(client_conn, juego) # Envía respuesta a todos
            # ¿Libera el candado?

            if control[0] == '1': # Checa si termina el juego
                juego_continua = False
            

        #print('El juego ha terminado')
        #enviar(client_conn, '{:.2f}'.format(juego.tiempoFin - juego.tiempoInicio))  # Envía duración del juego


def main(): # Funcion principal
    ip = None
    puerto = None
    numero_jugadores = None
    lista_hilos = []

    if len(sys.argv) != 4:          # Si no hay argumentos asigna la direccion local
        ip, puerto = ('127.0.0.1', '12345')
        numero_jugadores = 2
    else:
        ip, puerto = sys.argv[1:3]  # Recupera los argumentos de ejecución
        numero_jugadores = int(sys.argv[3])

    dirServidor = (ip, int(puerto))
    juego = Gato(numero_jugadores)  # Objeto gato vacío

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as SocketServidor:   # Crea el socket
        SocketServidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    # Opciones adicionales del socket
        SocketServidor.bind(dirServidor)                                        # Ligar socket a la dirección
        SocketServidor.listen(numero_jugadores)                                 # Espera conexion
        #SocketServidor.setblocking(False)

        logging.debug('El servidor TCP está disponible y en espera de solicitudes')

        # Creación de hilos por cada conexión
        try:
            for n in range(numero_jugadores):                                       # Espera 'numero_jugadores' conexiones
                client_conn, client_addr = SocketServidor.accept()                  # Aceptar al cliente
                juego.lista_conexiones.append(client_conn)                          # Agrega el socket a la lista de conexiones del juego
                logging.debug('Conectado a'.format(client_addr))
                hilo_cliente = threading.Thread(target=funcion_cliente, args=[client_conn, juego, n]) # Crear hilo para el cliente
                hilo_cliente.start() # Iniciar el hilo
                lista_hilos.append(hilo_cliente)
        except Exception as e:
            print(e)
        logging.debug('Todos los clientes conectados')
        for c in lista_hilos:
            c.join()


if __name__ == '__main__':
    main()
