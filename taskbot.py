#!/usr/bin/env python3

import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task

def get_token():
    file_token = "token.txt"
    inFile = open(file_token, 'r')
    token = inFile.readline()
    return token


TOKEN = get_token()
URL = "https://api.telegram.org/bot{}/".format(TOKEN.rstrip())

HELP = """
 /new NOME
 /todo ID
 /doing ID
 /date ID
 /done ID
 /delete ID
 /list
 /rename ID NOME
 /dependson ID ID...
 /duplicate ID
 /priority ID PRIORITY{low, medium, high}
 /help
"""

def getFunction(updates):
    for update in updates["result"]:
        if 'message' in update:
            message = update['message']
        elif 'edited_message' in update:
            message = update['edited_message']
        else:
            print('Can\'t process! {}'.format(update))
            return

        command = message["text"].split(" ", 1)[0]
        msg = ''
        if len(message["text"].split(" ", 1)) > 1:
            msg = message["text"].split(" ", 1)[1].strip()

        chat = message["chat"]["id"]

        print(command, msg, chat)

    return {
    '/new': newTask(),
    '/todo': printAllTasks(),
    '/rename':renameTask(),
    '/doing': doingTask(),
    #'/date':,
    '/done': taskDone(),
    '/delete': deleteTask(),
    '/list': listTasks(),
    '/rename': renameTask(),
    '/dependsOn': dependsOn(),
    '/duplicate': duplicateTask(),
    '/priority': taskPriority(),
    '/help': helpbot(),
    '/start': start(),
    }[command]



def handle_updates(updates):


   if command == '/new':
           newTask()

   elif command == '/rename':
           text = ''
           if msg != '':
               if len(msg.split(' ', 1)) > 1:
                   text = msg.split(' ', 1)[1]
               msg = msg.split(' ', 1)[0]

           if not msg.isdigit():
               send_message("You must inform the task id", chat)
           else:
               renameTask()

   elif command == '/duplicate':
       if not msg.isdigit():
           send_message("You must inform the task id", chat)
       else:
          duplicateTask()

   elif command == '/delete':
       if not msg.isdigit():
           send_message("You must inform the task id", chat)
       else:
           deleteTask()

   elif command == '/todo':
       if not msg.isdigit():
           send_message("You must inform the task id", chat)
       else:
           printAllTasks()

   elif command == '/doing':
       if not msg.isdigit():
           send_message("You must inform the task id", chat)
       else:
           doingTask()


   elif command == '/done':
       if not msg.isdigit():
           send_message("You must inform the task id", chat)
       else:
           taskDone()


   elif command == '/list':
       listTasks()

   elif command == '/dependson':
       text = ''
       if msg != '':
           if len(msg.split(' ', 1)) > 1:
               text = msg.split(' ', 1)[1]
           msg = msg.split(' ', 1)[0]

       if not msg.isdigit():
           send_message("You must inform the task id", chat)
       else:
           dependsOn()

   elif command == '/priority':
       text = ''
       if msg != '':
           if len(msg.split(' ', 1)) > 1:
               text = msg.split(' ', 1)[1]
           msg = msg.split(' ', 1)[0]

       if not msg.isdigit():
           send_message("You must inform the task id", chat)
       else:
           taskPriority()


   elif command == '/start':
       start()
   elif command == '/help':
       helpbot()
   else:
       send_message("I'm sorry dave. I'm afraid I can't do that.", chat)


def main():
    last_update_id = None

    while True:
        print("Updates")
        updates = get_updates(last_update_id)

        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            getFunction(updates)

        time.sleep(0.5)
