<template>
  <div>
    <header style="margin-bottom: 22px">
      <div class="studio-kicker">Writing</div>
      <h1 class="studio-title">Lyrics lab</h1>
      <p class="studio-lead">
        Concept → draft → placeholders for timing → send into Remix.
      </p>
    </header>

    <div class="create-grid">
      <section class="glass glass-pad">
        <div class="field">
          <label>Lyric concept</label>
          <textarea v-model="store.form.lyric_concept" placeholder="Theme, story, emotional arc…" />
        </div>
        <div class="field">
          <label>Style cues</label>
          <input v-model="store.form.prompt" type="text" placeholder="for assist tone" />
        </div>
        <div class="chip-row">
          <button v-for="tag in store.sectionTags" :key="tag" type="button" class="chip" @click="store.insertTag(tag)">
            {{ tag }}
          </button>
        </div>
        <div class="field lyrics">
          <label>Lyrics / placeholders</label>
          <textarea v-model="store.form.lyrics" placeholder="Structured lyrics or syllable placeholders" />
        </div>
        <div class="field">
          <label>Focus line</label>
          <input v-model="focusLine" type="text" placeholder="For rhyme / rewrite — blank uses last line" />
        </div>
        <div class="btn-row">
          <button class="btn btn-soft" type="button" :disabled="!store.lmAvailable" @click="draftAce">Draft (ACE)</button>
          <button class="btn btn-ghost" type="button" :disabled="!store.lmAvailable" @click="formatAce">Format (ACE)</button>
          <button class="btn btn-primary" type="button" @click="toRemix">Use in Remix</button>
          <button class="btn btn-ghost" type="button" @click="toCustom">Custom</button>
        </div>
      </section>

      <aside class="glass glass-pad">
        <div class="section-label">SpaceXAI assist</div>
        <p style="color: var(--muted); font-size: 0.88rem; margin-top: 0">
          {{ assistReady ? 'Key detected — ready.' : 'Add XAI_API_KEY to repo .env to unlock.' }}
        </p>
        <div class="btn-row" style="margin-bottom: 14px">
          <button class="btn btn-ghost" type="button" :disabled="!assistReady" @click="assist('rhyme')">Rhymes</button>
          <button class="btn btn-ghost" type="button" :disabled="!assistReady" @click="assist('rewrite_line')">Rewrite</button>
          <button class="btn btn-ghost" type="button" :disabled="!assistReady" @click="assist('continue_verse')">Continue</button>
          <button class="btn btn-ghost" type="button" :disabled="!assistReady" @click="assist('suggest_hooks')">Hooks</button>
          <button class="btn btn-ghost" type="button" :disabled="!assistReady" @click="assist('polish')">Polish</button>
        </div>
        <div class="field lyrics">
          <label>Assist output</label>
          <textarea v-model="assistOut" />
        </div>
        <div class="btn-row">
          <button class="btn btn-soft" type="button" :disabled="!assistOut" @click="appendAssist">Append</button>
          <button class="btn btn-ghost" type="button" :disabled="!assistOut" @click="replaceAssist">Replace lyrics</button>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useStudioStore } from '@/stores/studio'
import { api } from '@/api/client'

const store = useStudioStore()
const router = useRouter()
const $q = useQuasar()
const focusLine = ref('')
const assistOut = ref('')
const assistReady = computed(() => Boolean(store.engine.detail?.features?.lyric_assist))

async function draftAce() {
  try {
    await store.formatLyrics({ fromConcept: true })
    $q.notify({ type: 'positive', message: 'Draft ready' })
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message })
  }
}

async function formatAce() {
  try {
    await store.formatLyrics()
    $q.notify({ type: 'positive', message: 'Formatted' })
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message })
  }
}

async function assist(action) {
  try {
    const data = await api.assistLyrics({
      action,
      lyrics: store.form.lyrics,
      concept: store.form.lyric_concept,
      style: store.form.prompt,
      line: focusLine.value,
    })
    assistOut.value = data.text || ''
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message, timeout: 8000 })
  }
}

function appendAssist() {
  const cur = store.form.lyrics || ''
  const sep = !cur || cur.endsWith('\n') ? '' : '\n'
  store.form.lyrics = `${cur}${sep}${assistOut.value}\n`
}

function replaceAssist() {
  store.form.lyrics = assistOut.value
}

function toRemix() {
  store.mode = 'remix'
  router.push('/')
}

function toCustom() {
  store.mode = 'custom'
  router.push('/')
}
</script>
