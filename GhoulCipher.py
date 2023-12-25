from functools import reduce
import base64 as b64


def b64e(s):
    return b64.b64encode(s.encode()).decode()


def b64d(s):
    return b64.b64decode(s).decode()


def get_xor_key(key):
    return reduce(lambda x, y: x ^ y, key.encode())


def xor_cipher(message, key):
    return bytes([m ^ key[i % len(key)] for i, m in enumerate(message)])


def alg(m, xor_key, p, k):
    temp = p - k ** p * p ** k + p - p ** k
    return bytearray(
        (i ^ (temp % (k + 1)) ^ xor_key + (p % k)) % k
        for i in m
    )


def ghoul_cipher(message, p, k, key):
    message = bytearray(
        (m + p ** k + k ** p - p) % k
        for m in xor_cipher(message.encode(), key.encode())
    )
    return alg(message, get_xor_key(key), p, k)


def ghoul_decipher(cipher_message, p, k, key):
    cipher_message = bytearray(
        (cm - p ** k - k ** p + p) % k
        for cm in alg(cipher_message, get_xor_key(key), p, k)
    )
    try:
        cipher_message = xor_cipher(cipher_message, key.encode()).decode()
    except UnicodeDecodeError:
        return None
    return cipher_message


"""
def main():
  message = ".❤️.......................937, Sin que alguien dijera nada, sin dar su nombre, como un rompecabezas resolviéndose por sí mismo. De4th==■ Con una mirada fría y vivida, estaba el Dios de la muerte. 𝔤𝔥𝔬𝔲𝔩..."
  k = 104729
  n = 256
  # LLave generada aleatoriamente
  key = "frU0v^5MG%b@uHhQ5n5!jQ%Ok^BlVaFM4#^6HEDU"

  print(message)
  cm = ghoul_cipher(b64e(message), k, n, key)
  #print(list(cm))
  print(''.join(list(chr(c % n) for c in list(cm))))
  dm = ghoul_decipher(cm, k, n, "frU0v^5MG%b@uHhQ5n5!jQ%Ok^BlVaFM4#^6HEDU")
  print(b64d(dm) if dm is not None else "Clave Incorrecta")

if __name__ == '__main__':
  main()
"""
