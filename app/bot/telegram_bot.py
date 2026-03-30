import logging
from uuid import UUID
from html import escape

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.site_service import SiteService
from app.repositories.telegram_tokens import TelegramTokenRepository
from app.repositories.users import UsersRepository
from app.monitoring.status import SiteStatus

logger = logging.getLogger(__name__)

bot = None
dp = None

if settings.TELEGRAM_BOT_TOKEN:
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Мої сайти")],
            [KeyboardButton(text="ℹ️ Допомога"), KeyboardButton(text="🔌 Відключити")],
        ],
        resize_keyboard=True,
    )

def ascii_bar(percent: float, width: int = 10) -> str:
    percent = round(percent, 2)
    filled = int((percent / 100) * width)
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}] {percent:.2f}%"


async def safe_send(chat_id: int, text: str, reply_markup=None):
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    except TelegramForbiddenError:
        logger.warning(f"Bot blocked by user {chat_id}")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")

async def safe_edit(message: types.Message, text: str, keyboard=None):
    try:
        await message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        pass

async def safe_callback_answer(callback: CallbackQuery):
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    text = (
        "👋 <b>WebMonitor Bot</b>\n\n"
        "Я сповіщаю про зміну статусу ваших сайтів.\n\n"
        "Щоб підключити акаунт:\n"
        "<code>/connect CODE</code>"
    )
    await safe_send(message.chat.id, text, main_menu())


@dp.message(lambda m: m.text == "ℹ️ Допомога")
async def help_button(message: types.Message):
    text = (
        "📖 <b>Доступні дії:</b>\n\n"
        "📊 Мої сайти: переглянути список сайтів\n"
        "🔌 Відключити: відв’язати Telegram\n\n"
        "Або використовуйте для підключення:\n"
        "<code>/connect CODE</code>"
    )
    await safe_send(message.chat.id, text)


@dp.message(Command("connect"))
async def cmd_connect(message: types.Message):
    args = message.text.split()

    if len(args) != 2:
        await safe_send(message.chat.id, "⚠️ Використання: /connect CODE")
        return

    token = args[1]

    try:
        async with AsyncSessionLocal() as session:
            token_repo = TelegramTokenRepository(session)
            users_repo = UsersRepository(session)

            link = await token_repo.get_by_token(token)
            if not link:
                await safe_send(message.chat.id, "❌ Код недійсний або прострочений.")
                return

            user = await users_repo.get_by_id(link.user_id)
            if not user:
                await safe_send(message.chat.id, "❌ Користувача не знайдено.")
                return

            if user.telegram_chat_id:
                await safe_send(message.chat.id, "ℹ️ Telegram вже підключений.")
                return

            user.telegram_chat_id = message.chat.id
            await token_repo.delete(token)
            await session.commit()

        await safe_send(message.chat.id, "✅ Telegram успішно підключено.", main_menu())

    except Exception:
        logger.exception("Connect handler failed")
        await safe_send(message.chat.id, "⚠️ Помилка сервера.")

@dp.message(lambda m: m.text == "📊 Мої сайти")
async def list_sites(message: types.Message):
    try:
        async with AsyncSessionLocal() as session:
            service = SiteService(session=session)

            user, sites = await service.get_sites_for_telegram(
                telegram_chat_id=message.chat.id
            )

            if not user:
                await safe_send(message.chat.id, "⚠️ Спочатку підключіть акаунт через /connect")
                return

            if not sites:
                await safe_send(message.chat.id, "ℹ️ У вас немає активних сайтів.")
                return

            buttons = [
                [InlineKeyboardButton(text=escape(site.name), callback_data=f"site:{site.id}")]
                for site in sites
            ]

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await safe_send(
                message.chat.id,
                "📊 <b>Ваші сайти:</b>\nОберіть сайт:",
                keyboard,
            )

    except Exception:
        logger.exception("List sites failed")
        await safe_send(message.chat.id, "⚠️ Помилка сервера.")

@dp.callback_query(lambda c: c.data.startswith("site:"))
async def site_details(callback: CallbackQuery):
    if not callback.message:
        return

    try:
        site_id = UUID(callback.data.split(":")[1])

        async with AsyncSessionLocal() as session:
            service = SiteService(session=session)

            site, data = await service.get_site_details_for_telegram(
                telegram_chat_id=callback.message.chat.id,
                site_id=site_id,
            )

            if not site:
                await safe_callback_answer(callback)
                return

            uptime_24 = data["uptime_24"]
            uptime_7d = data["uptime_7d"]
            uptime_30d = data["uptime_30d"]
            last_checks = data["last_checks"]

            # Last check
            if last_checks:
                last = last_checks[0]
                last_time = last.checked_at.strftime("%d.%m %H:%M")
                status_name = last.status.name
                last_line = (
                    f"🕒 <b>Остання перевірка:</b>\n"
                    f"{last_time} | {status_name} | {last.response_time_ms or '-'} ms\n\n"
                )
            else:
                last_line = "🕒 <b>Остання перевірка:</b>\nНемає даних\n\n"

            history_lines = []
            for row in last_checks:
                emoji = "🟢" if row.status == SiteStatus.UP else "🔴"
                time_str = row.checked_at.strftime("%H:%M:%S")
                history_lines.append(
                    f"{emoji} {time_str} | {row.response_time_ms or '-'} ms"
                )

            history_text = "\n".join(history_lines) if history_lines else "Немає даних"

            if site.last_status == SiteStatus.UP:
                emoji = "🟢"
                status = "Працює"
            elif site.last_status == SiteStatus.DOWN:
                emoji = "🔴"
                status = "Недоступний"
            else:
                emoji = "⚪"
                status = "Невідомо"

            text = (
                f"{emoji} <b>{escape(site.name)}</b>\n\n"
                f"<b>URL:</b> {escape(site.url)}\n"
                f"<b>Статус:</b> {status}\n"
                f"<b>Інтервал:</b> {site.check_interval} сек\n\n"
                f"{last_line}"
                f"📈 <b>Uptime:</b>\n"
                f"24г  <code>{ascii_bar(uptime_24)}</code>\n"
                f"7д   <code>{ascii_bar(uptime_7d)}</code>\n"
                f"30д  <code>{ascii_bar(uptime_30d)}</code>\n\n"
                f"📉 <b>Останні 5 перевірок:</b>\n"
                f"{history_text}"
            )

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Оновити", callback_data=f"site:{site.id}")],
                    [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_sites")],
                ]
            )

            await safe_edit(callback.message, text, keyboard)
            await safe_callback_answer(callback)

    except Exception:
        logger.exception("Site details failed")
        await safe_callback_answer(callback)

@dp.message(lambda m: m.text == "🔌 Відключити")
async def disconnect(message: types.Message):
    try:
        async with AsyncSessionLocal() as session:
            users_repo = UsersRepository(session)

            user = await users_repo.get_by_telegram_chat_id(message.chat.id)
            if not user:
                await safe_send(message.chat.id, "ℹ️ Telegram не підключений.")
                return

            user.telegram_chat_id = None
            await session.commit()

        await safe_send(message.chat.id, "🔌 Telegram відключено.", main_menu())

    except Exception:
        logger.exception("Disconnect failed")
        await safe_send(message.chat.id, "⚠️ Помилка сервера.")

@dp.callback_query(lambda c: c.data == "back_to_sites")
async def back_to_sites(callback: CallbackQuery):
    if not callback.message:
        return

    try:
        async with AsyncSessionLocal() as session:
            service = SiteService(session=session)

            user, sites = await service.get_sites_for_telegram(
                telegram_chat_id=callback.message.chat.id
            )

            if not user:
                await safe_callback_answer(callback)
                return

            buttons = [
                [InlineKeyboardButton(text=escape(site.name), callback_data=f"site:{site.id}")]
                for site in sites
            ]

            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            await safe_edit(
                callback.message,
                "📊 <b>Ваші сайти:</b>\nОберіть сайт:",
                keyboard,
            )

            await safe_callback_answer(callback)

    except Exception:
        logger.exception("Back failed")
        await safe_callback_answer(callback)
