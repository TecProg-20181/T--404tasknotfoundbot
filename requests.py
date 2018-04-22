import json
import requests
import time
import urllib

import db
from db import Task

class Requests():
    def get_url(self, url):
        self.response = requests.get(url)
        self.content = response.content.decode("utf8")
        return self.content

    def get_json_from_url(self, url):
        self.content = get_url(url)
        self.js = json.loads(content)
        return self.js

    def get_updates(self, offset=None):
        self.url = URL + "getUpdates?timeout=100"
        if offset:
            self.url += "&offset={}".format(offset)
        self.js = get_json_from_url(url)
        return self.js

    def send_message(self, text, chat_id, reply_markup=None):
        self.text = urllib.parse.quote_plus(text)
        self.url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
        if reply_markup:
            self.url += "&reply_markup={}".format(reply_markup)
        get_url(self.url)

    def get_last_update_id(self, updates):
        self.update_ids = []
        for self.update in updates["result"]:
            self.update_ids.append(int(self.update["update_id"]))

        return max(self.update_ids)

    def deps_text(self, task, chat, preceed=''):
        self.text = ''

        for self.i in range(len(task.dependencies.split(',')[:-1])):
            self.line = preceed
            self.query = db.session.query(Task).filter_by(id=int(task.dependencies.split(',')[:-1][i]), chat=chat)
            self.dep = query.one()

            self.icon = '\U0001F195'
            if self.dep.status == 'DOING':
                self.icon = '\U000023FA'
            elif self.dep.status == 'DONE':
                self.icon = '\U00002611'

            if self.i + 1 == len(task.dependencies.split(',')[:-1]):
                self.line += '└── [[{}]] {} {}\n'.format(self.dep.id, self.icon, self.dep.name)
                self.line += deps_text(self.dep, chat, preceed + '    ')
            else:
                self.line += '├── [[{}]] {} {}\n'.format(self.dep.id, self.icon, self.dep.name)
                self.line += deps_text(self.dep, chat, preceed + '│   ')

            self.text += self.line

        return self.text
