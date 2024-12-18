from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import CallbackQuery
from functions import *
from config import *
from keyboards.keyboard import back_button, courses_button, back_button
from states.state import forpoint


async def generate_courses_keyboard():
    courses = await get_all_courses()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for curs in courses:
        curs = list(curs)
        course_id, course_name, points = curs[1], curs[0], curs[2]
        row = [
            InlineKeyboardButton(
                text=f"{course_name}", callback_data=f"view_course:{course_id}"
            ),
            InlineKeyboardButton(text="🚫", callback_data=f"delete_course:{course_id}"),
            InlineKeyboardButton(text="✏️", callback_data=f"change_points:{course_id}"),
        ]
        keyboard.inline_keyboard.append(row)
    return keyboard


@dp.callback_query(F.data.startswith("delete_course:"))
async def delete_course_callback(call: types.CallbackQuery):
    channel_identifier = (call.data.split(":")[1])
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM courses WHERE channel_identifier = ?", (channel_identifier,)
    )
    connection.commit()
    connection.close()
    await call.answer("Kurs o'chirildi ✅", show_alert=True)

    keyboard = await generate_courses_keyboard()
    await call.message.edit_reply_markup(reply_markup=keyboard)


@dp.callback_query(F.data.startswith("view_course:"))
async def view_course_callback(call: types.CallbackQuery):
    channel_identifier = int(call.data.split(":")[1])
    course_id = (
        channel_identifier
        if not "-100" in str(channel_identifier)
        else channel_identifier
    )
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()
    cursor.execute(
        "SELECT channel_name, channel_identifier,  points_required FROM courses WHERE channel_identifier = ?",
        (course_id,),
    )
    course = cursor.fetchone()
    connection.close()

    if course:
        channel_name, channel_identifier, points_required = course
        if str(channel_identifier)[0] != "@":
            channel_identifier = str(channel_identifier)[4:]
        await call.answer()
        await call.message.answer(
            f"📚 *Kurs Ma'lumotlari:*\n"
            f"🏷 *Nomi:* {channel_name}\n"
            f"🔗 *Username/ID:* {channel_identifier}\n"
            f"🎯 *Ballar:* {points_required}",
            parse_mode="Markdown",
        )
    else:
        await call.answer("Xatolik: Kurs topilmadi.", show_alert=True)


@dp.callback_query(F.data.startswith("change_points:"))
async def change_points_callback(call: types.CallbackQuery, state: FSMContext):
    course_id = int(call.data.split(":")[1])

    await state.update_data(course_id=course_id)
    await call.message.answer(
        "📝 Iltimos, yangi ballar sonini kiriting:", reply_markup=back_button
    )
    await state.set_state(forpoint.waiting_for_new_points)


@dp.message(forpoint.waiting_for_new_points)
async def process_new_points(message: types.Message, state: FSMContext):
    new_points = message.text.strip()

    if not new_points.isdigit():
        await message.answer(
            "❌ Iltimos, faqat raqam kiriting.", reply_markup=back_button
        )
        return

    data = await state.get_data()
    course_id = data.get("course_id")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE courses SET points_required = ? WHERE channel_identifier = ?",
        (new_points, course_id),
    )
    conn.commit()
    conn.close()

    await message.answer(
        f"✅ Ballar soni muvaffaqiyatli yangilandi: {new_points}",
        reply_markup=courses_button,
    )
    await state.clear()


@dp.callback_query(lambda callback: callback.data.startswith("course:"))
async def process_course_selection(callback_query: CallbackQuery):
    _, channel_id, points_required = callback_query.data.split(":")
    points_required = int(points_required)
    user_id = callback_query.from_user.id
    response = await give_channel_access(user_id=user_id, channel_id=channel_id, points_required=points_required)

    await callback_query.message.answer(response)
    await callback_query.answer()
