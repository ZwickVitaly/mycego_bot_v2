import json

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ParseMode

from FSM import WorkListDelivery
from api_services.mycego_site import get_delivery_products, get_categories
from helpers import aget_user_by_id, anotify_admins, make_delivery_works_done_msg, make_delivery_works_staged_msg
from keyboards import (
    deliveries_keyboard,
    delivery_products_keyboard,
    delivery_product_works_keyboard, menu_keyboard,
)
from settings import ADMINS, logger

work_list_delivery_router = Router()


@work_list_delivery_router.callback_query(WorkListDelivery.choice_marketplace, F.data.startswith("marketplace"))
async def choose_marketplace_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор маркетплейса поставки
    """
    try:
        # удаляем сообщение
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        # получаем данные из машины состояний
        data = await state.get_data()
        # получаем выбранный маркетплейс
        marketplace = callback_query.data.split("_")[-1]
        marketplaces = json.loads(data.get("marketplaces"))
        deliveries = {d_id: name for d_id, name in marketplaces.get(marketplace, {}).items()}
        data["deliveries"] = json.dumps(deliveries)
        await state.set_data(data)
        await callback_query.message.answer("Выберите поставку:", reply_markup=await deliveries_keyboard(deliveries))
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
            f"Ошибка обработки: лист работ - дата; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_router.callback_query(WorkListDelivery.choice_delivery, F.data.startswith("delivery"))
async def choose_delivery_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор поставки
    """
    try:
        # получаем данные из машины состояний
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        delivery_id = int(callback_query.data.split("_")[-1])
        # получаем работу, данные о которой вносим сейчас
        data = await state.get_data()
        deliveries = json.loads(data.get("deliveries"))
        products = await get_delivery_products(delivery_id)
        categories = {c.get("id"): {s.get("id"): s.get("name") for s in c.get("standards")} for c in await get_categories()}
        available_products = dict()
        for product in products:
            product_category = product.get("product_category")
            category_standards = categories.get(product_category, {})
            product_works = [w.get("standard_id") for w in product.get("works")]
            if len(category_standards) > len(product_works):
                available_products[product.get("id")] = {
                    "order": product.get("order"),
                    "name": product.get("product_art"),
                    "available_works": {
                        w_id: w_name for w_id, w_name in category_standards.items() if w_id not in product_works
                    }
                }
        staged_delivery = deliveries.get(str(delivery_id))
        await state.update_data({"available_products": json.dumps(available_products)})
        await state.update_data({"staged_delivery": staged_delivery})
        await callback_query.message.answer(
            f"Поставка: {staged_delivery}\n\nВыберите ❗❗❗ПОРЯДКОВЫЙ НОМЕР❗❗❗ товара в поставке:",
            reply_markup=await delivery_products_keyboard(available_products)
        )
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



@work_list_delivery_router.callback_query(WorkListDelivery.choice_product, F.data.startswith("delivery_product"))
async def choose_products_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор товара
    """
    try:
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        product_id = callback_query.data.split("_")[-1]
        data = await state.get_data()

        works_done = data.get("works_done")
        delivery_name = data.get("staged_delivery")
        works_done = json.loads(works_done) if works_done else dict()
        works_done_msg = make_delivery_works_done_msg(delivery_name, works_done)
        products = json.loads(data.get("available_products"))
        if product_id not in products or products.get(product_id, None) is None:
            await callback_query.message.answer("Товар не найден. Пожалуйста, используйте предложенную клавиатуру.")
            await callback_query.message.answer(
                f"{works_done_msg}\nВыберите ❗❗❗ПОРЯДКОВЫЙ НОМЕР❗❗❗ товара в поставке:",
                reply_markup=await delivery_products_keyboard(products)
            )
            return
        product = products.get(product_id)
        product["id"] = product_id
        available_works = product.get("available_works")
        if not available_works:
            await callback_query.message.answer("По товару не найдено доступных работ. Пожалуйста, выберите другой.")
            await callback_query.message.answer(
                f"{works_done_msg}\nВыберите ❗❗❗ПОРЯДКОВЫЙ НОМЕР❗❗❗ товара в поставке:",
                reply_markup=await delivery_products_keyboard(products)
            )
            return
        await callback_query.message.answer(
            f"{works_done_msg}Выбран товар:\n{product.get('name')}\nПорядковый номер в поставке: "
            f"{product.get('order')}\n\nВыберите проделанные работы\n"
            f"*Если работ в списке нет, значит кто-то уже отметил выполнение работы.",
            reply_markup=await delivery_product_works_keyboard(available_works)
        )
        data["staged_product"] = json.dumps(product)
        await state.set_data(data)
        await state.set_state(WorkListDelivery.choice_works)
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


@work_list_delivery_router.callback_query(WorkListDelivery.choice_works, F.data.startswith("delivery_work"))
async def choose_work_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбранную работу
    """
    try:
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        work_id = callback_query.data.split("_")[-1]
        # получаем работу, данные о которой вносим сейчас
        data = await state.get_data()
        product = json.loads(data.get("staged_product"))
        available_works = product.get("available_works", dict())
        works_staged = product.get("staged_works", dict())
        works_done = data.get("works_done")
        delivery_name = data.get("staged_delivery")
        works_done = json.loads(works_done) if works_done else dict()
        works_done_msg = make_delivery_works_done_msg(delivery_name, works_done)
        logger.info(works_staged)
        if work_id not in available_works:
            confirm = True if works_staged else None
            if not available_works:
                await callback_query.message.answer("Что-то пошло не так. Возвращаю главное меню.", reply_markup=menu_keyboard(callback_query.from_user.id))
                await state.clear()
            else:
                works_staged_msg = make_delivery_works_staged_msg(works_staged)
                await callback_query.message.answer("Нельзя выполнить работу по этому товару. Пожалуйста, используйте предложенную клавиатуру.")
                await callback_query.message.answer(
                    f"{works_done_msg}\nВыбран товар:\n{product.get('name')}\nПорядковый номер в поставке: "
                    f"{product.get('order')}{works_staged_msg}\nВыберите проделанные работы\n"
                    f"*Если работ в списке нет, значит кто-то уже отметил выполнение работы.",
                    reply_markup=await delivery_product_works_keyboard(available_works, confirm=confirm)
                )
            return
        work_chosen = available_works.pop(work_id)
        works_staged.update({work_id: work_chosen})
        confirm = True if works_staged else None
        product["staged_works"] = works_staged
        data["staged_product"] = json.dumps(product)
        works_staged_msg = make_delivery_works_staged_msg(works_staged)
        await callback_query.message.answer(
            f"{works_done_msg}\nВыбран товар:\n{product.get('name')}\nПорядковый номер в поставке: "
            f"{product.get('order')}{works_staged_msg}\nВыберите проделанные работы\n"
            f"*Если работ в списке нет, значит кто-то уже отметил выполнение работы.",
            reply_markup=await delivery_product_works_keyboard(available_works, confirm=confirm)
        )
        await state.set_data(data)
        await state.set_state(WorkListDelivery.choice_works)
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

@work_list_delivery_router.callback_query(WorkListDelivery.choice_works, F.data.startswith("confirm"))
@work_list_delivery_router.callback_query(WorkListDelivery.choice_works, F.data.startswith("back"))
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
        staged_product = json.loads(data.pop("staged_product"))
        works_done = data.get("works_done")
        works_done = json.loads(works_done) if works_done else dict()
        available_products = json.loads(data.get("available_products"))
        delivery_name = data.get("staged_delivery")
        if callback_query.data == "back":
            await callback_query.message.answer(
                "❌ОТМЕНЕНО❌ заполнение работ по товару:\n"
                f"{staged_product.get('name')}\nПорядковый номер в поставке: {staged_product.get('order')}\n"
            )
        elif callback_query.data == "confirm":
            p_id = staged_product.get('id')
            product = available_products.pop(p_id)
            if staged_product.get("available_works"):
                product["available_works"] = staged_product["available_works"]
                available_products[p_id] = product
                available_products = dict(sorted(available_products.items(), key=lambda x:x[0]))
            data["available_products"] = json.dumps(available_products)
            if p_id in works_done:
                works_done[p_id]["works_done"].update(staged_product.get("staged_works"))
            else:
                works_done[p_id] = {"works_done": staged_product.get("staged_works"), "name": staged_product.get("name"), "order": staged_product.get("order")}
            data["works_done"] = json.dumps(works_done)
        works_done_msg = make_delivery_works_done_msg(delivery_name, works_done)
        await callback_query.message.answer(
            f"{works_done_msg}"
            f"Выберите ❗❗❗ПОРЯДКОВЫЙ НОМЕР❗❗❗ товара в поставке:",
            reply_markup=await delivery_products_keyboard(available_products)
        )
        await state.set_state(WorkListDelivery.choice_product)
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



@work_list_delivery_router.callback_query(F.data == "send", WorkListDelivery.choice_product)
async def send_works(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем запрос отправки заполненного листа работ
    """
    try:
        # удаляем сообщение
        data = await state.get_data()
        works = data.get("works_done")
        if not works:
            await callback_query.message.answer("Вы не заполнили работы. Сначала заполните работы, потом отправляйте.")
            return
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        works = json.loads(works)
        logger.info(works)
        user = await aget_user_by_id(callback_query.from_user.id)
        payload = {"user_id": int(user.site_user_id), "orders": {int(key): [int(w) for w in item.get("works_done", {}).keys()] for key, item in works.items()}}
        await callback_query.message.answer(f"<code>{json.dumps(payload, indent=2, ensure_ascii=False)}</code>", parse_mode=ParseMode.HTML)
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
