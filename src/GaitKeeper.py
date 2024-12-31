from src.DiscordBot import DiscordBot
from datetime import datetime
from src.logger_config import logger

class GaitKeeper:
    def __init__(self):
        self.sent_messages = []

    def send_alert(self, message, tag_msg):
        alerter = DiscordBot()
        alerter.send_msg(message, tag_msg)

    def purge_message_list(self):
        self.sent_messages = []