<template>
  <q-page class="q-pa-md">
    <div class="ace-panel q-pa-md" style="max-width: 760px">
      <div class="text-h6 q-mb-md">Settings</div>

      <q-list dark bordered class="rounded-borders">
        <q-item>
          <q-item-section>
            <q-item-label>Engine status</q-item-label>
            <q-item-label caption>
              {{ store.engine.ok ? 'Online' : 'Offline' }}
              <span v-if="store.engine.error"> — {{ store.engine.error }}</span>
            </q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-btn outline dense color="primary" label="Recheck" @click="store.refreshHealth()" />
          </q-item-section>
        </q-item>

        <q-item>
          <q-item-section>
            <q-item-label>API base</q-item-label>
            <q-item-label caption>Dev proxy uses /api → :8787</q-item-label>
          </q-item-section>
        </q-item>

        <q-item>
          <q-item-section>
            <q-item-label>Hardware notes</q-item-label>
            <q-item-label caption>
              This laptop (≈15GB RAM / 8GB VRAM) is tight for ACE-Step weight loading. Prefer a desktop with 32GB+ RAM
              and a larger pagefile. Set ACESTEP_INIT_LLM=false for DiT-only if needed.
            </q-item-label>
          </q-item-section>
        </q-item>
      </q-list>

      <pre class="q-mt-md text-caption text-grey-5" style="white-space: pre-wrap">{{ pretty }}</pre>
    </div>
  </q-page>
</template>

<script setup>
import { computed } from 'vue'
import { useStudioStore } from '@/stores/studio'

const store = useStudioStore()
const pretty = computed(() => JSON.stringify(store.engine.detail, null, 2))
</script>
