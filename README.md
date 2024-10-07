# Административный бот компании Mycego

## Перед установкой или перезапуском:
Добавить значения в .env-template\
.env-template переименовать в .env

ИЛИ

отредактировать/проверить уже существующий .env


## Обязательные переменные:

BOT_TOKEN - токен бота от @BotFather

BOT_NAME - имя контейнера бота. ДОЛЖНО ОТЛИЧАТЬСЯ ЕСЛИ БОТОВ БОЛЬШЕ ЧЕМ 1

ADMINS - список id админов вида 123,321,213

SITE_DOMAIN - домен основного сайта

TIMEZONE - временна́я зона в формате Continent/City например Europe/Moscow,\
можно оставить пустым - будет <b>Asia/Novosibirsk</b>

PROXY_API_KEY - ключ от сервиса proxyapi.ru (chatGPT, gemini)

DEBUG=1 - расширенные логи. можно оставить как есть.

REDIS_HOST=redis - имя контейнера redis на случай нескольких контейнеров на сервере. можно оставить как есть.

REDIS_PORT=6379 - порт redis на тот-же случай. можно оставить как есть.

WEBHOOKS - указатель для запуска бота на веб-хуках. требуется reverse-proxy с ssl сертификатом

WEBHOOK_HOST=0.0.0.0 - хост для размещения бота внутри контейнера. можно оставить как есть. 

WEBHOOK_PORT - порт для размещения бота внутри контейнера. нужен минимум 4-значный int

WEBHOOK_PATH - url-path для принятия обновлений от telegram. должен начинаться с /

WEBHOOK_BASE - базовый url домена, на который принимаются запросы

WEBHOOK_SECRET_TOKEN - секретный токен для большей безопасности

SURVEY_GOOGLE_SHEET_URL - ссылка на гугл-таблицу. На таблице необходим доступ для сервисного аккаунта

CITY_MARKER=Новосибирск - город размещения

## Установка и (пере)запуск:
```
docker-compose up --build
```

## Для работы с Google-sheets:
1. Необходим файл ```gc.json``` в корне проекта с доступом к сервисному аккаунту 
Google (Google API документация в помощь)
Без файла любые попытки обновить гугл-таблицы будут просто не выполняться
2. Необходима гугл-таблица минимум с двумя листами. 
Первый лист - CITY_MARKER(работающие), 
второй - CITY_MARKER(уволенные). 
Идентификаторы работающих и уволенных могут быть любые, 
но ПЕРВЫЙ лист для РАБОТАЮЩИХ, а ВТОРОЙ лист для УВОЛЕННЫХ.
3. Ссылка на гугл-таблицу. Без ссылки любые попытки обновить гугл-таблицы будут просто не выполняться
4. На самой гугл-таблице необходимо выдать доступ сервисному 
аккаунту на уровне "Редактор" (при создании сервисного аккаунта 
создаётся почта этого аккаунта. В поиске пользователей вводим почту и добавляем)

#### результаты опросов всё равно будут сохранены в бд бота, в будущем будет команда для выгрузки.



## Список изменений:


### v2.1.0
Добавлены опросники (1 день, 1 неделя, 1 месяц, 2 месяца, 3 месяца), schedulers переведены на apscheduler, добавлена выгрузка
данных опроса в гугл-таблицу, добавлена модель Survey для хранения данных опросов в бд бота.
Добавлены команды:\
/contacts - список важных для работника контактов (руководитель, hr)\
/promo - детали проводимых акций компании\
/career - карьерная лестница компании\
/vacancies - ссылка на вакансии компании


### v2.0.4
!Добавлены вебхуки!\
Для работы требуется reverse-proxy (nginx, например) с ssl-сертификатом
Если nginx вне контейнера - необходимо будет пробросить порты в docker-compose.yaml

Изменена логика сборки dispatcher

Добавлено расширенное логирование некоторых функций

Изменена логика запуска schedules - теперь все schedules-функции регистрируются\
в startup или shutdown объекта Dispatcher, туда-же регистрируются функции,\
нужные в lifespan

Обновлён .env-template

### v2.0.3
Добавлены поздравления с днём рождения (ChatGPT)

Добавлена нулевая миграция (для создания базы данных с нуля)

Стикеры теперь отправляются по id, а не из файловой системы

Закрыты ошибки при отправке сообщения с пустым текстом (стикер/gif и т.п.)

Минорные фиксы и рефактор

### v2.0.2
Переведён из in-memory на Redis

Redis добавлен в docker-compose и .env-template

Минорные фиксы и рефактор

### v2.0.1
Отказ от создания базы данных при запуске бота (SQLAlchemyDBCreateAsyncManager)

Новый контекстный менеджер - уведомление админов (NotifyAdminsAsyncManager)

Добавлена модель Chat - для отслеживания чатов, где бот - админ

Добавлена проверка и удаление из отслеживаемых чатов и базы данных уволенных пользователей (запрос статусов с сайта)

Добавлены комментарии и докстринги

Добавлен отлов исключений во все хэндлеры и перезапуск docker-контейнера

Рефактор раздела keyboards - разделение по логическим группам

### v2.0.0
Полностью переписан на aiogram 3.10 и sqlalchemy

Переведён в docker

Большинство синхронных методов переведены в асинхронные

Хэндлеры переписаны на роутеры (Router)

На модель Works добавлено поле department_name

Добавлено автоматическое обновление нормативов и разделение по департаментам

Добавлено версионирование базы данных - alembic

Добавлены кнопки "Назад" и соответствующая логика для work_list и work_graf

Добавлена логика отображения уже заполненных работ для work_list