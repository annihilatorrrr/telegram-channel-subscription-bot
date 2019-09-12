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
    TOKEN = f.readline()

try:
    with open('CONFIG', 'r') as f:
        SETTING = json.load(f)
except:
    SETTING = {}

try:
    with open('STOP_SECRET', 'r') as f:
        STOP_SECRET = f.readline()
except Exception:
    STOP_SECRET = 'stop'

def saveSetting():
    with open('CONFIG', 'w') as f:
        f.write(json.dumps(SETTING, sort_keys=True, indent=2))

HELP_WORDS = ['help', '帮助', 'start']

HELP_MESSAGE = '''Feel free to use this free bot at your own risk. Feedback is welcomed at @dushufenxiang_chat.

Commands:
subscribe - `subscribe channel/group1 channel/group2` will automatically forward message from channel/group1 to channel/group2
unsubscribe - `unsubscribe channel/group1 channel/group2` will stop subscription

Both of the channels/groups should add this bot as admin.
channel/group can be room ID or room name.
'''

ADMIN_CHAT_ID = '@dhsdjk' # debug

LONG_TEXT_LIMIT = 300

def handleHelp(msg):
    if msg['chat']['type'] != 'private':
        return
    if not any([word in msg['text'].lower() for word in HELP_WORDS]):
        return
    bot.sendMessage(msg['chat']['id'], HELP_MESSAGE)    

def formatChatRoomId(roomId):
    if len(roomId) > 0 and roomId[0] == '@':
        return roomId
    try:
        float(roomId)
        return roomId
    except:
        return '@' + roomId

def getSubscriptionIndex(sender, receiver):
    if not sender in SETTING:
        return -1
    for index, config in enumerate(SETTING[sender]):
        if config['to'] == receiver:
            break
    if config['to'] == receiver:
        return index
    return -1

def handleUnsubscribeInternal(msg, sender, receiver):
    if getSubscriptionIndex(sender, receiver) == -1:
        return bot.sendMessage(msg['chat']['id'], 'FAIL. NO SUCH SUBSCRIPTION')    
    del SETTING[sender][index]
    if len(SETTING[sender]) == 0:
        del SETTING[sender]  
    saveSetting()          
    bot.sendMessage(msg['chat']['id'], 'unsubscribe success') 

def canSendMessage(roomId):
    try:
        result = bot.sendMessage(roomId, 'test') 
        bot.deleteMessage(telepot.message_identifier(result))
        return True
    except Exception as e:
        return False

def handleSubscribeInternal(msg, sender, receiver):
    if getSubscriptionIndex(sender, receiver) != -1:
        return bot.sendMessage(msg['chat']['id'], 'WARING: subscription already exists.')    
    for roomId in [sender, receiver]:
        if not canSendMessage(roomId):
            bot.sendMessage(msg['chat']['id'], 'CAN NOT SEND MESSAGE IN ' + roomId + '. Please add this bot into the channel/group and set as admin.')    
            return
    SETTING[sender] = SETTING.get(sender, [])
    SETTING[sender].append({'to': receiver})
    saveSetting()
    bot.sendMessage(msg['chat']['id'], 'subscribe success') 

def handleSubscribe(msg):
    if msg['chat']['type'] != 'private':
        return
    words = msg['text'].split()    
    if len(words) < 1:
        return
    command = words[0]
    if not 'subscribe' in command.lower():
        bot.sendMessage(msg['chat']['id'], HELP_MESSAGE)    
        return
    if len(words) != 3:
        bot.sendMessage(msg['chat']['id'], HELP_MESSAGE)    
        return
    sender, receiver = map(formatChatRoomId, words[1:])
    if 'unsubscribe' in command.lower():
        handleUnsubscribeInternal(msg, sender, receiver)
        return
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
    if not 'username' in msg['chat']:
        return
    group = '@' + msg['chat']['username']
    for config in SETTING.get(group, []):
        sendMessageDedup(config['to'], msg)

def handleLongChat(msg):
    if 'forward_from_chat' in msg or not 'text' in msg:
        return
    if len(msg['text']) > LONG_TEXT_LIMIT:
        sendMessageDedup(ADMIN_CHAT_ID, msg) 

def handleExit(msg): # for debug use
    if 'text' in msg and msg['text'] == STOP_SECRET and msg['date'] > time.time() - 1:
        os.kill(os.getpid(), signal.SIGINT)

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