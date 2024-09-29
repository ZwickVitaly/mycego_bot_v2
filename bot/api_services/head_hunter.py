from aiohttp import ClientSession


async def get_employer_active_vacancies_headhunter(employer_id: str):
    """
    Функция для аутентификации пользователя с помощью сайта
    """
    url = f"/api-auth/login/"
    async with ClientSession() as session:
        async with session.post(url=url) as response:
            if response.status == 200:
                user = await response.json()
                if user.get("status_work") is True:
                    return user
    return None