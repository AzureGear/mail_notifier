from mail_notifier import prepare_mailboxes, load_config, save_config, DEFAULT_CONFIG
import pytest
import os


@pytest.mark.parametrize('tmp_config', ['valid_with_mailboxes', 'valid_default'], indirect=True)
def test_valid_config(tmp_config):
    config = load_config(tmp_config, {})
    required_fields = ['check_interval', 'default_sounds', 'icon_error',
                       'icon_read', 'icon_unread', 'sound_enabled', 'sound_notification']

    for field in required_fields:
        assert field in config, f"Required field {field} is missing from config"

def test_load_config_default():
    config = load_config('nonexistent_file.yaml', DEFAULT_CONFIG)
    assert config == DEFAULT_CONFIG


@pytest.mark.parametrize('tmp_config', ['valid_with_mailboxes'], indirect=True)
def test_with_mailboxes(tmp_config):
    config = load_config(tmp_config, {})
    assert len(config['mailboxes']) == 2
    assert all('email' in mb for mb in config['mailboxes'])


@pytest.mark.parametrize('tmp_config', ['invalid_mailbox'], indirect=True)
def test_invalid_mailbox_raises(tmp_config):
    with pytest.raises((ValueError, KeyError)):
        config = load_config(tmp_config, {})
        prepare_mailboxes(config['mailboxes'])  # Проверяем инициализацию


@pytest.mark.parametrize('tmp_config', ['missing_required'], indirect=True)
def test_missing_requered(tmp_config):
    config = load_config(tmp_config, DEFAULT_CONFIG)
    assert config != DEFAULT_CONFIG
    assert len(config) == 1


def test_save_config(tmp_config):
    test_data = {'test': 42}
    save_config(tmp_config, test_data)
    assert os.path.exists(tmp_config)
    with open(tmp_config, 'r') as f:
        content = f.read()
    assert 'test' in content
