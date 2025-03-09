import tortoise

from src.db.models import Users, Subscribes
from src.worker.task import remove_subscription


async def get_user(user_id: int) -> Users:
    user =  await Users.get_or_create(id=user_id)
    return user[0]


async def subscrabe(user_id: int) -> None:
    user = await get_user(user_id)
    if user:
        user.is_subscribed = True
        await user.save()


async def unsubscrabe(user_id: int) -> None:
    user = await get_user(user_id)
    if user:
        user.is_subscribed = False
        await user.save()


async def add_crypto(user_id: int, crypto: str) -> None:
    user = await get_user(user_id)
    if user:
        try:
            await Subscribes.create(user=user, crypto=crypto)
            print(await user.subscribes.all().values_list())
        except tortoise.exceptions.IntegrityError:
            pass

async def stop_crypto(user_id: int, crypto: str) -> None:
    user = await get_user(user_id)
    if user:
        await Subscribes.filter(user=user, crypto=crypto).update(is_subscribed=False)
        await remove_subscription(crypto)

async def delete_crypto(user_id: int, crypto: str) -> None:
    user = await get_user(user_id)
    if user:
        await Subscribes.filter(user=user, crypto=crypto).delete()
        await remove_subscription(crypto)

async def get_user_subscribes(user_id: int) -> list:
    user = await get_user(user_id)
    if user:
        return await user.subscribes.all()
    return []

async def start_crypto(user_id: int, crypto: str) -> None:
    user = await get_user(user_id)
    if user:
        await Subscribes.filter(user=user, crypto=crypto).update(is_subscribed=True)
