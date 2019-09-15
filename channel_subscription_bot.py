#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import signal
import sys
import telepot
import time

from telepot.loop import MessageLoop

reload(sys)
sys.setdefaultencoding('utf-8')

with open('TOKEN') as f:
    TOKEN = f.readline().strip()

try:
    with open('CONFIG', 'r') as f:
        CONFIG = json.load(f)
except:
    CONFIG = {}

try:
    with open('STOP_SECRET', 'r') as f:
        STOP_SECRET = f.readline()
except:
    STOP_SECRET = 'stop'

def saveConfig():
    with open('CONFIG', 'w') as f:
        f.write(json.dumps(CONFIG, sort_keys=True, indent=2))

HELP_WORDS = ['help', '帮助', 'start']

HELP_MESSAGE = '''Feel free to use this free bot at your own risk. Feedback is welcomed at @dushufenxiang_chat.

Commands:
subscribe - `subscribe channel/group1 channel/group2` will automatically forward message from channel/group1 to channel/group2
unsubscribe - `unsubscribe channel/group1 channel/group2` will stop subscription

Both of the channels/groups should add this bot as admin.
channel/group can be room ID or room name.
'''

ADMIN_CHAT_ID = -1001198682178

LONG_TEXT_LIMIT = 300

def handleHelp(msg):
    if msg['chat']['type'] != 'private':
        return
    if not any([word in msg['text'].lower() for word in HELP_WORDS]):
        return
    bot.sendMessage(msg['chat']['id'], HELP_MESSAGE)    

def formatAndCheckRoomId(roomId):
    try:
        float(roomId)
    except:
        if roomId and roomId[0] != '@':
            roomId = '@' + roomId
    try:
        result = bot.sendMessage(roomId, 'test') 
        bot.deleteMessage(telepot.message_identifier(result))
        return str(result['chat']['id'])
    except:
        return None

def getSubscriptionIndex(sender, receiver):
    if not sender in CONFIG:
        return -1
    for index, conf in enumerate(CONFIG[sender]):
        if conf['to'] == receiver:
            break
    if conf['to'] == receiver:
        return index
    return -1

def handleUnsubscribeInternal(msg, sender, receiver):
    index = getSubscriptionIndex(sender, receiver)
    if index == -1:
        return bot.sendMessage(msg['chat']['id'], 'FAIL. NO SUCH SUBSCRIPTION')    
    del CONFIG[sender][index]
    if len(CONFIG[sender]) == 0:
        del CONFIG[sender]  
    saveConfig()          
    bot.sendMessage(msg['chat']['id'], 'unsubscribe success') 

def handleSubscribeInternal(msg, sender, receiver):
    CONFIG[sender] = CONFIG.get(sender, [])
    CONFIG[sender].append({'to': receiver})
    saveConfig()
    bot.sendMessage(msg['chat']['id'], 'subscribe success') 

def handleSubscribe(msg):
    if msg['chat']['type'] != 'private':
        return
    words = msg['text'].split()    
    if len(words) < 1:
        return
    command = words[0]
    if not 'subscribe' in command.lower() or len(words) != 3:
        return bot.sendMessage(msg['chat']['id'], HELP_MESSAGE)    
    sender, receiver = map(formatAndCheckRoomId, words[1:])
    if sender == None:
        return bot.sendMessage(msg['chat']['id'], "FAIL. Sender Invalid")
    if receiver == None:
        return bot.sendMessage(msg['chat']['id'], "FAIL. receiver Invalid")    
    if 'unsubscribe' in command.lower():
        return handleUnsubscribeInternal(msg, sender, receiver)
    handleSubscribeInternal(msg, sender, receiver)

def getChatLink(msg):
    return 't.me/' + msg['chat']['username'] + '/' + str(msg['message_id'])

def sendMessageSmart(receiver, msg):
    if not 'text' in msg or len(msg['text']) < LONG_TEXT_LIMIT:
        return bot.forwardMessage(receiver, '@' + msg['chat']['username'], msg['message_id'])
    else:
        return bot.sendMessage(receiver, getChatLink(msg))

sended = {}

def sendMessageDedup(receiver, msg):
    link = getChatLink(msg)
    message_identifier = str(receiver) + link
    if message_identifier in sended:
        bot.deleteMessage(sended[message_identifier])
    result = sendMessageSmart(receiver, msg)
    sended[message_identifier] = telepot.message_identifier(result)

def handleGroup(msg):
    for conf in CONFIG.get(str(msg['chat']['id']), []):
        sendMessageDedup(conf['to'], msg)

def handleLongChat(msg):
    if 'forward_from_chat' in msg or not 'text' in msg or len(msg['text']) < LONG_TEXT_LIMIT:
        return
    sendMessageDedup(ADMIN_CHAT_ID, msg) 

def handleExit(msg): # for debug use
    if 'text' in msg and msg['text'] == STOP_SECRET and msg['date'] > time.time() - 1:
        os.kill(os.getpid(), signal.SIGINT)
        exit(0)

def handle(msg):
    print msg # Debug use
    handleExit(msg) # Debug use
    handleHelp(msg)
    handleSubscribe(msg)
    handleGroup(msg)
    handleLongChat(msg)

bot = telepot.Bot(TOKEN)
MessageLoop(bot, handle).run_as_thread()
while 1:
    time.sleep(10)