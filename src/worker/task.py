import json
import asyncio
from collections import defaultdict
from decimal import Decimal
import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from loguru import logger
import backoff
from src.app import bot
from src.db.models import Subscribes


BYBIT_WS_URL = "wss://stream.bybit.com/v5/public/linear"
RECONNECT_DELAY = 5  # seconds
MAX_RETRIES = 100  # максимальное количество попыток переподключения

class LimitedDefaultDict(defaultdict):
    def __init__(self, max_len=4):
        super().__init__(dict)
        self.max_len = max_len

    def append(self, key, value):
        self[key].append(value)
        if len(self[key]) > self.max_len:
            self[key].pop(0)

kline_data = LimitedDefaultDict()
subscribe_queue = asyncio.Queue()
unsubscribe_queue = asyncio.Queue()


async def get_all_subscribes() -> list:
    # Get all subscribes that are active
    subscribes = await Subscribes.filter(is_subscribed=True).all().values_list("crypto", flat=True)
    return subscribes

async def send_notification(crypto: str, direction: str, count=2) -> None:
    subscribes = await Subscribes.filter(crypto=crypto, is_subscribed=True).prefetch_related("user")
    for subscribe in subscribes:
        user = await subscribe.user
        if not user.is_subscribed:
            continue

        if direction == "double":
            text = (
                f"🔔 Обоюдный сигнал для <b>{crypto}</b>\n"
                "<b>High/Low:</b> Double\n"
                f"<b>Свеча:</b> {count}"
            )
            await bot.send_message(chat_id=user.id, text=text)
        elif direction == "up":
            text = (
                f"🔔 Второй сигнал для <b>{crypto}</b>\n"
                "<b>High/Low:</b> High\n"
                f"<b>Свеча:</b> {count}"
            )
            await bot.send_message(chat_id=user.id, text=text)

        else:
            text = (
                f"🔔 Второй сигнал для <b>{crypto}</b>\n"
                "<b>High/Low:</b> Low\n"
                f"<b>Свеча:</b> {count}"
            )
            await bot.send_message(chat_id=user.id, text=text)

async def handle_subscriptions(ws):
    while True:
        try:
            if not subscribe_queue.empty():
                new_args = await subscribe_queue.get()
                await ws.send(json.dumps({"op": "subscribe", "args": new_args}))
                logger.info(f"Added subscription: {new_args}")

            if not unsubscribe_queue.empty():
                remove_args = await unsubscribe_queue.get()
                await ws.send(json.dumps({"op": "unsubscribe", "args": remove_args}))
                logger.info(f"Removed subscription: {remove_args}")

            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in subscription handler: {e}")
            await asyncio.sleep(1)

async def count_pips(data):
    decimals = []
    for field in ['high', 'low', 'open', 'close']:
        value = data["data"][0][field]
        if '.' in value:
            decimals.append(len(value.split('.')[1]))
    return 1 / (10 ** max(decimals)) if decimals else 1

async def count_data(start, topic, data):
    try:
        pips = await count_pips(data)
        if len(kline_data[topic]) == 2:
            idx = list(kline_data[topic].keys())
            old_data = kline_data[topic][idx[0]]
            last_data = kline_data[topic][idx[1]]
            if abs(Decimal(old_data["low"]) - Decimal(last_data["low"])) in [0, pips] and abs(Decimal(old_data["high"]) - Decimal(last_data["high"])) in [0, pips]:
                logger.info(f"{topic}: Double is the same")
                await send_notification(topic, "double")
                kline_data[topic].clear()
            elif abs(Decimal(old_data["low"]) - Decimal(last_data["low"])) in [0, pips]:
                logger.info(f"{topic}: Low is the same")
                await send_notification(topic, "down")
                kline_data[topic].clear()
            elif abs(Decimal(old_data["high"]) - Decimal(last_data["high"])) in [0, pips]:
                logger.info(f"{topic}: High is the same")
                await send_notification(topic, "up")
                kline_data[topic].clear()

        elif len(kline_data[topic]) >= 3:
            idx = list(kline_data[topic].keys())
            old_data = kline_data[topic][idx[-3]]
            last_data = kline_data[topic][idx[-1]]
            if abs(Decimal(old_data["low"]) - Decimal(last_data["low"])) in [0, pips] and abs(Decimal(old_data["high"]) - Decimal(last_data["high"])) in [0, pips]:
                logger.info(f"{topic}: Double is the same")
                await send_notification(topic, "double", 3)
                kline_data[topic].clear()
            elif abs(Decimal(old_data["low"]) - Decimal(last_data["low"])) in [0, pips]:
                logger.info(f"{topic}: Low is the same")
                await send_notification(topic, "down", 3)
                kline_data[topic].clear()
            elif abs(Decimal(old_data["high"]) - Decimal(last_data["high"])) in [0, pips]:
                logger.info(f"{topic}: High is the same")
                await send_notification(topic, "up", 3)
                kline_data[topic].clear()

        current_data = data["data"][0]
        kline_data[topic][start] = current_data
        logger.info(f"New snapshot for {topic}")
    except Exception as e:
        logger.error(f"Error processing data for {topic}: {e}")

@backoff.on_exception(backoff.expo,
                     (ConnectionClosedError, ConnectionClosedOK, websockets.exceptions.WebSocketException),
                     max_tries=MAX_RETRIES)
async def websocket_connect():
    return await websockets.connect(BYBIT_WS_URL)


async def listen_klines():
    while True:
        try:
            ws = await websocket_connect()
            logger.info("WebSocket connected successfully")
            subscription_handler = asyncio.create_task(handle_subscriptions(ws))
            all_subscribes = await get_all_subscribes()
            for crypto in all_subscribes:
                await add_new_subscription(crypto)

            try:
                while True:
                    response = await ws.recv()
                    data = json.loads(response)
                    if data.get("type") == "snapshot":
                        topic = data["topic"]
                        start = data["data"][0]["start"]
                        if start not in kline_data[topic]:
                            logger.info(f"{data=}")
                            await count_data(start, topic, data)
                        else:
                            current_data = data["data"][0]
                            kline_data[topic][start] = current_data
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                subscription_handler.cancel()
                await ws.close()
                continue

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            await asyncio.sleep(RECONNECT_DELAY)

async def add_new_subscription(symbol: str = "kline.1.ONEUSDT"):
    await subscribe_queue.put([symbol])

async def remove_subscription(symbol: str = "kline.1.ONEUSDT"):
    await unsubscribe_queue.put([symbol])
