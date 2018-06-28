import unittest

from botfunctions import BotFunctions


class TestBot(unittest.TestCase):
    bot = BotFunctions()

    def test_check_empty_msg(self):
        msg = ''
        msg, priority = self.bot.checkMsg(msg)
        self.assertEqual(msg, '')

    def test_check_msg(self):
        msg = 'id, 3'
        msg, priority = self.bot.checkMsg(msg)
        self.assertEqual(msg, 'id')
        self.assertEqual(priority, '3')


if __name__ == '__main__':
    unittest.main()
