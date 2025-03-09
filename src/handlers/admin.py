from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.filters.admin_filter import AdminFilter
from src.utils import subscrabe, unsubscrabe, add_crypto, stop_crypto, delete_crypto, get_user_subscribes, start_crypto
from src.worker.task import add_new_subscription

router = Router()
router.message.filter(AdminFilter())




@router.message(Command("add_crypto"))
async def subscribe_handler(message: Message) -> None:
    try:
        crypto = message.text.split(" ")[1]
        await add_crypto(message.from_user.id, "kline." + crypto.upper())
        await add_new_subscription("kline." + crypto.upper())
        await message.answer("Успешно добавлено")
    except IndexError:
        await message.answer("Введите название криптовалюты (/add_crypto 1.BTCUSDT)")

@router.message(Command("stop_crypto"))
async def subscribe_handler(message: Message) -> None:
    try:
        crypto = message.text.split(" ")[1]
        await stop_crypto(message.from_user.id, "kline." + crypto.upper())
        await message.answer("Успешно остановлено")
    except IndexError:
        await message.answer("Введите название криптовалюты (/stop_crypto 1.BTCUSDT)")

@router.message(Command("start_crypto"))
async def subscribe_handler(message: Message) -> None:
    try:
        crypto = message.text.split(" ")[1]
        await start_crypto(message.from_user.id, "kline." + crypto.upper())
        await add_new_subscription("kline." + crypto.upper())
        await message.answer("Успешно стартовано")
    except IndexError:
        await message.answer("Введите название криптовалюты (/start_crypto 1.BTCUSDT)")


@router.message(Command("delete_crypto"))
async def subscribe_handler(message: Message) -> None:
    try:
        crypto = message.text.split(" ")[1]
        await delete_crypto(message.from_user.id, "kline." + crypto.upper())
        await message.answer("Успешно удалено")
    except IndexError:
        await message.answer("Введите название криптовалюты (/delete_crypto 1.BTCUSDT)")


@router.message(Command("state"))
async def state_handler(message: Message) -> None:
    subscribes = await get_user_subscribes(message.from_user.id)
    text = "Ваши криптовалюты:\n"
    for subscribe in subscribes:
        text += f"{subscribe.crypto}: {'+' if subscribe.is_subscribed else '-'}\n"
    await message.answer(text)


@router.message(Command("subscribe"))
async def subscribe_handler(message: Message) -> None:
    await subscrabe(message.from_user.id)
    await message.answer("Вы успешно подписались")


@router.message(Command("unsubscribe"))
async def unsubscribe_handler(message: Message) -> None:
    await unsubscrabe(message.from_user.id)
    await message.answer("Вы успешно отписались")


@router.message(Command("start"))
async def activate_handler(message: Message) -> None:
    text =  "/subscribe - подписаться на канал\n" \
            "/unsubscribe - отписаться от канала\n" \
            "/state - проверить статус подписки\n" \
            "/add_crypto - добавить криптовалюту\n" \
            "/stop_crypto - остановить криптовалюту\n" \
            "/start_crypto - Стартовать криптовалюту\n" \
            "/delete_crypto - удалить криптовалюту\n"

    await message.answer(text)