/**
 * Secure Vault - Client-Side Encrypted Storage
 * Uses Web Crypto API for AES-256-GCM encryption.
 * Sensitive data (passwords, API keys) never leaves the browser unencrypted.
 */

const VAULT_PREFIX = 'sv_';
const SALT_KEY = 'sv_salt';
const ITERATIONS = 100000;

class SecureVault {
  constructor() {
    this._key = null;
    this._initialized = false;
  }

  async initialize(passphrase = 'super-manager-default-key') {
    if (this._initialized) return;

    let salt = localStorage.getItem(SALT_KEY);
    if (!salt) {
      const saltBytes = crypto.getRandomValues(new Uint8Array(16));
      salt = btoa(String.fromCharCode(...saltBytes));
      localStorage.setItem(SALT_KEY, salt);
    }

    const saltBytes = Uint8Array.from(atob(salt), c => c.charCodeAt(0));
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(passphrase),
      'PBKDF2',
      false,
      ['deriveKey']
    );

    this._key = await crypto.subtle.deriveKey(
      { name: 'PBKDF2', salt: saltBytes, iterations: ITERATIONS, hash: 'SHA-256' },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );

    this._initialized = true;
  }

  async encrypt(plaintext) {
    if (!this._key) await this.initialize();

    const iv = crypto.getRandomValues(new Uint8Array(12));
    const encoded = new TextEncoder().encode(plaintext);
    const ciphertext = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      this._key,
      encoded
    );

    const combined = new Uint8Array(iv.length + ciphertext.byteLength);
    combined.set(iv);
    combined.set(new Uint8Array(ciphertext), iv.length);

    return btoa(String.fromCharCode(...combined));
  }

  async decrypt(ciphertextB64) {
    if (!this._key) await this.initialize();

    const combined = Uint8Array.from(atob(ciphertextB64), c => c.charCodeAt(0));
    const iv = combined.slice(0, 12);
    const ciphertext = combined.slice(12);

    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      this._key,
      ciphertext
    );

    return new TextDecoder().decode(decrypted);
  }

  async store(key, value) {
    const encrypted = await this.encrypt(value);
    localStorage.setItem(VAULT_PREFIX + key, encrypted);
  }

  async retrieve(key) {
    const encrypted = localStorage.getItem(VAULT_PREFIX + key);
    if (!encrypted) return null;
    try {
      return await this.decrypt(encrypted);
    } catch {
      return null;
    }
  }

  listKeys() {
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith(VAULT_PREFIX)) {
        keys.push(k.slice(VAULT_PREFIX.length));
      }
    }
    return keys;
  }

  remove(key) {
    localStorage.removeItem(VAULT_PREFIX + key);
  }

  clear() {
    const keys = this.listKeys();
    keys.forEach(k => localStorage.removeItem(VAULT_PREFIX + k));
    localStorage.removeItem(SALT_KEY);
    this._key = null;
    this._initialized = false;
  }
}

// Singleton
const vault = new SecureVault();
export default vault;
export { SecureVault };
