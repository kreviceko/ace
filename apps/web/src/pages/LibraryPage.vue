<template>
  <div>
    <header style="margin-bottom: 22px" class="row items-start justify-between">
      <div>
        <div class="studio-kicker">Collection</div>
        <h1 class="studio-title">Library</h1>
        <p class="studio-lead">Export packs, separate stems, reopen takes into Create.</p>
      </div>
      <button class="btn btn-ghost" type="button" @click="reload">Refresh</button>
    </header>

    <div v-if="!stemsReady" class="notice warn">
      Stem separation needs Demucs — <code>cd apps/api && uv sync --extra stems</code>
    </div>

    <section class="glass glass-pad">
      <div v-if="loading" style="color: var(--muted)">Loading…</div>
      <div v-else-if="!store.library.length" style="color: var(--faint); padding: 24px 8px">
        No songs yet. Generate a remix to fill this space.
      </div>
      <div v-else class="lib-grid">
        <article v-for="row in store.library" :key="row.id" class="lib-card">
          <div class="lib-art" />
          <div class="lib-body">
            <h3>{{ row.title }}</h3>
            <p>{{ row.mode }} · {{ row.created_at?.slice(0, 19) }}</p>
            <div class="btn-row" style="margin-top: 12px">
              <button class="btn btn-soft" type="button" @click="play(row)">Play</button>
              <a class="btn btn-ghost" :href="api.audioUrl(row.id)" target="_blank">Audio</a>
              <a class="btn btn-ghost" :href="api.exportZipUrl(row.id)" target="_blank">ZIP</a>
              <button
                class="btn btn-ghost"
                type="button"
                :disabled="!stemsReady || stemBusy === row.id"
                @click="makeStems(row)"
              >
                {{ stemBusy === row.id ? 'Stems…' : 'Stems' }}
              </button>
              <button class="btn btn-ghost" type="button" @click="editSlice(row)">Edit</button>
              <button class="btn btn-ghost" type="button" @click="reuse(row)">Reuse</button>
              <button class="btn btn-danger" type="button" @click="remove(row)">Delete</button>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
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

function remove(row) {
  $q.dialog({ title: 'Delete song?', message: row.title, cancel: true, persistent: true }).onOk(async () => {
    try {
      await api.deleteSong(row.id)
      if (store.lastResult?.id === row.id) store.lastResult = null
      await reload()
    } catch (err) {
      $q.notify({ type: 'negative', message: err.message })
    }
  })
}

onMounted(reload)
</script>

<style scoped>
.lib-grid {
  display: grid;
  gap: 14px;
}
.lib-card {
  display: grid;
  grid-template-columns: 96px 1fr;
  gap: 16px;
  padding: 12px;
  border-radius: 18px;
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.02);
}
.lib-art {
  border-radius: 14px;
  background:
    radial-gradient(circle at 30% 30%, rgba(196, 245, 66, 0.35), transparent 45%),
    radial-gradient(circle at 70% 60%, rgba(124, 108, 240, 0.45), transparent 50%),
    #0a0b10;
}
.lib-body h3 {
  margin: 0 0 4px;
  font-size: 1.05rem;
  letter-spacing: -0.02em;
}
.lib-body p {
  margin: 0;
  color: var(--faint);
  font-size: 0.82rem;
}
@media (max-width: 700px) {
  .lib-card {
    grid-template-columns: 1fr;
  }
  .lib-art {
    height: 120px;
  }
}
</style>
