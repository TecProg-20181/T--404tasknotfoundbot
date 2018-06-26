import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task
from handlebot import HandleBot
from datetime import datetime

class BotFunctions(HandleBot):

    def __init__(self):
        HandleBot.__init__(self)

    def new(self, msg, chat):
        text = ''
        if msg != '':
                if len(msg.split(', ')) > 1:
                    text = msg.split(', ')[-1]  # get the priority
                msg = msg.split(', ', 1)[0]  # get the name task

        if text == '':
            task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority='')
            db.session.add(task)
            db.session.commit()
            self.send_message("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)
        else:
            if text.lower() not in ['high', 'medium', 'low']:
                self.send_message("The priority *must be* one of the following: high, medium, low", chat)
            else:
                priority = text.lower()
                task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority=priority)
                db.session.add(task)
                db.session.commit()
                self.send_message("New task *TODO* [[{}]] {} with priority {}".format(task.id, task.name, task.priority), chat)


    def rename(self, msg, chat):
        text = ''
        if msg != '':
            if len(msg.split(' ', 1)) > 1:
                text = msg.split(' ', 1)[1]
            msg = msg.split(' ', 1)[0]

        if not msg.isdigit():
            self.send_message("You must inform the task id", chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task).filter_by(id=task_id, chat=chat)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.four0four(chat, task_id)

            if text == '':
                self.send_message("You want to modify task {}, but you didn't provide any new text".format(task_id), chat)
                return

            old_text = task.name
            task.name = text
            db.session.commit()
            self.send_message("Task {} redefined from {} to {}".format(task_id, old_text, text), chat)

    def duplicate(self, msg, chat):
        if not msg.isdigit():
            self.send_message("You must inform the task id", chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task).filter_by(id=task_id, chat=chat)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.four0four(chat, task_id)
                return

            dtask = Task(chat=task.chat, name=task.name, status=task.status, dependencies=task.dependencies,
                         parents=task.parents, priority=task.priority, duedate=task.duedate)
            db.session.add(dtask)

            for t in task.dependencies.split(',')[:-1]:
                query = db.session.query(Task).filter_by(id=int(t), chat=chat)
                t = query.one()
                t.parents += '{},'.format(dtask.id)

            db.session.commit()
            self.send_message("New task *TODO* [[{}]] {}".format(dtask.id, dtask.name), chat)

    def delete(self, msg, chat):
        if not msg.isdigit():
            self.send_message("You must inform the task id", chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task).filter_by(id=task_id, chat=chat)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.four0four(chat, task_id)
                return
            for t in task.dependencies.split(',')[:-1]:
                query = db.session.query(Task).filter_by(id=int(t), chat=chat)
                t = query.one()
                t.parents = t.parents.replace('{},'.format(task.id), '')
            db.session.delete(task)
            db.session.commit()
            self.send_message("Task [[{}]] deleted".format(task_id), chat)

    def todo(self, msg, chat):
        text = ''
        if msg != '':
            if len(msg.split(' ', 1)) > 1:
                text = msg.split(' ', 1)[1]
            msg = msg.split(' ', 1)[0]

        if not msg.isdigit():
            self.send_message("You must inform the task id", chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task).filter_by(id=task_id, chat=chat)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.four0four(chat, task_id)
                return
            task.status = 'TODO'
            db.session.commit()
            self.send_message("*TODO* task [[{}]] {}".format(task.id, task.name), chat)

    def doing(self, msg, chat):
        if not msg.isdigit():
            self.send_message("You must inform the task id", chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task).filter_by(id=task_id, chat=chat)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.four0four(chat, task_id)
                return
            task.status = 'DOING'
            db.session.commit()
            self.send_message("*DOING* task [[{}]] {}".format(task.id, task.name), chat)

    def done(self, msg, chat):
        if not msg.isdigit():
            self.send_message("You must inform the task id", chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task).filter_by(id=task_id, chat=chat)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.four0four(chat, task_id)
                return
            task.status = 'DONE'
            db.session.commit()
            self.send_message("*DONE* task [[{}]] {}".format(task.id, task.name), chat)

    def lista(self, msg, chat):
        task_list = ''

        task_list += '\U0001F4CB Task List\n'
        query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.id)
        for task in query.all():
            icon = '\U0001F195'
            if task.status == 'DOING':
                icon = '\U000023FA'
            elif task.status == 'DONE':
                icon = '\U00002611'

            task_list += '[[{}]] {} {}\n'.format(task.id, icon, task.name)
            task_list += self.deps_text(task, chat)

        task_list += '\U0001F4DD _Status_\n'
        query = db.session.query(Task).filter_by(status='TODO', chat=chat).order_by(Task.id)
        task_list += '\n\U0001F195 *TO DO*\n'
        for task in query.all():
            task_list += '[[{}]] {}\n'.format(task.id, task.name)
        query = db.session.query(Task).filter_by(status='DOING', chat=chat).order_by(Task.id)
        task_list += '\n\U000023FA *DOING*\n'
        for task in query.all():
            task_list += '[[{}]] {}\n'.format(task.id, task.name)
        query = db.session.query(Task).filter_by(status='DONE', chat=chat).order_by(Task.id)
        task_list += '\n\U00002611 *DONE*\n'
        for task in query.all():
            task_list += '[[{}]] {}\n'.format(task.id, task.name)

        self.send_message(task_list, chat)

    def showpriority(self, msg, chat):
        task_list = ''

        task_list += '\U0001F4DD _Priority_\n'
        query = db.session.query(Task).filter_by(priority='high', chat=chat).order_by(Task.id)
        task_list += '\n\U0000203C High Priority task\n'
        for task in query.all():
            task_list += '[[{}]] {}\n'.format(task.id, task.name)
        query = db.session.query(Task).filter_by(priority='medium', chat=chat).order_by(Task.id)
        task_list += '\n\U00002757 Medium Priority task\n'
        for task in query.all():
            task_list += '[[{}]] {}\n'.format(task.id, task.name)
        query = db.session.query(Task).filter_by(priority='low', chat=chat).order_by(Task.id)
        task_list += '\n\U00002755 Low Priority task\n'
        for task in query.all():
            task_list += '[[{}]] {}\n'.format(task.id, task.name)

        self.send_message(task_list, chat)

    def dependson(self, msg, chat):
        text = ''
        if msg != '':
            if len(msg.split(' ', 1)) > 1:
                text = msg.split(' ', 1)[1]
            msg = msg.split(' ', 1)[0]

        if not msg.isdigit():
            self.send_message("You must inform the task id", chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task).filter_by(id=task_id, chat=chat)
            try:
                query = db.session.query(Task).filter_by(id=task_id, chat=chat)
                task = query.one()

            except sqlalchemy.orm.exc.NoResultFound:
                task_not_found_msg(task_id, chat)
                return

            if text == '':
                for i in task.dependencies.split(',')[:-1]:
                    i = int(i)
                    q = db.session.query(Task).filter_by(id=i, chat=chat)
                    t = q.one()
                    t.parents = t.parents.replace('{},'.format(task.id), '')

                task.dependencies = ''
                self.send_message("Dependencies removed from task {}".format(task_id), chat)
            else:
                for depid in text.split(' '):
                    if not depid.isdigit():
                        self.send_message("All dependencies ids must be numeric, and not {}".format(depid), chat)
                    else:
                        depid = int(depid)
                        query = db.session.query(Task).filter_by(id=depid, chat=chat)
                        try:
                            query = db.session.query(Task).filter_by(id=depid, chat=chat)
                            taskdep = query.one()
                            list_dependencies = taskdep.dependencies.split(',')

                            if self.check_dependency(task, taskdep.id, chat):
                                taskdep.parents += str(task.id) + ','
                            else:
                                self.send_message("As tarefas já estão associadas", chat)
                                break
                        except sqlalchemy.orm.exc.NoResultFound:
                            self.four0four(chat, task_id)
                            continue
                        deplist = task.dependencies.split(',')
                        if str(depid) not in deplist:
                            task.dependencies += str(depid) + ','

            db.session.commit()
            self.send_message("Task {} dependencies up to date".format(task_id), chat)

    def priority(self, msg, chat):
        text = ''
        if msg != '':
            if len(msg.split(' ', 1)) > 1:
                text = msg.split(' ', 1)[1]
            msg = msg.split(' ', 1)[0]

        if not msg.isdigit():
            self.send_message("You must inform the task id", chat)
        else:
            task_id = int(msg)
            query = db.session.query(Task).filter_by(id=task_id, chat=chat)
            try:
                task = query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.four0four(chat, task_id)
                return

            if text == '':
                task.priority = ''
                self.send_message("_Cleared_ all priorities from task {}".format(task_id), chat)
            else:
                if text.lower() not in ['high', 'medium', 'low']:
                    self.send_message("The priority *must be* one of the following: high, medium, low", chat)
                else:
                    task.priority = text.lower()
                    self.send_message("*Task {}* priority has priority *{}*".format(task_id, text.lower()), chat)
            db.session.commit()

    def start(self, chat):
        self.send_message("Come closer, I've got some merch that might be helpful.", chat)
        self.send_message(self.HELP, chat)

    def helpr(self, chat):
        self.send_message("Take a quick look at my wares", chat)
        self.send_message(self.HELP, chat)

    def handle_updates(self, updates):
        for update in updates["result"]:
            if 'message' in update:
                message = update['message']
            elif 'edited_message' in update:
                message = update['edited_message']
            else:
                print('Can\'t process! {}'.format(update))
                return

            split_message = message["text"].split(" ", 1)
            command = split_message[0]
            msg = ''
            lengh_message = len(message["text"].split(" ", 1))

            if lengh_message > 1:
                msg = split_message[1].strip()

            chat = message["chat"]["id"]

            print(command, msg, chat)

            if command == '/new':
                self.new(msg, chat)
            elif command == '/rename':
                self.rename(msg, chat)
            elif command == '/duplicate':
                self.duplicate(msg, chat)
            elif command == '/delete':
                self.delete(msg, chat)
            elif command == '/todo':
                self.todo(msg, chat)
            elif command == '/doing':
                self.doing(msg, chat)
            elif command == '/done':
                self.done(msg, chat)
            elif command == '/list':
                self.lista(msg, chat)
            elif command == '/showpriority':
                self.showpriority(msg, chat)
            elif command == '/dependson':
                self.dependson(msg, chat)
            elif command == '/priority':
                self.priority(msg, chat)
            elif command == '/start':
                self.start(chat)
            elif command == '/help':
                self.helpr(chat)
            else:
                self.send_message("So sorry m8. That's beyond me.", chat)
