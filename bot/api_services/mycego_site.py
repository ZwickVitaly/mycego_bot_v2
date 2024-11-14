import asyncio
import json
from copy import deepcopy

from aiohttp import ClientSession, ClientOSError
from db import Works, async_session
from settings import JSON_HEADERS, SITE_DOMAIN, logger
from sqlalchemy import delete

from utils import redis_connection


async def check_user_api(username, password, user_id, retries=3):
    """
    Функция для аутентификации пользователя с помощью сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/login/"
    data = {"username": username, "password": password, "telegram_id": str(user_id)}
    logger.debug(data)
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession() as session:
                async with session.post(url=url, json=data) as response:
                    logger.debug(f"{response.status}")
                    if response.status == 200:
                        user = await response.json()
                        logger.debug(user)
                        if user.get("status_work") is True:
                            return user
        except ClientOSError:
            continue
    return None


async def create_or_get_apport(date, start_time, end_time, user_id_site, retries=3):
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
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession() as session:
                async with session.post(url=url, data=data) as response:
                    return response.status
        except ClientOSError:
            continue
    return 0

async def get_users_statuses(retries=3):
    """
    Функция для получения статусов пользователей с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/users-status/"
    headers = deepcopy(JSON_HEADERS)
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession(headers=headers) as session:
                async with session.get(url=url) as response:
                    if response.status == 200:
                        return await response.json()
        except ClientOSError:
            continue
    return dict()


async def get_appointments(user_id_site, retries=3):
    """
    Функция для получения заявок в график
    """
    url = f"{SITE_DOMAIN}/api-auth/appointment/"
    data = {"user": user_id_site}
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession() as session:
                async with session.get(url=url, data=data) as response:
                    if response.status == 200:
                        return await response.json()
        except ClientOSError:
            continue
    return dict()


async def delete_appointments(user_id_site, id_row, retries=3):
    """
    Функция для удаления заявки в график
    """
    url = f"{SITE_DOMAIN}/api-auth/appointment_delete/"
    data = {"user": user_id_site, "id": id_row}
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession() as session:
                async with session.post(url=url, data=data) as response:
                    return response.status
        except ClientOSError:
            continue
    return 0


async def get_works(retries=3):
    """
    Функция для получения списка работ с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/works_departments/"
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession() as session:
                async with session.get(url=url) as response:
                    return await response.json()
        except ClientOSError:
            continue
    return dict()


async def get_departments(retries=3):
    """
    Функция для получения списка департаментов и работ с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/works_departments/"
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession() as session:
                async with session.get(url=url) as response:
                    return await response.json()
        except ClientOSError:
            continue
    return dict()


async def post_works(date, user_id_site, works, delivery=None, comment=None, retries=3):
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
    print(data)
    json_data = json.dumps(data)
    headers = deepcopy(JSON_HEADERS)
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession(headers=headers) as session:
                async with session.post(url=url, data=json_data) as response:
                    return response.status
        except ClientOSError:
            continue
    return 0


async def get_works_lists(user_id_site, retries=3):
    """
    Функция для получения листов работ с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/view_works/"
    data = {"user": user_id_site}
    json_data = json.dumps(data)
    headers = deepcopy(JSON_HEADERS)
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession(headers=headers) as session:
                async with session.get(url=url, data=json_data) as response:
                    return await response.json()
        except ClientOSError:
            continue
    return dict()


async def get_details_works_lists(work_id, retries=3):
    """
    Функция для получения деталей листа работ с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/view_detail_work/"
    data = {"work_id": work_id}
    json_data = json.dumps(data)
    headers = deepcopy(JSON_HEADERS)
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession(headers=headers) as session:
                async with session.get(url=url, data=json_data) as response:
                    return await response.json()
        except ClientOSError:
            continue
    return dict()

async def del_works_lists(work_id, user_id, retries=3):
    """
    Функция для удаления листа работ с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/view_detail_work/"
    data = {"work_id": work_id, "user_id": user_id}
    json_data = json.dumps(data)
    headers = deepcopy(JSON_HEADERS)
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession(headers=headers) as session:
                async with session.post(url=url, data=json_data) as response:
                    return response.status
        except ClientOSError:
            continue
    return 0


# async def get_delivery():
#     """
#     Функция для получения списка доставок с сайта
#     """
#     url = f"{SITE_DOMAIN}/api-auth/get_delivery/"
#     async with ClientSession() as session:
#         async with session.get(url=url) as response:
#             return (await response.json()).get("data", None)


async def get_data_delivery(user_id, retries=3):
    """
    Функция для получения деталей листа доставки с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/get_list_delivery/"
    data = {"user_id": user_id}
    json_data = json.dumps(data)
    headers = deepcopy(JSON_HEADERS)
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession(headers=headers) as session:
                async with session.get(url=url, data=json_data) as response:
                    return await response.json()
        except ClientOSError:
            continue
    return dict()

async def generate_works_base(retries=3):
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
                await session.commit()
        async with session.begin():
            commented_works = dict()
            for department, works in data.items():
                for name, work in works.items():
                    session.add(
                        Works(
                            id=None,
                            site_id=work.get("id"),
                            name=name,
                            delivery=work.get("delivery", False),
                            standard=work.get("quantity", 0),
                            department_name=department,
                        )
                    )
                    if department == "Общий":
                        if any([name.lower().startswith(nc) for nc in needs_comment]):
                            commented_works[work.get("id")] = name
            await session.commit()
            await redis_connection.hset("commented_works", mapping=commented_works)
        logger.info("Обновление нормативов завершено")
    else:
        logger.error("Не получилось обновить нормативы!")


async def get_statistic(user_id, retries=3):
    """
    Функция для получения статистики с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/statistic/"
    data = {"user_id": user_id}
    json_data = json.dumps(data)
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession(headers=JSON_HEADERS) as session:
                async with session.get(url=url, data=json_data) as response:
                    if response.status == 200:
                        return await response.json()
            return None
        except ClientOSError:
            continue
    return None


async def get_request(user_id, retries=3):
    """
    Функция для получения заявок на изменение с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/request/"
    data = {"user_id": user_id}
    json_data = json.dumps(data)
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession(headers=JSON_HEADERS) as session:
                async with session.get(url=url, data=json_data) as response:
                    return await response.json()
        except ClientOSError:
            continue
    return dict()


async def post_request(user_id, type_r, comment, retries=3):
    """
    Функция для создания заявки на изменение
    """
    url = f"{SITE_DOMAIN}/api-auth/request/"
    data = {"user_id": user_id, "type_r": type_r, "comment": comment}
    json_data = json.dumps(data)
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession(headers=JSON_HEADERS) as session:
                async with session.post(url=url, data=json_data) as response:
                    logger.info(f"{response}")
                    return response.status
        except ClientOSError:
            continue
    return 0


async def get_pay_sheet(user_id, retries=3):
    """
    Функция для получения расчетных листов с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/pay_sheet/"
    data = {"user_id": user_id}
    json_data = json.dumps(data)
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession(headers=JSON_HEADERS) as session:
                async with session.get(url=url, data=json_data) as response:
                    if response.status == 200:
                        return await response.json()
            return None
        except ClientOSError:
            continue
    return None


async def update_user_bio(user_id_site, birth_date, hobbies, retries=3):
    """
    Функция для обновления био пользователя на сайте
    """
    url = f"{SITE_DOMAIN}/api-auth/update-user/{user_id_site}/"
    data = {
        "birth_date": birth_date,
        "hobbies": hobbies,
    }
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession() as session:
                async with session.put(url=url, json=data) as response:
                    if response.status == 200:
                        return True
            return False
        except ClientOSError:
            continue
    return False


async def get_categories(retries=3):
    """
    Функция для получения категорий с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/categories/"
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession() as session:
                async with session.get(url=url) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except ClientOSError:
            continue
    return None


async def get_deliveries_in_progress(retries=3):
    """
    Функция для получения активных поставок с сайта
    """
    url = f"{SITE_DOMAIN}/api-auth/deliveries-in-progress/"
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession() as session:
                async with session.get(url=url) as response:
                    if response.status == 200:
                        return await response.json()
                    return []
        except ClientOSError:
            continue
    return []


async def get_delivery_products(delivery_id, retries=3):
    """
    Функция для получения ордеров и работ по поставкам
    """
    url = f"{SITE_DOMAIN}/api-auth/delivery-products/{delivery_id}/"
    count = 0
    while count <= retries:
        count += 1
        try:
            async with ClientSession() as session:
                async with session.get(url=url) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except ClientOSError:
            continue
    return None


if __name__ == "__main__":
    # check_user_api('admin', 'fma160392')
    # print(asyncio.run(get_categories()))
    # dates = [datetime.fromisoformat(x.get("date_joined")) for x in p]
    # print(dates)
    # print(asyncio.run(get_deliveries_in_progress()))
    print(asyncio.run(get_categories()))
