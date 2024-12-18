import sqlite3
import signal
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
import os
from dotenv import load_dotenv
load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 5000)) 
