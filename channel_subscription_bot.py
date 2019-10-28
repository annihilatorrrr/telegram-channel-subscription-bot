#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import signal
import sys
import telepot
import time

from telepot.loop import MessageLoop

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

reload(sys)
sys.setdefaultencoding('utf-8')

with open('TOKEN') as f:
    TOKEN = f.readline().strip()

def formatConfig(config):
    newConfig = {}
    for key in config:
        values = config[key]
        for v in values:
            v['to'] = int(v['to'])
        newConfig[int(key)] = values
    return newConfig

try:
    with open('CONFIG', 'r') as f:
        CONFIG = formatConfig(json.load(f))
except Exception as e:
    print(e)
    CONFIG = {}

try:
    with open('STOP_SECRET', 'r') as f:
        STOP_SECRET = f.readline()
except:
    STOP_SECRET = 'stop'

def saveConfig():
    with open('CONFIG', 'w') as f:
        f.write(json.dumps(CONFIG, sort_keys=True, indent=2, cls=SetEncoder))

HELP_WORDS = ['help', '帮助', 'start']

HELP_MESSAGE = '''Feel free to use this free bot at your own risk. Feedback is welcomed at @dushufenxiang_chat.

Commands:
subscribe - `subscribe channel/group1 channel/group2` will automatically forward message from channel/group1 to channel/group2
unsubscribe - `unsubscribe channel/group1 channel/group2` will stop subscription

Both of the channels/groups should add this bot as admin.
channel/group can be room ID or room name.
'''

KEY_HELP = '''
Experimental features:
addKey - `addKey channel/group1 channel/group2 key` will add key to the subsription. Message will forward only when message text or msg sender match one of the keys.
removeKey - `removeKey channel/group1 channel/group2` will remove all keys for this subscription.
'''

ADMIN_CHAT_ID = -1001198682178

LONG_TEXT_LIMIT = 300

def handleHelp(msg):
    if msg['chat']['type'] != 'private':
        return
    if not any([word in msg['text'].lower() for word in HELP_WORDS]):
        return
    bot.sendMessage(msg['chat']['id'], HELP_MESSAGE)   

def getKey(d):
    if not 'key' in d:
        return set()
    if isinstance(d['key'], set):
        return d['key']
    d['key'] = set(d['key'])
    return d['key']

def formatAndCheckRoomId(roomId):
    try:
        float(roomId)
    except:
        if roomId and roomId[0] != '@':
            roomId = '@' + roomId
    try:
        result = bot.sendMessage(roomId, 'test') 
        bot.deleteMessage(telepot.message_identifier(result))
        return result['chat']['id']
    except Exception as e:
        print e
        return None

def getSubscriptionIndex(sender, receiver, msg):
    if not sender in CONFIG:
        bot.sendMessage(msg['chat']['id'], 'FAIL. NO SUCH SUBSCRIPTION')    
        return -1
    for index, conf in enumerate(CONFIG[sender]):
        if conf['to'] == receiver:
            break
    if conf['to'] == receiver:
        return index
    bot.sendMessage(msg['chat']['id'], 'FAIL. NO SUCH SUBSCRIPTION')    
    return -1

def handleUnsubscribeInternal(msg, sender, receiver):
    index = getSubscriptionIndex(sender, receiver, msg)
    if index == -1:
        return  
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

def formatSenderReceiver(args, msg, help_message = HELP_MESSAGE):
    if len(args) != 2:
        return bot.sendMessage(msg['chat']['id'], help_message)  
    sender, receiver = map(formatAndCheckRoomId, args)
    if sender == None:
        bot.sendMessage(msg['chat']['id'], "FAIL. Sender Invalid. Both groups/channels need to add this bot as admin.")
        return None, None, False
    if receiver == None:
        bot.sendMessage(msg['chat']['id'], "FAIL. receiver Invalid. Both groups/channels need to add this bot as admin.")    
        return None, None, false
    return sender, receiver, True

def handleSubsriebCommand(msg, words, command):
    sender, receiver, success = formatSenderReceiver(words[1:3], msg)
    if not success:
        return 
    if 'unsubscribe' in command:
        return handleUnsubscribeInternal(msg, sender, receiver)
    handleSubscribeInternal(msg, sender, receiver)

def handleKeyCommand(msg, words, command):
    sender, receiver, success = formatSenderReceiver(words[1:3], msg, help_message = KEY_HELP)
    if not success:
        return
    index = getSubscriptionIndex(sender, receiver, msg)
    if index == -1:
        return 
    if 'remove' in command:
        if len(words) != 3:
            return bot.sendMessage(msg['chat']['id'], KEY_HELP) 
        del CONFIG[sender][index]['key']
        saveConfig()
        return bot.sendMessage(msg['chat']['id'], 'remove key success') 
    if len(words) != 4:
        return bot.sendMessage(msg['chat']['id'], KEY_HELP) 
    key = words[3]
    CONFIG[sender][index]['key'] = getKey(CONFIG[sender][index])
    CONFIG[sender][index]['key'].add(key)
    saveConfig()
    return bot.sendMessage(msg['chat']['id'], 'add key success') 

def handleConfigCommand(msg):
    if msg['chat']['type'] != 'private':
        return
    words = msg['text'].split()    
    if len(words) < 1:
        return
    command = words[0].lower()
    if 'subscribe' in command.lower() and len(words) == 3:
        return handleSubsriebCommand(msg, words, command)
    if 'key' in command.lower():
        return handleKeyCommand(msg, words, command)

    return bot.sendMessage(msg['chat']['id'], HELP_MESSAGE)    
        

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

def satisfyKey(conf, msg):
    conf['key'] = getKey(conf)
    if 'first_name' in msg['from'] and msg['from']['first_name'].lower() in conf['key']:
        return True
    if 'text' in msg:
        if len(msg['text']) > LONG_TEXT_LIMIT: # due to perfomance limitation, always forward long messages, these messages should be more valuable
            return True
        words = set(msg['text'].lower().split())
        if len(words.intersection(conf['key'])) > 1:
            return True
    return False

def handleGroup(msg):
    for conf in CONFIG.get(msg['chat']['id'], []):
        if not 'key' in conf or satisfyKey(conf, msg):
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
    handleConfigCommand(msg)
    handleGroup(msg)
    handleLongChat(msg)

bot = telepot.Bot(TOKEN)
MessageLoop(bot, handle).run_as_thread()
while 1:
    time.sleep(10)