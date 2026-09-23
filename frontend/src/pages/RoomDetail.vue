<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON, postJSON, putJSON, patchJSON, deleteJSON, errMessage } from '../api'

const route = useRoute()
const detail = ref(null)
const est = ref(null)
const saved = ref(null)
const error = ref('')
const saving = ref(false)

const dims = ref({ length: null, width: null, height: null })
const newOpening = ref({ kind: 'door', w: null, h: null })
const editOpening = ref({})

const roomId = () => +route.params.id
const locked = () => !!detail.value?.room.locked

async function load() {
  error.value = ''
  saved.value = null
  detail.value = await getJSON(`/api/rooms/${route.params.id}`)
  est.value = await postJSON('/api/estimate', { room_id: roomId(), persist: false })
  dims.value = {
    length: detail.value.room.length,
    width: detail.value.room.width,
    height: detail.value.room.height,
  }
  editOpening.value = Object.fromEntries(
    detail.value.openings.map((o) => [o.id, { kind: o.kind, w: o.w, h: o.h }]))
}

async function guard(fn) {
  saving.value = true
  error.value = ''
  try {
    await fn()
  } catch (e) {
    error.value = errMessage(e)
  } finally {
    saving.value = false
  }
}

async function toggleLock() {
  await guard(async () => {
    detail.value = await postJSON(`/api/rooms/${roomId()}/lock`, { locked: !locked() })
    await load()
  })
}

async function saveDimensions() {
  await guard(async () => {
    detail.value = await putJSON(`/api/rooms/${roomId()}/dimensions`, { ...dims.value })
    await load()
  })
}

async function addOpening() {
  await guard(async () => {
    detail.value = await postJSON(`/api/rooms/${roomId()}/openings`, { ...newOpening.value })
    newOpening.value = { kind: 'door', w: null, h: null }
    await load()
  })
}

async function patchOpening(o) {
  const b = editOpening.value[o.id] || {}
  await guard(async () => {
    detail.value = await patchJSON(`/api/openings/${o.id}`, {
      kind: b.kind ?? o.kind, w: b.w ?? o.w, h: b.h ?? o.h,
    })
    await load()
  })
}

async function removeOpening(o) {
  await guard(async () => {
    await deleteJSON(`/api/openings/${o.id}`)
    await load()
  })
}

async function saveEstimate() {
  await guard(async () => {
    saved.value = await postJSON('/api/estimate', { room_id: roomId(), persist: true })
  })
}

onMounted(load)
watch(() => route.params.id, load)
</script>
<template><div class="page" v-if="detail">
  <h1>
    {{ detail.room.name }}
    <span v-if="locked()" class="badge badge-locked">🔒 已锁定</span>
    <span v-else class="badge badge-unlocked">未锁定</span>
  </h1>

  <p class="actions">
    <button v-if="!locked()" class="secondary" :disabled="saving" @click="toggleLock">🔒 锁定房间</button>
    <button v-else :disabled="saving" @click="toggleLock">🔓 解锁房间</button>
  </p>

  <p v-if="error" class="error-text">⚠ {{ error }}</p>

  <section>
    <h2>实时估算（persist=false）</h2>
    <p>净面积 {{ est?.net_m2 }} m² · 需漆 <span class="hero-num">{{ est?.liters }} L</span>
       （{{ est?.coats }} 遍 · {{ est?.coverage }} m²/L）</p>
    <p>
      <button :disabled="saving" @click="saveEstimate">💾 保存估算（persist=true）</button>
      <span v-if="saved" class="saved-note">已写入 run #{{ saved.run_id }}：{{ saved.liters }} L / 净 {{ saved.net_m2 }} m²</span>
    </p>
  </section>

  <section>
    <h2>尺寸</h2>
    <p v-if="locked()" class="readonly-note">房间已锁定，尺寸字段 length、width、height 只读。</p>
    <label>长 <input type="number" step="0.01" v-model.number="dims.length" :disabled="locked() || saving" /></label>
    <label>宽 <input type="number" step="0.01" v-model.number="dims.width" :disabled="locked() || saving" /></label>
    <label>高 <input type="number" step="0.01" v-model.number="dims.height" :disabled="locked() || saving" /></label>
    <button :disabled="locked() || saving" @click="saveDimensions">保存尺寸</button>
  </section>

  <section>
    <h2>门窗洞口</h2>
    <p v-if="locked()" class="readonly-note">房间已锁定，开洞字段 openings.kind、openings.w、openings.h 只读，无法增删改。</p>
    <table>
      <thead><tr><th>类型</th><th>宽 (m)</th><th>高 (m)</th><th>面积 (m²)</th><th></th></tr></thead>
      <tbody>
        <tr v-for="o in detail.openings" :key="o.id">
          <td>
            <select v-model="editOpening[o.id].kind" :disabled="locked() || saving">
              <option value="door">door</option>
              <option value="window">window</option>
            </select>
          </td>
          <td><input type="number" step="0.01" v-model.number="editOpening[o.id].w"
                     :disabled="locked() || saving" /></td>
          <td><input type="number" step="0.01" v-model.number="editOpening[o.id].h"
                     :disabled="locked() || saving" /></td>
          <td>{{ (o.w * o.h).toFixed(2) }}</td>
          <td>
            <button :disabled="locked() || saving" @click="patchOpening(o)">改</button>
            <button class="secondary" :disabled="locked() || saving" @click="removeOpening(o)">删</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p class="actions">
      <select v-model="newOpening.kind" :disabled="locked() || saving">
        <option value="door">door</option>
        <option value="window">window</option>
      </select>
      <input type="number" step="0.01" placeholder="宽" v-model.number="newOpening.w" :disabled="locked() || saving" />
      <input type="number" step="0.01" placeholder="高" v-model.number="newOpening.h" :disabled="locked() || saving" />
      <button :disabled="locked() || saving" @click="addOpening">添加门窗</button>
    </p>
  </section>
</div></template>
