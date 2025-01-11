import sqlite3
import asyncio
import random
from aiogram import types
from aiogram.fsm.context import FSMContext
from config import *
from states.middleware import admin_required
from states.state import *
from functions import *
from keyboards.keyboard import *
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import CallbackQuery
from keyboards.inline import generate_courses_keyboard
from states.middleware import CheckSubscriptionMiddleware
from aiogram.utils.text_decorations import markdown_decoration as md
from aiogram.utils.keyboard import InlineKeyboardBuilder


def generate_callback(action: str, admin_id: int) -> str:
    return f"{action}:{admin_id}"


@dp.message(F.text == "ortga qaytish 🔙")
@admin_required()
async def back_buttton(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(f"Siz admin panelidasiz ⬇️", reply_markup=admin_panel_button)


@dp.message(F.text == "Bekor qilish 🚫")
@admin_required()
async def cancel_butt(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Jarayon bekor qilindi. ✔️\nSiz admin panelidasiz ⬇️",
        reply_markup=admin_panel_button,
    )


@dp.message(F.text == "🧑‍💻 admin panel")
@admin_required()
async def admin_panel(message: types.Message):
    await message.answer("Siz admin panelidasiz ⬇️", reply_markup=admin_panel_button)


@dp.message(F.text == "➕ Kanallar")
@admin_required()
async def list_channels(message: types.Message, state: FSMContext):
    await message.answer(
        f"Bu yerda siz botdan foydalanish uchun majburiy obuna kanallarini qo'shishingiz yoki ularni ko'rishingiz mumkin\nQuidagilardan birini tanlang ⏬",
        reply_markup=add_must_channel,
    )


@dp.message(F.text == "➕ Kanal qo'shish")
@admin_required()
async def add_channels__(message: types.Message, state: FSMContext):
    await message.answer(
        "Qo'shmoqchi bo'lgan kanalning foydalanuvchi nomini (@username) yoki ID sini kiriting",
        reply_markup=back_button,
    )
    await state.set_state(AddChannel.waiting_for_channel_name)


@dp.message(AddChannel.waiting_for_channel_name)
async def process_channel_id(message: types.Message, state: FSMContext):
    channel_id = message.text.strip()
    if channel_id[0] != "@":
        channel_id = "@" + channel_id
    try:
        chat = await bot.get_chat(channel_id)
        channel_name = chat.title
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        chat_id = str(chat.id)[4:]
        cursor.execute(
            "INSERT OR IGNORE INTO channels (channel_id, channel_name, channel_username) VALUES (?, ?, ?)",
            (chat_id, channel_name, channel_id),
        )
        conn.commit()
        await message.answer(
            f"Kanal muvaffaqiyatli qoshildi 🌟 :\n\nUsername: `{channel_id}`\nNomi: {channel_name}",
            reply_markup=admin_panel_button,
        )
        await state.clear()
    except Exception as e:
        await message.answer(
            "Xatolik ❗️❗️❗️\nKanal topilmadi. Yoki bot kanalda admin emas☹️",
            reply_markup=admin_panel_button,
        )
        await state.clear()


@dp.message(UserStates.waiting_for_phone)
async def process_phone_number(message: types.Message, state: FSMContext):
    if message.contact and message.contact.user_id == message.from_user.id:
        phone_number = message.contact.phone_number
        user_id = message.from_user.id
        data = await state.get_data()
        referrer_id = data.get("referrer_id")
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE phone = ?", (phone_number,))
        existing_user = cursor.fetchone()
        if not existing_user:
            cursor.execute(
                "INSERT INTO users (user_id, phone, referrals, points) VALUES (?, ?, 0, 0)",
                (user_id, phone_number),
            )

            conn.commit()
            if referrer_id:

                ref_id = referrer_id
                cursor.execute(
                    "UPDATE users SET referrals = referrals + 1, points = points + 1 WHERE user_id = ?",
                    (ref_id,),
                )
                conn.commit()
                await bot.send_message(
                    ref_id,
                    f"🎉 Tabriklaymiz do'stingiz {message.from_user.first_name} havola orqali ro'yhatdan o'tdi va sizga 1 ball taqdim etildi.",
                )
            menu = await get_main_menu(user_id=message.from_user.id)
            await message.answer(
                "Tabriklaymiz botdan muvaffaqiyatli ro'yhatdan o'tdingiz.\nQuidagilardan birini tanlang ⬇️",
                reply_markup=menu,
            )
        else:

            await message.answer("Siz allaqachon ro'yhatdan o'tgansiz.")

        conn.close()
        await state.clear()
    else:
        await message.answer("Botdan foydalanish uchun quidagi tugmani bosing 👇")


@dp.message(F.text == "🔙 asosiy menu")
async def main_to_menu(message: types.Message, state: FSMContext):
    await message.answer(
        f"Siz bosh menudasiz.", reply_markup=await get_main_menu(message.from_user.id)
    )


@dp.message(F.text == "🗒 Mavjud kanallar")
@admin_required()
async def show_channels(message: types.Message):
    channels = get_channels()
    if not channels:
        await message.answer("📭 Kanallar mavjud emas.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{channel[1]}",
                    url=f"https://t.me/{channel[2][1:]}" if channel[2] else None,
                ),
                InlineKeyboardButton(
                    text="🚫", callback_data=f"delete_channel:{channel[0]}"
                ),
            ]
            for channel in channels
        ]
    )
    await message.answer("📋 Mavjud kanallar:", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith("delete_channel:"))
@admin_required()
async def delete_channel(callback_query: CallbackQuery):
    channel_id = callback_query.data.split(":")[1]
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()

    await callback_query.answer("✅ Kanal muvaffaqiyatli o'chirildi.")
    await callback_query.message.delete()

    channels = get_channels()
    if not channels:
        await callback_query.message.answer("📭 Kanallar mavjud emas.")
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"{channel[1]}",
                        url=f"https://t.me/{channel[2][1:]}" if channel[2] else None,
                    ),
                    InlineKeyboardButton(
                        text="🚫", callback_data=f"delete_channel:{channel[0]}"
                    ),
                ]
                for channel in channels
            ]
        )
        await callback_query.message.answer(
            "📋 Mavjud kanallar:", reply_markup=keyboard
        )


@dp.message(F.text == "❄️ Kurslar")
@admin_required()
async def courses_state(message: types.Message, state: FSMContext):
    await message.answer(
        f"Bu yerda siz kurslarni qo'shishingiz yoki ularni ko'rishingiz mumkin\nQuidagilardan birini tanlang ⏬",
        reply_markup=courses_button,
    )


@dp.message(F.text == "➕ Kurs qo'shish")
@admin_required()
async def add_coursess(message: types.Message, state: FSMContext):
    await message.answer(
        "Qo'shmoqchi bo'lgan kurs kanalining foydalanuvchi nomini (@username) kiriting 🎯",
        reply_markup=back_button,
    )
    await state.set_state(AddCourse.waiting_for_course_username)


@dp.message(AddCourse.waiting_for_course_username)
async def process_channel_id(message: types.Message, state: FSMContext):
    channel_input = message.text.strip()
    chat_id = None
    try:
        if channel_input.isdigit() or channel_input.startswith("-100"):
            chat_id = int("-100" + channel_input)
        else:
            if channel_input[0] != "@":
                channel_input = "@" + channel_input
            chat_id = channel_input
        if course_exists(str(chat_id)):
            await message.answer(
                f"Bu kurs sizda allaqachon mavjud.", reply_markup=admin_panel_button
            )
            await state.clear()
            return
        chat = await bot.get_chat(chat_id)
        channel_name = chat.title
        await state.update_data(waiting_for_course_username=chat_id)
        await message.answer(
            f"Kanal nomi: {channel_name}\nEndi esa kurs uchun nom bering.\nMisol: IELTS full course",
            reply_markup=back_button,
        )
        await state.set_state(AddCourse.just_name)

    except Exception as e:
        await message.answer(
            "Xatolik ❗️❗️❗️\nKanal topilmadi yoki bot kanalda admin emas☹️",
            reply_markup=admin_panel_button,
        )
        await state.clear()


@dp.message(AddCourse.just_name)
async def add_just_name(message: types.Message, state: FSMContext):
    msg = message.text.strip()
    await state.update_data(just_name=msg)
    await message.answer(
        f"Endi esa kursni olish uchun kerak bo'luvchi ballar sonini kiriting. 🗳"
    )
    await state.set_state(AddCourse.waiting_for_course_point)


@dp.message(AddCourse.waiting_for_course_point)
async def process_course_points(message: types.Message, state: FSMContext):
    points = message.text.strip()
    if not points.isdigit() or int(points) <= 0:
        await message.answer(
            "❌ Siz noto'g'ri ma'lumot kiritdingiz. Iltimos, musbat son kiriting.",
            reply_markup=admin_panel_button,
        )
        return

    data = await state.get_data()

    try:
        await add_course(data["just_name"], data["waiting_for_course_username"], points)
    except Exception as e:
        await message.answer(
            "❌ Kursni qo'shishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
            reply_markup=admin_panel_button,
        )
        print(
            f"Error adding course: {e}",
        )
        return

    username_display = data["waiting_for_course_username"]
    course_name = data["just_name"]
    points_display = points
    if str(username_display)[0] != "@":
        username_display = str(username_display)[4:]
    await message.answer(
        f"✅ Kurs muvaffaqiyatli qo'shildi! 🎉\n\n"
        f"🏷 Kurs nomi: {course_name}\n"
        f"🔗 Foydalanuvchi/ID: {username_display}\n"
        f"🎯 Ballar: {points_display}",
        reply_markup=admin_panel_button,
    )
    await state.clear()


@dp.message(F.text == "🗒 Mavjud kurslar")
@admin_required()
async def show_courses(message: types.Message):
    keyboard = await generate_courses_keyboard()
    if not keyboard.inline_keyboard:
        await message.answer(f"📭 Kurslar mavjud emas.")
    else:
        await message.answer("📋 Kurslar ro'yxati:", reply_markup=keyboard)


@dp.message(F.text == "🧑‍🎓 foydalanuvchilar")
@admin_required()
async def users_butn(message: types.Message):
    if message.from_user.id != 6807731973:
        await message.answer(f"Bu bo'limdan faqat asosiy admin foydalana oladi!!!", reply_markup=admin_panel)
    else:
        await message.answer(
            f"Bu bo'limda siz foydalanuvchilar bilan bog'liq amallarni bajarishingiz mumkin",
            reply_markup=users_control_button,
        )


USERS_PER_PAGE = 10


def generate_user_list(users, page):
    start_index = (page - 1) * USERS_PER_PAGE
    end_index = start_index + USERS_PER_PAGE
    page_users = users[start_index:end_index]

    user_list = []
    for index, (user_id, phone) in enumerate(page_users, start=start_index + 1):
        user_list.append(f"{index}. <a href='tg://user?id={user_id}'>{user_id}</a>")

    return user_list


def create_pagination_buttons(page, total_users):
    keyboard = []
    if page > 1:
        keyboard.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}")
        )
    if page * USERS_PER_PAGE < total_users:
        keyboard.append(
            InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}")
        )
    return InlineKeyboardMarkup(inline_keyboard=[keyboard])


@dp.message(F.text == "🪪 foydalanuvchilar ro'yhati")
@admin_required()
async def list_users(message: types.Message):
    try:
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, phone FROM users")
            users = cursor.fetchall()
    except sqlite3.Error as e:
        print(e)
        await message.answer("Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")
        return

    async def show_users(page=1):
        user_list = generate_user_list(users, page)
        user_details = "\n".join(user_list)
        pagination_buttons = create_pagination_buttons(page, len(users))
        await message.answer(
            f"Foydalanuvchilar ro'yhati ({page}-chi sahifa):\n\n{user_details}",
            parse_mode="HTML",
            reply_markup=pagination_buttons,
        )

    await show_users(page=1)


@dp.callback_query(lambda c: c.data.startswith("page_"))
async def paginate_users(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split("_")[1])
    try:
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, phone FROM users")
            users = cursor.fetchall()
    except sqlite3.Error as e:
        print(e)
        await callback_query.answer(
            "Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.", show_alert=True
        )
        return
    if page < 1 or (page - 1) * USERS_PER_PAGE >= len(users):
        await callback_query.answer(
            "Siz birinchi sahifadasiz!" if page < 1 else "Siz oxirgi sahifadasiz!",
            show_alert=True,
        )
        return

    user_list = generate_user_list(users, page)
    user_details = "\n".join(user_list)
    pagination_buttons = create_pagination_buttons(page, len(users))
    await callback_query.message.edit_text(
        f"Foydalanuvchilar ro'yhati ({page}-chi sahifa):\n\n{user_details}",
        parse_mode="HTML",
        reply_markup=pagination_buttons,
    )
    await callback_query.answer()


@dp.message(F.text == "🗒 foydalanuvchi ma'lumotlari")
@admin_required()
async def info_users(message: types.Message, state: FSMContext):
    await message.answer(
        f"Kerakli foydalanuvchining id raqamini kiriting.", reply_markup=back_button
    )
    await state.set_state(UserInformations.userid_state)


@dp.message(UserInformations.userid_state)
@admin_required()
async def state_info_users(message: types.Message, state: FSMContext):
    user_id = message.text
    if not user_id.isdigit():
        await message.answer(
            "Siz noto'g'ri ma'lumot kiritdingiz. Qaytadan urinib ko'ring."
        )
    else:
        if not check_user_exists(int(user_id)):
            await message.answer(
                f"Berilgan ID orqali hech qanday foydalanuvchi topilmadi.",
                reply_markup=admin_panel_button,
            )
        else:
            user_id = int(user_id)
            is_admin = "admin 🧑‍💻" if is_user_admin(user_id) else "foydalanuvchi 🙍‍♂️"
            user_info = get_user_info(user_id)

            if user_info:
                user_details = (
                    f"👤 *Shaxsiy kabinet*\n\n"
                    f"🎟 *Maqomi:* {is_admin}\n"
                    f"📞 *Telefon raqami:* [{user_info['phone']}](tel:{user_info['phone']})\n"
                    f"🆔 *Foydalanuvchi ID:* [{user_info['user_id']}](tg://user?id={user_info['user_id']})\n"
                    f"👥 *Takliflari soni:* {user_info['referrals']}\n"
                    f"⭐️ *Ballari:* {user_info['points']}\n"
                )
                await message.answer(
                    user_details, parse_mode="Markdown", reply_markup=edit_user_info
                )
                global vaqtincha
                vaqtincha = user_id
            else:
                await message.answer(
                    "❌ Foydalanuvchi haqida ma'lumot topilmadi. Iltimos, qaytadan urinib ko'ring",
                    reply_markup=admin_panel_button,
                )
                await state.clear()
        await state.clear()


@dp.message(F.text == "➕ bal qo'shish")
@admin_required()
async def info_users(message: types.Message, state: FSMContext):
    await message.answer(
        f"Foydalanuvchiga qo'shmoqchi bo'lgan ballaringiz sonini kiriting.",
        reply_markup=back_button,
    )
    await state.set_state(Addpontstouser.pointstoadd)


@dp.message(Addpontstouser.pointstoadd)
@admin_required()
async def state_info_users(message: types.Message, state: FSMContext):
    text = message.text
    if not text.isdigit() or int(text) < 0:
        await message.answer(
            f"Siz noto'g'ri ma'lumot kiritdingiz, iltimos to'g'ri raqam kiriting. ",
            reply_markup=back_button,
        )
    else:
        user_id = vaqtincha
        text = int(text)
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        try:
            up_points = max(0, result[0] + text)
            cursor.execute(
                "UPDATE users SET points =  ? WHERE user_id = ?",
                (up_points, user_id),
            )
            await bot.send_message(
                chat_id=user_id,
                text=f"Admin tomonidan hisobingizga {text} ball qo'shildi ✅",
            )
            await message.answer(
                f"Foydalanuvchi hisobiga {text} ball qo'shildi ✅",
                reply_markup=admin_panel_button,
            )
            await state.clear()
        except TelegramBadRequest as e:
            await message.answer(
                f"Xatolik yuz berdi ❗️qaytadan urinib ko'ring",
                reply_markup=admin_panel_button,
            )
        conn.commit()
        conn.close()


@dp.message(F.text == "➖ bal ayrish")
@admin_required()
async def info_users(message: types.Message, state: FSMContext):
    await message.answer(
        f"Foydalanuvchidan ayrimoqchi bo'lgan ballaringiz sonini kiriting.",
        reply_markup=back_button,
    )
    await state.set_state(Addpontstouser.minuspoints)


@dp.message(Addpontstouser.minuspoints)
@admin_required()
async def state_info_users(message: types.Message, state: FSMContext):
    text = message.text
    if not text.isdigit() or int(text) < 0:
        await message.answer(
            f"Siz noto'g'ri ma'lumot kiritdingiz, iltimos to'g'ri raqam kiriting. ",
            reply_markup=back_button,
        )
    else:
        user_id = vaqtincha
        text = int(text)
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        try:
            up_points = max(0, result[0] - text)
            cursor.execute(
                "UPDATE users SET points =  ? WHERE user_id = ?",
                (up_points, user_id),
            )
            await bot.send_message(
                chat_id=user_id,
                text=f"Admin tomonidan hisobingizdan {text} ball ayrildi 🤕",
            )
            await message.answer(
                f"Foydalanuvchi hisobidan {text} ball ayrildi ✅",
                reply_markup=admin_panel_button,
            )
            await state.clear()
        except TelegramBadRequest as e:
            await message.answer(
                f"Xatolik yuz berdi ❗️qaytadan urinib ko'ring",
                reply_markup=admin_panel_button,
            )
        conn.commit()
        conn.close()


@dp.message(F.text == "🕹 o'yinlar")
async def games_butnn(message: types.Message):
    await message.answer(
        f"Bu bo'limda siz qiziqarli o'yinlar orqali ballaringizni ko'paytirib olishingiz mumkin.\nQuidagilardan birini tanlang 👇",
        reply_markup=games_button,
    )


@dp.message(F.text == "ortga 🔙")
async def games_bun(message: types.Message):
    await message.answer(f"Siz o'yinlar bo'limidasiz.", reply_markup=games_button)


@dp.message(F.text == "🎲 dice")
async def send_dice(message: types.Message):
    await message.answer(
        f"🎲 *Dice o'yiniga xush kelibsiz*\n\n"
        f"➡️ Har bir tashlangan 🎲 uchun *3 ball* hisobingizdan yechiladi\n"
        f"🎁 *Sovrin*: Sizga nechchi son tushsa, o‘sha son ball sifatida hisobingizga qo‘shiladi 💵\n\n"
        f"💳 *Sizning hisobingiz:* {get_user_points(message.from_user.id)} ball\n\n"
        f"O'yinni boshlash uchun pastdagi tugmani bosing 👇",
        parse_mode="MarkdownV2",
        reply_markup=dice_play,
    )


@dp.message(F.text == "asosiy menu 🔙")
async def asosiy_menu(message: types.Message):
    await message.answer(
        f"Siz asosiy menudasiz 👇",
        reply_markup=await get_main_menu(message.from_user.id),
    )


@dp.message(F.text == "🎲 boshlash")
async def send_dice(message: types.Message):
    user_id = message.from_user.id
    result = get_user_points(user_id)
    if result > 2:
        sent_message = await message.answer_dice(emoji="🎲")
        res = sent_message.dice.value
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET points = points - ? WHERE user_id = ?",
            (3, user_id),
        )
        cursor.execute(
            "UPDATE users SET points = points + ? WHERE user_id = ?",
            (res, user_id),
        )
        await asyncio.sleep(3)
        await message.answer(
            f"*️⃣ Tushgan raqam — {res}\nHisobingizga {res} ball qo'shildi 🎉\nYana o'ynash uchun pastdagi tugmani bosing👇",
            reply_markup=dice_play,
        )
        conn.commit()
        conn.close()
    else:
        await message.answer(
            f"Sizda yetarlicha ballar yo'q 😕\nKo'proq do'stlaringizni taklif qiling va ballarni ishlang.",
            reply_markup=games_button,
        )


@dp.message(F.text == "⚽️ soccer")
async def send_soccer(message: types.Message):
    await message.answer(
        f"⚽️ *Soccer o'yiniga xush kelibsiz*\n\n"
        f"➡️ Har bir urinish uchun *2 ball* hisobingizdan yechiladi\n"
        f"🎁 *Sovrin*: Agar go'l urilsa sizga 4 ball beriladi aks holda 0 ball olasiz💵\n\n"
        f"💳 *Sizning hisobingiz:* {get_user_points(message.from_user.id)} ball\n\n"
        f"O'yinni boshlash uchun pastdagi tugmani bosing 👇",
        parse_mode="MarkdownV2",
        reply_markup=soccer_play,
    )


@dp.message(F.text == "⚽️ boshlash")
async def start_soccer(message: types.Message):
    user_id = message.from_user.id
    result = get_user_points(user_id)
    if result > 1:
        sent_message = await message.answer_dice(emoji="⚽️")
        res = sent_message.dice.value
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET points = points - ? WHERE user_id = ?",
            (2, user_id),
        )
        await asyncio.sleep(3)
        if res < 3:
            await message.answer(
                f"Afsuski go'l ura olmadingiz 😕\nYana o'ynash uchun pastdagi tugmani bosing👇",
                reply_markup=soccer_play,
            )
        else:
            await message.answer(
                f"go'l urildi 🥳🥳🥳\nHisobingizga 4 ball qo'shildi 🎉\nYana o'ynash uchun pastdagi tugmani bosing👇",
                reply_markup=soccer_play,
            )
            cursor.execute(
                "UPDATE users SET points = points + ? WHERE user_id = ?",
                (4, user_id),
            )
        conn.commit()
        conn.close()
    else:
        await message.answer(
            f"Sizda yetarlicha ballar yo'q 😕\nKo'proq do'stlaringizni taklif qiling va ballarni ishlang.",
            reply_markup=games_button,
        )


def create_random_game_buttons():
    buttons = [
        InlineKeyboardButton(
            text=str(["1️⃣", "2️⃣", "3️⃣"][i - 1]), callback_data=f"choose_{i}"
        )
        for i in range(1, 4)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


@dp.message(F.text == "🎰 radnom")
async def send_random_game(message: types.Message):
    user_points = get_user_points(message.from_user.id)
    await message.answer(
        f"🎰 *Random o'yiniga xush kelibsiz*\n"
        f"➡️ Har bir urinish uchun *3 ball* hisobingizdan yechiladi\n"
        f"🎁 *Sovrin*: Agar siz tanlagan son va random tanlagan son bir biriga to'g'ri kelsa, balingiz 2 barobar bo'lib qaytadi💵\n\n"
        f"💳 *Sizning hisobingiz:* {user_points} ball\n\n"
        f"O'yinni boshlash uchun pastdagi uchta tugmadan birini bosing 👇",
        parse_mode="MarkdownV2",
        reply_markup=create_random_game_buttons(),
    )


@dp.callback_query(lambda c: c.data.startswith("choose_"))
async def process_random_choice(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_choice = int(callback_query.data.split("_")[1])
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    user_points = result[0] if result else 0
    if user_points < 3:
        await callback_query.answer(
            "Sizda yetarlicha ball mavjud emas!", show_alert=True
        )
        return
    new_points = user_points - 3
    random_choice = random.randint(1, 3)
    if user_choice == random_choice:
        new_points += 6
        message = (
            f"Random tanlagan son: {random_choice}\n"
            f"Siz tanlagan son: {user_choice}\n"
            f"Sizga 6 ball qo'shildi! 🥳🥳🥳"
        )
    else:
        message = (
            f"Random tanlagan son: {random_choice}\n"
            f"Siz tanlagan son: {user_choice}\n"
            f"Afsuski, yutolmadingiz. 😔"
        )
    cursor.execute(
        "UPDATE users SET points = ? WHERE user_id = ?", (new_points, user_id)
    )
    conn.commit()
    conn.close()
    await callback_query.answer(message, show_alert=True)


@dp.message(F.text == "❓ help")
async def help_butn(message: types.Message, state: FSMContext):
    await message.answer(
        f"Bot haqida savol va takliflaringiz bo'lsa shu yerda yozib qoldirishingiz mumkin ⬇️",
        reply_markup=back_button_everyone,
    )
    await state.set_state(MessagetoAdmin.msgt)


@dp.message(MessagetoAdmin.msgt)
async def help_button_state(message: types.Message, state: FSMContext):
    if message.text != "ortga qaytish 🚫":
        await bot.send_message(
            chat_id=6807731973,
            text=f"Foydalanuvchi — {message.from_user.first_name} (<a href='tg://openmessage?user_id={message.from_user.id}'>{message.from_user.id}</a>) sizga habar yubordi: \n{message.text}",
            parse_mode="HTML",
        )
        await message.answer(
            f"Habaringiz adminga muvaffaqiyatli yuborildi ✅",
            reply_markup=await get_main_menu(message.from_user.id),
        )
        await state.clear()
    else:
        await state.clear()
        await message.answer(
            f"Siz asosiy menudasiz 👇",
            reply_markup=await get_main_menu(message.from_user.id),
        )


@dp.message(F.text == "📊 Statistika")
@admin_required()
async def statistics(message: types.Message):
    stats = get_bot_statistics()
    stats_message = (
        f"📊 *Bot Statistikasi:*\n\n"
        f"👥 *Jami Foydalanuvchilar:* {stats['total_users']}\n"
        f"📚 *Jami Kurslar:* {stats['total_courses']}\n"
        f"🛠️ *Jami Adminlar:* {stats['total_admins']}\n"
    )

    await message.answer(
        stats_message, parse_mode="Markdown", reply_markup=admin_panel_button
    )


@dp.message(F.text == "📤 Habar yuborish")
@admin_required()
async def send_messages_to_users(message: types.Message):
    await message.answer(
        f"Bu yerda siz barcha obunachilarga yoki faqatgina 1 ta obunachiga habar yuborishingiz mumkin\nQuidagilardan birini tanlang ⏬",
        reply_markup=send_messages,
    )


@dp.message(F.text == "📨 Barchaga xabar yuborish")
@admin_required()
async def send_message_to_all(message: types.Message, state: FSMContext):
    await message.answer(
        f"Yuborish kerak bo'lgan xabar matnini kiriting 📝", reply_markup=back_button
    )
    await state.set_state(msgtoall.sendtoall)


@dp.message(msgtoall.sendtoall)
async def state_send_msg_to_all_stat(message: types.Message, state: FSMContext):
    message_id = message.message_id
    from_chat_id = message.chat.id
    await forward_message_to_all_users(from_chat_id, message_id, message.from_user.id)
    await message.answer(
        "Xabar barcha foydalanuvchilarga muvaffaqiyatli yuborildi ✅",
        reply_markup=admin_panel_button,
    )
    await state.clear()

async def forward_message_to_all_users(from_chat_id: int, message_id: int, admin_id: int):
    users = await get_all_user_ids(admin_id)

    for user_id in users:
        try:
            await bot.forward_message(chat_id=user_id, from_chat_id=from_chat_id, message_id=message_id)
        except Exception as e:
            return


@dp.message(F.text == "📩 Alohida habar yuborish")
@admin_required()
async def send_message_to_all(message: types.Message, state: FSMContext):
    await message.answer(
        "Habar yubormoqchi bo'lgan foydalanuvchining ID raqamini kiriting 📝",
        reply_markup=back_button,
    )
    await state.set_state(msgtoindividual.userid)


@dp.message(msgtoindividual.userid)
async def state_send_msg_to_individual(message: types.Message, state: FSMContext):
    user_id = message.text.strip()
    if not user_id.isdigit():
        await message.answer(
            "Siz noto'g'ri ma'lumot kiritdingiz. Qaytadan urinib ko'ring."
        )
        return
    user_id = int(user_id)
    if user_id == message.from_user.id:
        await message.answer(
            "Siz o'zingizga o'zingiz habar yubora olmaysiz.",
            reply_markup=admin_panel_button,
        )
        await state.clear()
        return
    if not await check_user_exists(user_id):
        await message.answer(
            "Berilgan ID orqali hech qanday foydalanuvchi topilmadi.",
            reply_markup=admin_panel_button,
        )
        await state.clear()
        return
    await state.update_data(userid=user_id)
    await message.answer("Endi esa yuboriladigan habarni yuboring (turli formatda bo'lishi mumkin).")
    await state.set_state(msgtoindividual.sendtoone)


@dp.message(msgtoindividual.sendtoone, content_types=types.ContentType.ANY)
async def state_forward_message_to_individual(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = int(data["userid"])

    try:
        await bot.forward_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
        await message.answer(
            "Habar foydalanuvchiga muvaffaqiyatli yuborildi ✅",
            reply_markup=admin_panel_button,
        )
    except Exception as e:
        await message.answer(
            f"Habar yuborishda xatolik yuz berdi: {e}",
            reply_markup=admin_panel_button,
        )
    finally:
        await state.clear()
@dp.message(F.text == "💠 Referal dastur")
async def send_referral_link(message: types.Message):
    referral_link = f"https://t.me/free_courses_robot?start={message.from_user.id}"

    await message.answer(
        f"🎁 Sizning referral silkangiz 👇👇👇:\n"
        f"{referral_link}\n\n"
        "Ushbu havolani do'stlaringizga yuboring va har bir taklif qilgan do'stingiz uchun 1 ball ga ega bo'ling 🌟"
    )


@dp.message(F.text == "👤 Shaxsiy kabinet")
async def personal_infos(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_info = get_user_info(user_id)

    if user_info:
        user_details = (
            f"👤 *Shaxsiy kabinet*\n\n"
            f"📞 Telefon raqami: {user_info['phone']}\n"
            f"👥 Takliflar soni: *{user_info['referrals']}*\n"
            f"⭐️ Ballar: *{user_info['points']}*\n"
        )
        await message.answer(user_details, parse_mode="Markdown")
    else:
        await message.answer(
            "❌ Foydalanuvchi haqida ma'lumot topilmadi. Iltimos, ro'yhatdan o'ting."
        )


@dp.message(F.text == "🗒 Kurslar ro'yhati")
async def show_courses(message: types.Message):
    courses = get_courses()
    if not courses:
        await message.answer("❌ Hozircha hech qanday kurs mavjud emas.")
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{course['channel_name']} ({course['points_required']} ball)",
                    callback_data=f"course:{course['channel_identifier']}:{course['points_required']}",
                )
            ]
            for course in courses
        ]
    )

    await message.answer(
        "📚 *Kurslar ro'yhati*\nKursni sotib olish uchun shunchaki ustiga bosing:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


@dp.message(F.text == "🧩 Bot haqida")
async def about_bot(message: types.Message):
    await message.answer(
        f"Bu bot sizga do'stlaringizni taklif qilish orqali ball yig'ish va to'plangan ballar evaziga qiziqarli kurslarni sotib olish imkoniyatini taqdim etadi! \n🎯 Har bir taklifingiz — 1 ballga teng. Do'stlaringizni taklif qiling va bilim olishingizni yanada foydali qiling! 🚀",
        reply_markup=await get_main_menu(message.from_user.id),
    )


@dp.message(F.text == "👤 Adminlar")
@admin_required()
async def admins_button(message: types.Message):
    await message.answer(
        f"Bu bo'limda siz admin qo'shishingiz yoki ular ro'yhatini ko'rishingiz mumkin. ",
        reply_markup=admins_list_button,
    )


@dp.message(F.text == "➕ Admin qo'shish")
@admin_required()
async def add_admin_command(message: types.Message, state: FSMContext):
    await message.answer(
        f"Admin etib tayinlamoqchi bo'lgan foydalanuvchini ID raqamini kiriting.",
        reply_markup=back_button,
    )
    await state.set_state(Adminid.admin_id)


@dp.message(Adminid.admin_id)
async def add_admin_state(message: types.Message, state: FSMContext):
    i_d = message.text.strip()
    if not i_d.isdigit():
        await message.answer(
            f"❌ Kiritlgan ma'lumot noto'g'ri. Qaytadan urinib ko'ring",
            reply_markup=back_button,
        )
    elif not check_user_exists(i_d):
        await message.answer(
            f"❌ Foydalanuvchi topilmadi yoki u botning a'zosi emas.",
            reply_markup=admin_panel_button,
        )
        await state.clear()
    else:
        try:
            user_id = int(message.text.strip())
            add_admin(user_id)
            print(list(get_admins()))
            await message.answer(
                f"✅ User {user_id} has been added as an admin.",
                reply_markup=admin_panel_button,
            )
            await state.clear()
        except ValueError:
            await message.answer(
                "❌ Kiritlgan ma'lumot noto'g'ri. Qaytadan urinib ko'ring",
                reply_markup=back_button,
            )


@dp.message(F.text == "🧾 Adminlar ro'yhati")
async def list_admins(message: types.Message):
    admins = get_admins2()
    if not admins:
        await message.answer("Hozircha adminlar ro'yxati bo'sh.")
        return

    keyboard = InlineKeyboardBuilder()
    for admin in admins:
        callback_data = generate_callback("delete_admin", admin["id"])
        keyboard.row(
            InlineKeyboardButton(
                text=f"❌ {admin['name'] or admin['id']}",
                callback_data=callback_data,
            )
        )

    await message.answer("Adminlar ro'yxati:", reply_markup=keyboard.as_markup())


from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


@dp.callback_query(F.data.startswith("delete_admin"))
async def delete_admin_callback(query: types.CallbackQuery):
    callback_data = query.data.split(":")
    action = callback_data[0]
    admin_id = int(callback_data[1])

    if int(admin_id) == 6807731973:
        await query.answer("Bu botning asosiy admini. Siz uni o'chira olmaysiz❗️")
    else:
        if action == "delete_admin":
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admins WHERE user_id = ?", (admin_id,))
            conn.commit()
            conn.close()
            await query.answer("Admin muvaffaqiyatli o'chirildi.")

            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM admins")
            remaining_admins = [row[0] for row in cursor.fetchall()]
            conn.close()
            keyboard_builder = InlineKeyboardBuilder()
            for admin in remaining_admins:
                keyboard_builder.button(
                    text=f"❌ Admin {admin}", callback_data=f"delete_admin:{admin}"
                )
            keyboard = keyboard_builder.as_markup()
            await query.message.edit_reply_markup(reply_markup=keyboard)
