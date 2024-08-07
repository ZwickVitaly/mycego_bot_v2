### v2.01
Отказ от создания базы данных при запуске бота (SQLAlchemyDBCreateAsyncManager)

Новый контекстный менеджер - уведомление админов (NotifyAdminsAsyncManager)

Добавлена модель Chat - для отслеживания чатов, где бот - админ

Добавлена проверка и удаление из отслеживаемых чатов и базы данных уволенных пользователей (запрос статусов с сайта)

Добавлены комментарии и докстринги

Добавлен отлов исключений во все хэндлеры и перезапуск docker-контейнера

Рефактор раздела keyboards - разделение по логическим группам

### v2.00
Полностью переписан на aiogram 3.10 и sqlalchemy

Переведён в docker

Большинство синхронных методов переведены в асинхронные

Хэндлеры переписаны на роутеры (Router)

На модель Works добавлено поле department_name

Добавлено автоматическое обновление нормативов и разделение по департаментам

Добавлено версионирование базы данных - alembic

Добавлены кнопки "Назад" и соответствующая логика для work_list и work_graf

Добавлена логика отображения уже заполненных работ для work_list