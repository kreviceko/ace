<template>
  <div>
    <header style="margin-bottom: 22px">
      <div class="studio-kicker">Studio</div>
      <h1 class="studio-title">Make the next track</h1>
      <p class="studio-lead">
        Upload a melody idea, shape the vibe, keep placeholder lyrics for timing — then generate.
      </p>
    </header>

    <div class="mode-grid">
      <button
        v-for="m in modes"
        :key="m.value"
        type="button"
        class="mode-card"
        :class="{ active: store.mode === m.value }"
        @click="store.mode = m.value"
      >
        <strong>{{ m.label }}</strong>
        <span>{{ m.blurb }}</span>
      </button>
    </div>

    <div v-if="capabilityBanner" class="notice" :class="{ warn: !store.engineOnline }">
      {{ capabilityBanner }}
    </div>

    <div class="create-grid">
      <section class="glass glass-pad">
        <div v-if="store.needsSource">
          <div class="section-label">Source</div>
          <div
            class="dropzone"
            :class="{ drag: dragging }"
            @click="fileInput?.click()"
            @dragover.prevent="dragging = true"
            @dragleave.prevent="dragging = false"
            @drop.prevent="onDrop"
          >
            <div class="dz-icon"><i class="material-icons">upload_file</i></div>
            <strong>{{ store.mode === 'remix' ? 'Drop your MP3 idea' : 'Drop audio to edit' }}</strong>
            <p>or click to browse · mp3, wav, flac, m4a</p>
            <div v-if="sourceLabel" class="file-name">{{ sourceLabel }}</div>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept="audio/*,.mp3,.wav,.flac,.m4a"
            hidden
            @change="onFilePick"
          />

          <div v-if="store.mode === 'edit' && waveformUrl" style="margin-bottom: 18px">
            <div class="section-label">Edit region</div>
            <WaveformEditor
              :url="waveformUrl"
              v-model:start="store.form.repainting_start"
              v-model:end="store.form.repainting_end"
            />
          </div>
        </div>

        <div v-if="store.mode === 'simple'" class="field">
          <label>Album / style experiment</label>
          <textarea
            v-model="store.form.sample_query"
            placeholder="late-night synthwave opener, neon melancholy, driving bass"
          />
        </div>

        <template v-else>
          <div class="field">
            <label>Styles / caption</label>
            <textarea
              v-model="store.form.prompt"
              placeholder="genre, mood, vocal character, production…"
            />
          </div>
          <div class="field">
            <label>Lyric concept <span class="hint">optional</span></label>
            <textarea
              v-model="store.form.lyric_concept"
              placeholder="Theme or story beats — draft into structured lyrics when ready"
            />
          </div>
        </template>

        <div class="section-label">Lyrics</div>
        <div class="chip-row">
          <button
            v-for="tag in store.sectionTags"
            :key="tag"
            type="button"
            class="chip"
            @click="store.insertTag(tag)"
          >
            {{ tag }}
          </button>
        </div>
        <div class="field lyrics">
          <label>Lines & placeholders <span class="hint">great for matching melody timing</span></label>
          <textarea
            v-model="store.form.lyrics"
            :disabled="store.form.instrumental"
            placeholder="[Verse]&#10;da da melody placeholder&#10;&#10;[Chorus]&#10;hook goes here…"
          />
        </div>

        <div class="btn-row" style="margin-bottom: 14px">
          <button class="btn btn-soft" type="button" :disabled="!store.lmAvailable || store.generating" @click="onDraft">
            Draft lyrics
          </button>
          <button class="btn btn-ghost" type="button" :disabled="!store.lmAvailable || store.generating" @click="onFormat">
            Format
          </button>
          <RouterLink class="btn btn-ghost" to="/lyrics">Open Lyrics lab</RouterLink>
        </div>

        <div class="toggle-row">
          <label class="toggle" :class="{ on: store.form.instrumental }">
            <input v-model="store.form.instrumental" type="checkbox" /> Instrumental
          </label>
          <label
            class="toggle"
            :class="{ on: store.form.thinking }"
            :style="{ opacity: !store.lmAvailable || store.mode === 'remix' || store.mode === 'edit' ? 0.45 : 1 }"
          >
            <input
              v-model="store.form.thinking"
              type="checkbox"
              :disabled="!store.lmAvailable || store.mode === 'remix' || store.mode === 'edit'"
            />
            Thinking
          </label>
          <label class="toggle" :class="{ on: store.form.use_format }" :style="{ opacity: !store.lmAvailable ? 0.45 : 1 }">
            <input v-model="store.form.use_format" type="checkbox" :disabled="!store.lmAvailable" />
            Format on generate
          </label>
        </div>

        <details class="glass" style="border-radius: 18px; margin-bottom: 18px">
          <summary class="section-label" style="cursor: pointer; padding: 14px 16px; margin: 0">Advanced</summary>
          <div style="padding: 0 16px 16px">
            <div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px">
              <div class="field">
                <label>Duration (sec, 0=auto)</label>
                <input v-model.number="store.form.duration" type="number" min="0" max="600" step="5" />
              </div>
              <div class="field">
                <label>BPM (0=auto)</label>
                <input v-model.number="store.form.bpm" type="number" min="0" />
              </div>
              <div class="field">
                <label>Key</label>
                <input v-model="store.form.key" type="text" placeholder="C Major" />
              </div>
              <div class="field">
                <label>Language</label>
                <input v-model="store.form.vocal_language" type="text" />
              </div>
              <div class="field">
                <label>Seed (−1 random)</label>
                <input v-model.number="store.form.seed" type="number" />
              </div>
              <div class="field">
                <label>Batch 1–4</label>
                <input v-model.number="store.form.batch_size" type="number" min="1" max="4" />
              </div>
            </div>
            <div v-if="store.mode === 'remix'" class="field">
              <label>Cover strength {{ store.form.audio_cover_strength }}</label>
              <input v-model.number="store.form.audio_cover_strength" type="range" min="0" max="1" step="0.05" />
            </div>
            <div v-if="store.mode === 'remix'" class="field">
              <label>Remix strength {{ store.form.cover_noise_strength }}</label>
              <input v-model.number="store.form.cover_noise_strength" type="range" min="0" max="1" step="0.05" />
            </div>
            <div v-if="store.mode === 'custom'" class="field">
              <label>Reference audio (optional)</label>
              <input type="file" accept="audio/*" @change="onRefPick" />
            </div>
          </div>
        </details>

        <div class="btn-row">
          <button class="btn btn-primary" type="button" :disabled="!store.engineOnline || store.generating" @click="onGenerate">
            <i class="material-icons" style="font-size: 18px">play_arrow</i>
            {{ store.generating ? 'Generating…' : 'Generate' }}
          </button>
          <button v-if="store.generating" class="btn btn-danger" type="button" @click="store.cancelGenerate()">
            Cancel wait
          </button>
          <span v-if="store.jobStatus" style="color: var(--muted); font-size: 0.85rem">{{ store.jobStatus }}</span>
        </div>
      </section>

      <aside class="stage-card glass glass-pad">
        <div class="stage-art"><span>Stage</span></div>
        <div class="section-label">Session</div>
        <h2 class="stage-title">{{ store.lastResult?.title || 'Nothing playing yet' }}</h2>
        <p style="color: var(--muted); font-size: 0.9rem; margin: 0 0 16px">
          {{ emptyHint }}
        </p>

        <div class="section-label">Recent</div>
        <ul class="recent-list">
          <li v-for="item in store.library.slice(0, 6)" :key="item.id">
            <button type="button" @click="playItem(item)">
              <strong>{{ item.title }}</strong>
              <small>{{ item.mode }} · {{ item.created_at?.slice(0, 19) }}</small>
            </button>
          </li>
          <li v-if="!store.library.length" style="color: var(--faint); padding: 8px">No songs yet</li>
        </ul>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { useQuasar } from 'quasar'
import { useStudioStore } from '@/stores/studio'
import WaveformEditor from '@/components/WaveformEditor.vue'

const $q = useQuasar()
const store = useStudioStore()
const fileInput = ref(null)
const dragging = ref(false)
const localObjectUrl = ref('')

const modes = [
  { value: 'remix', label: 'Remix MP3', blurb: 'Upload a demo and restyle it' },
  { value: 'custom', label: 'Custom', blurb: 'Styles + lyrics from scratch' },
  { value: 'simple', label: 'Simple', blurb: 'Album experiments from a vibe' },
  { value: 'edit', label: 'Edit', blurb: 'Repaint a slice of a track' },
]

const waveformUrl = computed(() => localObjectUrl.value || store.editSourceUrl || '')
const sourceLabel = computed(() => {
  const f = store.srcFile
  if (f instanceof File) return f.name
  if (store.editSourceUrl) return 'Library audio loaded'
  return ''
})

const capabilityBanner = computed(() => {
  if (!store.engineOnline) return 'Engine offline — start ACE-Step before generating.'
  if (!store.lmAvailable && (store.mode === 'simple' || store.form.use_format)) {
    return 'Language model is off. Simple / Draft / Format need ACESTEP_INIT_LLM=true. Remix with your lyrics still works.'
  }
  return ''
})

const emptyHint = computed(() =>
  store.engineOnline
    ? 'Finished takes appear in the dock below and in Library.'
    : 'Bring the engine online to generate.',
)

function revokeLocalUrl() {
  if (localObjectUrl.value) {
    URL.revokeObjectURL(localObjectUrl.value)
    localObjectUrl.value = ''
  }
}

function setSourceFile(file) {
  if (!(file instanceof File)) return
  revokeLocalUrl()
  store.srcFile = file
  store.editSourceUrl = ''
  localObjectUrl.value = URL.createObjectURL(file)
}

function onFilePick(e) {
  const file = e.target.files?.[0]
  if (file) setSourceFile(file)
}

function onDrop(e) {
  dragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) setSourceFile(file)
}

function onRefPick(e) {
  const file = e.target.files?.[0]
  store.refFile = file || null
}

function playItem(item) {
  store.lastResult = item
}

async function onDraft() {
  try {
    $q.loading.show({ message: 'Drafting lyrics…' })
    await store.formatLyrics({ fromConcept: true })
    $q.notify({ type: 'positive', message: 'Lyrics drafted' })
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message, timeout: 8000 })
  } finally {
    $q.loading.hide()
  }
}

async function onFormat() {
  try {
    $q.loading.show({ message: 'Formatting…' })
    await store.formatLyrics()
    $q.notify({ type: 'positive', message: 'Formatted' })
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message })
  } finally {
    $q.loading.hide()
  }
}

async function onGenerate() {
  try {
    const job = await store.generate()
    $q.notify({ type: 'positive', message: 'Song ready' })
    if (job?.song) store.lastResult = job.song
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message, timeout: 10000 })
  }
}

onBeforeUnmount(revokeLocalUrl)
</script>
