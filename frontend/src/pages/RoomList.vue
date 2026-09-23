<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/rooms')).items })
</script>
<template><div class="page"><h1>房间</h1>
<table><tr><th>名称</th><th>尺寸 (m)</th><th>状态</th><th></th></tr>
<tr v-for="r in items" :key="r.id">
  <td>{{ r.name }}</td>
  <td>{{ r.length }}×{{ r.width }}×{{ r.height }}</td>
  <td>
    <span v-if="r.locked" class="lock-badge" title="参数已锁定，尺寸与门窗只读">🔒 已锁定</span>
    <span v-else class="unlock-badge">未锁定</span>
  </td>
  <td><router-link :to="`/rooms/${r.id}`">详情</router-link></td>
</tr></table></div></template>
