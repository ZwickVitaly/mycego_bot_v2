import json

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ParseMode

from FSM import WorkDeliveryView
from api_services import delete_user_delivery_works
from helpers import (
    aget_user_by_id,
    anotify_admins,
    make_delivery_works_staged_msg,
    try_parse_delivery_works_nums, make_confirmed_delete_message,
)
from keyboards import (
    delivery_product_works_keyboard,
    menu_keyboard,
    delivery_category_keyboard,
    send_delivery_keyboard, deliveries_view_keyboard,
)
from settings import ADMINS, logger

work_list_delivery_view_router = Router()


@work_list_delivery_view_router.callback_query(
    WorkDeliveryView.choice_marketplace, F.data.startswith("marketplace")
)
async def choose_marketplace_view_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор маркетплейса поставки
    """
    try:
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        data = await state.get_data()
        marketplaces = data.get("marketplaces")
        marketplace = callback_query.data.split("_", 1)[-1]
        deliveries = marketplaces.pop(marketplace)
        await state.update_data({"staged_marketplace": marketplace})
        await callback_query.message.answer(
            "Выберите поставку:", reply_markup=await deliveries_view_keyboard(deliveries)
        )
        await state.set_state(WorkDeliveryView.choice_delivery)

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
            f"Ошибка обработки: просмотр поставкивки, маркетплейс; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_view_router.callback_query(
    WorkDeliveryView.choice_delivery, F.data.startswith("delivery")
)
async def choose_delivery_view_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор поставки
    """
    try:
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        delivery_id = callback_query.data.split("_", 1)[-1]
        data = await state.get_data()
        marketplaces = data.get("marketplaces")
        staged_delivery = marketplaces[data["staged_marketplace"]][delivery_id]
        await callback_query.message.answer(
            f"Поставка: {staged_delivery.get('name')}\n\nВыберите категорию товаров:",
            reply_markup=await delivery_category_keyboard(staged_delivery.get("categories")),
        )
        await state.update_data({"staged_delivery": delivery_id})
        await state.set_state(WorkDeliveryView.choice_category)
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
            f"Ошибка обработки: просмотр поставкивки, категория; пользователь: "
            f"{callback_query.message.from_user.id}; данные: {callback_query.message.text}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_view_router.callback_query(
    WorkDeliveryView.choice_category, F.data.startswith("delivery_category")
)
async def choose_category_view_handler(callback_query: CallbackQuery, state: FSMContext):
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

        delivery = data["marketplaces"][data["staged_marketplace"]][data["staged_delivery"]]
        category = delivery["categories"][category_id]
        available_products_msg = (
            f"\n".join(
                [
                    f"{p.get('order')}. {p.get('name')}"
                    for p in category.get("products").values()
                    if p.get("works")
                ]
            )
            + "\n"
        )
        # works_done = json.loads(works_done) if works_done else dict()
        # works_done_msg = make_delivery_works_done_msg(delivery_name, works_done)
        await callback_query.message.answer(
            f"В категории <b>{category.get('name')}</b> "
            f"Вы выполняли работы по товарам:\n{available_products_msg}\n"
            f"Напишите номера товаров через запятую или интервал от - до через тире (максимальный 1-99).\n"
            f"<b>Например</b>:\n"
            f"1-10, 15, 17\n\n"
            f"<i>такая запись будет соответствовать номерам с 1 по 10, а также 15 и 17</i>",
            parse_mode=ParseMode.HTML,
        )
        await state.set_data(data)
        await state.set_state(WorkDeliveryView.choice_product)
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
            f"Ошибка обработки: просмотр поставки - количество работ; пользователь: "
            f"{callback_query.message.from_user.id}; данные: {callback_query.message.text}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_view_router.message(
    WorkDeliveryView.choice_product, F.chat.type == "private"
)
async def choose_products_view_handler(message: Message, state: FSMContext):
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
        category = data["marketplaces"][data["staged_marketplace"]][data["staged_delivery"]]["categories"][data["staged_category"]]
        category_products = category["products"]
        inverted_products = {val.get("order"): key for key, val in category_products.items()}
        error_products = []
        staged_products = dict()
        available_works = dict()
        for w_o in works_orders:
            w_o = w_o
            if w_o not in inverted_products or not category_products[inverted_products[w_o]].get("works"):
                error_products.append(str(w_o))
            else:
                p_id = inverted_products.get(w_o)
                staged_products[w_o] = p_id
                product = category_products.get(p_id)
                for st_id, work in product.get("works").items():
                    available_works[st_id] = work.get("name")

        if not staged_products:
            await message.answer(
                "Нет доступных работ для выбранных номеров товаров\nВыберите другие товары\n\nПожалуйста напишите номера товаров через запятую или интервал от - до через тире (максимальный 1-99).\n<b>Например</b>:\n"
                f"1 - 7, 8, 16\n\n"
                f"<i>такая запись будет соответствовать номерам с 1 по 7, а также 8 и 16</i>"
            )
            return
        data["staged_products"] = staged_products
        data["available_works"] = available_works
        msg = f"{
            ('<b>Не доступны товары с номерами:</b>\n' + ','.join(error_products) + '\n\n') if error_products else ''
        }<b>Выбранные товары:</b>\n{
            '\n'.join([f"{p_o}. {category_products.get(p).get('name')}" for p_o, p in staged_products.items()])
        }"
        await message.answer(msg, parse_mode=ParseMode.HTML)
        await message.answer(
            "Выберите работы, которые Вы хотите удалить.\n\n⚠️⚠️⚠️<b>!!! Важно !!!</b>⚠️⚠️⚠️\n"
            "Если Вы НЕ ХОТИТЕ УДАЛЯТЬ кую-то работу <b>хотя-бы по одному</b> товару из списка - <b>Не указывайте работу! "
            "После подтверждения сформируйте новый список и укажите работу в новом списке!</b>\n\n",
            parse_mode=ParseMode.HTML,
            reply_markup=await delivery_product_works_keyboard(available_works),
        )
        await state.set_data(data)
        await state.set_state(WorkDeliveryView.choice_works)
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
            f"Ошибка обработки: просмотр поставки - количество работ; пользователь: "
            f"{message.from_user.id}; данные: {message.text}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_view_router.callback_query(
    WorkDeliveryView.choice_works, F.data.startswith("delivery_work")
)
async def choose_work_view_handler(callback_query: CallbackQuery, state: FSMContext):
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
        staged_standards = data.get("staged_standards", dict())
        available_works = data["available_works"]
        staged_standards[standard_id] = available_works.pop(standard_id, None)
        staged_works_msg = make_delivery_works_staged_msg(staged_standards)
        chosen_standards_msg = (
            f"{staged_works_msg}\n"
            "Выберите работы, которые Вы хотите удалить.\n\n⚠️⚠️⚠️<b>!!! Важно !!!</b>⚠️⚠️⚠️\n"
            "Если Вы НЕ хотите удалять какую-то работу хотя-бы по одному товару из списка - <b>Не указывайте работу! "
            "После подтверждения сформируйте новый список и укажите работу в новом списке!</b>\n\n"
        )
        await callback_query.message.answer(
            chosen_standards_msg,
            parse_mode=ParseMode.HTML,
            reply_markup=await delivery_product_works_keyboard(
                available_works, confirm=True
            ),
        )
        data["staged_standards"] = staged_standards
        data["available_works"] = available_works
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
            f"Ошибка обработки: просмотр поставки - количество работ; пользователь: "
            f"{callback_query.message.from_user.id}; данные: {callback_query.message.text}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_view_router.callback_query(
    WorkDeliveryView.choice_works, F.data.startswith("confirm")
)
@work_list_delivery_view_router.callback_query(
    WorkDeliveryView.choice_works, F.data.startswith("back")
)
async def choose_work_view_handler(callback_query: CallbackQuery, state: FSMContext):
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
        category = data["marketplaces"][data["staged_marketplace"]][data["staged_delivery"]]["categories"][
            data.pop("staged_category")]
        category_products = category.get("products")
        staged_products = data.pop("staged_products")
        staged_delivery = data["marketplaces"][data["staged_marketplace"]][data["staged_delivery"]]
        data.pop("staged_category", 0)
        staged_standards = data.pop("staged_standards", dict())
        if callback_query.data == "back":
            await callback_query.message.answer(
                f"❌ОТМЕНЕНО❌ удаление работ из товаров:\n"
                f"{'\n'.join(f'{p_o}. {category_products.get(p).get('name')}' for p_o, p in staged_products.items())}",
            )
        else:
            available_works = dict()
            unavailable_works = dict()
            for p_o, product in staged_products.items():
                for s_id, standard in staged_standards.items():
                    product_full = category["products"][product]
                    work_done = product_full["works"].pop(s_id, None)
                    if work_done:
                        available_works[p_o] = product_full
                        product_full.setdefault("deleted_works", dict())
                        product_full["deleted_works"].update({s_id: work_done})
                    else:
                        product_full.setdefault("not_accepted", dict())
                        product_full["not_accepted"].update({s_id: standard})
                        unavailable_works[p_o] = product_full
            not_accepted_msg = f"{'\n'.join(f'{p_o}. {p.get('name')}\n{'\n'.join(s for s in p.pop('not_accepted', dict()).values())}' for p_o, p in unavailable_works.items())}"
            await callback_query.message.answer(
                "\n✅Принято удаление работ по товарам:✅\n"
                f"{'\n'.join(f'{p_o}. {p.get('name')}' for p_o, p in available_works.items())}\n\n"
                f"{f'❌Не принято удаление работ по товарам❌\n{not_accepted_msg}' if not_accepted_msg else ''}",
            )
        products_left = any(
            [
                p.get("works")
                for p in category_products.values()
            ]
        )
        # products_works = {}
        # for c in delivery_available.values():
        #     c_name = c.get("name")
        #     products_works[c_name] = dict()
        #     for p_o, p in c.get("products").items():
        #         for w in p.get("works_done").values():
        #             w_list = products_works[c_name].get(w, [])
        #             w_list.append(p_o)
        #             products_works[c_name][w] = w_list
        # logger.info(products_works)

        # works_done_msg = make_delivery_works_done_msg(staged_delivery, products_works)
        confirmed_msg = make_confirmed_delete_message(staged_delivery)
        await callback_query.message.answer(confirmed_msg)
        await callback_query.message.answer(
            f"{'Выберите категорию товаров:' if products_left else 'Не осталось работ по товарам в поставке. Отправьте заполненные работы или нажмите \"Отмена\"'}",
            reply_markup=(
                await delivery_category_keyboard(staged_delivery.get("categories"))
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
        await state.set_state(WorkDeliveryView.choice_category)
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
            f"Ошибка обработки: просмотр поставки - количество работ; пользователь: "
            f"{callback_query.message.from_user.id}; данные: {callback_query.message.text}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_delivery_view_router.callback_query(
    F.data == "send", WorkDeliveryView.choice_category
)
async def send_works(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем запрос отправки заполненного листа работ
    """
    try:
        # удаляем сообщение
        data = await state.get_data()
        staged_delivery_key = data.get("staged_delivery", "None")
        staged_delivery = data["marketplaces"][data["staged_marketplace"]].get(staged_delivery_key, dict())
        if not staged_delivery:
            await callback_query.message.answer("Произошла ошибка при выборе поставки.\nПопробуйте заполнить лист поставок ещё раз\nВозвращаю главное меню", reply_markup=menu_keyboard())
            await state.clear()
        products_works = [
            s.get("id")
            for cat in staged_delivery.get("categories", dict()).values()
            for p in cat.get("products", dict()).values()
            for s in p.get("deleted_works", dict()).values()
            if p.get("deleted_works")
        ]
        if not any(products_works):
            await callback_query.message.answer(
                "Вы не заполнили работы. Сначала заполните работы, потом отправляйте.",
            )
            return
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        user = await aget_user_by_id(callback_query.from_user.id)
        resp = await delete_user_delivery_works(data={"user_id": user.site_user_id, "works": products_works})
        if resp:
            msg = "Успешно✅"
        else:
            msg = "Возникла ошибка☣️"
        await callback_query.message.answer(msg)
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
            f"Ошибка обработки: просмотр поставки - отправить; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )