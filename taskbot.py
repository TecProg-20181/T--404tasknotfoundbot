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

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js

def get_updates(offset=None):
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

def msg_not_empty(msg):
    if msg != '':
        return True

def condition_test(msg):
    if len(msg.split(' ', 1)) > 1:
        return True

def split_msg(msg, element):
    return msg.split(' ', 1)[element]

def check_msg_not_exists(msg):
    if not msg.isdigit():
        return True

def query_one(task_id, chat):
    query = db.session.query(Task).filter_by(id=task_id,chat=chat)
    task = query.one()
    return task

def search_parent(task, target, chat):
    if not task.parents == '':
        parent_id = task.parents.split(',')
        parent_id.pop()

        numbers = [ int(id_pai) for id_pai in parent_id ]

        if target in numbers:
            return False
        else:
            parent = self.query_one(numbers[0], chat)
            return self.search_parent(parent, target, chat)

    return True
def puts_icon_to_priority(task):
    icon_priority = ''
    if task == 'low':
        icon_priority += '\U00002755'
    elif task == 'medium':
        icon_priority += '\U00002757'
    elif task == 'high':
        icon_priority += '\U0000203C'
    return icon_priority


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
            text = ''
            if msg != '':
                if len(msg.split(', ')) > 1:
                    text = msg.split(', ')[-1]
                msg = msg.split(', ', 1)[0]
            if text == '':
                # priority = ''
                task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority='')
                send_message("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)
            else:
                if text.lower() not in ['high', 'medium', 'low']:
                    send_message("The priority *must be* one of the following: high, medium, low", chat)
                else:
                    priority = text.lower()
                    task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority=priority)
                    send_message("New task *TODO* [[{}]] {} with priority {}".format(task.id, task.name, task.priority), chat)

            # task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority='')
            db.session.add(task)
            db.session.commit()
            #send_message("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)

        elif command == '/rename':
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]

            if not msg.isdigit():
                send_message("You must inform the task id", chat)
            else:
                task_id = int(msg)
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    send_message("_404_ Task {} not found x.x".format(task_id), chat)
                    return

                if text == '':
                    send_message("You want to modify task {}, but you didn't provide any new text".format(task_id), chat)
                    return

                old_text = task.name
                task.name = text
                db.session.commit()
                send_message("Task {} redefined from {} to {}".format(task_id, old_text, text), chat)
        elif command == '/duplicate':
            if not msg.isdigit():
                send_message("You must inform the task id", chat)
            else:
                task_id = int(msg)
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    send_message("_404_ Task {} not found x.x".format(task_id), chat)
                    return

                dtask = Task(chat=task.chat, name=task.name, status=task.status, dependencies=task.dependencies,
                             parents=task.parents, priority=task.priority, duedate=task.duedate)
                db.session.add(dtask)

                for t in task.dependencies.split(',')[:-1]:
                    qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
                    t = qy.one()
                    t.parents += '{},'.format(dtask.id)

                db.session.commit()
                send_message("New task *TODO* [[{}]] {}".format(dtask.id, dtask.name), chat)

        elif command == '/delete':
            if not msg.isdigit():
                send_message("You must inform the task id", chat)
            else:
                task_id = int(msg)
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    send_message("_404_ Task {} not found x.x".format(task_id), chat)
                    return
                for t in task.dependencies.split(',')[:-1]:
                    qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
                    t = qy.one()
                    t.parents = t.parents.replace('{},'.format(task.id), '')
                db.session.delete(task)
                db.session.commit()
                send_message("Task [[{}]] deleted".format(task_id), chat)

        elif command == '/todo':
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]

            if not msg.isdigit():
                send_message("You must inform the task id", chat)
            else:
                task_id = int(msg)
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    send_message("_404_ Task {} not found x.x".format(task_id), chat)
                    return
                task.status = 'TODO'
                db.session.commit()
                send_message("*TODO* task [[{}]] {}".format(task.id, task.name), chat)

        elif command == '/doing':
            if not msg.isdigit():
                send_message("You must inform the task id", chat)
            else:
                task_id = int(msg)
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    send_message("_404_ Task {} not found x.x".format(task_id), chat)
                    return
                task.status = 'DOING'
                db.session.commit()
                send_message("*DOING* task [[{}]] {}".format(task.id, task.name), chat)

        elif command == '/done':
            if not msg.isdigit():
                send_message("You must inform the task id", chat)
            else:
                task_id = int(msg)
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    send_message("_404_ Task {} not found x.x".format(task_id), chat)
                    return
                task.status = 'DONE'
                db.session.commit()
                send_message("*DONE* task [[{}]] {}".format(task.id, task.name), chat)

        elif command == '/list':
            a = ''

            a += '\U0001F4CB Task List\n'
            query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.id)
            for task in query.all():
                icon = '\U0001F195'
                if task.status == 'DOING':
                    icon = '\U000023FA'
                elif task.status == 'DONE':
                    icon = '\U00002611'

                a += '[[{}]] {} {}\n'.format(task.id, icon, task.name)
                a += deps_text(task, chat)

            send_message(a, chat)
            a = ''

            a += '\U0001F4DD _Status_\n'
            query = db.session.query(Task).filter_by(status='TODO', chat=chat).order_by(Task.id)
            a += '\n\U0001F195 *TODO*\n'
            for task in query.all():
                icon_priority = puts_icon_to_priority(task.priority)
                a += '[[{}]] {}\n'.format(task.id, task.name)
            query = db.session.query(Task).filter_by(status='DOING', chat=chat).order_by(Task.id)
            a += '\n\U000023FA *DOING*\n'
            for task in query.all():
                icon_priority = puts_icon_to_priority(task.priority)
                a += '[[{}]] {}\n'.format(task.id, task.name)
            query = db.session.query(Task).filter_by(status='DONE', chat=chat).order_by(Task.id)
            a += '\n\U00002611 *DONE*\n'
            for task in query.all():
                icon_priority = puts_icon_to_priority(task.priority)
                a += '[[{}]] {}\n'.format(task.id, task.name)

            send_message(a, chat)

        elif command == '/showpriority':
            a = ''

            a += '\U0001F4DD _Priority_\n'
            query = db.session.query(Task).filter_by(priority='high', chat=chat).order_by(Task.id)
            a += '\n\U0000203C High Priority task\n'
            for task in query.all():
                icon_priority = puts_icon_to_priority(task.priority)
                a += '[[{}]] {}\n'.format(task.id, task.name)
            query = db.session.query(Task).filter_by(priority='medium', chat=chat).order_by(Task.id)
            a += '\n\U00002757 Medium Priority task\n'
            for task in query.all():
                icon_priority = puts_icon_to_priority(task.priority)
                a += '[[{}]] {}\n'.format(task.id, task.name)
            query = db.session.query(Task).filter_by(priority='low', chat=chat).order_by(Task.id)
            a += '\n\U00002755 Low Priority task\n'
            for task in query.all():
                icon_priority = puts_icon_to_priority(task.priority)
                a += '[[{}]] {}\n'.format(task.id, task.name)

            send_message(a, chat)
        elif command == '/dependson':
            text = ''
            if msg_not_empty(msg):
                if condition_test(msg):
                    text = split_msg(msg, 1)
                msg = split_msg(msg, 0)

            if check_msg_not_exists(msg):
                msg_no_task(chat)
            else:
                task_id = int(msg)
                query = db.session.query(Task).filter_by(id=task_id,\
                                                         chat=chat)
                try:
                    task = query_one(task_id, chat)
                except sqlalchemy.orm.exc.NoResultFound:
                    task_not_found_msg(task_id, chat)
                    return

                if text == '':
                    for i in task.dependencies.split(',')[:-1]:
                        i = int(i)
                        q = db.session.query(Task).filter_by(id=i,\
                                                             chat=chat)
                        t = q.one()
                        t.parents = t.parents.replace('{},'\
                                                      .format(task.id), '')

                    task.dependencies = ''
                    send_message("Dependencies removed from task {}"\
                                 .format(task_id), chat)
                else:
                    for depid in text.split(' '):
                        if not depid.isdigit():
                            send_message("All dependencies ids must be"
                                          " numeric, and not {}"\
                                          .format(depid), chat)
                        else:
                            depid = int(depid)
                            query = db.session.query(Task)\
                                                     .filter_by(id=depid,\
                                                     chat=chat)
                            try:
                                taskdep = query_one(depid, chat)
                                list_dependencies = taskdep.dependencies\
                                                           .split(',')

                                if search_parent(task, taskdep.id, chat):
                                    taskdep.parents += str(task.id) + ','
                                else:
                                    send_message("Essa tarefa já é filha"
                                                  " da sub tarefa", chat)
                                    break
                            except sqlalchemy.orm.exc.NoResultFound:
                                task_not_found_msg(task_id, chat)
                                continue
                            deplist = task.dependencies.split(',')
                            if str(depid) not in deplist:
                                task.dependencies += str(depid) + ','

                db.session.commit()
                text_message = 'Task {} dependencies up to date'
                send_message(text_message\
                             .format(task_id), chat)
                send_message("Task {} dependencies up to date".format(task_id), chat)

        elif command == '/priority':
            text = ''
            if msg != '':
                if len(msg.split(' ', 1)) > 1:
                    text = msg.split(' ', 1)[1]
                msg = msg.split(' ', 1)[0]

            if not msg.isdigit():
                send_message("You must inform the task id", chat)
            else:
                task_id = int(msg)
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                try:
                    task = query.one()
                except sqlalchemy.orm.exc.NoResultFound:
                    send_message("_404_ Task {} not found x.x".format(task_id), chat)
                    return

                if text == '':
                    task.priority = ''
                    send_message("_Cleared_ all priorities from task {}".format(task_id), chat)
                else:
                    if text.lower() not in ['high', 'medium', 'low']:
                        send_message("The priority *must be* one of the following: high, medium, low", chat)
                    else:
                        task.priority = text.lower()
                        send_message("*Task {}* priority has priority *{}*".format(task_id, text.lower()), chat)
                db.session.commit()

        elif command == '/start':
            send_message("Welcome! Here is a list of things you can do.", chat)
            send_message(HELP, chat)
        elif command == '/help':
            send_message("Here is a list of things you can do.", chat)
            send_message(HELP, chat)
        else:
            send_message("I'm sorry dave. I'm afraid I can't do that.", chat)


def main():
    last_update_id = None

    while True:
        print("Updates")
        updates = get_updates(last_update_id)

        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)

        time.sleep(0.5)


if __name__ == '__main__':
    main()
