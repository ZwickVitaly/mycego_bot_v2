import asyncio
import json
from copy import deepcopy

from aiohttp import ClientSession
from db import Works, async_session
from settings import COMMENTED_WORKS, JSON_HEADERS, SITE_DOMAIN, logger
from sqlalchemy import delete


async def check_user_api(username, password, user_id):
    """
    Функция для аутентификации пользователя с помощью сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/login/"
    data = {"username": username, "password": password, "telegram_id": str(user_id)}
    async with ClientSession() as session:
        async with session.post(url=url, data=data) as response:
            if response.status == 200:
                user = await response.json()
                if user.get("status_work") is True:
                    return user
    return None


async def create_or_get_apport(date, start_time, end_time, user_id_site):
    """
    Функция для создания заявки в график
    """
    url = f"{SITE_DOMAIN}/api-auth/appointment/"
    data = {
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "user": user_id_site,
    }
    async with ClientSession() as session:
        async with session.post(url=url, data=data) as response:
            return response.status


async def get_users_statuses():
    """
    Функция для получения статусов пользователей с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/users-status/"
    headers = deepcopy(JSON_HEADERS)
    async with ClientSession(headers=headers) as session:
        async with session.get(url=url) as response:
            if response.status == 200:
                return await response.json()


async def get_appointments(user_id_site):
    """
    Функция для получения заявок в график
    """
    url = f"{SITE_DOMAIN}/api-auth/appointment/"
    data = {"user": user_id_site}
    async with ClientSession() as session:
        async with session.get(url=url, data=data) as response:
            if response.status == 200:
                return await response.json()
    return None


async def delete_appointments(user_id_site, id_row):
    """
    Функция для удаления заявки в график
    """
    url = f"{SITE_DOMAIN}/api-auth/appointment_delete/"
    data = {"user": user_id_site, "id": id_row}
    async with ClientSession() as session:
        async with session.post(url=url, data=data) as response:
            return response.status


async def get_works():
    """
    Функция для получения списка работ с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/works_departments/"
    async with ClientSession() as session:
        async with session.get(url=url) as response:
            return await response.json()


async def get_departments():
    """
    Функция для получения списка департаментов и работ с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/works_departments/"
    async with ClientSession() as session:
        async with session.get(url=url) as response:
            return await response.json()


async def post_works(date, user_id_site, works, delivery=None, comment=None):
    """
    Функция для создания листа работ на сайте
    """
    url = f"{SITE_DOMAIN}/api-auth/add_works/"
    data = {
        "date": date,
        "user": user_id_site,
        "works": works,
        "delivery": delivery,
        "comment": comment,
    }
    json_data = json.dumps(data)
    headers = deepcopy(JSON_HEADERS)
    async with ClientSession(headers=headers) as session:
        async with session.post(url=url, data=json_data) as response:
            return response.status


async def get_works_lists(user_id_site):
    """
    Функция для получения листов работ с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/view_works/"
    data = {"user": user_id_site}
    json_data = json.dumps(data)
    headers = deepcopy(JSON_HEADERS)
    async with ClientSession(headers=headers) as session:
        async with session.get(url=url, data=json_data) as response:
            return await response.json()


async def get_details_works_lists(work_id):
    """
    Функция для получения деталей листа работ с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/view_detail_work/"
    data = {"work_id": work_id}
    json_data = json.dumps(data)
    headers = deepcopy(JSON_HEADERS)

    async with ClientSession(headers=headers) as session:
        async with session.get(url=url, data=json_data) as response:
            return await response.json()


async def del_works_lists(work_id, user_id):
    """
    Функция для удаления листа работ с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/view_detail_work/"
    data = {"work_id": work_id, "user_id": user_id}
    json_data = json.dumps(data)
    headers = deepcopy(JSON_HEADERS)
    async with ClientSession(headers=headers) as session:
        async with session.post(url=url, data=json_data) as response:
            return response.status


async def get_delivery():
    """
    Функция для получения списка доставок с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/get_delivery/"
    async with ClientSession() as session:
        async with session.get(url=url) as response:
            return (await response.json()).get("data", None)


async def get_data_delivery(user_id):
    """
    Функция для получения деталей листа доставки с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/get_list_delivery/"
    data = {"user_id": user_id}
    json_data = json.dumps(data)
    headers = deepcopy(JSON_HEADERS)
    async with ClientSession(headers=headers) as session:
        async with session.get(url=url, data=json_data) as response:
            return await response.json()


async def generate_works_base():
    """
    Функция для обновления базы нормативов
    """
    data: dict = (await get_works()).get("data")
    logger.info("Обновление нормативов - api")
    # работы к которым нужен комментарий
    needs_comment = ["другие работы", "обучение 3", "грузчик", "план"]
    if data and isinstance(data, dict):
        async with async_session() as session:
            async with session.begin():
                await session.execute(delete(Works))
                for department, works in data.items():
                    for name, work in works.items():
                        session.add(
                            Works(
                                id=work.get("id"),
                                name=name,
                                delivery=work.get("delivery", False),
                                standard=work.get("quantity", 0),
                                department_name=department,
                            )
                        )
                        if department == "Общий":
                            if any(
                                [name.lower().startswith(nc) for nc in needs_comment]
                            ):
                                COMMENTED_WORKS[work.get("id")] = name
                await session.commit()
        logger.info("Обновление нормативов завершено")
    else:
        logger.error("Не получилось обновить нормативы!")


async def get_statistic(user_id):
    """
    Функция для получения статистики с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/statistic/"
    data = {"user_id": user_id}
    json_data = json.dumps(data)
    async with ClientSession(headers=JSON_HEADERS) as session:
        async with session.get(url=url, data=json_data) as response:
            if response.status == 200:
                return await response.json()
    return None


async def get_request(user_id):
    """
    Функция для получения заявок на изменение с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/request/"
    data = {"user_id": user_id}
    json_data = json.dumps(data)
    async with ClientSession(headers=JSON_HEADERS) as session:
        async with session.get(url=url, data=json_data) as response:
            return await response.json()


async def post_request(user_id, type_r, comment):
    """
    Функция для создания заявки на изменение
    """
    url = f"{SITE_DOMAIN}/api-auth/request/"
    data = {"user_id": user_id, "type_r": type_r, "comment": comment}
    json_data = json.dumps(data)
    async with ClientSession(headers=JSON_HEADERS) as session:
        async with session.post(url=url, data=json_data) as response:
            return response.status


async def get_pay_sheet(user_id):
    """
    Функция для получения расчетных листов с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/pay_sheet/"
    data = {"user_id": user_id}
    json_data = json.dumps(data)
    async with ClientSession(headers=JSON_HEADERS) as session:
        async with session.get(url=url, data=json_data) as response:
            if response.status == 200:
                return await response.json()
    return None


if __name__ == "__main__":
    # check_user_api('admin', 'fma160392')
    logger.debug(asyncio.run(get_users_statuses()).get("data"))
