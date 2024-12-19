import sqlite3
import signal
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
load_dotenv()
import os
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher(storage=MemoryStorage()) 
port = int(os.getenv("PORT", 4000))
def ignore_sigterm(*args):
    print("SIGTERM received, ignoring...")
signal.signal(signal.SIGTERM, ignore_sigterm)