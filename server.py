#!/usr/bin/env python3

import ServerKeys as sk
import sys
import socket
import pickle
import hashlib
import json
import simpleaudio as sa
import wolframalpha
from os.path import join, dirname 
from cryptography.fernet import Fernet
from ibm_watson import TextToSpeechV1, ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator



"""
*** GLOBALS ****
"""

serverIP = ''
serverPort = None
socketSize = None
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


#Connecting to IBM Watson
#Creating the autehtication for IBM Watson
authenticator = IAMAuthenticator(sk.watson_api_key)
text_to_speech = TextToSpeechV1(authenticator=authenticator)

#Connecnting to URL server
text_to_speech.set_service_url(sk.watson_url)

#Using the wolfram alpha api to get an answer to our question
def wolfram_get_answer(question):
    #Creating a client object using the wolframalpha python library
    client = wolframalpha.Client(sk.wolfram_app_id)

    #Generating a results object from the client
    client_results = client.query(question)

    #Getting the answer to our question in plaintext 
    answer = next(client_results.results).text

    #Returning a string of our answer
    return answer

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
            play_obj = wave_obj.play()
            play_obj.wait_done() 

            # TODO check the send data back to client
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
    
        