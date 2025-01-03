import requests
from datetime import datetime
from discord_webhook import DiscordWebhook
import os
from logger_config import logger

class DiscordBot:
    @staticmethod
    def send_msg(body, tag_msg):
        try:
            if tag_msg == "exit_request":
                url = os.getenv("DISCORD_HOOK")
                message = f"LIDO VALIDATOR EXIT REQUEST \n{body}"
            elif tag_msg == "low_eff":
                url = os.getenv("DISCORD_HOOK")
                message = f"ALERT LOW EFFECTIVENESS \n{body}"
            elif tag_msg == "rated_stats":
                url = os.getenv("DISCORD_HOOK_RATED")
                message = f"CSM DAILY STATS \n{body}"
            else:
                return
            
            webhook = DiscordWebhook(url=url, content=message)
            _ = webhook.execute()
        except Exception as e:
            logger.error(f"Error in Discord Hook: {e}")