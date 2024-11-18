import json
from asyncio import TaskGroup

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ParseMode

from FSM import WorkListDelivery
from api_services import post_user_delivery_products
from api_services.mycego_site import get_delivery_products, get_categories
from helpers import (
    aget_user_by_id,
    anotify_admins,
    make_delivery_works_done_msg,
    make_delivery_works_staged_msg,
    try_parse_delivery_works_nums,
)
from keyboards import (
    deliveries_keyboard,
    delivery_product_works_keyboard,
    menu_keyboard,
    delivery_category_keyboard,
    send_delivery_keyboard,
)
from settings import ADMINS, logger

work_list_delivery_router = Router()


@work_list_delivery_router.callback_query(
    WorkListDelivery.choice_marketplace, F.data.startswith("marketplace")
)
async def choose_marketplace_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор маркетплейса поставки
    """
    try:
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        data = await state.get_data()
        marketplace = callback_query.data.split("_")[-1]
        marketplaces = json.loads(data.get("marketplaces"))
        deliveries = {
            d_id: name for d_id, name in marketplaces.get(marketplace, {}).items()
        }
        data["deliveries"] = json.dumps(deliveries)
        await state.set_data(data)
        await callback_query.message.answer(
            "Выберите поставку:", reply_markup=await deliveries_keyboard(deliveries)
        )
        await state.set_state(WorkListDelivery.choice_delivery)

    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: лист поставки, маркетплейс; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_router.callback_query(
    WorkListDelivery.choice_delivery, F.data.startswith("delivery")
)
async def choose_delivery_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор поставки
    """
    try:
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        delivery_id = int(callback_query.data.split("_")[-1])
        data = await state.get_data()
        deliveries = json.loads(data.get("deliveries"))
        async with TaskGroup() as tg:
            products = tg.create_task(get_delivery_products(delivery_id))
            categories_data = tg.create_task(get_categories())
        products = products.result()
        categories_data = categories_data.result()
        categories_standards = {
            c.get("id"): {
                "name": c.get("name"),
                "standards": {s.get("id"): s.get("name") for s in c.get("standards")},
            }
            for c in categories_data
        }
        delivery_available = dict()
        for product in products:
            product_category = product.get("product_category")
            category_standards = categories_standards.get(product_category, {}).get(
                "standards", dict()
            )
            product_works = [w.get("standard_id") for w in product.get("works")]
            data = {
                    "id": product.get("id"),
                    "name": product.get("product_art"),
                    "available_works": {
                        w_id: w_name
                        for w_id, w_name in category_standards.items()
                        if w_id not in product_works
                    },
                    "works_done": {},
                }
            if not data.get("available_works"):
                continue
            delivery_available.setdefault(
                product_category,
                {
                    "name": categories_standards.get(product_category, {}).get("name"),
                    "standards": categories_standards.get(product_category, {}).get("standards", []),
                    "products": {},
                }
            )
            if len(category_standards) > len(product_works):
                delivery_available[product_category]["products"][
                    product.get("order")
                ] = data
        if not delivery_available:
            await callback_query.message.answer(
                "В поставке нет доступных для работ товаров. Возвращаю главное меню.",
                reply_markup=menu_keyboard(callback_query.from_user.id),
            )
            await state.clear()
            return
        staged_delivery = deliveries.get(str(delivery_id))
        await state.update_data({"delivery_available": json.dumps(delivery_available)})
        await state.update_data({"staged_delivery": staged_delivery})
        await callback_query.message.answer(
            f"Поставка: {staged_delivery}\n\nВыберите категорию товаров:",
            reply_markup=await delivery_category_keyboard(delivery_available),
        )
        await state.set_state(WorkListDelivery.choice_category)
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            callback_query.message.bot,
            f"Ошибка обработки: лист поставки, категория; пользователь: "
            f"{callback_query.message.from_user.id}; данные: {callback_query.message.text}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_router.callback_query(
    WorkListDelivery.choice_category, F.data.startswith("delivery_category")
)
async def choose_category_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор категории
    """
    try:
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        category_id = callback_query.data.split("_")[-1]
        data = await state.get_data()
        data["staged_category"] = category_id

        works_done = data.get("works_done")
        delivery_name = data.get("staged_delivery")
        delivery_available = json.loads(data["delivery_available"])
        category_available = delivery_available.get(category_id).get("products")
        available_products_msg = (
            f"\n".join(
                [
                    f"{p_o}. {p.get('name')}"
                    for p_o, p in category_available.items()
                    if p.get("available_works")
                ]
            )
            + "\n"
        )
        works_done = json.loads(works_done) if works_done else dict()
        works_done_msg = make_delivery_works_done_msg(delivery_name, works_done)
        await callback_query.message.answer(works_done_msg)
        await callback_query.message.answer(
            f"В категории <b>{delivery_available.get(category_id).get('name')}</b> "
            f"доступны товары:\n{available_products_msg}\n"
            f"Напишите номера товаров через запятую или интервал от - до через тире (максимальный 1-99).\n"
            f"<b>Например</b>:\n"
            f"1-10, 15, 17\n\n"
            f"<i>такая запись будет соответствовать номерам с 1 по 10, а также 15 и 17</i>",
            parse_mode=ParseMode.HTML,
        )
        await state.set_data(data)
        await state.set_state(WorkListDelivery.choice_product)
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            callback_query.message.bot,
            f"Ошибка обработки: лист работ - количество работ; пользователь: "
            f"{callback_query.message.from_user.id}; данные: {callback_query.message.text}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_router.message(
    WorkListDelivery.choice_product, F.chat.type == "private"
)
async def choose_products_handler(message: Message, state: FSMContext):
    """
    Обрабатываем выбранные товары
    """
    try:
        logger.info(message.text)
        try:
            works_orders = try_parse_delivery_works_nums(message.text)
        except Exception as e:
            logger.error(f"{e}")
            await message.answer(
                "<b>Неправильный формат ввода номеров товаров</b>.\nПожалуйста напишите номера товаров через запятую или интервал от - до через тире (максимальный 1-99).\n<b>Например</b>:\n"
                f"1 - 7, 8, 16\n\n"
                f"<i>такая запись будет соответствовать номерам с 1 по 7, а также 8 и 16</i>",
                parse_mode=ParseMode.HTML,
            )
            return

        # получаем работу, данные о которой вносим сейчас
        data = await state.get_data()
        delivery_available = json.loads(data.get("delivery_available"))
        staged_category = data["staged_category"]
        staged_category_products = delivery_available.get(staged_category).get(
            "products"
        )
        error_products = []
        staged_products = dict()
        available_works = dict()
        for w_o in works_orders:
            w_o = str(w_o)
            if not staged_category_products.get(w_o, {}).get("available_works"):
                error_products.append(w_o)
            else:
                product = staged_category_products[w_o]
                staged_products[w_o] = product
                available_works.update(product.get("available_works"))
        if not staged_products:
            await message.answer(
                "Нет доступных работ для выбранных номеров товаров\nВыберите другие товары\n\nПожалуйста напишите номера товаров через запятую или интервал от - до через тире (максимальный 1-99).\n<b>Например</b>:\n"
                f"1 - 7, 8, 16\n\n"
                f"<i>такая запись будет соответствовать номерам с 1 по 7, а также 8 и 16</i>"
            )
            return
        data["staged_products"] = json.dumps(staged_products)
        data["available_works"] = json.dumps(available_works)
        msg = f"{
            ('<b>Не доступны товары с номерами:</b>\n' + ','.join(error_products) + '\n\n') if error_products else ''
        }<b>Выбранные товары:</b>\n{
            '\n'.join([f"{p_o}. {p.get('name')}" for p_o, p in staged_products.items()])
        }"
        await message.answer(msg, parse_mode=ParseMode.HTML)
        await message.answer(
            "Выберите работы, которые вы выполнили по товарам.\n\n⚠️⚠️⚠️<b>!!! Важно !!!</b>⚠️⚠️⚠️\n"
            "Если Вы НЕ выполняли какую-то работу хотя-бы по одному товару из списка - <b>Не указывайте работу! "
            "После подтверждения сформируйте новый список и укажите работу в новом списке!</b>\n\n"
            "⚠️Работы, которые УЖЕ выполнены по выбранному товару, засчитаны не будут!⚠️",
            parse_mode=ParseMode.HTML,
            reply_markup=await delivery_product_works_keyboard(available_works),
        )
        await state.set_data(data)
        await state.set_state(WorkListDelivery.choice_works)
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            message.bot,
            f"Ошибка обработки: лист работ - количество работ; пользователь: "
            f"{message.from_user.id}; данные: {message.text}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_router.callback_query(
    WorkListDelivery.choice_works, F.data.startswith("delivery_work")
)
async def choose_work_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор товара
    """
    try:
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        standard_id = callback_query.data.split("_")[-1]
        data = await state.get_data()
        staged_standards = data.get("staged_standards")
        staged_standards = json.loads(staged_standards) if staged_standards else dict()
        available_works = json.loads(data["available_works"])
        staged_standards[standard_id] = available_works.pop(standard_id, None)
        staged_works_msg = make_delivery_works_staged_msg(staged_standards)
        chosen_standards_msg = (
            f"{staged_works_msg}\n"
            "Выберите работы, которые вы выполнили по товарам.\n\n⚠️⚠️⚠️<b>!!! Важно !!!</b>⚠️⚠️⚠️\n"
            "Если Вы НЕ выполняли какую-то работу хотя-бы по одному товару из списка - <b>Не указывайте работу! "
            "После подтверждения сформируйте новый список и укажите работу в новом списке!</b>\n\n"
            "⚠️Работы, которые УЖЕ выполнены по выбранному товару, засчитаны не будут!⚠️"
        )
        await callback_query.message.answer(
            chosen_standards_msg,
            parse_mode=ParseMode.HTML,
            reply_markup=await delivery_product_works_keyboard(
                available_works, confirm=True
            ),
        )
        data["staged_standards"] = json.dumps(staged_standards)
        data["available_works"] = json.dumps(available_works)
        await state.set_data(data)
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            callback_query.message.bot,
            f"Ошибка обработки: лист работ - количество работ; пользователь: "
            f"{callback_query.message.from_user.id}; данные: {callback_query.message.text}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_router.callback_query(
    WorkListDelivery.choice_works, F.data.startswith("confirm")
)
@work_list_delivery_router.callback_query(
    WorkListDelivery.choice_works, F.data.startswith("back")
)
async def choose_work_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбранную работу
    """
    try:
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass

        # получаем работу, данные о которой вносим сейчас
        data = await state.get_data()
        staged_products = json.loads(data.pop("staged_products"))
        staged_delivery = data["staged_delivery"]
        staged_category_id = data.pop("staged_category")
        staged_standards = json.loads(data.pop("staged_standards", "null"))
        delivery_available = json.loads(data.get("delivery_available"))
        if callback_query.data == "back":
            if staged_standards:
                await callback_query.message.answer(
                    "❌ОТМЕНЕНО❌ заполнение работ по товарам:\n"
                    f"{'\n'.join(f'{p_o}. {p.get('name')}' for p_o, p in staged_products.items())}",
                )
        else:
            staged_category = delivery_available.pop(staged_category_id)
            available_products = staged_category.pop("products")
            unavailable_works = {}
            available_works = {}
            for p_o, p in staged_products.items():
                for s_id, s_name in staged_standards.items():
                    aw = available_products[p_o].get("available_works")
                    if s_id in aw:
                        available_products[p_o]["works_done"].update(
                            {s_id: aw.pop(s_id)}
                        )
                        available_works[p_o] = available_works.get(
                            p_o, {"works": {}, "name": p.get("name")}
                        )
                        available_works[p_o]["works"].update({s_id: s_name})
                    else:
                        unavailable_works[p_o] = unavailable_works.get(
                            p_o, {"works": {}, "name": p.get("name")}
                        )
                        unavailable_works[p_o]["works"].update({s_id: s_name})

            staged_category["products"] = available_products
            delivery_available[staged_category_id] = staged_category
            data["delivery_available"] = json.dumps(delivery_available)
            not_accepted_msg = f"{'\n'.join(f'{p_o}. {p.get('name')}\n{'\n'.join(s for s in p.get('works',{}).values())}' for p_o, p in unavailable_works.items())}"
            await callback_query.message.answer(
                "✅Сохранено✅ заполнение работ по товарам:\n"
                f"{'\n'.join(f'{p_o}. {p.get('name')}' for p_o, p in available_works.items())}\n\n"
                f"{f'❌Не приняты❌ работы по товарам:\n{not_accepted_msg}' if not_accepted_msg else ''}",
            )
        products_left = any(
            [
                p.get("available_works")
                for c in delivery_available.values()
                for p in c.get("products").values()
            ]
        )
        products_works = {}
        for c in delivery_available.values():
            c_name = c.get("name")
            products_works[c_name] = dict()
            for p_o, p in c.get("products", dict()).items():
                for w in p.get("works_done", dict()).values():
                    w_list = products_works[c_name].get(w, [])
                    w_list.append(p_o)
                    products_works[c_name][w] = w_list
            if not products_works[c_name]:
                products_works.pop(c_name)
        logger.info(products_works)

        works_done_msg = make_delivery_works_done_msg(staged_delivery, products_works)
        await callback_query.message.answer(works_done_msg)
        await callback_query.message.answer(
            f"{'Выберите категорию товаров:' if products_left else 'Не осталось работ по товарам в поставке. Отправьте заполненные работы или нажмите \"Отмена\"'}",
            reply_markup=(
                await delivery_category_keyboard(delivery_available)
                if products_left
                else await send_delivery_keyboard()
            ),
        )
        # works_done_msg = make_delivery_works_done_msg(delivery_name, works_done)
        # await callback_query.message.answer(
        #     f"{works_done_msg}"
        #     f"Выберите ❗❗❗ПОРЯДКОВЫЙ НОМЕР❗❗❗ товара в поставке:",
        #     reply_markup=await delivery_products_keyboard(available_products)
        # )
        await state.set_state(WorkListDelivery.choice_category)
        await state.set_data(data)
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            callback_query.message.bot,
            f"Ошибка обработки: лист работ - количество работ; пользователь: "
            f"{callback_query.message.from_user.id}; данные: {callback_query.message.text}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_router.callback_query(
    F.data == "send", WorkListDelivery.choice_category
)
async def send_works(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем запрос отправки заполненного листа работ
    """
    try:
        # удаляем сообщение
        data = await state.get_data()
        delivery_available = json.loads(data.get("delivery_available"))
        products_works = {
            int(p.get("id")): [s for s in p.get("works_done")]
            for c in delivery_available.values()
            for p in c.get("products").values()
            if p.get("works_done")
        }
        if not any([w for w in products_works.values()]):
            await callback_query.message.answer(
                "Вы не заполнили работы. Сначала заполните работы, потом отправляйте."
            )
            return
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        user = await aget_user_by_id(callback_query.from_user.id)
        payload = {"user_id": int(user.site_user_id), "products": products_works}
        resp = await post_user_delivery_products(data=payload)
        if resp:
            not_created = resp.get('Not created', {})
            try:
                not_created_msg = f"\n{'\n'.join([f'{key}:\n{', '.join([w for w in value])}' for key, value in not_created.items()])}"
            except Exception as e:
                logger.exception(e)
                not_created_msg = ""
            await callback_query.message.answer(
                f"✅{resp.get('data')}\n\n"
                f"❌Не принятые работы: {not_created_msg if not_created else '✅все приняты.'}",
                parse_mode=ParseMode.HTML,
            )
        else:
            await callback_query.message.answer(
                "Что-то пошло не так, возможно нет связи с сайтом. "
                "Пожалуйста попробуйте ещё раз заполнить поставку.",
                reply_markup=menu_keyboard()
            )
        await state.clear()

    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: лист работ - отправить; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )
