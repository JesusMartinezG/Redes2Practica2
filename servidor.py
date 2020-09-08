import time
import socket
import sys
import random
import threading


class Gato:

    def __init__(self): # Crea un objeto base, sin valores en sus atributos
        self.tiempoInicio = None
        self.tiempoFin = None
        self.tam = None
        self.numJugadores = None
        self.tablero = None
        self.turno = None
        self.numTiros = None
        self.tiros_maximos = None
        self.simbolos = []
        self.lista_conexiones = []  # Lista vacía donde se guardará los sockets para la conexión con los clientes


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

    # def agregarJugador(self, simbolo):


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
    cadena = str(cadena).encode()
    sock.sendall(cadena)


def funcion_cliente(client_conn, juego, num_cliente): # Ejecuta la instancia que atiende a un cliente
    # Recibe el socket de comunicación con el cliente,
    # el objeto Gato que contiene los datos del juego,
    # el numero de conexión correspondiente al cliente

    with client_conn: # Cuando el juego termina, cierra la conexión con el cliente
        print(num_cliente)
        client_conn.sendall(str(num_cliente).encode())  # Enviar turno asignado al cliente

        if num_cliente == 0: # Si es el primer cliente en conectarse
            tam = int(((client_conn.recv(512)).decode('utf-8')))  # Espera la dificultad
            juego.inicializar(tam)  # Modifica el objeto
            print('Juego creado tablero {}x{}'.format(tam, tam))

        continuar = True

        juego.enviarTablero(client_conn, '0' + juego.simbolos[juego.turno]) # Envía el tablero inicial a todos los clientes

        while continuar:  # Recibe y envía tiros

            if juego.simbolos[juego.turno] == 'x':  # Turno del cliente
                print('Turno del cliente')
                r = recibirTiro(client_conn, juego)  # Analiza la cadena del cliente
                if r[0] == '0':
                    # juego.cambiarTurno()
                    juego.enviarTablero(client_conn, r)
                    print('Tiro registrado, el juego continúa')
                elif r[0] == '1':
                    print('{} gana'.format(r[1]))
                    juego.enviarTablero(client_conn, r)  # Envía tablero al cliente
                    continuar = False
                else:
                    juego.enviarTablero(client_conn, r)  # Error en la cadena recibida
                    print('Error en los datos recibidos')

            else:  # Turno del cpu
                print('Turno del CPU')
                if r[0] == '0':
                    r = juego.cpu()
                    # juego.cambiarTurno()
                    print('Tiro de CPU registrado')
                    juego.enviarTablero(client_conn, r)
                    print('Tiro registrado, el juego continúa')
                elif r[0] == '1':
                    print('{} gana'.format(r[1]))
                    juego.enviarTablero(client_conn, r)  # Envía tablero al cliente
                    continuar = False
        print('El juego ha terminado')
        enviar(client_conn, '{:.2f}'.format(juego.tiempoFin - juego.tiempoInicio))  # Envía duración del juego


def main(): # Funcion principal
    ip = None
    puerto = None
    numero_jugadores = None
    juego = Gato()  # Objeto gato vacío
    lista_hilos = []

    if len(sys.argv) != 4:          # Si no hay argumentos asigna la direccion local
        ip, puerto = ('127.0.0.1', '12345')
        numero_jugadores = 2
    else:
        ip, puerto = sys.argv[1:3]  # Recupera los argumentos de ejecución
        numero_jugadores = int(sys.argv[3])

    dirServidor = (ip, int(puerto))
    juego.numJugadores = numero_jugadores

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as SocketServidor:   # Crea el socket
        SocketServidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    # Opciones adicionales del socket
        SocketServidor.bind(dirServidor)                                        # Ligar socket a la dirección
        SocketServidor.listen(numero_jugadores)                                 # Espera conexion

        print("El servidor TCP está disponible y en espera de solicitudes")

        # Creación de hilos por cada conexión
        try:
            for n in range(numero_jugadores): # Espera 'numero_jugadores' conexiones
                client_conn, client_addr = SocketServidor.accept()               # Aceptar al cliente
                juego.lista_conexiones.append(client_conn)  # Agrega el socket a la lista de conexiones del juego
                print("Conectado a", client_addr)
                hilo_cliente = threading.Thread(target=funcion_cliente, args=[client_conn, juego, n]) # Crear hilo para el cliente
                hilo_cliente.start() # Iniciar el hilo
                lista_hilos.append(hilo_cliente)
        except Exception as e:
            print(e)
        print('El juego ha terminado. Cerrando todos los hilos')
        for c in lista_hilos:
            c.join()


if __name__ == '__main__':
    main()
