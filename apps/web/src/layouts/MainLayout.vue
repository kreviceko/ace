<template>
  <div class="studio-app">
    <aside class="studio-rail">
      <div class="studio-logo" title="ACE Studio">A</div>
      <nav class="studio-nav">
        <RouterLink v-for="link in links" :key="link.to" :to="link.to">
          <i class="material-icons">{{ link.icon }}</i>
          <span>{{ link.label }}</span>
        </RouterLink>
      </nav>
      <div style="flex: 1" />
      <button class="btn btn-ghost" style="padding: 10px; border-radius: 14px" title="Refresh engine" @click="store.refreshHealth()">
        <i class="material-icons" style="font-size: 18px">refresh</i>
      </button>
    </aside>

    <main class="studio-main">
      <div class="studio-topbar">
        <div />
        <div class="studio-chip">
          <span class="dot" :class="store.engine.ok ? 'on' : 'off'" />
          <span>{{ store.engine.loading ? 'Checking…' : store.engine.ok ? 'Engine online' : 'Engine offline' }}</span>
          <span v-if="modelCaption" style="color: var(--faint)">· {{ modelCaption }}</span>
        </div>
      </div>
      <RouterView />
    </main>

    <footer class="player-dock">
      <div v-if="currentAudioUrl">
        <div class="stage-title" style="font-size: 1rem">{{ currentTitle }}</div>
        <div v-if="metaLine" class="stage-meta" style="margin-bottom: 8px">{{ metaLine }}</div>
        <audio :src="currentAudioUrl" controls />
      </div>
      <div v-else class="empty">Generate a remix or track — playback lives here.</div>
      <div class="btn-row" v-if="currentAudioUrl">
        <a class="btn btn-ghost" :href="currentAudioUrl" target="_blank">Download</a>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useStudioStore } from '@/stores/studio'
import { api } from '@/api/client'

const store = useStudioStore()

const links = [
  { to: '/', label: 'Create', icon: 'graphic_eq' },
  { to: '/library', label: 'Library', icon: 'library_music' },
  { to: '/lyrics', label: 'Lyrics', icon: 'edit_note' },
  { to: '/settings', label: 'Settings', icon: 'tune' },
]

const modelCaption = computed(() => {
  const m = store.engine.detail?.models
  if (!m) return ''
  return m.loaded_dit || m.configured_dit || m.default_model || ''
})

const currentAudioUrl = computed(() => (store.lastResult?.id ? api.audioUrl(store.lastResult.id) : null))
const currentTitle = computed(() => store.lastResult?.title || 'Untitled')
const metaLine = computed(() => {
  const m = store.lastResult?.metas || {}
  const parts = []
  if (m.bpm) parts.push(`${m.bpm} BPM`)
  if (m.keyscale || m.key_scale) parts.push(m.keyscale || m.key_scale)
  if (m.duration) parts.push(`${m.duration}s`)
  return parts.join(' · ')
})

onMounted(() => {
  store.refreshHealth()
  store.refreshLibrary().catch(() => {})
})
</script>
