from mail_notifier import SOUND_DIR
import pytest
import os


@pytest.mark.parametrize("status, expected_icon, expected_title", [
    # No unread messages, no errors
    ({'test_email_notifier@inbox.lt': 0, 'dummy@mail.test': 0},
     'icon_read',
     "No new mail"),

    # Unread messages in one account
    ({'test_email_notifier@inbox.lt': 5, 'dummy@mail.test': 0},
     'icon_unread',
     "5 unread in test_email_notifier@inbox.lt"),

    # Error in one account
    ({'test_email_notifier@inbox.lt': -1, 'dummy@mail.test': 0},
     'icon_error',
     "test_email_notifier@inbox.lt: error"),

    # Unread messages and error
    ({'test_email_notifier@inbox.lt': 5, 'dummy@mail.test': -1},
     'icon_error',
     "5 unread in test_email_notifier@inbox.lt\ndummy@mail.test: error"),
])
def test_update_icon(mock_icon_manager, mocker, status, expected_icon, expected_title):
    # Mock get_status to return the test status
    mocker.patch.object(mock_icon_manager.checker, 'get_status', return_value=status)
    mock_icon_manager.update_icon()
    assert mock_icon_manager.icon.title == expected_title
    assert mock_icon_manager.icon.icon == mock_icon_manager.icons[expected_icon]


def test_open_mail(mock_icon_manager, mocker):
    # Mock webbrowser.open
    mock_open = mocker.patch('webbrowser.open')
    
    # Set status: one account has unread messages
    status = {'test_email_notifier@inbox.lt': 5, 'dummy@mail.test': 0}
    mocker.patch.object(mock_icon_manager.checker, 'get_status', return_value=status)
    mock_icon_manager.open_mail(None, None)
    mock_open.assert_called_once_with('https://email.inbox.lt/mailbox')


def test_open_mail_no_unread(mock_icon_manager, mocker):
    # Mock webbrowser.open
    mock_open = mocker.patch('webbrowser.open')
    
    # Set status: no unread messages
    status = {'test_email_notifier@inbox.lt': 0, 'dummy@mail.test': 0}
    mocker.patch.object(mock_icon_manager.checker, 'get_status', return_value=status)
    mock_icon_manager.open_mail(None, None)
    mock_open.assert_not_called()


def test_open_mail_multiple_unread(mock_icon_manager, mocker):
    # Mock webbrowser.open
    mock_open = mocker.patch('webbrowser.open')
    
    # Set status: both accounts have unread messages
    status = {'test_email_notifier@inbox.lt': 5, 'dummy@mail.test': 3}
    mocker.patch.object(mock_icon_manager.checker, 'get_status', return_value=status)
    mock_icon_manager.open_mail(None, None)
    expected_calls = [
        mocker.call('https://email.inbox.lt/mailbox'),
        mocker.call('https://dummy.mail.test/mailbox')
    ]
    mock_open.assert_has_calls(expected_calls, any_order=True)


def test_sound_notification(mock_icon_manager, mocker):
    # Mock play_notification_sound
    mock_play_sound = mocker.patch('mail_notifier.play_notification_sound')
    
    # Patch config to enable sound
    mocker.patch('mail_notifier.config', {
        'sound_enabled': True,
        'default_sounds': False,
        'sound_notification': 'ring.wav'
    })
    # Set previous and current statuses to simulate new unread messages
    previous_status = {'test_email_notifier@inbox.lt': 0, 'dummy@mail.test': 0}
    current_status = {'test_email_notifier@inbox.lt': 5, 'dummy@mail.test': 0}
    mocker.patch.object(mock_icon_manager.checker, 'get_previous_status', return_value=previous_status)
    mocker.patch.object(mock_icon_manager.checker, 'get_status', return_value=current_status)
    mock_icon_manager.update_icon()
    sound_file = os.path.join(SOUND_DIR, 'ring.wav')
    mock_play_sound.assert_called_once_with(sound_file, False)


def test_no_sound_notification(mock_icon_manager, mocker):
    # Mock play_notification_sound
    mock_play_sound = mocker.patch('mail_notifier.play_notification_sound')
    
    # Patch config to enable sound
    mocker.patch('mail_notifier.config', {
        'sound_enabled': True,
        'default_sounds': False,
        'sound_notification': 'ring.wav'
    })
    # Set previous and current statuses with no new unread messages
    status = {'test_email_notifier@inbox.lt': 5, 'dummy@mail.test': 0}
    mocker.patch.object(mock_icon_manager.checker, 'get_previous_status', return_value=status)
    mocker.patch.object(mock_icon_manager.checker, 'get_status', return_value=status)
    mock_icon_manager.update_icon()
    mock_play_sound.assert_not_called()


def test_sound_disabled(mock_icon_manager, mocker):
    # Mock play_notification_sound
    mock_play_sound = mocker.patch('mail_notifier.play_notification_sound')
    
    # Patch config to disable sound
    mocker.patch('mail_notifier.config', {
        'sound_enabled': False,
        'default_sounds': False,
        'sound_notification': 'ring.wav'
    })
    # Set previous and current statuses to simulate new unread messages
    previous_status = {'test_email_notifier@inbox.lt': 0, 'dummy@mail.test': 0}
    current_status = {'test_email_notifier@inbox.lt': 5, 'dummy@mail.test': 0}
    mocker.patch.object(mock_icon_manager.checker, 'get_previous_status', return_value=previous_status)
    mocker.patch.object(mock_icon_manager.checker, 'get_status', return_value=current_status)
    mock_icon_manager.update_icon()
    mock_play_sound.assert_not_called()


def test_manual_check_email(mock_icon_manager, mocker):
    # Mock the check_all method of MailChecker
    mock_check_all = mocker.patch.object(mock_icon_manager.checker, 'check_all')
    mock_update_icon = mocker.patch.object(mock_icon_manager, 'update_icon')

    # Trigger manual check
    mock_icon_manager.check_now(None, None)
    mock_check_all.assert_called_once()
    mock_update_icon.assert_called_once()
    

def test_quit(mocker, mock_icon_manager, mock_checker):
    """Clear Shutdown Test"""
    mock_stop = mocker.patch.object(mock_checker, 'stop')
    mock_icon_stop = mocker.patch.object(mock_icon_manager.icon, 'stop')

    mock_icon_manager.quit(None, None)

    # Cheking calls
    mock_stop.assert_called_once()
    mock_icon_stop.assert_called_once()
