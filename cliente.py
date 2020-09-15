import socket
import sys
import threading
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-2s) %(message)s')

class jugador: # Clase auxiliar para el acceso a valores del jugador entre diferentes hilos

    def __init__(self):
        self.turno = None
        self.cadenaEnviar = None
        self.simbolo = None
        self.recibido = None
        self.tamTablero = None
        self.continuar = True
        self.condicionRecibo = threading.Condition()
        self.condicionEnvio = threading.Condition()
    
    def inicializar(self, turno, simbolo, tamTablero):
        self.turno = turno
        self.simbolo = simbolo
        #self.tiro = tiro
        self.tam = tamTablero

def recibirTablero(sock, tamTablero):
    s = sock.recv(512).decode("utf-8")  # control simbolo tablero
    #print('R: ',s)
    if s[0] == '0' or s[0] == '1' or s[0] =='2':
        print('Tablero actual')
        print('____________________')
        imprimirTablero(s[2:], tamTablero)  # imprime el tablero recibido
        print('\n____________________')
    return s[0:2]                       # retorna la porcion de control de la cadena

def enviarTiro(sock, simbolo, par_coordenado):
    cadena = simbolo + ',' + par_coordenado
    cadena = cadena.encode()
    sock.sendall(cadena)


def imprimirTablero(s, tam):
    for i in range(0, len(s)):
        if (i%tam) == 0:
            print("\n")
        print("{} \t".format(s[i]), end="", flush=True)

def escuchar(sock, yo):
    while yo.continuar:
        logging.debug('Esperando mensajes del servidor')
        yo.recibido = recibirTablero(sock, yo.tamTablero)    # Espera e imprime el tablero. codigo indica el estado del juego
        with yo.condicionRecibo:
            logging.debug('Mensaje recibido {} notificando al hilo principal'.format(yo.recibido))
            yo.condicionRecibo.notify()                        # Despierta al hilo principal cuando se han recibido datos

def enviar(sock, yo):
    while yo.continuar:
        with yo.condicionEnvio:
            logging.debug('Esperando notificacion del hilo principal para enviar datos')
            yo.condicionEnvio.wait() # Espera al hilo principal para enviar los datos
        logging.debug('Notificación recibida, enviando datos')
        sock.sendall(yo.cadenaEnviar.encode())
        

def main():
    # Argumentos de ejecución
    if len(sys.argv) != 3:
        print("usage:", sys.argv[0], "<host> <port>")
        sys.exit(1)
    ip, puerto = sys.argv[1:3]
    dirServidor = (ip, int(puerto))
    yo = jugador()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as SocketCliente: # Creación del socket
        SocketCliente.connect(dirServidor) # Conexión del socket
        logging.debug('Conectado al servidor')
        hilo_escuchar = threading.Thread(target=escuchar, args=[SocketCliente, yo])# Crear hilo de escucha
        hilo_enviar = threading.Thread(target=enviar, args=[SocketCliente, yo])# Crear hilo de escucha
        hilo_escuchar.start() # Comienza a escuchar
        hilo_enviar.start() # Comenza a esperar una solicitud de envío
        logging.debug('Hilos de comunicación creados')

        # En el hilo principal

        while yo.continuar: # while juego_continua
            with yo.condicionRecibo:
                logging.debug('Esperando al hilo que recibe datos')
                yo.condicionRecibo.wait() # Espera una notificación del hilo de escucha
            
            if yo.recibido[0] == '0':                                  # Seguir jugando
                if yo.recibido[1] == yo.simbolo:                  # Si es mi turno
                    print('Su turno. Ingrese las coordenadas de su tiro: ')
                    yo.cadenaEnviar = yo.simbolo + ',' + input()
                    with yo.condicionEnvio:
                        yo.condicionEnvio.notify()                         # Despierta al hilo de envío
                else:                                                       # Si no es mi turno
                    print('Jugador {} ha tirado'.format(yo.recibido[1])) # Indica el tiro que hizo otro jugador

            elif yo.recibido[0] == '1':                                # El juego termina
                print('{} gana'.format(yo.recibido[1]))
                continuar = False

            elif yo.recibido[0] == '3':                                # Guardar turno asignado
                yo.turno = int(yo.recibido[1:])

            elif yo.recibido[0] == '4':                                # Enviar simbolo
                print('Ingrese el caracter que quiera usar en el tablero')
                yo.cadenaEnviar = input()
                with yo.condicionEnvio:
                    yo.condicionEnvio.notify()                             # Despierta al hilo de envío

            elif yo.recibido[0] == '5':                                # Enviar tamaño del tablero
                print('Ingrese la dificultad del juego:\n1) 3x3\n2) 5x5')
                tam = int(input())*2+1
                yo.cadenaEnviar = '{}'.format(tam)
                yo.tamTablero = tam
                with yo.condicionEnvio:
                    yo.condicionEnvio.notify()                             # Despierta al hilo de envío

            else: # Error
                if yo.recibido[1] == yo.simbolo:
                    print('Error en la cadena enviada, intente de nuevo')
                    yo.cadenaEnviar = input()
                    with yo.condicionEnvio:
                        yo.condicionEnvio.notify()
                else:
                    pass


if __name__ == '__main__':
    main()
