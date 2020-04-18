# -*- coding: utf-8 -*-
import hashlib
import struct
from binascii import hexlify, unhexlify
from Crypto.Cipher import AES

from graphenebase.base58 import base58encode, base58decode
from graphenebase.memo import get_shared_secret, _unpad, _pad

from .objects import Memo


def init_aes(shared_secret, nonce):
    """ Initialize AES instance

        :param hex shared_secret: Shared Secret to use as encryption key
        :param int nonce: Random nonce
        :return: AES instance and checksum of the encryption key
        :rtype: length 2 tuple

    """
    " Seed "
    ss = unhexlify(shared_secret)
    n = struct.pack("<Q", int(nonce))
    encryption_key = hashlib.sha512(n + ss).hexdigest()
    " Check'sum' "
    check = hashlib.sha256(unhexlify(encryption_key)).digest()
    check = struct.unpack_from("<I", check[:4])[0]
    " AES "
    key = unhexlify(encryption_key[0:64])
    iv = unhexlify(encryption_key[64:96])
    return AES.new(key, AES.MODE_CBC, iv), check


def encode_memo(priv, pub, nonce, message, **kwargs):
    """ Encode a message with a shared secret between Alice and Bob

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
    BS = 16
    if len(raw) % BS:
        raw = _pad(raw, BS)
    " Encryption "
    cipher = hexlify(aes.encrypt(raw)).decode("ascii")
    prefix = kwargs.pop("prefix")
    s = {
        "from": format(priv.pubkey, prefix),
        "to": format(pub, prefix),
        "nonce": nonce,
        "check": check,
        "encrypted": cipher,
    }

    tx = Memo(**s)

    return "#" + base58encode(hexlify(bytes(tx)).decode("ascii"))


def decode_memo(priv, message):
    """ Decode a message with a shared secret between Alice and Bob

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
    except:
        raise ValueError(message)


def involved_keys(message):
    """ decode structure """
    raw = base58decode(message[1:])
    from_key = PublicKey(raw[:66])
    raw = raw[66:]
    to_key = PublicKey(raw[:66])

    return [from_key, to_key]
