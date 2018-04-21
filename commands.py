import  re
import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task

class Commands():

    def newTask(self):
        self.task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority='')
        db.session.add(self.task)
        db.session.commit()
        send_message("New task *TODO* [[{}]] {}".format(self.task.id, self.task.name), chat)

   def renameTask(self,chat):
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



   def duplicateTask(self):
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



   def deleteTask(self):
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


    def printAllTasks(self):
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
    def doingTask(self):
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()def get_url(url):
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
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return
        task.status = 'DOING'
        db.session.commit()
        send_message("*DOING* task [[{}]] {}".format(task.id, task.name), chat)

    def taskDone(self):
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

    def listTasks(self):

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
            a += '[[{}]] {}\n'.format(task.id, task.name)
        query = db.session.query(Task).filter_by(status='DOING', chat=chat).order_by(Task.id)
        a += '\n\U000023FA *DOING*\n'
        for task in query.all():
            a += '[[{}]] {}\n'.format(task.id, task.name)
        query = db.session.query(Task).filter_by(status='DONE', chat=chat).order_by(Task.id)
        a += '\n\U00002611 *DONE*\n'
        for task in query.all():
            a += '[[{}]] {}\n'.format(task.id, task.name)

        send_message(a, chat)

    def dependsOn(self):
        task_id = int(msg)
        query = db.session.query(Task).filter_by(id=task_id, chat=chat)
        try:
            task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        if text == '':
            for i in task.dependencies.split(',')[:-1]:
                i = int(i)
                q = db.session.query(Task).filter_by(id=i, chat=chat)
                t = q.one()
                t.parents = t.parents.replace('{},'.format(task.id), '')

            task.dependencies = ''
            send_message("Dependencies removed from task {}".format(task_id), chat)
        else:
            for depid in text.split(' '):
                if not depid.isdigit():
                    send_message("All dependencies ids must be numeric, and not {}".format(depid), chat)
                else:
                    depid = int(depid)
                    query = db.session.query(Task).filter_by(id=depid, chat=chat)
                    try:
                        taskdep = query.one()
                        taskdep.parents += str(task.id) + ','
                    except sqlalchemy.orm.exc.NoResultFound:
                        send_message("_404_ Task {} not found x.x".format(depid), chat)
                        continue

                    deplist = task.dependencies.split(',')
                    if str(depid) not in deplist:
                        task.dependencies += str(depid) + ','

        db.session.commit()
        send_message("Task {} dependencies up to date".format(task_id), chat)


    def taskPriority(self):
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
    def start():
        send_message("Welcome! Here is a list of things you can do.", chat)
        send_message(HELP, chat)

    def helpbot():
        send_message("Here is a list of things you can do.", chat)
        send_message(HELP, chat)
