from aiogram import BaseMiddleware
from aiogram.types import Message, ChatMember
from aiogram.exceptions import TelegramBadRequest
from typing import Callable, Dict, Any
from functools import wraps
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from functions import *
from aiogram.types import CallbackQuery
from config import *
from keyboards.keyboard import get_main_menu, phone_number
from states.state import UserStates

class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def __call__(
        self, handler: Callable, event: Message, data: Dict[str, Any]
    ) -> Any:
        channels = list(get_channels())
        required_channels = []
        for i in range(len(channels)):
            channels[i] = list(channels[i])
            required_channels.append(channels[i][2])
        if not isinstance(event, Message):
            return await handler(event, data)
        user_id = event.from_user.id
        referrerid = None
        if event.text and event.text.startswith("/start"):
            referrer_text = event.text.split("start=")[0].split()[-1]
            if referrer_text.strip().isdigit():
                referrerid = int(referrer_text)
                print("Middleware referral handling works")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            await save_referral(user_id, referrerid)

        bot = data["bot"]
        channels = list(get_channels())
        ad = [channel[2] for channel in channels]
        
        if not ad:
            return await handler(event, data)

        not_subscribed = []
        for channel in ad:
            try:
                member: ChatMember = await bot.get_chat_member(
                    chat_id=channel, user_id=user_id
                )
                if member.status in ("left", "kicked"):
                    not_subscribed.append(channel)
            except TelegramBadRequest:
                print(f"Error checking subscription for {channel}")

        if not not_subscribed:
            return await handler(event, data)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"{(await bot.get_chat(ch)).title}",
                        url=f"https://t.me/{ch[1:]}",
                    )
                ]
                for ch in not_subscribed
            ]
            + [
                [
                    InlineKeyboardButton(
                        text="✅ Tasdiqlash", callback_data="confirm_subscriptions"
                    )
                ]
            ]
        )

        await bot.send_message(
            chat_id=user_id,
            text=(
                "⛔️ Botdan foydalanish uchun avval siz quidagi kanallarga obuna bo'lishingiz shart:\n"
                + "\Obuna bo'lgandan so'ng '✅ Tasdiqlash' tugmasini bosing"
            ),
            reply_markup=keyboard,
        )

        return


def admin_required():
    def decorator(handler):
        @wraps(handler)
        async def wrapper(message: types.Message, *args, **kwargs):
            admin_list = list(get_admins())
            user_id = message.from_user.id
            if not user_id in admin_list:
                await message.answer("Siz noto'g'ri buyruq yubordingiz!")
                return
            return await handler(message, *args, **kwargs)

        return wrapper

    return decorator


@dp.callback_query(lambda c: c.data == "confirm_subscriptions")
async def confirm_subscription(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    bot = callback_query.bot
    not_subscribed = []
    for channel in list(get_channels()):
        try:
            member: ChatMember = await bot.get_chat_member(
                chat_id=channel[2], user_id=user_id
            )
            if member.status in ("left", "kicked"):
                not_subscribed.append(channel[2])
        except TelegramBadRequest:
            print(f"Error checking subscription for {channel[2]}")

    if not not_subscribed:
        await bot.delete_message(
            callback_query.from_user.id, callback_query.message.message_id
        )
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            await state.set_state(UserStates.waiting_for_phone)
            ref_id = await get_referrer(callback_query.from_user.id)
            await state.update_data(referrer_id = ref_id)
            await callback_query.message.answer(
            "Botdan foydalanish uchun quidagi tugmani bosing 👇",
            reply_markup=phone_number,
        )
        else:
            await bot.send_message(
                chat_id=callback_query.from_user.id,
                text="✅ Endi esa botdan to'liq foydalanishingiz mumkin.",
                reply_markup=await get_main_menu(callback_query.from_user.id),
            )
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"{(await bot.get_chat(cha)).title}",
                        url=f"https://t.me/{cha[1:]}",
                    )
                ]
                for cha in not_subscribed
            ]
            + [
                [
                    InlineKeyboardButton(
                        text="✅ Tasdiqlash", callback_data="confirm_subscriptions"
                    )
                ]
            ]
        )
        await callback_query.message.edit_text(
            text=(
                "⚠️Siz quidagi kanallarga obuna bo'lmadingiz❗️\nBotdan to'liq foydalanish uchun avval barcha kanallarga obuna bo'lish shart:\n"
                + "\nObuna bo'lgandan so'ng '✅ Tasdiqlash' tugmasini bosing."
            ),
            reply_markup=keyboard,
        )
