<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/rooms')).items })
</script>
<template><div class="page"><h1>房间</h1>
<table>
  <thead><tr><th>房间</th><th>长×宽×高</th><th>状态</th><th></th></tr></thead>
  <tbody>
    <tr v-for="r in items" :key="r.id" :class="{ 'row-locked': r.locked }">
      <td>{{ r.name }}</td>
      <td>{{ r.length }}×{{ r.width }}×{{ r.height }}</td>
      <td>
        <span v-if="r.locked" class="badge badge-locked">🔒 已锁定</span>
        <span v-else class="badge badge-unlocked">未锁定</span>
      </td>
      <td><router-link :to="`/rooms/${r.id}`">详情</router-link></td>
    </tr>
  </tbody>
</table></div></template>
