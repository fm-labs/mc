export function bufferToBase64url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let str = "";
  for (const b of bytes) str += String.fromCharCode(b);
  return btoa(str)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

export function base64urlToBuffer(base64url: string): ArrayBuffer {
  const padding = "=".repeat((4 - (base64url.length % 4)) % 4);
  const base64 = (base64url + padding)
    .replace(/-/g, "+")
    .replace(/_/g, "/");
  const str = atob(base64);
  const buffer = new ArrayBuffer(str.length);
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < str.length; i++) bytes[i] = str.charCodeAt(i);
  return buffer;
}
