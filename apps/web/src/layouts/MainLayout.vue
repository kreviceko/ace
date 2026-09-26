<template>
  <q-layout view="hHh LpR lFf" class="bg-dark-page text-white">
    <q-header elevated class="bg-dark text-white" height-hint="64">
      <q-toolbar class="q-px-md" style="min-height: 64px">
        <div class="row items-center q-gutter-sm">
          <q-avatar size="36px" color="primary" text-color="white" font-size="18px">A</q-avatar>
          <div>
            <div class="text-subtitle1 text-weight-bold" style="line-height: 1.1">ACE Studio</div>
            <div class="text-caption text-grey-5">Local ACE-Step 1.5</div>
          </div>
        </div>

        <q-space />

        <q-tabs
          dense
          active-color="primary"
          indicator-color="primary"
          class="text-grey-4 gt-xs"
          narrow-indicator
        >
          <q-route-tab to="/" label="Create" icon="music_note" />
          <q-route-tab to="/library" label="Library" icon="library_music" />
          <q-route-tab to="/lyrics" label="Lyrics" icon="edit_note" />
          <q-route-tab to="/settings" label="Settings" icon="settings" />
        </q-tabs>

        <q-space />

        <div class="row items-center q-gutter-sm q-mr-md">
          <span class="engine-dot" :class="store.engine.ok ? 'ok' : 'down'" />
          <span class="text-caption text-grey-4">
            {{ store.engine.loading ? 'Checking…' : store.engine.ok ? 'Engine online' : 'Engine offline' }}
          </span>
          <q-btn flat dense round icon="refresh" @click="store.refreshHealth()" />
        </div>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { onMounted } from 'vue'
import { useStudioStore } from '@/stores/studio'

const store = useStudioStore()
onMounted(() => {
  store.refreshHealth()
  store.refreshLibrary().catch(() => {})
})
</script>
