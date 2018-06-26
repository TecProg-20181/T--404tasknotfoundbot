#!/usr/bin/env python3
import json
import requests
import time
import urllib

import sqlalchemy

import db
from db import Task
from handlebot import HandleBot
from botfunctions import BotFunctions

def main():
    last_update_id = None
    taskbot = BotFunctions()

    while True:
        print("Updates")
        updates = taskbot.get_updates(last_update_id)

        if len(updates["result"]) > 0:
            last_update_id = taskbot.get_last_update_id(updates) + 1
            taskbot.handle_updates(updates)

        time.sleep(0.5)


if __name__ == '__main__':
    main()
