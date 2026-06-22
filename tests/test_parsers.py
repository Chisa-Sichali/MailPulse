from app.services.email_processing.parsers.sender import parse_sender
from app.services.email_processing.parsers.subject import clean_subject


def test_parse_sender_with_display_name():
    name, address = parse_sender("Jane Doe <jane@example.com>")
    assert name == "Jane Doe"
    assert address == "jane@example.com"


def test_parse_sender_bare_address():
    name, address = parse_sender("jane@example.com")
    assert name == ""
    assert address == "jane@example.com"


def test_clean_subject_decodes_encoded_words():
    subject = "=?UTF-8?Q?Hello_World?="
    assert clean_subject(subject) == "Hello World"
