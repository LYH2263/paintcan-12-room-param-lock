async function requestJSON(method, path, body) {
  const opts = { method, headers: {} }
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }
  const r = await fetch(path, opts)
  if (!r.ok) throw new Error(await r.text())
  return r.status === 204 ? null : r.json()
}
export const getJSON = (p) => requestJSON('GET', p)
export const postJSON = (p, b) => requestJSON('POST', p, b)
export const putJSON = (p, b) => requestJSON('PUT', p, b)
export const patchJSON = (p, b) => requestJSON('PATCH', p, b)
export const deleteJSON = (p) => requestJSON('DELETE', p)

export function errMessage(e) {
  try {
    const d = JSON.parse(e.message)
    return d.detail || e.message
  } catch {
    return e.message
  }
}
