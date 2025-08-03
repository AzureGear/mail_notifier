from mail_notifier import MailChecker, TrayIconManager, DEFAULT_CONFIG
from unittest.mock import MagicMock
import pytest
import yaml


@pytest.fixture(params=[
    pytest.param("valid_with_mailboxes", id="Valid config with mailboxes", marks=pytest.mark.valid),
    pytest.param("valid_default", id="Valid default config", marks=pytest.mark.valid),
    pytest.param("invalid_mailboxes", id="Invalid mailboxes config", marks=pytest.mark.invalid),
    pytest.param("missing_required", id="Missing required params", marks=pytest.mark.invalid)
])
def tmp_config(request, tmp_path, mock_mailboxes):
    """Fixture with parameterization for creating different types of configs"""
    config_path = tmp_path / 'config.yaml'

    if request.param == 'valid_with_mailboxes':
        # Valid config with mailboxes
        config = {
            **DEFAULT_CONFIG,
            'mailboxes': mock_mailboxes
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f)

    elif request.param == 'valid_default':
        # Just DEFAULT_CONFIG as is
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(DEFAULT_CONFIG, f)

    elif request.param == 'invalid_mailbox':
        config = {
            **DEFAULT_CONFIG,
            'mailboxes': ['there_is_no_valid_data']
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f)

    elif request.param == 'missing_required':
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump({'check_interval': 30}, f)  # One field

    return config_path


@pytest.fixture
def mock_mailboxes():
    return [
        {
            'email': 'test_email_notifier@inbox.lt',
            'host': 'mail.inbox.lt',
            'username': 'test_email_notifier@inbox.lt',
            'folder': 'INBOX',
            'web_url': 'https://email.inbox.lt/mailbox'
        },
        {
            'email': 'dummy@mail.test',
            'host': 'not.real.host',
            'username': 'dummy@mail.test',
            'folder': 'INBOX',
            'web_url': 'https://dummy.mail.test/mailbox'
        }
    ]


@pytest.fixture
def mock_checker(mock_mailboxes):
    """Maiboxes checker"""
    checker = MailChecker(mock_mailboxes)
    checker.check_mailbox = MagicMock(side_effect=lambda mb: 5 if mb['email'] == 'test_email_notifier@inbox.lt' else -1)
    return checker


@pytest.fixture
def mock_icon_manager(mock_checker):
    """Icon tray manager"""
    icon_manager = TrayIconManager(mock_checker)
    icon_manager.icon = MagicMock()
    return icon_manager
