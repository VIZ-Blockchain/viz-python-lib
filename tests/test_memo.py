import pytest

from viz.memo import Memo


@pytest.mark.usefixtures('viz')
def test_encrypt_decrypt():
    memo = Memo('alice', 'bob')
    text = 'test memo'
    encrypted = memo.encrypt(text)
    decrypted = memo.decrypt(encrypted)
    assert decrypted == text
