<template>
  <div>
    <header style="margin-bottom: 22px" class="row items-start justify-between">
      <div>
        <div class="studio-kicker">System</div>
        <h1 class="studio-title">Settings</h1>
        <p class="studio-lead">Engine, models, and optional integrations.</p>
      </div>
      <button class="btn btn-ghost" type="button" @click="store.refreshHealth()">Recheck</button>
    </header>

    <section class="glass glass-pad" style="max-width: 760px">
      <div class="settings-list">
        <div class="settings-row">
          <div>
            <strong>Engine</strong>
            <p>{{ store.engine.ok ? 'Online' : 'Offline' }}<span v-if="store.engine.error"> — {{ store.engine.error }}</span></p>
          </div>
          <span class="dot" :class="store.engine.ok ? 'on' : 'off'" />
        </div>
        <div class="settings-row">
          <div>
            <strong>Configured DiT</strong>
            <p>{{ models.configured_dit || models.default_model || '—' }}</p>
          </div>
        </div>
        <div class="settings-row">
          <div>
            <strong>Language model</strong>
            <p>
              {{ models.configured_lm || '—' }}
              · {{ models.init_llm ? 'enabled' : 'disabled in ACE .env' }}
            </p>
          </div>
        </div>
        <div class="settings-row">
          <div>
            <strong>SpaceXAI lyric assist</strong>
            <p>{{ features.lyric_assist ? 'XAI_API_KEY detected' : 'Set XAI_API_KEY in repo .env' }}</p>
          </div>
        </div>
        <div class="settings-row">
          <div>
            <strong>Demucs stems</strong>
            <p>{{ features.demucs_stems ? 'Installed' : 'uv sync --extra stems' }}</p>
          </div>
        </div>
      </div>

      <details style="margin-top: 18px">
        <summary class="section-label" style="cursor: pointer">Raw health</summary>
        <pre class="raw">{{ pretty }}</pre>
      </details>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useStudioStore } from '@/stores/studio'

const store = useStudioStore()
const models = computed(() => store.engine.detail?.models || {})
const features = computed(() => store.engine.detail?.features || {})
const pretty = computed(() => JSON.stringify(store.engine.detail, null, 2))
</script>

<style scoped>
.settings-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.settings-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px 4px;
  border-bottom: 1px solid var(--line);
}
.settings-row strong {
  display: block;
  font-size: 0.95rem;
}
.settings-row p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 0.85rem;
}
.raw {
  margin: 10px 0 0;
  padding: 14px;
  border-radius: 14px;
  background: rgba(0, 0, 0, 0.35);
  color: var(--faint);
  font-size: 0.75rem;
  overflow: auto;
}
</style>
