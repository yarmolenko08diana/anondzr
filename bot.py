import asyncio
import json
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties

import os

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
REPLY_MAP_FILE = os.getenv("REPLY_MAP_FILE")

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

intro_text = (
    "🚀 Здесь можно отправить анонимное сообщение d1zyru.\n\n"
    "✍️ Напишите сюда всё, что хотите ему передать, и через несколько секунд он получит ваше сообщение, но не будет знать от кого.\n\n"
    "Отправить можно фото, видео, 💬 текст, 🔊 голосовые, 📷 видеосообщения (кружки), а также ✨ стикеры"
)

sent_text = "💬 Сообщение отправлено, ожидайте ответ!"


def load_reply_map():
    if not os.path.exists(REPLY_MAP_FILE):
        return {}

    try:
        with open(REPLY_MAP_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

            # на всякий случай приводим ключи и значения к int
            cleaned_data = {}
            for key, value in data.items():
                cleaned_data[int(key)] = int(value)

            return cleaned_data
    except (json.JSONDecodeError, ValueError, OSError):
        return {}


def save_reply_map(reply_map):
    try:
        with open(REPLY_MAP_FILE, "w", encoding="utf-8") as file:
            json.dump(reply_map, file, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"Ошибка сохранения reply_map: {e}")


reply_map = load_reply_map()


def build_header(message: Message) -> str:
    user = message.from_user
    full_name = user.full_name if user else "Без имени"
    username = f"@{user.username}" if user and user.username else "без username"
    user_id = user.id if user else 0

    return (
        f"📩 <b>Новое сообщение в боте</b>\n\n"
        f"<b>Имя:</b> {full_name}\n"
        f"<b>Username:</b> {username}\n"
        f"<b>ID:</b> {user_id}\n\n"
    )


def remember_message(owner_message_id: int, user_id: int):
    reply_map[owner_message_id] = user_id
    save_reply_map(reply_map)


@dp.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer(intro_text)


@dp.message(F.from_user.id == OWNER_ID)
async def owner_reply_handler(message: Message):
    if not message.reply_to_message:
        return

    target_user_id = reply_map.get(message.reply_to_message.message_id)

    if not target_user_id:
        await message.answer("Не удалось понять, кому отправлять ответ.")
        return

    try:
        if message.text:
            await bot.send_message(
                target_user_id,
                f"💌 Вам пришел ответ:\n\n{message.text}"
            )

        elif message.photo:
            largest_photo = message.photo[-1].file_id
            caption_text = "💌 Вам пришел ответ с фото"
            if message.caption:
                caption_text += f":\n\n{message.caption}"

            await bot.send_photo(
                target_user_id,
                photo=largest_photo,
                caption=caption_text
            )

        elif message.video:
            caption_text = "💌 Вам пришел ответ с видео"
            if message.caption:
                caption_text += f":\n\n{message.caption}"

            await bot.send_video(
                target_user_id,
                video=message.video.file_id,
                caption=caption_text
            )

        elif message.animation:
            caption_text = "💌 Вам пришел ответ"
            if message.caption:
                caption_text += f":\n\n{message.caption}"

            await bot.send_animation(
                target_user_id,
                animation=message.animation.file_id,
                caption=caption_text
            )

        elif message.document:
            caption_text = "💌 Вам пришел ответ с файлом"
            if message.caption:
                caption_text += f":\n\n{message.caption}"

            await bot.send_document(
                target_user_id,
                document=message.document.file_id,
                caption=caption_text
            )

        elif message.voice:
            await bot.send_voice(
                target_user_id,
                voice=message.voice.file_id,
                caption="💌 Вам пришел голосовой ответ"
            )

        elif message.audio:
            caption_text = "💌 Вам пришел аудио-ответ"
            if message.caption:
                caption_text += f":\n\n{message.caption}"

            await bot.send_audio(
                target_user_id,
                audio=message.audio.file_id,
                caption=caption_text
            )

        elif message.sticker:
            await bot.send_sticker(
                target_user_id,
                sticker=message.sticker.file_id
            )

        elif message.video_note:
            await bot.send_video_note(
                target_user_id,
                video_note=message.video_note.file_id
            )

        else:
            await bot.copy_message(
                chat_id=target_user_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )

        await message.answer("✅ Ответ отправлен пользователю.")

    except Exception as e:
        await message.answer(f"Ошибка при отправке ответа: {e}")


@dp.message()
async def handle_user_message(message: Message):
    if message.from_user and message.from_user.id == OWNER_ID:
        return

    header = build_header(message)
    sent_to_owner = None

    try:
        if message.text:
            sent_to_owner = await bot.send_message(
                OWNER_ID,
                header + f"<b>Текст сообщения:</b>\n{message.text}"
            )

        elif message.photo:
            largest_photo = message.photo[-1].file_id
            caption_text = header + "<b>Фото</b>"
            if message.caption:
                caption_text += f"\n\n{message.caption}"

            sent_to_owner = await bot.send_photo(
                OWNER_ID,
                photo=largest_photo,
                caption=caption_text
            )

        elif message.video:
            caption_text = header + "<b>Видео</b>"
            if message.caption:
                caption_text += f"\n\n{message.caption}"

            sent_to_owner = await bot.send_video(
                OWNER_ID,
                video=message.video.file_id,
                caption=caption_text
            )

        elif message.animation:
            caption_text = header + "<b>GIF / анимация</b>"
            if message.caption:
                caption_text += f"\n\n{message.caption}"

            sent_to_owner = await bot.send_animation(
                OWNER_ID,
                animation=message.animation.file_id,
                caption=caption_text
            )

        elif message.document:
            caption_text = header + "<b>Документ</b>"
            if message.caption:
                caption_text += f"\n\n{message.caption}"

            sent_to_owner = await bot.send_document(
                OWNER_ID,
                document=message.document.file_id,
                caption=caption_text
            )

        elif message.voice:
            sent_to_owner = await bot.send_voice(
                OWNER_ID,
                voice=message.voice.file_id,
                caption=header + "<b>Голосовое сообщение</b>"
            )

        elif message.audio:
            caption_text = header + "<b>Аудио</b>"
            if message.caption:
                caption_text += f"\n\n{message.caption}"

            sent_to_owner = await bot.send_audio(
                OWNER_ID,
                audio=message.audio.file_id,
                caption=caption_text
            )

        elif message.sticker:
            sent_to_owner = await bot.send_sticker(
                OWNER_ID,
                sticker=message.sticker.file_id
            )

        elif message.video_note:
            sent_to_owner = await bot.send_video_note(
                OWNER_ID,
                video_note=message.video_note.file_id
            )

        else:
            sent_to_owner = await bot.copy_message(
                chat_id=OWNER_ID,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )

        if sent_to_owner and message.from_user:
            remember_message(sent_to_owner.message_id, message.from_user.id)

            await message.answer(sent_text)

    except Exception as e:
        await message.answer("Произошла ошибка при отправке сообщения.")
        print(f"Ошибка: {e}")


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())