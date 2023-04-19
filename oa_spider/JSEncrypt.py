import sys
import base64
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pksc1_v1_5
from Crypto.PublicKey import RSA
# use pycryptodome instead of PyCrypto
# https://github.com/Legrandin/pycryptodome

# https://192.168.20.190/js/login_code.js?v=1.1  function encryption()
key = 'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDDJdxHylPhhOHyQQjiSH5Q6iiU0NTIyaFW+WQwi8R69un0IS4nxgdUaBIIbXipBwod0EZ125JAXGmYQbt9bQy8cq4kQJ0pdZ3vpzCxEUfnDWznBKVP/IYal9DuuPs7qE8M0oBAGaudwS83Er+Gw52x1KI3fIsUNyXwzLosfaL2ZQIDAQAB'
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