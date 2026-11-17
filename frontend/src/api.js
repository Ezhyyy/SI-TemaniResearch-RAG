const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api';

export async function api(path, { token, method = 'GET', body, formData } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body) headers['Content-Type'] = 'application/json';
  const response = await fetch(`${API_URL}${path}`, {
    method, headers, body: formData || (body ? JSON.stringify(body) : undefined),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || 'Permintaan gagal.');
  return data;
}

export const documentFileUrl = (id) => `${API_URL}/documents/${id}/file`;

export async function openDocumentFile(id, token) {
  const response = await fetch(documentFileUrl(id), { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || 'PDF tidak dapat dibuka.');
  }
  const url = URL.createObjectURL(await response.blob());
  window.open(url, '_blank', 'noopener,noreferrer');
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

