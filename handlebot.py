import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task

class HandleBot():
    def __init__(self):
        self.TOKEN = self.get_token()
        self.URL = "https://api.telegram.org/bot{}/".format(self.TOKEN.rstrip())
        self.HELP = """
/new NOME
/new NOME, PRIORITY{low, medium, high}
/todo ID
/doing ID
/done ID
/delete ID
/list
/rename ID NOME
/dependson ID ID...
/duplicate ID
/priority ID PRIORITY{low, medium, high}
/showpriority
/help
"""
    def get_token(self):
        file_token = "token.txt"
        inFile = open(file_token, 'r')
        token = inFile.readline()
        return token

    def get_url(self, url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        content = self.get_url(url)
        js = json.loads(content)
        return js

    def get_updates(self, offset=None):
        url = self.URL + "getUpdates?timeout=100"
        if offset:
            url += "&offset={}".format(offset)
        js = self.get_json_from_url(url)
        return js

    def send_message(self, text, chat_id, reply_markup=None):
        text = urllib.parse.quote_plus(text)
        url = self.URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
        if reply_markup:
            url += "&reply_markup={}".format(reply_markup)
        self.get_url(url)

    def get_last_update_id(self, updates):
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))
        max_update = max(update_ids)
        return max_update

    def deps_text(self, task, chat, preceed=''):
        text = ''
        last_dependency = len(task.dependencies.split(',')[:-1])
        range_dependency = range(last_dependency)
        for i in range_dependency:
            line = preceed
            query = db.session.query(Task).filter_by(id=int(task.dependencies.split(',')[:-1][i]), chat=chat)
            dep = query.one()

            icon = '\U0001F195'
            if dep.status == 'DOING':
                icon = '\U000023FA'
            elif dep.status == 'DONE':
                icon = '\U00002611'

            if i + 1 == last_dependency:
                line += '└── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '    ')
            else:
                line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
                line += self.deps_text(dep, chat, preceed + '│   ')

            text += line

        return text

    def message_check(self, msg):
        if msg != '':
            if len(msg.split(', ')) > 1:
                text = msg.split(', ')[-1]
            return msg.split(', ', 1)[0]
        else:
            return msg

    def query_one(self, task_id, chat):
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        task = query.one()
        return task

    def check_dependency(self, task, target, chat):
        if not task.parents == '':
            epic_id = task.parents.split(',')
            epic_id.pop()

            numbers = [int(id_epic) for id_epic in epic_id]

            if target in numbers:
                return False
            else:
                query = db.session.query(Task).filter_by(id=numbers[0], chat=chat)
                epic_id = query.one()
                return check_dependency(parent, target, chat)

        return True

    def puts_icon_to_priority(self, task):
        icon_priority = ''
        if task == 'low':
            icon_priority += '\U00002755'
        elif task == 'medium':
            icon_priority += '\U00002757'
        elif task == 'high':
            icon_priority += '\U0000203C'
        return icon_priority

    def four0four(self, chat, task_id):
        self.send_message("_404_ Task {} not found, 404taskbot working as intended".format(task_id), chat)
        return True


"""
Functions for the bot
"""