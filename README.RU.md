## Mail notifier  
Минималистичное приложение которое проверяет почту (или несколько почтовых адресов) и уведомляет о новых письмах из трея (панели задач).

## Краткое руководство по запуску

### Релиз (`Mail_notifier.exe`)

1. Скачайте последнюю версию из [Releases](https://github.com/AzureGear/mail_notifier/releases).  
2. Настройте `config.yaml` (лежит рядом с `.exe`):  
    
    ```yaml
    mailboxes:
    - email: test_email_notifier@inbox.lt     # Папка для проверки (обычно INBOX)
    folder: INBOX 
    host: mail.inbox.lt                       # IMAP-сервер
    username: test_email_notifier@inbox.lt    # Логин (чаще все является email'ом)
    web_url: https://email.inbox.lt/mailbox   # Ссылка для кнопки "Open Mail"
    sound_enabled: true                       # Включить звук
    sound_notification: ring.wav              
    check_interval: 60                        # Интервал проверки (в секундах)
    default_sounds: false                     # Использовать системный звук вместо ring.wav
    icon_error: (128, 128, 128, 255)          # Цвет иконки при новых письмах (R,G,B,A)
    icon_read: (0, 160, 255, 255)             # Цвет иконки, когда писем нет
    icon_unread: (155, 20, 115, 255)          # Цвет иконки при ошибке
    ```

3. Добавьте пароли в `.env` (в той же папке):  
    
    ```
    # .env
    test_email_notifier@inbox.lt=CMxd85xE1T
    ```

    🔐 Для большинства почтовых сервисов требуется создать *App Password*, например:
    - [gmail.com](https://myaccount.google.com/apppasswords)  
    - [mail.ru](https://help.mail.ru/mail/security/protection/external)  

4. Запустите `Mail_notifier.exe` – появится иконка в трее.  В случае проблем смотреть `app.log`.

### Опционально: через исходный код
1. Клонируйте репозиторий:  
    ```sh
    git clone https://github.com/AzureGear/mail_notifier.git
    cd mail_notifier
    ```
2. Установите зависимости (через Poetry):  
    ```sh
    poetry install
    ```
3. Настройте `config.yaml` и `.env` (как в `Релиз...`, но уже используя каталог проекта).  
4. Запустите (с помощью `pythonw` можно скрыть окно консоли):  
    ```sh
    pythonw main.py
    ```
   или через Poetry:  
    ```sh
    poetry run pythonw main.py
    ```

## Описание
Легкое приложение, которое работает в системном трее и периодически проверяет почтовые ящики по IMAP. Показывает почтовые адреса с непрочитанными письмами при наведении.   

**Особенности:**

✔ Быстрый доступ к почте – выбор меню `Open mail` открывает веб-страницы только почтовых ящиков с непрочитанными письмами.  
✔ Несколько почтовых ящиков – можно добавить любое количество аккаунтов (Gmail, Mail.ru и др.)  
✔ Интервал проверки (от 15 секунд до 1 часа)  
✔ Звуковые уведомления – опционально, можно отключить или использовать системный звук  
✔ Кастомизация иконок – настройте цвет иконок в зависимости от вашей темы или предпочтений `(R, G, B, A)`  
✔ Кастомизация звукового оповещения. Поместите `.wav`-файл в папку `sounds` и укажите его имя в `config.yaml`  
✔ Логирование (`app.log`)   


## Лицензия  
MIT License – свободное использование и модификация.
