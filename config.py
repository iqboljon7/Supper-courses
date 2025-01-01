import sqlite3
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup

bot = Bot(token="7551552738:AAFP7dn4wvg-v3AM75uAFfB9I2XAHjSDbVo")
dp = Dispatcher(storage=MemoryStorage())
