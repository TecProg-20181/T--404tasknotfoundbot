import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task
from db import Log
from handlebot import HandleBot
from datetime import datetime


class BotFunctions(HandleBot):

    def __init__(self):
        HandleBot.__init__(self)

    def checkMsg(self, msg):
        text = ''
        if msg != '':
            if len(msg.split(', ')) > 1:
                text = msg.split(', ')[-1]  # get the priority
            msg = msg.split(', ', 1)[0]  # get the name task
        return msg, text

    def newTask(self, msg, chat):
        text, msg = self.checkMsg(msg)

        if text == '':
            task = Task(chat=chat, name=msg, status='TODO', dependencies='',
                        parents='', priority='')
            db.session.add(task)
            db.session.commit()
            self.send_message("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)
            self.upload_github_issue(task.name, 'ID : [{}]\n\
                                                Name : [{}]\n\
                                                Priority : [None]\n\
                                                Issue created from and with 404tasknotfoundbot tasks'
                                                 .format(task.id, task.name))
        else:
            if text.lower() not in ['high', 'medium', 'low']:
                self.send_message("The priority *must be* one of the following: high, medium, low", chat)
            else:
                priority = text.lower()
                task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority=priority)
                db.session.add(task)
                db.session.commit()
                self.send_message("New task *TODO* [[{}]] {} with priority {}".format(task.id, task.name, task.priority), chat)
                self.upload_github_issue(task.name, 'ID : [{}]\n\
                                                     Name : [{}]\n\
                                                     Priority : [{}]\n\
                                                     Issue created from and with 404tasknotfoundbot tasks'
                                                     .format(task.id, task.name,task.priority))



    def renameTask(self, msg, chat):
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

    def deleteTask(self, msg, chat):
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

    def listTask(self, msg, chat):
        task_list = ''

        task_list += '\U0001F4CB Task List\n'
        query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.id)
        for task in query.all():
            icon = '\U0001F195'
            if task.status == 'DOING':
                icon = '\U000023FA'
            elif task.status == 'DONE':
                icon = '\U00002611'
            duedateprint = '\n  Deadline: {}'.format(task.duedate)
            if task.duedate == None:
                task_list += '[[{}]] {} {}\n'.format(task.id, icon, task.name)
                task_list += self.deps_text(task, chat)
            else:
                task_list += '[[{}]] {} {} {}\n'.format(task.id, icon, task.name, duedateprint)
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
                self.four0four(task_id, chat)
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
                return self.check_dependency(epic_id, target, chat)

        return True

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

    def get_github_user_data(self):
        loginText = 'login.txt'
        fileOpen = open(loginText, 'r')
        login = fileOpen.read().split('\n')
        return login

    def upload_github_issue(self, issueName, issueContent):
        credentials = self.get_github_user_data()
        '''Create an issue on github.com using the given parameters.'''
        repoUrl = 'https://api.github.com/repos/TecProg-20181/T--404tasknotfoundbot/issues'
        session = requests.session()
        session.auth = (credentials[0], credentials[1])
        issue = {'title': issueName,
                 'body': issueContent,
                 }
        r = session.post(repoUrl, json.dumps(issue))
        if r.status_code == 201:
            print ('Successfully created Issue {0:s}'.format(issueName))
        else:
            print ('Could not create Issue {0:s}'.format(issueName))
            print('Response:', r.content)

    def date_format(self, text):
        try:
            datetime.strptime(text, '%m/%d/%Y')
            return True
        except ValueError:
            return False

    def duedate(self, msg, chat):
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
                        self.send_message("_404_ Task {} not found x.x".format(task_id), chat)
                        return

                    if text == '':
                        self.send_message("You need to give any data to task {}".format(task_id), chat)
                        return
                    else:
                        if not self.date_format(text):
                            self.send_message("The duedate needs put on US Format: mm/dd/YYYY", chat)
                        else:
                            task.duedate = datetime.strptime(text, '%m/%d/%Y')
                            self.send_message("Task {} deadline is on: {}".format(task_id, text), chat)
                    db.session.commit()

    def observer(self, text):
        obs = Log(log=text)
        db.session.add(obs)
        db.session.commit()

    def send_log(self, chat):
        query = db.session.query(Log).order_by(Log.id)
        log_list = '\U0001F4CB Log List:\n'
        for log in query.all():
            log_list += '{}: {}\n'.format(log.id, log.log)
        self.send_message(log_list, chat)

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
            self.observer(command)

            if lengh_message > 1:
                msg = split_message[1].strip()

            chat = message["chat"]["id"]

            print(command, msg, chat)

            if command == '/new':
                self.newTask(msg, chat)
            elif command == '/rename':
                self.renameTask(msg, chat)
            elif command == '/duplicate':
                self.duplicate(msg, chat)
            elif command == '/delete':
                self.deleteTask(msg, chat)
            elif command == '/todo':
                self.todo(msg, chat)
            elif command == '/doing':
                self.doing(msg, chat)
            elif command == '/done':
                self.done(msg, chat)
            elif command == '/list':
                self.listTask(msg, chat)
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
            elif command == '/duedate':
                self.duedate(msg, chat)
            elif command == '/log':
                self.send_log(chat)
            else:
                self.send_message("So sorry m8. That's beyond me.", chat)
