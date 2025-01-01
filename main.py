import asyncio
import logging
import sqlite3
from config import *
from states.state import UserStates
from keyboards.keyboard import phone_number, get_main_menu
from states.middleware import CheckSubscriptionMiddleware
from functions import *


conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    phone TEXT,
    referrals INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0
);
"""
)

conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_name TEXT NOT NULL,
    channel_identifier TEXT UNIQUE NOT NULL,  
    points_required INTEGER NOT NULL
);

    """
)


MAIN_ADMIN_ID = 6807731973


conn = sqlite3.connect("users.db")
cursor = conn.cursor()


cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER UNIQUE
    );
"""
)
cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (MAIN_ADMIN_ID,))
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS referrals (
    invitee_id INTEGER PRIMARY KEY,
    referrer_id INTEGER NOT NULL
);
    """
)
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS channels (
    channel_id TEXT PRIMARY KEY,
    channel_username TEXT,
    channel_name TEXT
);
"""
)
conn.commit()
conn.close()

import handlers


dp.message.middleware(CheckSubscriptionMiddleware())

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    referrerid = None
    if message.text.startswith("/start"):
        referrer_text = message.text.split("start=")[0].split()[-1]
        if referrer_text.strip().isdigit():
            referrerid = int(referrer_text)
            await save_referral(message.from_user.id, referrerid)
            print("ishlayapti")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        await state.update_data(referrer_id=referrerid)
        await state.set_state(UserStates.waiting_for_phone)
        await message.answer(
            "Botdan foydalanish uchun quidagi tugmani bosing 👇",
            reply_markup=phone_number,
        )
    else:
        menu = await get_main_menu(user_id=message.from_user.id)
        await message.answer("Siz asosiy menudasiz 👇", reply_markup=menu)
    conn.close()


@dp.message()
async def any_word(msg: types.Message):
    await msg.answer("Siz notog'ri buyruq yubordingiz!")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())