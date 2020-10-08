import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}
newPlayer = {}

def connectionLoop(sock):
    while True:
        # Listen to the next message
        data, addr = sock.recvfrom(1024)
        
        if addr in clients:
            data = json.loads(data)
            if data['heartbeat'] == "heartbeat":
               clients[addr]['lastBeat'] = datetime.now()
               clients[addr]['position'] = data['playerLocation']

        else:
            data = str(data)
            if 'connect' in data:
               
               ConnectedPlayers = {"cmd" : 0, "Connected Players" : []}

               for c in clients:
                  player = {}
                  player['id'] = str(c)
                  player['color'] = clients[c]['color']
                  player['position'] = clients[c]['position']
                  ConnectedPlayers['Connected Players'].append(player)

               newPlayer['id'] = str(addr)
               newPlayer['init'] = True
               NewPlayer = {"cmd": 0, "newPlayer" : newPlayer}
            
               clients[addr] = {}
               # update the last beat of the client object
               clients[addr]['lastBeat'] = datetime.now()
               # add a field called color
               clients[addr]['color'] = 0
               # add a field called position
               clients[addr]['position'] = 0
               # create a message object with a command value and an array of player objects
               message = {"cmd": 0,"player":{"id":str(addr)},"newPlayer": True}  # {"id":addr}}
               
               uniqueID = {"cmd" : 3, "uniqueID" : str(addr)}
               
                # create a JSON string.
                # google what the separator function does. Why do we use it here? Its not always needed.
               m2 = json.dumps(ConnectedPlayers)
               m = json.dumps(newPlayer)
               uniqueIDm = json.dumps(uniqueID)

               # send the messages to the new client
               for c in clients:
                  sock.sendto(bytes(m, 'utf8'), c)
               sock.sendto(bytes(uniqueID, 'utf8'), addr)
               sock.sendto(bytes(m2, 'utf8'), addr)


def cleanClients(sock):
   
    while True:
        # for every client in keys
        # How is this different from what we did in line 67? Try and find out.
        for c in list(clients.keys()):
            # Check if its been longer than 5 seconds since the last heartbeat
            if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
               print('Dropped Client: ', c)
               
               playerLeft = {"cmd": 2,"playerLeft":{"id":str(c)}}
               m = json.dumps(playerLeft)

               # for thread safety, gain the lock
               clients_lock.acquire()
               # delete the client identified by c
               del clients[c]
               # releast the lock we have
               clients_lock.release()

               # send the messages to the clients
               for c in clients:
                  sock.sendto(bytes(m, 'utf8'), c)

        time.sleep(1)


def gameLoop(sock):
    pktID = 0  # just to identify a particular network packet while debugging
    while True:
      # create a game state object
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      print(clients)

      #      print (clients)
      for c in clients:
            # create a player object
            player = {}
            # assign a random color
            clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
            # fill the player details
            player['id'] = str(c)
            player['color'] = clients[c]['color']
            player['position'] = clients[c]['position']
            
            if(newPlayer['init'] == True):
               player['init'] = True
            else:
               player['init'] = False
            
            GameState['players'].append(player)
      s = json.dumps(GameState)
      print(s)
      # send the gamestate json to all clients
      for c in clients:
         sock.sendto(bytes(s, 'utf8'), c)
      clients_lock.release()
      
      time.sleep(1 / 30)

def main():
    print("Running server")
    """
      Start 3 new threads 
    """
    port = 12345
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', port))
    start_new_thread(gameLoop, (s, ))
    start_new_thread(connectionLoop, (s, ))
    start_new_thread(cleanClients, (s, ))
    # keep the main thread alive so the children threads stay alive
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()