const b64e = (s) => {
  return btoa(s).toString();
};

const b64d = (s) => {
  return atob(s).toString();
};

function get_xor_key(key) {
  let xorKey = 0;
  for (let i = 0; i < key.length; i++) {
    xorKey ^= key.charCodeAt(i);
  }
  return xorKey;
}

function xor_cipher(message, key) {
  return message.map((byte, index) => byte ^ key.charCodeAt(index % key.length));
}

function alg(m, xorKey, p, k) {
  let temp = p - Math.pow(k, p) * Math.pow(p, k) + p - Math.pow(p, k);
  let result = [];
  for (let i = 0; i < m.length; i++) {
    result.push((m[i] ^ temp % (k + 1) ^ (xorKey + (p % k))) % k);
  }
  return new Uint8Array(result);
}

function ghoul_cipher(message, p, k, key) {
  let encodedMessage = [];
  let xorKey = get_xor_key(key);
  for (let i = 0; i < message.length; i++) {
    let cipheredByte = (message[i] + Math.pow(p, k) + Math.pow(k, p) - p) % k;
    encodedMessage.push(cipheredByte);
  }
  let cipheredMessage = xor_cipher(encodedMessage, key);
  return cipheredMessage;
}

function ghoul_decipher(cipher_message, p, k, key) {
  let xorKey = get_xor_key(key);
  let decodedMessage = xor_cipher(cipher_message, key);
  let decipheredMessage = [];
  for (let i = 0; i < decodedMessage.length; i++) {
    decipheredMessage.push((decodedMessage[i] - xorKey - (p % k) + k) % k);
  }
  try {
    decipheredMessage = new Uint8Array(decipheredMessage);
    return decipheredMessage.reduce(
      (str, byte) => str + String.fromCharCode(byte),
      ""
    );
  } catch (error) {
    return null;
  }
}
