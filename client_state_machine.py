# -*- coding: utf-8 -*-
"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
import pygame
import random
import ast
import string
from chat_utils import *


class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = M_CONNECT + peer
        mysend(self.s, msg)
        response = myrecv(self.s)
        if response == (M_CONNECT + 'ok'):
            self.peer = peer
            self.out_msg += 'You are connected with ' + self.peer + '\n'
            return (True)
        elif response == (M_CONNECT + 'busy'):
            self.out_msg += 'User is busy. Please try again later\n'
        elif response == (M_CONNECT + 'hey you'):
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return (False)

    def disconnect(self):
        msg = M_DISCONNECT
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def error(self, msg, error_rate):
        msg = list(msg)
        for i in range(len(msg)):
            point = random.uniform(0, 1)
            if point < error_rate:
                if msg[i].isdigit():
                    new_range = list(string.digits)
                    new_range.remove(msg[i])
                    #print(new_range)
                    msg[i] = random.choice(new_range)
                if msg[i].isalpha():
                    new_range = list(string.ascii_lowercase)
                    new_range.remove(msg[i])
                    #print(new_range)
                    msg[i] = random.choice(new_range)

        msg = ''.join(msg)
        return msg



    def proc(self, my_msg, peer_code, peer_msg, world):
        self.out_msg = ''
        #==============================================================================
        # Once logged in, do a few things: get peer listing, connect, search
        # And, of course, if you are so bored, just go
        # This is event handling instate "S_LOGGEDIN"
        #==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, M_TIME)
                    time_in = myrecv(self.s)
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, M_LIST)
                    logged_in = myrecv(self.s)
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, M_SEARCH + term)
                    search_rslt = myrecv(self.s)[1:].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p':
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, M_POEM + poem_idx)
                    poem = myrecv(self.s)[1:].strip()
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                if peer_code == M_CONNECT:
                    """
                    self.peer = peer_msg
                    self.out_msg += 'Request from ' + self.peer + '\n'
                    self.out_msg += 'You are connected with ' + self.peer
                    self.out_msg += '. Chat away!\n\n'
                    self.out_msg += '------------------------------------\n'
                    """
                    print(peer_msg)
                    posdict = ast.literal_eval(peer_msg)
                    world.interpretPos(self.me, posdict)
                    self.state = S_CHATTING

#==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
#==============================================================================
        elif self.state == S_CHATTING:
            direction_list = ['left', 'right', 'up', 'down']

            pygame.event.pump()
            pressed = pygame.key.get_pressed()

            if pressed[pygame.K_a]:
                if world.players[self.me].changeDirection('left'):
                    mysend(self.s, M_EXCHANGE + self.me + ":left")
            if pressed[pygame.K_d]:
                if world.players[self.me].changeDirection('right'):
                    mysend(self.s, M_EXCHANGE + self.me + ":right")
            if pressed[pygame.K_w]:
                if world.players[self.me].changeDirection('up'):
                    mysend(self.s, M_EXCHANGE + self.me + ":up")
            if pressed[pygame.K_s]:
                if world.players[self.me].changeDirection('down'):
                    mysend(self.s, M_EXCHANGE + self.me + ":down")

            if pressed[pygame.K_RETURN]:
                mysend(self.s, M_EXCHANGE + "start")

            world.tick()

            if world.getWinner() != None:
                self.disconnect()
                self.state = S_LOGGEDIN
                self.peer = ''

            if len(my_msg) > 0:  # my stuff going out
                my_msg = self.error(my_msg, 0.2)
                mysend(self.s, M_EXCHANGE + "[" + self.me + "]:" + my_msg)
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
            if len(peer_msg) > 0:  # peer's stuff, coming in
                if peer_code == M_CONNECT:
                    posdict = ast.literal_eval(peer_msg)
                    world.interpretPos(self.me, posdict)
                    print(posdict)
                elif peer_code == M_START:
                    world.start()
                else:
                    spltmsg = peer_msg.split(":")
                    if spltmsg[1] in direction_list:
                        world.players[spltmsg[0]].changeDirection(spltmsg[1])
                    self.out_msg += peer_msg

            # I got bumped out
            if peer_code == M_DISCONNECT:
                while world.getWinner() == None:
                    world.tick()
                self.state = S_LOGGEDIN

            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu

#==============================================================================
# invalid state
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
