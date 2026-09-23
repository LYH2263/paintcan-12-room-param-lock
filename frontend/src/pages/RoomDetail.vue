<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { delJSON, getJSON, patchJSON, postJSON } from '../api'

const route = useRoute()
const detail = ref(null)
const est = ref(null)
const error = ref('')
const note = ref('')

// 尺寸编辑
const dims = ref({ length: '', width: '', height: '' })
// 新增门窗
const draft = ref({ kind: 'door', w: '', h: '' })
// 各行门窗的编辑草稿
const edits = ref({})

const locked = computed(() => !!detail.value?.room?.locked)

const load = async () => {
  error.value = ''
  detail.value = await getJSON(`/api/rooms/${route.params.id}`)
  const r = detail.value.room
  dims.value = { length: r.length, width: r.width, height: r.height }
  edits.value = Object.fromEntries(detail.value.openings.map(o =>
    [o.id, { kind: o.kind, w: o.w, h: o.h }]))
  est.value = await postJSON('/api/estimate', { room_id: +route.params.id, persist: false })
}

const showError = (e) => {
  // 锁定时后端 409：消息中已点名只读的尺寸/开洞字段
  note.value = ''
  error.value = e?.message || String(e)
}
const clearMsg = () => { error.value = ''; note.value = '' }

const toggleLock = async () => {
  try {
    const next = !locked.value
    // 列表与详情共用的 room.locked 字段在这里更新
    detail.value.room = await postJSON(`/api/rooms/${route.params.id}/lock`, { locked: next })
    clearMsg()
  } catch (e) { showError(e) }
}

const saveDimensions = async () => {
  try {
    detail.value.room = await patchJSON(`/api/rooms/${route.params.id}/dimensions`, {
      length: +dims.value.length, width: +dims.value.width, height: +dims.value.height,
    })
    await refreshEstimate()
    note.value = '尺寸已保存'
    error.value = ''
  } catch (e) { showError(e) }
}

const addOpening = async () => {
  try {
    await postJSON(`/api/rooms/${route.params.id}/openings`, {
      kind: draft.value.kind, w: +draft.value.w, h: +draft.value.h,
    })
    draft.value = { kind: 'door', w: '', h: '' }
    await reload()
    note.value = '门窗已添加'
  } catch (e) { showError(e) }
}

const saveOpening = async (o) => {
  const f = edits.value[o.id]
  try {
    await patchJSON(`/api/openings/${o.id}`, { kind: f.kind, w: +f.w, h: +f.h })
    await reload()
    note.value = '门窗已更新'
  } catch (e) { showError(e) }
}

const removeOpening = async (o) => {
  try {
    await delJSON(`/api/openings/${o.id}`)
    await reload()
    note.value = '门窗已删除'
  } catch (e) { showError(e) }
}

const persistEstimate = async () => {
  try {
    const out = await postJSON('/api/estimate', { room_id: +route.params.id, persist: true })
    note.value = `估算已写入记录（run #${out.run_id}）：${out.liters} L`
    error.value = ''
  } catch (e) { showError(e) }
}

const refreshEstimate = async () => {
  est.value = await postJSON('/api/estimate', { room_id: +route.params.id, persist: false })
}
const reload = async () => {
  detail.value = await getJSON(`/api/rooms/${route.params.id}`)
  edits.value = Object.fromEntries(detail.value.openings.map(o =>
    [o.id, { kind: o.kind, w: o.w, h: o.h }]))
  await refreshEstimate()
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<template><div class="page" v-if="detail">
  <h1>{{ detail.room.name }}
    <span v-if="locked" class="lock-badge">🔒 已锁定</span>
    <span v-else class="unlock-badge">未锁定</span>
  </h1>
  <p class="lock-hint" v-if="locked">房间参数已锁定：长、宽、高与所有门窗字段只读，修改将被整单拒绝。估算仍可正常发起与写入。</p>
  <button @click="toggleLock">{{ locked ? '解锁房间' : '锁定房间' }}</button>

  <p v-if="error" class="msg-error">⛔ {{ error }}</p>
  <p v-if="note" class="msg-ok">{{ note }}</p>

  <p>净面积 {{ est?.net_m2 }} m² · 需漆 <span class="hero-num">{{ est?.liters }} L</span></p>
  <button @click="persistEstimate">保存本次估算到记录 (persist=true)</button>

  <h2>尺寸</h2>
  <fieldset :disabled="locked" class="locked-fieldset">
    <label>长 <input v-model.number="dims.length" type="number" step="0.01" /></label>
    <label>宽 <input v-model.number="dims.width" type="number" step="0.01" /></label>
    <label>高 <input v-model.number="dims.height" type="number" step="0.01" /></label>
    <button @click="saveDimensions" :disabled="locked">保存尺寸</button>
  </fieldset>
  <p v-if="locked" class="readonly-note">只读字段：length、width、height</p>

  <h2>门窗开洞</h2>
  <table>
    <tr v-for="o in detail.openings" :key="o.id">
      <td>
        <fieldset :disabled="locked" class="locked-fieldset inline">
          <select v-model="edits[o.id].kind">
            <option value="door">门 door</option>
            <option value="window">窗 window</option>
          </select>
          <label>宽 <input v-model.number="edits[o.id].w" type="number" step="0.01" /></label>
          <label>高 <input v-model.number="edits[o.id].h" type="number" step="0.01" /></label>
          <button @click="saveOpening(o)" :disabled="locked">保存</button>
          <button class="btn-danger" @click="removeOpening(o)" :disabled="locked">删除</button>
        </fieldset>
      </td>
    </tr>
  </table>
  <p v-if="locked" class="readonly-note">只读字段：门窗 kind、w、h（增删改均被拒绝）</p>

  <fieldset :disabled="locked" class="locked-fieldset">
    <legend>新增门窗</legend>
    <select v-model="draft.kind">
      <option value="door">门 door</option>
      <option value="window">窗 window</option>
    </select>
    <label>宽 <input v-model.number="draft.w" type="number" step="0.01" /></label>
    <label>高 <input v-model.number="draft.h" type="number" step="0.01" /></label>
    <button @click="addOpening" :disabled="locked">添加</button>
  </fieldset>
</div></template>
