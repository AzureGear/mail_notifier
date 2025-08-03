def test_mail_checker_init(mock_checker):
    assert len(mock_checker.mailboxes) == 2
    assert mock_checker.error_counters['test_email_notifier@inbox.lt'] == 0
    assert mock_checker.error_counters['dummy@mail.test'] == 0

def test_check_mailbox(mock_checker, mock_mailboxes):
    # The first mailbox should return 5 unread
    result1 = mock_checker.check_mailbox(mock_mailboxes[0])
    assert result1 == 5

    # The second mailbox should return an error (-1)
    result2 = mock_checker.check_mailbox(mock_mailboxes[1])
    assert result2 == -1

def test_check_all(mock_checker):
    mock_checker.check_all()
    assert mock_checker.unread_counts['test_email_notifier@inbox.lt'] == 5
    assert mock_checker.unread_counts['dummy@mail.test'] == -1

def test_has_new_unread_messages(mock_checker):
    # Initially there are no unread
    assert not mock_checker.has_new_unread_messages()
    
    # Emulating new messages
    mock_checker.unread_counts['test_email_notifier@inbox.lt'] = 5
    assert mock_checker.has_new_unread_messages()