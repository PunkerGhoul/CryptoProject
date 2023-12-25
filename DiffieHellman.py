import secrets

class DiffieHellman:
    """
    Implementación del algoritmo de Diffie-Hellman para intercambio de claves.
    """
    def __init__(self):
        self.g = self.generate_prime_number()
        self.p = self.generate_prime_number()

    def generate_prime_number(self):
        """
        Genera un número primo aleatorio.
        """
        while True:
            #num = secrets.randbits(40)
            # valor aleatorio de numero primo menor a 1000
            num = secrets.randbits(9)
            if self.is_prime(num):
                return num

    def is_prime(self, num):
        """
        Determina si un número es primo o no.
        """
        if num < 2:
            return False
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                return False
        return True

    def generate_public_key(self, secret_key):
        """
        Genera una clave pública a partir de una clave secreta.
        """
        return pow(self.g, secret_key, self.p)

    def generate_shared_key(self, public_key, secret_key):
        """
        Genera una clave compartida a partir de una clave pública y una clave secreta.
        """
        return pow(public_key, secret_key, self.p)
