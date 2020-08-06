import socket
import select
import errno
import sys
import pickle
from bitarray import bitarray
import random
import zlib
import hammingL2 as ham
import codecs

HEADER_LENGTH = 10 
IP = "127.0.0.1"
PORT = 5555

def receive_message(client_socket,header = ''):
    try:
        if header == '': 
            message_header = client_socket.recv(HEADER_LENGTH)
        else:
            message_header = header
        if not len(message_header):
            return False
        
        message_length  = int(message_header.decode('utf-8').strip())
        data = pickle.loads(client_socket.recv(message_length))
        msg = {"header": message_header, "data": data}
        return {"header": message_header, "data": data}
    except:
        return False

def signin(username):
    dprotocol = {
        'type': 'signin',
        'username': username
    }
    # serializing dprotocol
    msg = pickle.dumps(dprotocol)
    # adding header to msg
    msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", "utf-8") + msg
    return msg

def signinok():
    dprotocol = {
        "type":"signinok",
    }
    # serializing dprotocol
    msg = pickle.dumps(dprotocol)
    # adding header to msg
    msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", "utf-8") + msg
    return msg

def sendmessage(message):
    crc32 = zlib.crc32(pickle.dumps(message))
    dprotocol = {
        "type":"sendmessage",
        "message": message,
        "crc32": crc32
    }
    # serializing dprotocol
    msg = pickle.dumps(dprotocol)
    # adding header to msg
    msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", "utf-8") + msg
    return msg

def sendNoisyMessage(message):
    crc32 = zlib.crc32(pickle.dumps(message))
    noisymessage = addNoise(pickle.dumps(message))
    dprotocol = {
        "type":"sendmessage",
        "message": noisymessage,
        "crc32": crc32
    }
    # serializing dprotocol
    msg = pickle.dumps(dprotocol)
    # adding header to msg
    msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", "utf-8") + msg
    return msg


def addNoise(pickledmsg):
    # se crea el bitarray
    ba = bitarray()
    # se genera el bitarray apartir del mensaje pickled
    ba.frombytes(pickledmsg)
    # se agrega 1 ruido por cada 100 bytes
    for i in range(int(round(len(ba)/100,0))):
        # al azar se modifica el valor de un bit
        ba[random.randint(0,len(ba))] = not ba[random.randint(0,len(ba))]
    # se returna el mensaje pickled con el array con ruido.
    return ba.tobytes()


# Funciones tratar de implementar para Hamming en correccion de errores
'''
def hammingDistance(a, b):
    distance = 0
    for i in xrange(len(a)):
        distance += a[i]^b[i]
    return distance
def minHammingDistance(code):
    minHammingDistance = len(code[0])
    for a in code:
        for b in code:
            if a != b:
                tmp = hammingDistance(a, b)
                if tmp < minHammingDistance:
                    minHammingDistance = tmp
    return minHammingDistance
'''

# make conncection
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP,PORT))
client_socket.setblocking(False)
print(f"Connected to server in {IP}:{PORT}")
signedin = False

my_username = input("Username: ")
msg = signin(my_username)
client_socket.send(msg)

while not signedin:
    try:
        while True:
            #wait for useraccepted
            message = receive_message(client_socket)
            if message:
                if message['data']['username'] == my_username:
                    # send signinok
                    print(f"Singned in server @{IP}:{PORT} as {my_username}")
                    msg = signinok()
                    client_socket.send(msg)
                    signedin = True
                    break
                else:
                    print(f"Server thought you were {message['data']['username']}")
                    print("Disconnecting...")
                    sys.exit()

    except IOError as e:
        # errores de lectura
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error',str(e))
            sys.exit()
        continue

    except Exception as e:
        print('General error', str(e))
        sys.exit()




while True:
    message = input(f"{my_username} > ")


    if message:
        msg = sendNoisyMessage(message)
        client_socket.send(msg)

    try:
        while True:
            # receive things
            username_header = client_socket.recv(HEADER_LENGTH)
            if not len(username_header):
                print("Connection closed by the server")
                sys.exit()

            msg = receive_message(client_socket,username_header)
            if msg['data']['crc32'] == zlib.crc32(pickle.dumps(msg['data']['message'])):
                username = msg['data']['username']
                message = msg['data']['message']
                print(f"{username} > {message}")
            else:
                username = msg['data']['username']
                print(f"You received a message with error from {username}")
                r = ham.calcRedundantBits(len(msg['data']['message']))
                mg = msg['data']['message']
                arr = ham.posRedundantBits(mg, r)
                arr = ham.calcParityBits(arr, r)
                arreglo = ham.detectError(msg['data']['message'], r)
                print(f"Bitarray using Hamming with no error:", arr)
                msg1 = msg['data']['message']
                arr2 = ham.posRedundantBits(msg1, r)
                arr2 = ham.calcParityBits(arr2, r)
                print(f"Bitarray using Hamming with  error:",  arr2)
                print(f"Position of error:" + str(arreglo))


    except IOError as e:
        # errores de lectura
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error',str(e))
            sys.exit()
        continue


    except Exception as e:
        print('General error', str(e))
        sys.exit()
