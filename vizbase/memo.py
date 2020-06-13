# -*- coding: utf-8 -*-
import hashlib
import struct
from binascii import hexlify, unhexlify

from Crypto.Cipher import AES  # noqa: DUO133  # we're using pycryptodome
from graphenebase.base58 import base58decode, base58encode
from graphenebase.memo import get_shared_secret

from .account import PublicKey
from .objects import Memo


def init_aes(shared_secret, nonce):
    """
    Initialize AES instance.

    :param hex shared_secret: Shared Secret to use as encryption key
    :param int nonce: Random nonce
    :return: AES instance and checksum of the encryption key
    :rtype: length 2 tuple
    """
    " Seed "
    ss = unhexlify(shared_secret)
    non = struct.pack("<Q", int(nonce))
    encryption_key = hashlib.sha512(non + ss).hexdigest()
    " Check'sum' "
    check = hashlib.sha256(unhexlify(encryption_key)).digest()
    check = struct.unpack_from("<I", check[:4])[0]
    " AES "
    key = unhexlify(encryption_key[0:64])
    iv = unhexlify(encryption_key[64:96])
    return AES.new(key, AES.MODE_CBC, iv), check


def encode_memo(priv, pub, nonce, message, **kwargs):
    """
    Encode a message with a shared secret between Alice and Bob.

    :param PrivateKey priv: Private Key (of Alice)
    :param PublicKey pub: Public Key (of Bob)
    :param int nonce: Random nonce
    :param str message: Memo message
    :return: Encrypted message
    :rtype: hex
    """
    shared_secret = get_shared_secret(priv, pub)
    aes, check = init_aes(shared_secret, nonce)
    raw = bytes(message, "utf8")

    " Padding "
    bs = 16
    if len(raw) % bs:
        raw = _pad(raw, bs)
    " Encryption "
    cipher = hexlify(aes.encrypt(raw)).decode("ascii")
    prefix = kwargs.pop("prefix")
    op = {
        "from": format(priv.pubkey, prefix),
        "to": format(pub, prefix),
        "nonce": nonce,
        "check": check,
        "encrypted": cipher,
    }

    tx = Memo(**op)

    return "#" + base58encode(hexlify(bytes(tx)).decode("ascii"))


def decode_memo(priv, message):
    """
    Decode a message with a shared secret between Alice and Bob.

    :param PrivateKey priv: Private Key (of Bob)
    :param base58encoded message: Encrypted Memo message
    :return: Decrypted message
    :rtype: str
    :raise ValueError: if message cannot be decoded as valid UTF-8
           string
    """
    " decode structure "
    raw = base58decode(message[1:])
    from_key = PublicKey(raw[:66])
    raw = raw[66:]
    to_key = PublicKey(raw[:66])
    raw = raw[66:]
    nonce = str(struct.unpack_from("<Q", unhexlify(raw[:16]))[0])
    raw = raw[16:]
    check = struct.unpack_from("<I", unhexlify(raw[:8]))[0]
    raw = raw[8:]
    cipher = raw

    if repr(to_key) == repr(priv.pubkey):
        shared_secret = get_shared_secret(priv, from_key)
    elif repr(from_key) == repr(priv.pubkey):
        shared_secret = get_shared_secret(priv, to_key)
    else:
        raise ValueError("Incorrect PrivateKey")

    " Init encryption "
    aes, checksum = init_aes(shared_secret, nonce)

    " Check "
    assert check == checksum, "Checksum failure"

    " Encryption "
    # remove the varint prefix (FIXME, long messages!)
    message = cipher[2:]
    message = aes.decrypt(unhexlify(bytes(message, "ascii")))
    try:
        return _unpad(message.decode("utf8"), 16)
    except Exception:
        raise ValueError(message)


def involved_keys(message):
    """decode structure."""
    raw = base58decode(message[1:])
    from_key = PublicKey(raw[:66])
    raw = raw[66:]
    to_key = PublicKey(raw[:66])

    return [from_key, to_key]


def _pad(raw_message, bs):
    num_bytes = bs - len(raw_message) % bs
    return raw_message + num_bytes * struct.pack("B", num_bytes)


def _unpad(raw_message, bs):
    count = int(struct.unpack("B", bytes(raw_message[-1], "ascii"))[0])
    if bytes(raw_message[-count::], "ascii") == count * struct.pack("B", count):
        return raw_message[:-count]
    return raw_message
