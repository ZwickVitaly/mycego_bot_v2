from constructors import bot


async def test_send_message(user_id):
    await bot.send_message(user_id, "ШАЛОМ ЁПТА")
