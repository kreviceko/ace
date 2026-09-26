<template>
  <q-page class="q-pa-md">
    <div class="ace-panel q-pa-md">
      <div class="row items-center justify-between q-mb-md">
        <div>
          <div class="ace-page-title">Library</div>
          <div class="ace-page-sub q-mt-xs">Local generations — export packs and stems</div>
        </div>
        <q-btn outline icon="refresh" label="Refresh" class="ace-btn-ghost" @click="reload" />
      </div>

      <q-banner v-if="!stemsReady" dense rounded class="bg-grey-10 text-grey-4 q-mb-md">
        Stem separation needs Demucs: <code>cd apps/api && uv sync --extra stems</code>
      </q-banner>

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
            <q-btn flat dense round icon="play_arrow" @click="play(props.row)">
              <q-tooltip>Play in Create</q-tooltip>
            </q-btn>
            <q-btn flat dense round icon="download" :href="api.audioUrl(props.row.id)" target="_blank">
              <q-tooltip>Download audio</q-tooltip>
            </q-btn>
            <q-btn flat dense round icon="folder_zip" :href="api.exportZipUrl(props.row.id)" target="_blank">
              <q-tooltip>Export ZIP pack</q-tooltip>
            </q-btn>
            <q-btn
              flat
              dense
              round
              icon="graphic_eq"
              :loading="stemBusy === props.row.id"
              :disable="!stemsReady"
              @click="makeStems(props.row)"
            >
              <q-tooltip>Separate stems (Demucs)</q-tooltip>
            </q-btn>
            <q-btn flat dense round icon="edit" @click="reuse(props.row)">
              <q-tooltip>Reuse in Create</q-tooltip>
            </q-btn>
            <q-btn flat dense round icon="content_cut" @click="editSlice(props.row)">
              <q-tooltip>Edit slice (waveform)</q-tooltip>
            </q-btn>
            <q-btn flat dense round icon="delete" color="negative" @click="remove(props.row)" />
          </q-td>
        </template>
      </q-table>
    </div>
  </q-page>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useStudioStore } from '@/stores/studio'
import { api } from '@/api/client'

const store = useStudioStore()
const router = useRouter()
const $q = useQuasar()
const loading = ref(false)
const stemBusy = ref('')

const stemsReady = computed(() => Boolean(store.engine.detail?.features?.demucs_stems))

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
    await store.refreshHealth()
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

function editSlice(row) {
  store.loadFromLibrary(row)
  store.mode = 'edit'
  store.form.repainting_start = 0
  store.form.repainting_end = 0
  // Use library audio as edit source via URL marker the Create page can load
  store.editSourceUrl = api.audioUrl(row.id)
  router.push('/')
}

async function makeStems(row) {
  stemBusy.value = row.id
  try {
    const res = await api.separateStems(row.id)
    $q.notify({
      type: 'positive',
      message: `Stems ready: ${(res.stems || []).join(', ')}`,
      actions: [{ label: 'Download', color: 'white', handler: () => window.open(api.stemsZipUrl(row.id), '_blank') }],
      timeout: 8000,
    })
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message, timeout: 10000 })
  } finally {
    stemBusy.value = ''
  }
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
