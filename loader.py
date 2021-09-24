from dotenv import load_dotenv
from bot import Bot
import os
from db import User

load_dotenv()

my_token = os.getenv('bot_token')
api_key = os.getenv('api_key')
bot = Bot(my_token)
User.create_table()
