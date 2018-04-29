#!/usr/bin/env python3

import json
import time
import urllib
import requests


import sqlalchemy

import db
from db import Task
from classes.commands import Commands
from classes.requests import Requests

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

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url( url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates( offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js

def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))

    return max(update_ids)

def deps_text(task, chat, preceed=''):
    text = ''

    for i in range(len(task.dependencies.split(',')[:-1])):
        line = preceed
        query = db.session.query(Task).filter_by(id=int(task.dependencies.split(',')[:-1][i]), chat=chat)
        dep = query.one()

        icon = '\U0001F195'
        if dep.status == 'DOING':
            icon = '\U000023FA'
        elif dep.status == 'DONE':
            icon = '\U00002611'

        if i + 1 == len(task.dependencies.split(',')[:-1]):
            line += '└── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += deps_text(dep, chat, preceed + '    ')
        else:
            line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += deps_text(dep, chat, preceed + '│   ')

        text += line

    return text

def handle_updates(updates):

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

if __name__ == '__main__':
    main()
