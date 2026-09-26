<template>
  <q-page class="q-pa-md">
    <div class="ace-panel q-pa-md">
      <div class="row items-center justify-between q-mb-md">
        <div>
          <div class="text-h6">Library</div>
          <div class="text-caption text-grey-5">Local generations saved under data/library</div>
        </div>
        <q-btn outline color="primary" icon="refresh" label="Refresh" @click="reload" />
      </div>

      <q-table
        dark
        flat
        :rows="store.library"
        :columns="columns"
        row-key="id"
        :loading="loading"
        binary-state-sort
      >
        <template #body-cell-actions="props">
          <q-td :props="props">
            <q-btn flat dense round icon="play_arrow" @click="play(props.row)" />
            <q-btn flat dense round icon="download" :href="api.audioUrl(props.row.id)" target="_blank" />
            <q-btn flat dense round icon="edit" @click="reuse(props.row)" />
            <q-btn flat dense round icon="delete" color="negative" @click="remove(props.row)" />
          </q-td>
        </template>
      </q-table>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useStudioStore } from '@/stores/studio'
import { api } from '@/api/client'

const store = useStudioStore()
const router = useRouter()
const $q = useQuasar()
const loading = ref(false)

const columns = [
  { name: 'created_at', label: 'Created', field: (r) => r.created_at?.slice(0, 19), sortable: true },
  { name: 'mode', label: 'Mode', field: 'mode', sortable: true },
  { name: 'title', label: 'Title', field: 'title', align: 'left', sortable: true },
  { name: 'actions', label: '', field: 'id', align: 'right' },
]

async function reload() {
  loading.value = true
  try {
    await store.refreshLibrary()
  } finally {
    loading.value = false
  }
}

function play(row) {
  store.lastResult = row
  router.push('/')
}

function reuse(row) {
  store.loadFromLibrary(row)
  router.push('/')
}

async function remove(row) {
  $q.dialog({
    title: 'Delete song?',
    message: row.title,
    cancel: true,
    persistent: true,
  }).onOk(async () => {
    try {
      await api.deleteSong(row.id)
      if (store.lastResult?.id === row.id) store.lastResult = null
      await reload()
      $q.notify({ type: 'positive', message: 'Deleted' })
    } catch (err) {
      $q.notify({ type: 'negative', message: err.message })
    }
  })
}

onMounted(reload)
</script>
