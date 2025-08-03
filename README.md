## Mail Notifier  
A minimalist application that checks email (or multiple email accounts) and notifies about new messages from the system tray (taskbar).

## Quick Start Guide

### Release (`Mail_notifier.exe`)
1. Download the latest version from [Releases](https://github.com/AzureGear/mail_notifier/releases).  
2. Configure `config.yaml` (located next to the `.exe` file):  

    ```yaml
    mailboxes:
    - email: test_email_notifier@inbox.lt     # Mailbox folder to check (usually INBOX)
    folder: INBOX 
    host: mail.inbox.lt                       # IMAP server
    username: test_email_notifier@inbox.lt    # Login (often same as email)
    web_url: https://email.inbox.lt/mailbox   # Link for "Open Mail" button
    sound_enabled: true                       # Enable sound
    sound_notification: ring.wav              
    check_interval: 60                        # Check interval (in seconds)
    default_sounds: false                     # Use system sound instead of ring.wav
    icon_error: (128, 128, 128, 255)          # Icon color for errors (R,G,B,A)
    icon_read: (0, 160, 255, 255)             # Icon color when no unread emails
    icon_unread: (155, 20, 115, 255)          # Icon color for new emails
    ```

3. Add passwords to `.env` (in the same folder):  

    ```
    # .env
    test_email_notifier@inbox.lt=CMxd85xE1T
    ```

    🔐 Most email services require an *App Password*, for example:

    - [gmail.com](https://myaccount.google.com/apppasswords)  
    - [yahoo.com](https://help.yahoo.com/kb/SLN4075.html)  

4. Run `Mail_notifier.exe` – an icon will appear in the system tray. Check `app.log` if any issues occur.


### Option: running from source code (for developers)  
1. Clone the repository:  
   ```sh
   git clone https://github.com/AzureGear/mail_notifier.git
   cd mail_notifier
   ```
2. Install dependencies (via Poetry):  
   ```sh
   poetry install
   ```
3. Configure `config.yaml` and `.env` (as in `Release...`, but using the project directory).
4. Run (use `pythonw` to avoid console window):  
   ```sh
   pythonw main.py
   ```
   or via Poetry:  
   ```sh
   poetry run pythonw main.py
   ```

## Description
A lightweight application that runs in the system tray and periodically checks mailboxes via IMAP. Displays email addresses with unread messages on hover.  

**Features:**

✔ Quick mail access – selecting `Open mail` from the menu opens web interfaces only for mailboxes with unread messages.  
✔ Multiple mailboxes – supports any number of accounts (gmail, yahoo.com, mail.com, etc.)  
✔ Adjustable check interval (from 15 seconds to 1 hour)  
✔ Sound notifications – optional, can be disabled or replaced with system sound  
✔ Icon customization – configure icon colors to match your theme/preferences `(R, G, B, A)`  
✔ Custom sound alerts – place `.wav` files in the `sounds` folder and specify in `config.yaml`  
✔ Logging (`app.log`)  

### Building
```bash
pyinstaller --onefile --windowed --name "mail_notifier" --icon=icons/app.ico --add-data "icons/*.png;icons" --add-data "sounds/*.wav;sounds" --add-data "config.yaml;." --add-data ".env;." main.py
```

### License  
MIT License – free to use and modify.