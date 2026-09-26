<template>
  <q-layout view="hHh LpR lFf" class="text-white">
    <q-header class="ace-shell-header" height-hint="68">
      <q-toolbar class="q-px-md" style="min-height: 68px">
        <q-btn flat dense round icon="menu" class="lt-md" aria-label="Menu" @click="leftDrawer = !leftDrawer" />

        <div class="row items-center q-gutter-sm q-ml-xs">
          <div class="ace-brand-mark">A</div>
          <div>
            <div class="text-weight-bold" style="line-height: 1.1; letter-spacing: -0.02em">ACE Studio</div>
            <div class="text-caption" style="color: var(--ace-faint)">Local music creation</div>
          </div>
        </div>

        <q-space />

        <q-tabs dense class="ace-nav-tabs gt-sm" active-color="primary" indicator-color="transparent">
          <q-route-tab v-for="link in links" :key="link.to" :to="link.to" :label="link.label" :icon="link.icon" />
        </q-tabs>

        <q-space class="gt-sm" />

        <div class="ace-status-pill">
          <span class="engine-dot" :class="store.engine.ok ? 'ok' : 'down'" />
          <div class="column gt-xs" style="line-height: 1.15">
            <span class="text-caption" style="color: var(--ace-muted)">
              {{ store.engine.loading ? 'Checking…' : store.engine.ok ? 'Engine online' : 'Engine offline' }}
            </span>
            <span v-if="modelCaption" class="text-caption" style="color: var(--ace-faint)">{{ modelCaption }}</span>
          </div>
          <q-btn flat dense round size="sm" icon="refresh" @click="store.refreshHealth()" />
        </div>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawer" bordered overlay behavior="mobile" class="ace-drawer text-white">
      <div class="q-pa-md row items-center q-gutter-sm">
        <div class="ace-brand-mark">A</div>
        <div class="text-weight-bold">ACE Studio</div>
      </div>
      <q-list padding>
        <q-item
          v-for="link in links"
          :key="link.to"
          clickable
          v-ripple
          :to="link.to"
          exact
          @click="leftDrawer = false"
        >
          <q-item-section avatar><q-icon :name="link.icon" /></q-item-section>
          <q-item-section>{{ link.label }}</q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useStudioStore } from '@/stores/studio'

const store = useStudioStore()
const leftDrawer = ref(false)

const links = [
  { to: '/', label: 'Create', icon: 'music_note' },
  { to: '/library', label: 'Library', icon: 'library_music' },
  { to: '/lyrics', label: 'Lyrics', icon: 'edit_note' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
]

const modelCaption = computed(() => {
  const m = store.engine.detail?.models
  if (!m) return ''
  const dit = m.loaded_dit || m.configured_dit || m.default_model
  if (!dit) return ''
  const state = m.models_initialized ? 'loaded' : 'configured'
  return `${state}: ${dit}`
})

onMounted(() => {
  store.refreshHealth()
  store.refreshLibrary().catch(() => {})
})
</script>
