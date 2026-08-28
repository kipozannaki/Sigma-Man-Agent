/**
 * 端到端 AES 加密：请求发出前对消息载荷加密。
 * 密钥由本次会话临时生成（存在内存），刷新即失效，不持久化。
 *
 * 依赖：npm i crypto-js @types/crypto-js
 */
import CryptoJS from "crypto-js";

/** 会话级临时密钥：每个标签页生命周期内只生成一次 */
const sessionKey = CryptoJS.lib.WordArray.random(256 / 24).toString();

/** 加密消息载荷，返回可传输的密文字符串 */
export function encryptPayload(payload: object): string {
  return CryptoJS.AES.encrypt(JSON.stringify(payload), sessionKey).toString();
}

/** 解密服务端返回的密文（同会话内） */
export function decryptPayload<T>(ciphertext: string): T {
  const bytes = CryptoJS.AES.decrypt(ciphertext, sessionKey);
  return JSON.parse(bytes.toString(CryptoJS.enc.Utf8));
}

/** 密钥不导出原始值，仅提供指纹供日志对账 */
export function keyFingerprint(): string {
  return CryptoJS.SHA256(sessionKey).toString().slice(0, 8);
}
