import  re
import json
import requests
import time
import urllib
import sqlalchemy

import db
from db import Task

class Commands():

    def newTask(self,chat):
        self.task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority='')
        db.session.add(self.task)
        db.session.commit()
        send_message("New task *TODO* [[{}]] {}".format(self.task.id, self.task.name), chat)

    def renameTask(self,chat,msg):
        self.task_id = int(msg)
        self.query = db.session.query(Task).filter_by(id=self.task_id, chat=self.chat)
        try:
            self.task = self.query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(task_id), chat)
            return

        if text == '':
            send_message("You want to modify task {}, but you didn't provide any new text".format(self.task_id), chat)
            return

        self.old_text = self.task.name
        self.task.name = self.text
        db.session.commit()
        send_message("Task {} redefined from {} to {}".format(self.task_id, self.old_text, self.text), chat)

    def duplicateTask(self,chat,msg):
        self.task_id = int(msg)
        self.query = db.session.query(Task).filter_by(id=self.task_id, chat=chat)
        try:
            self.task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(self.task_id), chat)
            return

        self.dtask = Task(chat=self.task.chat, name=self.task.name, status=self.task.status, dependencies=self.task.dependencies,
                     parents=self.task.parents, priority=self.task.priority, duedate=self.task.duedate)
        db.session.add(self.dtask)

        for t in self.task.dependencies.split(',')[:-1]:
            self.qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
            t = self.qy.one()
            t.parents += '{},'.format(self.dtask.id)

        db.session.commit()
        send_message("New task *TODO* [[{}]] {}".format(self.dtask.id, self.dtask.name), chat)

    def deleteTask(self,chat,msg):
       self.task_id = int(msg)
       self.query = db.session.query(Task).filter_by(id=self.task_id, chat=self.chat)
       try:
           self.task = self.query.one()
       except sqlalchemy.orm.exc.NoResultFound:
           send_message("_404_ Task {} not found x.x".format(self.task_id), chat)
           return
       for t in self.task.dependencies.split(',')[:-1]:
           self.qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
           t = self.qy.one()
           t.parents = t.parents.replace('{},'.format(self.task.id), '')
       db.session.delete(self.task)
       db.session.commit()
       send_message("Task [[{}]] deleted".format(self.task_id), chat)

    def printAllTasks(self,chat,msg):
            self.task_id = int(msg)
            self.query = db.session.query(Task).filter_by(id=self.task_id, chat=self.chat)
            try:
                self.task = self.query.one()
            except sqlalchemy.orm.exc.NoResultFound:
                send_message("_404_ Task {} not found x.x".format(self.task_id), self.chat)
                return
            self.task.status = 'TODO'
            db.session.commit()
            send_message("*TODO* task [[{}]] {}".format(self.task.id, self.task.name), chat)

    def doingTask(self,chat,msg):
        self.task_id = int(msg)
        self.query = db.session.query(Task).filter_by(id=self.task_id, chat=chat)
        try:
            self.task = self.query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(self.task_id), chat)
            return
        self.task.status = 'DOING'
        db.session.commit()
        send_message("*DOING* task [[{}]] {}".format(self.task.id, self.task.name), chat)

    def taskDone(self,chat,msg):
        self.task_id = int(msg)
        self.query = db.session.query(Task).filter_by(id=self.task_id, chat=chat)
        try:
            self.task = query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(self.task_id), chat)
            return
        self.task.status = 'DONE'
        db.session.commit()
        send_message("*DONE* task [[{}]] {}".format(self.task.id, self.task.name), chat)

    def listTasks(self,chat,msg):

        self.a = ''

        self.a += '\U0001F4CB Task List\n'
        self.query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.id)
        for self.task in self.query.all():
            self.icon = '\U0001F195'
            if task.status == 'DOING':
                self.icon = '\U000023FA'
            elif task.status == 'DONE':
                self.icon = '\U00002611'

            self.a += '[[{}]] {} {}\n'.format(self.task.id, self.icon, self.task.name)
            self.a += deps_text(self.task, chat)

        send_message(self.a, chat)
        self.a = ''

        self.a += '\U0001F4DD _Status_\n'
        self.query = db.session.query(Task).filter_by(status='TODO', chat=chat).order_by(Task.id)
        self.a += '\n\U0001F195 *TODO*\n'
        for self.task in self.query.all():
            self.a += '[[{}]] {}\n'.format(self.task.id, self.task.name)
        self.query = db.session.query(Task).filter_by(status='DOING', chat=chat).order_by(Task.id)
        self.a += '\n\U000023FA *DOING*\n'
        for self.task in self.query.all():
            self.a += '[[{}]] {}\n'.format(self.task.id, self.task.name)
        self.query = db.session.query(Task).filter_by(status='DONE', chat=chat).order_by(Task.id)
        self.a += '\n\U00002611 *DONE*\n'
        for self.task in query.all():
            self.a += '[[{}]] {}\n'.format(self.task.id, self.task.name)

        send_message(self.a, chat)

    def dependsOn(self,chat,msg):
        self.task_id = int(msg)
        self.query = db.session.query(Task).filter_by(id=self.task_id, chat=chat)
        try:
            self.task = self.query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(self.task_id), chat)
            return

        if text == '':
            for self.i in self.task.dependencies.split(',')[:-1]:
                self.i = int(i)
                self.q = db.session.query(Task).filter_by(id=i, chat=self.chat)
                self.t = self.self.q.one()
                self.t.parents = self.t.parents.replace('{},'.format(self.task.id), '')

            self.task.dependencies = ''
            send_message("Dependencies removed from task {}".format(self.task_id), chat)
        else:
            for self.depid in self.text.split(' '):
                if not self.depid.isdigit():
                    send_message("All dependencies ids must be numeric, and not {}".format(self.depid), chat)
                else:
                    depid = int(depid)
                    self.query = db.session.query(Task).filter_by(id=self.depid, chat=chat)
                    try:
                        self.taskdep = query.one()
                        self.taskdep.parents += str(self.task.id) + ','
                    except sqlalchemy.orm.exc.NoResultFound:
                        send_message("_404_ Task {} not found x.x".format(self.depid), chat)
                        continue

                    self.deplist = self.task.dependencies.split(',')
                    if str(self.depid) not in self.deplist:
                        self.task.dependencies += str(self.depid) + ','

        db.session.commit()
        send_message("Task {} dependencies up to date".format(self.task_id), chat)


    def taskPriority(self,chat,msg):
        self.task_id = int(msg)
        self.query = db.session.query(Task).filter_by(id=self.task_id, chat=chat)
        try:
            self.task = self.query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            send_message("_404_ Task {} not found x.x".format(self.task_id), chat)
            return

        if self.text == '':
            self.task.priority = ''
            send_message("_Cleared_ all priorities from task {}".format(self.task_id), chat)
        else:
            if self.text.lower() not in ['high', 'medium', 'low']:
                send_message("The priority *must be* one of the following: high, medium, low", chat)
            else:
                self.task.priority = self.text.lower()
                send_message("*Task {}* priority has priority *{}*".format(self.task_id, self.text.lower()), chat)
        db.session.commit()
    def start(self,chat,HELP):
        send_message("Welcome! Here is a list of things you can do.", chat)
        send_message(HELP, chat)

    def helpbot(self,chat,HELP):
        send_message("Here is a list of things you can do.", chat)
        send_message(HELP, chat)
