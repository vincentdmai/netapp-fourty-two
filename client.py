#!/usr/bin/env python3

import sys
import socket
import ClientKeys as ck 
import tweepy
import re
import hashlib
import pickle
from cryptography.fernet import Fernet


"""
*** GLOBALS ****
"""

serverIP = None
serverPort = None
socketSize = None
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# Stream Listener for real time tweet extraction
class StreamListener(tweepy.streaming.StreamListener):
    def on_status(self, status):
        # TODO: REMOVE PRINT HERE
        parsed = re.findall(r'\'(.+?)\'',status.text)
        tweet_question = parsed[0].strip("'")

        #Creating decryption
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        cipher_text = cipher_suite.encrypt(bytes(tweet_question))
        #plain_text = cipher_suite.decrypt(cipher_text)
        md5Hash = hashlib.md5(bytes(cipher_text)) #md5 Hash
        #creating pickled payload
        msg = pickle.dump((key, cipher_text, md5Hash))

        #Connecting to server and sending payload
        s.connect((serverIP, serverPort))
        s.send(bytes(msg))

        #Recieving new PayLoad
        data = s.recv(socketSize)
        
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




        
        





