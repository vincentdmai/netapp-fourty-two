#!/usr/bin/env python3

import sys
import socket
import tweepy
import re
import hashlib
import pickle
import ClientKeys as ck 
import simpleaudio as sa
from cryptography.fernet import Fernet
from ibm_watson import TextToSpeechV1, ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from os.path import join, dirname 

"""
*** GLOBALS ****
"""

serverIP = None
serverPort = None
socketSize = None
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Connecting to IBM Watson
#Creating the autehtication for IBM Watson
authenticator = IAMAuthenticator(ck.watson_api_key)
text_to_speech = TextToSpeechV1(authenticator=authenticator)

#Connecnting to URL server
text_to_speech.set_service_url(ck.watson_url)

# Stream Listener for real time tweet extraction
class StreamListener(tweepy.streaming.StreamListener):
    def on_status(self, status):
        s.connect((serverIP, serverPort))
        print("Connecting to " + serverIP + " on port " + str(serverPort))
        print("Listening for tweets from Twitter API that contain questions")

        parsed = re.findall(r'\'(.+?)\'',status.text)
        tweet_question = parsed[0].strip("'")

        print("New question found: " + tweet_question)

        #Creating decryption
        key = Fernet.generate_key()
        print("Generated Encryption key: " + str(key))

        cipher_suite = Fernet(key)
        cipher_text = cipher_suite.encrypt(tweet_question.encode('utf-8'))
        print("Cipher Text: " + str(cipher_text))

        #plain_text = cipher_suite.decrypt(cipher_text)
        md5Hash = hashlib.md5(cipher_text) #md5 Hash
        print("Question payload: " + str(md5Hash.digest()))
        
        #creating pickled payload
        msg = pickle.dumps((key, cipher_text, md5Hash.digest()))

        #Connecting to server and sending payload
        print("Sending Question: " + str(msg))
        s.send(bytes(msg))

        #Recieving new PayLoad
        data = s.recv(socketSize)
        print("Received data: " + str(data))
        if data:
            #Recieving the payload
            answer_key, answer_cipher_text, answer_md5Hash = pickle.loads(data)
            print("Decrypt Key: " + str(answer_key))

            #Check sum
            newmd5Hash = hashlib.md5(answer_cipher_text) #md5 Hash
            if newmd5Hash.digest() != answer_md5Hash:
                print('Check Sum failed')

            #Reverseing the encription on the cipher text
            answer_cipher_suite = Fernet(answer_key)
            plain_text = answer_cipher_suite.decrypt(answer_cipher_text)

            #Decoding for raw string
            plain_text = plain_text.decode('utf-8')
            print("Plain Text: " + plain_text)

            #Creating Audio file name
            audioFile = 'client_outputAnswer.wav'
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
            print("Speaking answer: " + plain_text)
            play_obj = wave_obj.play()
            play_obj.wait_done()
        #Ending Session
        s.close()


if __name__ == '__main__':
    # Parse the Command Line Server Info
    # Call Method that takes it in

    # Check correct number of parameters in command line
    if (len(sys.argv) != 7):
        print('ERROR: FAILURE TO INITIALIZE CLIENT')
        print('Invalid Number of Arguments. Specify -sip <SERVER_IP> -sp <SERVER_PORT> -z <SOCKET_SIZE>.')
        sys.exit()
    else:    
        # Iterate through the command line arguments and check if valid parameter flags
        for i, arg in enumerate(sys.argv):
            if (i + 1 < len(sys.argv)):
                if arg == '-sip':
                    serverIP = sys.argv[i+1]
                elif arg == '-sp':
                    serverPort = int(sys.argv[i+1])
                elif arg == '-z':
                    socketSize = int(sys.argv[i+1])
            
        # If invalid parameter flags, then break with ERROR
        if not serverPort or not serverIP or not socketSize:
            print('ERROR: INVALID ARGUMENT FLAGS. Specify -sip <SERVER_IP> -sp <SERVER_PORT> -z <SOCKET_SIZE>.')
            sys.exit()

        """
        *** TWITTER STREAM LISTENER
        """
        # Authentication and Complete End Points
        auth = tweepy.OAuthHandler(ck.twitter_api_key, ck.twitter_secret_api_key)
        auth.set_access_token(ck.twitter_token, ck.twitter_secret_token)
        twitter_api = tweepy.API(auth)

        # Initialize Stream
        sl = StreamListener()
        stream = tweepy.Stream(auth = twitter_api.auth, listener = sl)
        tags = ['#ECE4564T23']
        stream.filter(track=tags)
        """
        *** END TWITTER STREAM LISTENER
        """




        
        





