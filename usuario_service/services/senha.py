# Camada Service (apoio): geração e conferência do hash de senha.
# Usa só a biblioteca padrão (hashlib.pbkdf2_hmac). A senha em texto puro
# nunca é gravada no banco.

import hashlib
import hmac
import os

ALGORITMO = "sha256"
ITERACOES = 100_000
TAMANHO_SALT = 16
SEPARADOR = "$"


def _calcular_hash(senha: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac(ALGORITMO, senha.encode("utf-8"), salt, ITERACOES).hex()


def gerar_hash_senha(senha: str) -> str:
    """Devolve "salt$hash" em hexadecimal, que é o que fica gravado no banco."""
    # O salt é aleatório por usuário: duas senhas iguais geram hashes diferentes.
    salt = os.urandom(TAMANHO_SALT)
    return salt.hex() + SEPARADOR + _calcular_hash(senha, salt)


def senha_confere(senha: str, senha_hash: str) -> bool:
    """Refaz o hash com o salt guardado e compara com o hash guardado."""
    salt_hex, hash_guardado = senha_hash.split(SEPARADOR)
    hash_calculado = _calcular_hash(senha, bytes.fromhex(salt_hex))
    # compare_digest leva sempre o mesmo tempo, o que evita ataque por tempo de resposta.
    return hmac.compare_digest(hash_calculado, hash_guardado)
