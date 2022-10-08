import sys
import base64
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pksc1_v1_5
from Crypto.PublicKey import RSA
# use pycryptodome instead of PyCrypto
# https://github.com/Legrandin/pycryptodome

key = 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDWtsQ5yzNpsysN8z/UOJu8JBVFWBH3UUHslkpk33dVKF2IAtcfp6DvwYyQkLl33ttJYAWajgtX7i9qW6/9e5vtCDtw6xo04F6JjiLd0ACboHa6FsOKkQzn3hGKa7Dw3bRaNGXxwKqYnAdgsx0ZoRoNX+WRA/bYF1YM0Ck5m/GXNwIDAQAB'
hbwjw_public_key = '-----BEGIN PUBLIC KEY-----\n' + key + '\n-----END PUBLIC KEY-----'

def public_key_format(key):
    return '-----BEGIN PUBLIC KEY-----\n{}\n-----END PUBLIC KEY-----'.format(key)


def encrpt(password, public_key):
    rsakey = RSA.importKey(public_key)
    cipher = Cipher_pksc1_v1_5.new(rsakey)
    cipher_text = base64.b64encode(cipher.encrypt(password.encode()))
    return cipher_text.decode()

if __name__ == "__main__":
    pwd = sys.argv[1]
    p = encrpt(pwd, hbwjw_public_key)
    print('password:', p)