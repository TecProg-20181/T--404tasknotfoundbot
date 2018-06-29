import unittest
import unittest.mock as mock
from unittest.mock import MagicMock
from unittest.mock import mock_open

from botfunctions import BotFunctions
from handlebot import HandleBot
from db import Task


class TestBot(unittest.TestCase):
    bot = BotFunctions()
    handle = HandleBot()

    def setUp(self):
        self.task = Task(chat=1, name="teste",
                         status='TODO', dependencies='',
                         parents='2, 3', priority='')

    def test_check_empty_msg(self):
        msg = ''
        msg, priority = self.bot.checkMsg(msg)
        result2 = self.handle.message_check(msg)
        self.assertEqual(msg, '')
        self.assertEqual(msg, result2)

    def test_check_msg(self):
        msg = 'id, 3'
        msg, priority = self.bot.checkMsg(msg)
        self.assertEqual(msg, 'id')
        self.assertEqual(priority, '3')

    def test_icon_to_priority(self):
        result = ''
        task = 'low'
        result = self.handle.puts_icon_to_priority(task)
        self.assertEqual('\U00002755', result)

    def test_four0four(self):
        result = self.handle.four0four(1, 1)
        self.assertTrue(result)

    def test_date_format_correct(self):
        text = "12/12/2018"
        result = self.bot.date_format(text)
        self.assertTrue(result)

    def test_date_format_wrong(self):
        text = "22/12/2018"
        result = self.bot.date_format(text)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
