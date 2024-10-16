from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from FSM import EditContactsState
from keyboards import delete_or_edit_contact, select_contacts_keyboard
from settings import logger
from utils import RedisKeys, redis_connection

# Роутер для редактирования контактов (админ)
admin_edit_contacts_router = Router()


@admin_edit_contacts_router.callback_query(
    EditContactsState.waiting_for_selected_contact
)
async def process_admin_contact_callback(
    callback_query: CallbackQuery, state: FSMContext
):
    try:
        logger.info(f"{callback_query.from_user.id} редактирует контакты")
        await callback_query.message.delete()
        if callback_query.data == "add_new_contact":
            await callback_query.message.answer(
                "Добавьте контакты в формате:\n\n"
                "Имя(произвольная строка) - контакт(произвольная строка)\n\n"
                "ПРОБЕЛ ТИРЕ ПРОБЕЛ ОБЯЗАТЕЛЬНЫ!",
            )
            await state.set_state(EditContactsState.waiting_for_added_contact_info)
        else:
            selected = callback_query.data.split("_")[-1]
            contact = await redis_connection.hget(RedisKeys.CONTACTS_KEY, selected)
            await callback_query.message.answer(
                f"Выберите действие для контакта: \n{contact}",
                reply_markup=await delete_or_edit_contact(callback_query.data),
            )
            await state.set_state(EditContactsState.waiting_for_action_type)
            logger.info(callback_query.data)
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")


@admin_edit_contacts_router.message(EditContactsState.waiting_for_added_contact_info)
async def process_new_contact(message: Message, state: FSMContext):
    try:
        logger.info(f"{message.from_user.id} добавляет контакт: {message.text}")
        edited = (await state.get_data()).get("edited_contact")
        action = "добавлен"
        if edited:
            await redis_connection.hdel(RedisKeys.CONTACTS_KEY, edited)
            action = "изменён"
        counter = await redis_connection.incrby(RedisKeys.CONTACTS_COUNTER_KEY)
        await redis_connection.hset(RedisKeys.CONTACTS_KEY, counter, message.text)
        contacts = await redis_connection.hgetall(RedisKeys.CONTACTS_KEY)
        msg = f"{'\n'.join([f'{val}' for val in contacts.values()])}"
        await state.set_state(EditContactsState.waiting_for_selected_contact)
        await message.answer(
            f"Контакт {action}. Новый список:\n{msg}\n\nВыберите контакт, который нужно отредактировать или добавьте новый",
            reply_markup=await select_contacts_keyboard(contacts),
        )
        await message.delete()
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await message.answer("☣️Возникла ошибка☣️")


@admin_edit_contacts_router.callback_query(EditContactsState.waiting_for_action_type)
async def process_action_type(callback_query: CallbackQuery, state: FSMContext):
    try:
        logger.info(callback_query.data)
        contact_key = callback_query.data.split("_")[-1]
        await callback_query.message.delete()
        if callback_query.data.startswith("delete"):
            await redis_connection.hdel(RedisKeys.CONTACTS_KEY, contact_key)
            contacts = await redis_connection.hgetall(RedisKeys.CONTACTS_KEY)
            msg = f"{'\n'.join([f'{key} - {val}' for key, val in contacts.items()])}"
            await state.set_state(EditContactsState.waiting_for_selected_contact)
            await callback_query.message.answer(
                f"Контакт Удалён. Новый список:\n{msg}\n\n"
                "Выберите контакт, который нужно отредактировать или добавьте новый",
                reply_markup=await select_contacts_keyboard(contacts),
            )
        else:
            await state.set_data({"edited_contact": contact_key})
            await callback_query.message.answer(
                "Введите обновлённый контакт в формате:\n\n"
                "Имя(произвольная строка) - контакт(произвольная строка)\n\n"
                "ПРОБЕЛ ТИРЕ ПРОБЕЛ ОБЯЗАТЕЛЬНЫ!",
            )
            await state.set_state(EditContactsState.waiting_for_added_contact_info)
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")
