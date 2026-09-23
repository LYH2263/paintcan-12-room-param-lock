async function requestJSON(path, options) {
  const r = await fetch(path, options)
  if (!r.ok) {
    let payload = null
    try { payload = await r.json() } catch { /* 非 JSON 错误体 */ }
    const detail = payload?.detail
    const message = typeof detail === 'object' && detail?.message
      ? detail.message
      : (typeof detail === 'string' ? detail : `请求失败 (${r.status})`)
    const err = new Error(message)
    err.status = r.status
    err.payload = payload
    throw err
  }
  if (r.status === 204) return null
  return r.json()
}
export function getJSON(path) { return requestJSON(path) }
export function postJSON(path, body) {
  return requestJSON(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) })
}
export function patchJSON(path, body) {
  return requestJSON(path, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
}
export function delJSON(path) {
  return requestJSON(path, { method: 'DELETE' })
}
