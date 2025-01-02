from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from functions import *

phone_number = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Ro'yxatdan o'tish 📲", request_contact=True),
        ],
    ],
    resize_keyboard=True,
)


async def get_main_menu(user_id: int):
    is_admin = is_user_admin(user_id)
    buttons = [
        [
            KeyboardButton(text="🗒 Kurslar ro'yhati"),
            KeyboardButton(text="💠 Referal dastur"),
        ],
        [
            KeyboardButton(text="👤 Shaxsiy kabinet"),
            KeyboardButton(text="🕹 o'yinlar"),
        ],
        [
            KeyboardButton(text="🧩 Bot haqida"),
            KeyboardButton(text="❓ help"),
        ],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="🧑‍💻 admin panel")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


admin_panel_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Kanallar"),
            KeyboardButton(text="❄️ Kurslar"),
        ],
        [
            KeyboardButton(text="👤 Adminlar"),
            KeyboardButton(text="🧑‍🎓 foydalanuvchilar"),
        ],
        [
            KeyboardButton(text="📊 Statistika"),
            KeyboardButton(text="📤 Habar yuborish"),
        ],
        [
            KeyboardButton(text="🔙 asosiy menu"),
        ],
    ],
    resize_keyboard=True,
)

back_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Bekor qilish 🚫"),
        ],
    ],
    resize_keyboard=True,
)

back_button_everyone = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="ortga qaytish 🚫"),
        ],
    ],
    resize_keyboard=True,
)

add_must_channel = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Kanal qo'shish"),
            KeyboardButton(text="🗒 Mavjud kanallar"),
        ],
        [
            KeyboardButton(text="ortga qaytish 🔙"),
        ],
    ],
    resize_keyboard=True,
)


courses_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Kurs qo'shish"),
            KeyboardButton(text="🗒 Mavjud kurslar"),
        ],
        [
            KeyboardButton(text="ortga qaytish 🔙"),
        ],
    ],
    resize_keyboard=True,
)


send_messages = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📨 Barchaga xabar yuborish"),
            KeyboardButton(text="📩 Alohida habar yuborish"),
        ],
        [
            KeyboardButton(text="ortga qaytish 🔙"),
        ],
    ],
    resize_keyboard=True,
)

admins_list_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Admin qo'shish"),
            KeyboardButton(text="🧾 Adminlar ro'yhati"),
        ],
        [
            KeyboardButton(text="ortga qaytish 🔙"),
        ],
    ],
    resize_keyboard=True,
)

users_control_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🪪 foydalanuvchilar ro'yhati"),
        ],
        [
            KeyboardButton(text="🗒 foydalanuvchi ma'lumotlari"),
        ],
        [
            KeyboardButton(text="ortga qaytish 🔙"),
        ],
    ],
    resize_keyboard=True,
)

edit_user_info = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ bal qo'shish"),
            KeyboardButton(text="➖ bal ayrish"),
        ],
        [
            KeyboardButton(text="ortga qaytish 🔙"),
        ],
    ],
    resize_keyboard=True,
)
