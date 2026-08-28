# -*- coding: utf-8 -*-
"""服务端 AES 解密工具：解密前端 crypto.ts 加密的请求载荷。

安全纪律：密钥由会话临时协商，解密后即刻使用、不落日志不落盘。
"""

import base64
import hashlib

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def _derive_key(session_key: str) -> bytes:
    """由会话密钥派生 32 字节 AES-256 密钥（与前端 SHA-256 口径一致）。"""
    return hashlib.sha256(session_key.encode("utf-8")).digest()


def decrypt_payload(encrypted_b64: str, session_key: str) -> bytes:
    """解密 Base64 编码的 AES 密文，返回原始字节（由调用方 JSON 解析）。

    采用 AES-256-CBC + PKCS7（crypto-js 默认输出格式），
    IV 取密文前 16 字节（前端约定拼接传输）。
    """
    raw = base64.b64decode(encrypted_b64)
    iv, body = raw[:16], raw[16:]

    cipher = Cipher(algorithms.AES(_derive_key(session_key)), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(body) + decryptor.finalize()

    # 去除 PKCS7 填充
    pad_len = padded[-1]
    return padded[:-pad_len]
