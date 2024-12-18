from aiogram.types import ChatInviteLink
from aiogram.exceptions import TelegramBadRequest
from config import *
import sqlite3


def add_admin(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def remove_admin(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def is_user_admin(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_admins2():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins")
    admins = [{"id": row[0], "name": f"Admin {row[0]}"} for row in cursor.fetchall()]
    conn.close()
    return admins
def get_admins():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins")
    admins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return admins


def get_channels():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id, channel_name, channel_username FROM channels")
    channels = cursor.fetchall()
    conn.close()
    return channels

async def give_channel_access(user_id: int, channel_id: str, points_required: int):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if not result or result[0] < points_required:
        conn.close()
        return f"❌ Sizda yetarli ball mavjud emas. Kursni olish uchun yana {points_required - result[0]} ball kerak."

    try:
        invite_link: ChatInviteLink = await bot.create_chat_invite_link(
            chat_id=channel_id,
            member_limit=1, 
            expire_date=None 
        )
    except TelegramBadRequest as e:
        print(f"Error creating invite link: {e}")
        conn.close()
        return "❌ Kanalga taklif havolasini yaratishda xatolik yuz berdi."

    # Deduct points from the user
    cursor.execute(
        "UPDATE users SET points = points - ? WHERE user_id = ?",
        (points_required, user_id),
    )
    conn.commit()
    conn.close()

    return (
        f"✅ Sizning kanalga taklif havolangiz:\n{invite_link.invite_link}\n\n"
        "⚠️ Unutmang ushbu havola faqat 1 marta foydalanish uchun amal qiladi."
    )



async def add_course(channel_name: str, channel_username: str, points_required: int):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    points_required = int(points_required)
    try:
        cursor.execute(
            """
            INSERT INTO courses (channel_name, channel_identifier, points_required)
            VALUES (?, ?, ?)
        """,
            (channel_name, channel_username, points_required),
        )
        conn.commit()
        print("✅ Course added successfully!")
    except sqlite3.IntegrityError:
        print("❌ Course with this username already exists!")
    finally:
        conn.close()


async def get_all_courses():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT channel_name, channel_identifier, points_required FROM courses"
    )
    courses = cursor.fetchall()
    conn.close()
    return courses



def course_exists(channel_identifier: str) -> bool:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM courses WHERE channel_identifier = ?", (channel_identifier,)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None



def get_bot_statistics():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM courses")
    total_courses = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM admins")
    total_admins = cursor.fetchone()[0]
    conn.close()
    statistics = {
        "total_users": total_users,
        "total_courses": total_courses,
        "total_admins": total_admins,
    }
    return statistics


async def send_message_to_all_users(message_text: str, userid):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    for user in users:
        print(user)
        user_id = user[0]
        if user_id != userid:
            try:
                await bot.send_message(user_id, message_text, parse_mode="Markdown")
            except Exception as e:
                print(f"Failed to send message to user {user_id}: {e}")


async def send_message_to_user(user_id: int, message_text: str):
    try:
        await bot.send_message(user_id, message_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Failed to send message to user {user_id}: {e}")


def check_user_exists(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    return result[0] > 0


async def save_referral(invitee_id: int, referrer_id: int):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO referrals (invitee_id, referrer_id)
            VALUES (?, ?)
        """, (invitee_id, referrer_id))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Invitee ID {invitee_id} already exists in referrals.")
    finally:
        conn.close()
        
async def get_referrer(invitee_id: int):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT referrer_id FROM referrals WHERE invitee_id = ?
    """, (invitee_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_user_info(user_id: int) -> dict:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT user_id, phone, referrals, points FROM users WHERE user_id = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        return {
            "user_id": user[0],
            "phone": user[1],
            "referrals": user[2],
            "points": user[3],
        }
    return None


def get_courses():

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT channel_name, channel_identifier, points_required FROM courses")
    courses = cursor.fetchall()
    conn.close()

    return [
        {
            "channel_name": course[0],
            "channel_identifier": course[1],
            "points_required": course[2],
        }
        for course in courses
    ]
