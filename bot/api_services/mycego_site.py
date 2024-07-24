import asyncio
import json

from aiohttp import ClientSession
from db import Works, async_session
from settings import SITE_DOMAIN, logger
from sqlalchemy import delete


async def check_user_api(username, password):
    url = f"{SITE_DOMAIN}/api-auth/login/"
    data = {"username": username, "password": password}
    async with ClientSession() as session:
        async with session.post(url=url, data=data) as response:
            if response.status == 200:
                return await response.json()
    return None


async def create_or_get_apport(date, start_time, end_time, user_id_site):
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


async def get_appointments(user_id_site):
    url = f"{SITE_DOMAIN}/api-auth/appointment/"
    data = {"user": user_id_site}
    async with ClientSession() as session:
        async with session.get(url=url, data=data) as response:
            if response.status == 200:
                return await response.json()
    return None


async def delete_appointments(user_id_site, id_row):
    url = f"{SITE_DOMAIN}/api-auth/appointment_delete/"
    data = {"user": user_id_site, "id": id_row}
    async with ClientSession() as session:
        async with session.post(url=url, data=data) as response:
            return response.status


async def get_works():
    url = f"{SITE_DOMAIN}/api-auth/get_works/"
    async with ClientSession() as session:
        async with session.get(url=url) as response:
            return await response.json()


async def post_works(date, user_id_site, works, delivery=None, comment=None):
    url = f"{SITE_DOMAIN}/api-auth/add_works/"
    data = {
        "date": date,
        "user": user_id_site,
        "works": works,
        "delivery": delivery,
        "comment": comment,
    }
    json_data = json.dumps(data)
    headers = {"Content-Type": "application/json"}
    async with ClientSession(headers=headers) as session:
        async with session.post(url=url, data=json_data) as response:
            return response.status


async def get_works_lists(user_id_site):
    url = f"{SITE_DOMAIN}/api-auth/view_works/"
    data = {"user": user_id_site}
    json_data = json.dumps(data)
    headers = {"Content-Type": "application/json"}
    async with ClientSession(headers=headers) as session:
        async with session.get(url=url, data=json_data) as response:
            return await response.json()


async def get_details_works_lists(work_id):
    url = f"{SITE_DOMAIN}/api-auth/view_detail_work/"
    data = {"work_id": work_id}
    json_data = json.dumps(data)
    headers = {"Content-Type": "application/json"}
    async with ClientSession(headers=headers) as session:
        async with session.get(url=url, data=json_data) as response:
            return await response.json()


async def del_works_lists(work_id, user_id):
    url = f"{SITE_DOMAIN}/api-auth/view_detail_work/"
    data = {"work_id": work_id, "user_id": user_id}
    json_data = json.dumps(data)
    headers = {"Content-Type": "application/json"}
    async with ClientSession(headers=headers) as session:
        async with session.post(url=url, data=json_data) as response:
            return response.status


async def get_delivery():
    url = f"{SITE_DOMAIN}/api-auth/get_delivery/"
    async with ClientSession() as session:
        async with session.get(url=url) as response:
            return (await response.json()).get("data", None)


async def get_data_delivery(user_id):
    url = f"{SITE_DOMAIN}/api-auth/get_list_delivery/"
    data = {"user_id": user_id}
    json_data = json.dumps(data)
    headers = {"Content-Type": "application/json"}
    async with ClientSession(headers=headers) as session:
        async with session.get(url=url, data=json_data) as response:
            return await response.json()


async def generate_works_base():
    data = (await get_works()).get("data")
    if data:
        async with async_session() as session:
            async with session.begin():
                await session.execute(delete(Works))
                for i in data:
                    session.add(Works(id=i[0], name=i[1], delivery=i[2], standard=i[3]))
                await session.commit()


async def get_statistic(user_id):
    url = f"{SITE_DOMAIN}/api-auth/statistic/"
    data = {"user_id": user_id}
    json_data = json.dumps(data)
    headers = {"Content-Type": "application/json"}
    async with ClientSession(headers=headers) as session:
        async with session.get(url=url, data=json_data) as response:
            if response.status == 200:
                return await response.json()
    return None


async def get_request(user_id):
    url = f"{SITE_DOMAIN}/api-auth/request/"
    data = {"user_id": user_id}
    json_data = json.dumps(data)
    headers = {"Content-Type": "application/json"}
    async with ClientSession(headers=headers) as session:
        async with session.get(url=url, data=json_data) as response:
            return await response.json()


async def post_request(user_id, type_r, comment):
    url = f"{SITE_DOMAIN}/api-auth/request/"
    data = {"user_id": user_id, "type_r": type_r, "comment": comment}
    json_data = json.dumps(data)
    headers = {"Content-Type": "application/json"}
    async with ClientSession(headers=headers) as session:
        async with session.post(url=url, data=json_data) as response:
            return response.status


if __name__ == "__main__":
    # check_user_api('admin', 'fma160392')
    logger.debug(asyncio.run(get_statistic(1)))
