from concurrent.futures import ThreadPoolExecutor, as_completed
from logging.handlers import RotatingFileHandler
from imapclient import IMAPClient
from pystray import MenuItem as item
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
from ast import literal_eval
from PIL import Image
import webbrowser
import threading
import winsound
import pystray
import logging
import keyring
import time
import yaml
import ssl
import sys
import os


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler('app.log', maxBytes=10**6, backupCount=2)]
)


def get_base_dir():
    """Get base directory, works for both development and packaged"""
    if getattr(sys, 'frozen', False):
        # If app is packed into PyInstaller
        return os.path.dirname(sys.executable)
    else:
        # Dev
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = get_base_dir()


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # type: ignore
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


ICON_DIR = resource_path('icons')
SOUND_DIR = resource_path('sounds')
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yaml')  # Config always with .exe
logging.info(f"BASE_DIR resolved to: {BASE_DIR}")


# Default configurations
DEFAULT_CONFIG = {
    # Mailboxes config
    'mailboxes': [],
    'check_interval': 60,

    # Sound notifications
    'sound_enabled': True,
    'default_sounds': False,
    'sound_notification': 'ring.wav',

    # Icon colors
    'icon_error': (128, 128, 128, 255),   # Grey
    'icon_unread': (155, 20, 115, 255),   # Red
    'icon_read': (0, 160, 255, 255),    # Blue
}


def load_config(path: str, default: dict) -> dict:
    """Load configuration from YAML file or return default if not found."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or default
    except FileNotFoundError:
        logging.warning(f"Config file not found: {path}, using defaults")
        return default
    except yaml.YAMLError as e:
        logging.error(f"Error parsing config {path}: {e}, using defaults")
        return default
    except Exception as e:
        logging.error(f"Error loading config {path}: {e}, using defaults")
        return default


def save_config(path: str, data: dict):
    """Save configuration to YAML file."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f)
    except Exception as e:
        logging.error(f"Error saving config {path}: {e}")


def get_password(email: str) -> Optional[str]:
    """Fetch password securely using keyring"""
    password = keyring.get_password("email_notifier", email)
    if password is None:
        logging.warning(f"Password not found in keyring for {email}")
    return password


def prepare_mailboxes(mailboxes: List[Dict[str, str]]) -> None:
    """Safe storage and checking of passwords"""
    load_dotenv()  # Load environment variables from .env file

    for mail in mailboxes:
        if not isinstance(mail, dict):
            logging.error(f"Invalid mailbox config: expected dict, got {type(mail)}")
            raise ValueError(f"Invalid mailbox config: expected dict, got {type(mail)}")
        
        missing_keys = [key for key in ['email', 'host', 'username'] if key not in mail]  # Checking only critical entry
        if missing_keys:
            email = mail.get('email', 'unknown')
            logging.error(f"Invalid mailbox config for {email}: missing keys {missing_keys}")
            raise ValueError(f"Invalid mailbox config for {email}: missing keys {missing_keys}")
        
        env_value = os.getenv(mail['email'])

        if env_value is None:
            logging.error(f"Missing .env entry for {mail['email']}")
            sys.exit(1)

        keyring.set_password("email_notifier", mail['email'], env_value)


# Load configurations
config = load_config(CONFIG_PATH, DEFAULT_CONFIG)
MAILBOXES: List[dict] = config['mailboxes']
CHECK_INTERVAL: int = config['check_interval']
prepare_mailboxes(MAILBOXES)


class MailChecker:
    def __init__(self, mailboxes: List[dict]):
        self.mailboxes = mailboxes
        self.error_counters = {mb['email']: 0 for mb in mailboxes}
        self.unread_counts = {mb['email']: 0 for mb in mailboxes}
        self.previous_unread_counts = {mb['email']: 0 for mb in mailboxes}
        self.running = True
        self.executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="mail_checker_")
        self.lock = threading.Lock()
        self.last_check = time.time()

    def check_mailbox(self, mailbox: dict):
        """Check a single mailbox for unread messages."""
        try:
            password = get_password(mailbox['email'])
            if password:
                with IMAPClient(mailbox['host'], timeout=30, ssl=True, ssl_context=ssl.create_default_context()) as server:
                    server.login(mailbox['username'], password)
                    server.select_folder(mailbox.get('folder', 'INBOX'))
                    unread = server.search('UNSEEN')
                    self.error_counters[mailbox['email']] = 0  # Reset on success
                    logging.info(f"{mailbox['email']}: {len(unread)} unread")
                    return len(unread)
        except ssl.SSLError as e:
            logging.error(f"SSL/TLS connection failed for {mailbox['host']}: {e}")
            return -1
        except Exception as e:
            err_count = self.error_counters[mailbox['email']] + 1
            self.error_counters[mailbox['email']] = err_count
            wait = min(300, 5 * 2 ** err_count)  # Exponential error retry
            logging.warning(f"Will retry {mailbox['email']} in {wait}s: {e}")
            time.sleep(wait)
            return -1

    def check_all(self):
        """Check all mailboxes using thread pool"""
        # Map futures to email identifiers
        futures = {self.executor.submit(self.check_mailbox, mb): mb['email'] for mb in self.mailboxes}
        results = {}

        # Process completed futures
        for future in as_completed(futures):
            email = futures[future]
            results[email] = future.result()

        # Update state with thread safety
        with self.lock:
            self.previous_unread_counts = dict(self.unread_counts)  # Preserve previous state
        self.unread_counts.update(results)  # Merge new results
        self.last_check = time.time()

    def get_status(self) -> Dict[str, int]:
        """Get current mailbox status."""
        with self.lock:
            return dict(self.unread_counts)

    def get_previous_status(self) -> Dict[str, int]:
        """Get previous mailbox status."""
        with self.lock:
            return dict(self.previous_unread_counts)

    def has_new_unread_messages(self) -> bool:
        """Check if there are new unread messages since last check."""
        current = self.get_status()
        previous = self.get_previous_status()

        for email in current:
            if email in previous:
                # Check if we went from 0 unread to >0 unread
                if previous[email] == 0 and current[email] > 0:
                    return True
        return False

    def stop(self):
        """Stop the mail checker."""
        self.running = False
        self.executor.shutdown(wait=True, cancel_futures=True)


def load_and_color_icon(
    icon_name: str,
    color: Tuple[int, int, int, int],
    threshold: int = 40
) -> Image.Image:
    """Load and recolor icon image."""
    try:
        icon_path = os.path.join(ICON_DIR, f"{icon_name}.png")
        img = Image.open(icon_path).convert('RGBA')
        data = img.getdata()
        new_data = []
        for pixel in data:
            r, g, b, a = pixel
            if a > 0 and r < threshold and g < threshold and b < threshold:
                new_data.append(tuple(color))
            else:
                new_data.append(pixel)
        img.putdata(new_data)
        return img
    except Exception as e:
        logging.error(f"Error loading icon {icon_name}: {e}")
        # Fallback: create a simple colored icon
        img = Image.new('RGBA', (64, 64), tuple(color))
        return img


def play_notification_sound(sound_path: str | None = None, default_sounds: bool = False):
    """Play notification sound."""
    if default_sounds:
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        logging.info("Played system beep")
    else:
        try:
            if sound_path and os.path.exists(sound_path):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME)
                logging.info(f"Played notification sound: {sound_path}")

        except Exception as e:
            logging.error(f"Error playing sound: {e}")


class TrayIconManager:
    def __init__(self, checker: MailChecker):
        self.icons = self.load_icons()
        self.checker = checker

        # def on_double_click(icon: Any) -> None:
        #     webbrowser.open(self.checker.mailboxes[0]['web_url'])

        # --- Checking interval submenu ---
        self.intervals = [
            (15, '15 sec'),
            (30, '30 sec'),
            (60, '1 min'),
            (300, '5 min'),
            (600, '10 min'),
            (1800, '30 min'),
            (3600, '60 min'),
        ]

        def make_interval_handler(seconds):
            def handler(icon, item):
                global CHECK_INTERVAL
                config['check_interval'] = seconds
                save_config(CONFIG_PATH, config)
                CHECK_INTERVAL = seconds
                self.update_icon()
            return handler

        def is_interval_checked(seconds):
            return lambda item: config.get('check_interval', 60) == seconds

        interval_menu = pystray.Menu(
            *[
                item(
                    label,
                    make_interval_handler(seconds),
                    checked=is_interval_checked(seconds)
                ) for seconds, label in self.intervals
            ]
        )
        # --- End Checking interval submenu ---

        self.icon = pystray.Icon('Mail notifier')
        # self.icon.on_activate = on_double_click
        self.icon.title = "Mail notifier"
        self.icon.menu = pystray.Menu(
            item('Open mail', self.open_mail),
            item('Check now', self.check_now),
            item(
                'Checking interval',
                interval_menu
            ),
            item(
                'Notifications',
                pystray.Menu(
                    item(
                        'Sound Notification',
                        self.enable_sound,
                        checked=lambda item: config.get('sound_enabled', True)
                    ),
                    item(
                        'System notification sound',
                        self.toggle_system_sound,
                        checked=lambda item: config.get('default_sounds', False)
                    ),
                )
            ),
            item('Quit', self.quit)
        )
        self.icon.icon = self.icons['icon_read']

    @staticmethod
    def load_icons():
        return {
            'icon_unread': load_and_color_icon('bell_icon', literal_eval(config['icon_unread'])),
            'icon_read': load_and_color_icon('empty_mail_icon', literal_eval(config['icon_read'])),
            'icon_error': load_and_color_icon('error_icon', literal_eval(config['icon_error']))
        }

    def enable_sound(self, icon, item):
        """Toggle sound notification."""
        config['sound_enabled'] = not config.get('sound_enabled', True)
        save_config(CONFIG_PATH, config)
        self.update_icon()

    def toggle_system_sound(self, icon, item):
        """Toggle system notification sound usage."""
        config['default_sounds'] = not config.get('default_sounds', False)
        save_config(CONFIG_PATH, config)
        self.update_icon()

    def update_icon(self):
        """Update tray icon based on mailbox status."""
        status = self.checker.get_status()
        total_unread = sum(max(0, v) for v in status.values())
        has_error = any(v == -1 for v in status.values())

        # Build status message
        messages = []
        for email, count in status.items():
            if count == -1:
                messages.append(f"{email}: error")
            elif count > 0:
                messages.append(f"{count} unread in {email}")

        self.icon.title = "\n".join(messages) if messages else "No new mail"

        # Set appropriate icon
        if has_error:
            self.icon.icon = self.icons['icon_error']
        elif total_unread > 0:
            self.icon.icon = self.icons['icon_unread']
        else:
            self.icon.icon = self.icons['icon_read']

        # Play sound if enabled
        if config.get('sound_enabled', True) and self.checker.has_new_unread_messages():
            sound_file = os.path.join(SOUND_DIR, config.get('sound_notification', 'ring.wav'))
            play_notification_sound(sound_file, config.get('default_sounds', False))

    def check_now(self, icon, item):
        """Manual check trigger."""
        logging.info("Manual check triggered")
        self.checker.check_all()
        self.update_icon()

    def open_mail(self, icon, item):
        """Open the default web browser to the web URLs of mailboxes with unread mails only."""
        status = self.checker.get_status()
        for mailbox in self.checker.mailboxes:
            email = mailbox['email']
            web_url = mailbox.get('web_url')
            unread_count = status.get(email, 0)
            if web_url and unread_count > 0:
                webbrowser.open(web_url)

    def quit(self, icon, item):
        """Quit application."""
        logging.info("Closing application")
        self.checker.stop()
        self.icon.stop()

    def run(self):
        """Start the tray icon."""
        self.icon.run()


def main():
    # Create initial configs if missing
    if not os.path.exists(CONFIG_PATH):
        save_config(CONFIG_PATH, DEFAULT_CONFIG)

    checker = MailChecker(MAILBOXES)
    tray_manager = TrayIconManager(checker)

    def check_loop():
        try:
            while checker.running:
                checker.check_all()
                tray_manager.update_icon()
                elapsed = time.time() - checker.last_check
                # 15 seconds is the minimum interval, to avoid too aggressive polling
                sleep_time = max(15, CHECK_INTERVAL - elapsed)

                # Sleep in chunks to respond to shutdown faster
                for _ in range(int(sleep_time)):
                    if not checker.running:
                        return
                    time.sleep(1)
        except Exception as e:
            logging.exception(f"Check loop crashed:{e}")
        finally:
            logging.info("Check loop exited cleanly")

    threading.Thread(target=check_loop, daemon=True).start()
    tray_manager.run()


if __name__ == '__main__':
    main()
