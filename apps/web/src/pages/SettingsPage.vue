<template>
  <q-page class="q-pa-md">
    <div class="ace-panel q-pa-md" style="max-width: 820px">
      <div class="row items-center justify-between q-mb-md">
        <div class="text-h6">Settings</div>
        <q-btn outline dense color="primary" icon="refresh" label="Recheck" @click="store.refreshHealth()" />
      </div>

      <q-list dark bordered class="rounded-borders q-mb-md">
        <q-item>
          <q-item-section avatar>
            <span class="engine-dot" :class="store.engine.ok ? 'ok' : 'down'" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Engine status</q-item-label>
            <q-item-label caption>
              {{ store.engine.ok ? 'Online' : 'Offline' }}
              <span v-if="store.engine.error"> — {{ store.engine.error }}</span>
            </q-item-label>
          </q-item-section>
        </q-item>

        <q-item>
          <q-item-section>
            <q-item-label>Default / configured DiT</q-item-label>
            <q-item-label caption class="text-primary">{{ models.configured_dit || models.default_model || '—' }}</q-item-label>
          </q-item-section>
        </q-item>

        <q-item>
          <q-item-section>
            <q-item-label>Configured LM</q-item-label>
            <q-item-label caption>
              {{ models.init_llm ? (models.configured_lm || '—') : `${models.configured_lm || '—'} (disabled — ACESTEP_INIT_LLM=false)` }}
            </q-item-label>
          </q-item-section>
        </q-item>

        <q-item>
          <q-item-section>
            <q-item-label>Loaded DiT</q-item-label>
            <q-item-label caption>
              {{ models.loaded_dit || (store.engine.ok ? 'Not loaded yet (lazy — loads on first Generate)' : 'Engine offline') }}
            </q-item-label>
          </q-item-section>
        </q-item>

        <q-item>
          <q-item-section>
            <q-item-label>Loaded LM</q-item-label>
            <q-item-label caption>
              {{ models.loaded_lm || (models.init_llm ? 'Not loaded yet' : 'Off') }}
            </q-item-label>
          </q-item-section>
        </q-item>

        <q-item>
          <q-item-section>
            <q-item-label>Initialized</q-item-label>
            <q-item-label caption>
              DiT: {{ models.models_initialized ? 'yes' : 'no' }} · LM: {{ models.llm_initialized ? 'yes' : 'no' }}
            </q-item-label>
          </q-item-section>
        </q-item>

        <q-item v-if="models.available?.length">
          <q-item-section>
            <q-item-label>Available from API</q-item-label>
            <q-item-label caption>{{ models.available.join(', ') }}</q-item-label>
          </q-item-section>
        </q-item>

        <q-item>
          <q-item-section>
            <q-item-label>ACE-Step API</q-item-label>
            <q-item-label caption>{{ store.engine.detail?.acestep_api_url || 'http://127.0.0.1:8001' }}</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>

      <q-banner dense rounded class="bg-grey-10 text-grey-4 q-mb-md">
        Configured names come from <code>ACE-Step-1.5/.env</code>. Weights load on first Generate when
        <code>ACESTEP_NO_INIT=true</code>. For Draft lyrics / Simple / Format, set
        <code>ACESTEP_INIT_LLM=true</code> (needs enough RAM). Remix with your own or placeholder lyrics works with LM off.
      </q-banner>

      <div class="ace-panel-title q-mb-sm">Raw health</div>
      <pre class="text-caption text-grey-5" style="white-space: pre-wrap; margin: 0">{{ pretty }}</pre>
    </div>
  </q-page>
</template>

<script setup>
import { computed } from 'vue'
import { useStudioStore } from '@/stores/studio'

const store = useStudioStore()
const models = computed(() => store.engine.detail?.models || {})
const pretty = computed(() => JSON.stringify(store.engine.detail, null, 2))
</script>
