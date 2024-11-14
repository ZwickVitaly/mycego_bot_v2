from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from api_services import post_works
from custom_filters import not_digits_filter
from FSM import WorkList
from helpers import aform_works_done_message, aget_user_by_id, anotify_admins
from keyboards import call_back, generate_departments, generate_works, menu_keyboard
from settings import ADMINS, logger
from utils import redis_connection

# роутер листов работ
work_list_router = Router()


@work_list_router.callback_query(WorkList.choice_date, F.data.startswith("prevdate"))
async def choose_department(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор даты при заполнении листа работ
    """
    try:
        # удаляем сообщение
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        # получаем данные из машины состояний
        data = await state.get_data()
        # получаем дату
        date = callback_query.data.split("_")[1]
        # добавляем в данные
        data["date"] = date
        # предлагаем пользователю выбрать департамент работ
        await callback_query.message.answer(
            f"{date}\nВыберите департамент:", reply_markup=await generate_departments()
        )
        # обновляем данные машины состояний
        await state.update_data(data=data)
        # устанавливаем соответствующее состояние
        await state.set_state(WorkList.choice_department)
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


@work_list_router.message(
    WorkList.input_num,
    F.chat.type == "private",
    not_digits_filter,
)
async def process_amount_invalid(message: Message):
    """
    Обрабатываем невалидный ответ пользователя на запрос количества работ
    """
    await message.answer("Введите целое положительное число, пожалуйста.")


@work_list_router.message(WorkList.input_num, F.chat.type == "private")
async def nums_works(message: Message, state: FSMContext):
    """
    Обрабатываем валидное количество работ
    """
    try:
        # получаем данные из машины состояний
        data = await state.get_data()
        # получаем работу, данные о которой вносим сейчас
        current_work = data.get("current_work")
        if current_work is None:
            # обрабатываем возможность отсутствия этой работы
            await message.answer(
                "Ошибка: вид работы не указан. Пожалуйста, выберите вид работы сначала."
            )
            return
        try:
            # получаем количество работы, введённое пользователем
            quantity = int(message.text)
            # проверяем есть ли работа в обязательно комментируемых
            commented_works = (await redis_connection.hgetall("commented_works")) or dict()
            commented = commented_works.get(current_work)
            print(commented_works, commented)
            if quantity <= 0:
                # обрабатываем возможность отрицательного числа или нуля
                await message.answer("Ошибка: количество не может быть отрицательным.")
            elif (
                commented
                and commented.lower().startswith("другие работы")
                and quantity > 720
            ):
                # количество других работ не может быть больше 720
                await message.answer(
                    "Ошибка: по этому виду работ нельзя указать больше 720 минут!"
                )
            else:
                if "works" not in data:
                    data["works"] = (
                        {}
                    )  # Создаем словарь для хранения видов работ и их количества

                data["works"][
                    str(current_work)
                ] = quantity  # Сохраняем количество работы в словарь
                await message.answer(f"Вы указали {quantity} единиц работы.")

                # После сохранения количества работы можно вернуться к выбору видов работ
                if commented:
                    # если работа в комментируемых - запрашиваем комментарий
                    await message.answer(
                        "К этому виду работ необходим комментарий, добавьте пожалуйста."
                    )
                    # устанавливаем соответствующее состояние
                    await state.set_state(WorkList.send_comment)
                    # сохраняем данные в машину состояний
                    await state.update_data(data=data)
                    return
                # получаем работы
                works: dict = data.get("works")
                logger.info(works)
                # формируем ответное сообщение
                msg = "Выберите следующий вид работы или нажмите 'Отправить', если все работы указаны."
                if works:
                    # если работы есть - формируем сообщение заполненных работ
                    works_msg = await aform_works_done_message(works)
                    # сохраняем сообщение в данные
                    data["works_msg"] = works_msg
                    # получаем имеющиеся комментарии к комментируемым работам
                    comment = data.get("comment")
                    if comment:
                        # если комментарий есть - добавляем к сообщению
                        works_msg = (
                            works_msg
                            + f"Комментарий:\n{comment.replace('; ', '\n')}"
                            + "\n\n"
                        )
                    # добавляем заполненные работы в начало ответного сообщения
                    msg = works_msg + msg
                # отвечаем пользователю, предлагаем добавить работы
                await message.answer(
                    msg,
                    reply_markup=await generate_departments(),
                )
                # сохраняем данные в машину состояний
                await state.update_data(data=data)
                # устанавливаем соответствующее состояние
                await state.set_state(WorkList.choice_department)

        except ValueError:
            # обрабатываем невалидный ответ пользователя на запрос количества работ
            await message.answer(
                "Ошибка: введите число, пожалуйста.", reply_markup=call_back
            )
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


@work_list_router.callback_query(F.data == "send", WorkList.choice_work)
@work_list_router.callback_query(F.data == "send", WorkList.choice_department)
async def send_works(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем запрос отправки заполненного листа работ
    """
    try:
        # удаляем сообщение
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        # получаем данные из машины состояний
        data = await state.get_data()
        # получаем дату
        date = data.get("date")
        # получаем заполненные работы
        works = data.get("works")
        if not works:
            # если нет заполненных работ - возвращаем пользователя в главное меню
            await callback_query.message.answer(
                "❗️Вы ни чего не заполнили, чтобы отправлять❗️",
                reply_markup=menu_keyboard(callback_query.from_user.id),
            )
        else:
            # получаем пользователя из бд
            user = await aget_user_by_id(callback_query.from_user.id)
            # получаем id пользователя на сайте
            user_id_site = user.site_user_id
            # получаем комментарий из данных
            comment = data.get("comment", None)
            logger.success(works)
            # ищем есть ли комментируемые работы без комментария
            commented_works = await redis_connection.hgetall("commented_works")
            for key, value in works.items():
                if (
                    int(key) in commented_works
                    and commented_works[int(key)] not in comment
                ):
                    # просим добавить комментарий
                    await callback_query.message.answer(
                        f'⚠️Вы заполнили работы: "{commented_works[int(key)]}" необходимо указать комментарий, '
                        "что именно они в себя включали⚠️",
                    )
                    # устанавливаем id работы, к которой требуется комментарий как current_work
                    data["current_work"] = key
                    # обновляем данные машины состояний
                    await state.update_data(data=data)
                    # устанавливаем соответствующее состояние
                    await state.set_state(WorkList.send_comment)
                    # прекращаем выполнение
                    return
            else:
                logger.debug(f"{date, user_id_site, works, comment}")
                # отправляем заполненные работы
                code = await post_works(date, user_id_site, works, comment=comment)
                # отвечаем пользователю в зависимости от ответа сервера, возвращаем главное меню
                if code == 200:
                    mes = "✅Отправлено✅"
                elif code == 401:
                    mes = "🛑Запись на эту дату существует🛑"
                elif code == 403:
                    mes = "❌Вы не работаете❌"
                else:
                    mes = "☣️Возникла ошибка☣️"
                await callback_query.message.answer(
                    mes, reply_markup=menu_keyboard(callback_query.from_user.id)
                )
                # очищаем машину состояний
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


@work_list_router.callback_query(WorkList.choice_work)
async def add_works(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем запрос выбора работы
    """
    try:
        # удаляем сообщение
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        # получаем данные из машины состояний
        data = await state.get_data()
        if callback_query.data == "back":
            # получаем дату из данных
            date = data.get("date")
            # получаем сообщение об уже заполненных работах
            works_msg = data.get("works_msg")
            # формируем сообщение
            message = f"{date}\nВыберите департамент:"
            if works_msg:
                # получаем комментарии к уже заполненным работам
                comment = data.get("comment")
                if comment:
                    # добавляем комментарии
                    works_msg = (
                        works_msg
                        + f"Комментарий:\n{comment.replace('; ', '\n')}"
                        + "\n\n"
                    )
                # добавляем сообщение об уже заполненных работах в начало сообщения
                message = works_msg + message
            # возвращаем в предыдущее меню
            await callback_query.message.answer(
                message, reply_markup=await generate_departments()
            )
            # устанавливаем соответствующее состояние
            await state.set_state(WorkList.choice_department)
        else:
            try:
                # получаем id работы и сохраняем его в данные
                data["current_work"] = int(callback_query.data.split("_")[-1])
                # обновляем данные машины состояний
                await state.update_data(data=data)
                # просим пользователя ввести количество выполненной работы
                await callback_query.message.answer(f"Теперь введите количество:")
                # устанавливаем соответствующее состояние
                await state.set_state(WorkList.input_num)
            except (ValueError, IndexError):
                # обрабатываем возможное исключение когда пользователь нажимает 2 раза на выбор департамента
                await callback_query.message.answer(
                    f"При выборе работы что-то пошло не так. Может быть Вы нажали на кнопку выбора департамента "
                    f"несколько раз подряд? Пожалуйста, не торопитесь."
                )
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
            f"Ошибка обработки: лист работ - выбор работ; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_router.callback_query(WorkList.choice_department)
async def add_work_list(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем запрос на выбор департамента
    """
    try:
        # удаляем сообщение
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        # получаем данные из машины состояний
        data = await state.get_data()
        # получаем дату из данных
        date = data.get("date")
        # формируем сообщение
        msg = f"{date}\nВыберите работу:"
        # получаем сообщение об уже заполненных работах
        works_msg = data.get("works_msg")
        if works_msg:
            # получаем комментарии к работам
            comment = data.get("comment")
            if comment:
                # добавляем к сообщению
                works_msg = (
                    works_msg + f"Комментарий:\n{comment.replace('; ', '\n')}" + "\n\n"
                )
            # добавляем сообщение об уже заполненных работах в начало ответа пользователю
            msg = works_msg + msg
        # отвечаем пользователю, предлагаем выбрать вид работ
        await callback_query.message.answer(
            msg, reply_markup=await generate_works(callback_query.data)
        )
        # обновляем данные машины состояний
        await state.update_data(data)
        # устанавливаем соответствующее состояние
        await state.set_state(WorkList.choice_work)
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
            f"Ошибка обработки: лист работ - выбор департамента; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )


@work_list_router.message(WorkList.send_comment, F.chat.type == "private", F.text)
async def comment_work(message: Message, state: FSMContext):
    """
    Обработка запроса на добавление комментария к комментируемым работам
    """
    try:
        # получаем данные из машины состояний
        data = await state.get_data()
        # получаем комментарии из данных
        comment = data.get("comment", "")
        # на всякий случай меняем ';' на '.' т.к. ';' - это наш разделитель комментариев
        new_comment = message.text.replace(";", ".")
        # получаем current_work
        current_work = data.get("current_work")
        commented_works = await redis_connection.hgetall("commented_works")
        if comment and commented_works[current_work] in comment:
            comment = comment.split("; ")
            for i, sub in enumerate(comment):
                if commented_works[current_work] in sub:
                    # если комментарий к этой работе уже есть - меняем его на новый
                    comment[i] = f"{commented_works[current_work]}: {new_comment}"
                    break
            # собираем комментарий обратно
            comment = "; ".join(comment)
        else:
            if comment:
                # если комментарий уже есть - добавляем разделитель
                comment += f"; "
            # добавляем комментарий в комментарии
            comment += f"{commented_works[current_work]}: {new_comment}"
        # сохраняем комментарии в данные
        data["comment"] = comment
        # получаем данные о заполненных работах
        works: dict | None = data.get("works")
        # формируем сообщение
        msg = "Комментарий принят. Выберите ещё работы или отправьте резуьтат."
        if works:
            # если заполненные работы есть - формируем сообщение
            works_msg = await aform_works_done_message(works)
            if comment:
                # добавляем комментарии если есть
                works_msg = (
                    works_msg + f"Комментарий:\n{comment.replace('; ', '\n')}" + "\n\n"
                )
            # сохраняем сообщение
            data["works_msg"] = works_msg
            # добавляем сообщение в начало ответа пользователю
            msg = works_msg + msg
        # обновляем данные машины состояний
        await state.update_data(data=data)
        # устанавливаем соответствующее состояние
        await state.set_state(WorkList.choice_department)
        # отвечаем пользователю, предлагаем выбрать департамент
        await message.answer(msg, reply_markup=await generate_departments())
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
            f"Ошибка обработки: расчётные листы - комментарий; пользователь: "
            f"{message.from_user.id}; данные: {message.text}, причина: {e}",
            admins_list=ADMINS,
        )
