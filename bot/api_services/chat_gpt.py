import asyncio
import json
from copy import deepcopy

from aiohttp import ClientSession
from settings import JSON_HEADERS, PROXY_API_GPT_URL, PROXY_API_KEY, logger


async def get_happy_birthday_message(names: list[str]):
    headers = deepcopy(JSON_HEADERS)
    headers["Authorization"] = f"Bearer {PROXY_API_KEY}"
    happy_birthday_request = {
        "model": "gpt-3.5-turbo-1106",
        "messages": [
            {
                "role": "system",
                "content": "Напиши поздравление с днём рождения "
                "для сотрудников, имя и фамилию которых предоставит пользователь. "
                "Поздравление должно быть от лица компании Mycego, "
                "должно выглядеть как объявление в общем чате "
                "и должно быть сердечным и уважительным.'",
            },
            {"role": "user", "content": ", ".join(names)},
        ],
    }
    try:
        async with ClientSession(headers=headers) as session:
            async with session.post(
                url=PROXY_API_GPT_URL, data=json.dumps(happy_birthday_request)
            ) as response:
                data = await response.json()
                message = data.get("choices")[0].get("message").get("content")
                return message
    except Exception as e:
        logger.error(f"Не получилось получить ответ от chatgpt: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(get_happy_birthday_message(["Лена Каменева", "Иван Охлобыстин"]))
