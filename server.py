#!/usr/bin/env python3

import sys
import socket
import pickle
from cryptography.fernet import Fernet
import hashlib



"""
*** GLOBALS ****
"""

serverIP = ''
serverPort = None
socketSize = None
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def runServer():
    #Binding port to host
    s.bind((serverIP, serverPort))
    s.listen()
    while 1:
        client, address = s.accept()
        data = client.recv(socketSize)   
        if data:
            #Recieving the payload
            key, cipher_text, md5Hash = pickle.loads(data)
            #Check sum
            newmd5Hash = hashlib.md5(cipher_text) #md5 Hash
            if newmd5Hash.digest() != md5Hash:
                print('Check Sum failed')

            #Reverseing the encription on the cipher text
            cipher_suite = Fernet(key)
            plain_text = cipher_suite.decrypt(cipher_text)

            #Decoding for raw string
            plain_text = plain_text.decode('utf-8')
            print(new)
            #client.send(data)
        client.close()


if __name__ == '__main__':
    # Parse the Command Line Server Info
    # Call Method that takes it in

    # Check correct number of parameters in command line
    if (len(sys.argv) != 5):
        print('ERROR: FAILURE TO INITIALIZE CLIENT')
        print('Invalid Number of Arguments. Specify -sp <SERVER_PORT> -z <SOCKET_SIZE>.')
        sys.exit()
    else:    
        # Iterate through the command line arguments and check if valid parameter flags
        for i, arg in enumerate(sys.argv):
            if (i + 1 < len(sys.argv)):
                if arg == '-sp':
                    serverPort = int(sys.argv[i+1])
                elif arg == '-z':
                    socketSize = int(sys.argv[i+1])
            
        # If invalid parameter flags, then break with ERROR
        if not serverPort or not socketSize:
            print('ERROR: INVALID ARGUMENT FLAGS. Specify -sp <SERVER_PORT> -z <SOCKET_SIZE>.')
            sys.exit()

        #Run Server
        runServer()
        