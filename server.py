#!/usr/bin/env python3
# python .\server.py  -sp 50000 -z 1024
# Vincent Mai, Justin Nguyen, Malik Eleman

import ServerKeys as sk
import sys
import socket
import pickle
import hashlib
import simpleaudio as sa
import wolframalpha
from os.path import join, dirname 
from cryptography.fernet import Fernet
from ibm_watson import TextToSpeechV1, ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator



"""
*** GLOBALS ****
"""
#TODO always check IP4 connection matches with server IP
serverIP = '192.168.0.121'
serverPort = None
socketSize = None
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#Allows us to use same port and address
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


#Connecting to IBM Watson
#Creating the autehtication for IBM Watson
authenticator = IAMAuthenticator(sk.watson_api_key)
text_to_speech = TextToSpeechV1(authenticator=authenticator)

#Connecnting to URL server
text_to_speech.set_service_url(sk.watson_url)

#Using the wolfram alpha api to get an answer to our question
def wolfram_get_answer(question):
    try:
        #Creating a client object using the wolframalpha python library
        client = wolframalpha.Client(sk.wolfram_app_id)

        #Generating a results object from the client
        client_results = client.query(question)

        #Getting the answer to our question in plaintext 
        answer = next(client_results.results).text
    except AttributeError as ex:
        print('Current question payload has no results attribute on Wolfram Alpha')
        return 'Invalid Question. Please make sure question is answerable on Wolfram Alpha.'

    #Returning a string of our answer
    return answer

def run_server():
    s.listen()
    print("[Server 02] – Listening for client connections")
    client, address = s.accept()
    print("[Server 03] – Accepted client connection from " + str(address) + " on port " + str(client.getsockname()))
    while 1:
        data = client.recv(socketSize)
        print("[Server 04] – Received data: " + str(data))   
        if data:
            #Recieving the payload
            key, cipher_text, md5Hash = pickle.loads(data)
            print("[Server 05] – Decrypt Key: " + str(key))
            #Check sum
            newmd5Hash = hashlib.md5(cipher_text) #md5 Hash
            if newmd5Hash.digest() != md5Hash:
                print('Check Sum failed')

            #Reverseing the encription on the cipher text
            cipher_suite = Fernet(key)
            plain_text = cipher_suite.decrypt(cipher_text)

            #Decoding for raw string
            plain_text = plain_text.decode('utf-8')
            print("[Server 06] – Plain Text: " + plain_text)
            
            #Creating Audio file name
            audioFile = 'outputServer.wav'
            #Tries to use IBM watson to create audio file
            try:
                with open(join(dirname(__file__), audioFile), 'wb') as audio_file:
                    response = text_to_speech.synthesize(plain_text, accept='audio/wav', voice="en-US_AllisonVoice").get_result()
                    audio_file.write(response.content)
            #Will throw out error on temrinal if it fails
            except ApiException as ex:
                    print("Method failed with status code " + str(ex.code) + ": " + ex.message)

            #Inits the audio object and plays, and waits till audio file is done
            wave_obj = sa.WaveObject.from_wave_file(audioFile)
            print("[Server 07] – Speaking Question: " + plain_text)
            play_obj = wave_obj.play()
            play_obj.wait_done() 

            #Using Wolfram Alpha to generate an answer string from question
            print("[Server 08] – Sending question to Wolframalpha")
            ans = wolfram_get_answer(plain_text)
            print("[Server 09] – Received answer from Wolframalpha: " + str(ans))

            #Creating encryption
            answer_key = Fernet.generate_key()
            print("[Server 10] – Encryption key: " + str(answer_key))
            answer_cipher_suite = Fernet(answer_key)
            answer_cipher_text = answer_cipher_suite.encrypt(ans.encode('utf-8'))
            print("[Server 11] – Cipher Text: " + str(answer_cipher_text))
            #plain_text = cipher_suite.decrypt(cipher_text)
            answer_md5Hash = hashlib.md5(answer_cipher_text) #md5 Hash
            print("[Server 12] – Generated MD5 Checksum: " + str(answer_md5Hash.digest()))
            #creating pickled payload
            print("[Server 13] – Answer payload: " + str(answer_cipher_text))
            msg = pickle.dumps((answer_key, answer_cipher_text, answer_md5Hash.digest()))
            print("[Server 14] – Sending answer: " + str(msg))

            #Send data back to client
            client.send(bytes(msg))
        print('[Server END] – Server successfully sent data back to Client.')
        #client.close()


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

        #Binding port to host
        s.bind((serverIP, serverPort))
        print("[Server 01] – Created socket at " + serverIP + " on port " + str(serverPort))

        #Run Server
        run_server()
    
        