<template>
  <q-page class="q-pa-md">
    <div class="row q-col-gutter-md">
      <div class="col-12 col-lg-8">
        <div class="ace-panel q-pa-md">
          <div class="row items-center justify-between q-mb-sm">
            <div class="ace-panel-title">Create</div>
            <q-btn-toggle
              v-model="store.mode"
              toggle-color="primary"
              unelevated
              dense
              no-caps
              :options="modeOptions"
              class="bg-grey-10 mode-toggle"
            />
          </div>

          <div class="text-caption text-grey-5 q-mb-md">{{ modeHint }}</div>

          <q-banner
            v-if="capabilityBanner"
            dense
            rounded
            class="bg-grey-10 text-grey-4 q-mb-md"
          >
            {{ capabilityBanner }}
          </q-banner>

          <!-- Remix / Edit: source audio first -->
          <div v-if="store.needsSource" class="q-mb-md">
            <q-file
              v-model="store.srcFile"
              outlined
              dark
              label="Source MP3 / audio (required)"
              accept="audio/*,.mp3,.wav,.flac,.m4a"
              clearable
              max-files="1"
            >
              <template #prepend><q-icon name="upload_file" /></template>
              <template #hint>Your melody sketch or demo — structure is preserved in Remix</template>
            </q-file>
          </div>

          <q-input
            v-if="store.mode === 'simple'"
            v-model="store.form.sample_query"
            type="textarea"
            autogrow
            outlined
            dark
            label="Album / style experiment"
            placeholder="late-night synthwave album opener, neon melancholy, driving bass"
            class="q-mb-md"
          />

          <template v-if="store.mode !== 'simple'">
            <q-input
              v-model="store.form.prompt"
              type="textarea"
              autogrow
              outlined
              dark
              label="Styles / caption"
              placeholder="genre, mood, vocal character, production…"
              class="q-mb-md"
            />

            <q-input
              v-model="store.form.lyric_concept"
              type="textarea"
              autogrow
              outlined
              dark
              label="Lyric concept (optional)"
              placeholder="Theme or story beats — use Draft lyrics to expand into structured lines"
              class="q-mb-md"
            />
          </template>

          <div class="row items-center justify-between q-mb-xs">
            <div class="text-subtitle2">
              Lyrics
              <span class="text-caption text-grey-5 q-ml-sm">
                placeholders OK for melody timing
              </span>
            </div>
          </div>
          <StructureTags :tags="store.sectionTags" class="q-mb-sm" @insert="store.insertTag" />

          <q-input
            v-model="store.form.lyrics"
            type="textarea"
            outlined
            dark
            :disable="store.form.instrumental"
            placeholder="[Verse]&#10;da da melody placeholder&#10;&#10;[Chorus]&#10;hook goes here…"
            input-style="min-height: 200px"
            class="lyrics-editor q-mb-sm"
          />

          <div class="row q-gutter-sm q-mb-md">
            <q-btn
              outline
              color="secondary"
              icon="auto_awesome"
              label="Draft lyrics from concept"
              :disable="store.generating || !store.lmAvailable"
              @click="onDraftLyrics"
            />
            <q-btn
              outline
              color="grey-5"
              icon="auto_fix"
              label="Format lyrics"
              :disable="store.generating || !store.lmAvailable"
              @click="onFormat"
            />
            <q-btn flat dense color="grey-5" label="Open Lyrics lab" to="/lyrics" />
          </div>

          <div class="row q-col-gutter-md q-mb-md">
            <div class="col-12 col-sm-4">
              <q-checkbox v-model="store.form.instrumental" dark label="Instrumental" />
            </div>
            <div class="col-12 col-sm-4">
              <q-checkbox
                v-model="store.form.thinking"
                dark
                label="Thinking (LM)"
                :disable="!store.lmAvailable || store.mode === 'remix' || store.mode === 'edit'"
              />
            </div>
            <div class="col-12 col-sm-4">
              <q-checkbox
                v-model="store.form.use_format"
                dark
                label="Format on generate"
                :disable="!store.lmAvailable"
              />
            </div>
          </div>

          <q-expansion-item dense dark label="Advanced" header-class="text-grey-4" class="q-mb-md">
            <div class="row q-col-gutter-md q-pt-sm">
              <div class="col-12 col-sm-6 col-md-3">
                <q-slider v-model="store.form.duration" :min="0" :max="600" :step="5" label dark color="primary" />
                <div class="text-caption text-grey-5">Duration: {{ store.form.duration || 'auto' }}s</div>
              </div>
              <div class="col-6 col-md-3">
                <q-input v-model.number="store.form.bpm" type="number" outlined dark dense label="BPM (0=auto)" />
              </div>
              <div class="col-6 col-md-3">
                <q-input v-model="store.form.key" outlined dark dense label="Key" placeholder="C Major" />
              </div>
              <div class="col-6 col-md-3">
                <q-select
                  v-model="store.form.time_signature"
                  :options="timeOptions"
                  outlined
                  dark
                  dense
                  label="Time signature"
                  emit-value
                  map-options
                  clearable
                />
              </div>
              <div class="col-6 col-md-3">
                <q-input v-model="store.form.vocal_language" outlined dark dense label="Language" />
              </div>
              <div class="col-6 col-md-3">
                <q-input
                  v-model.number="store.form.seed"
                  type="number"
                  outlined
                  dark
                  dense
                  label="Seed (−1 = random)"
                />
              </div>
              <div class="col-6 col-md-3">
                <q-input
                  v-model.number="store.form.batch_size"
                  type="number"
                  outlined
                  dark
                  dense
                  label="Batch (1–4)"
                  :min="1"
                  :max="4"
                />
              </div>
              <div class="col-12 col-md-6">
                <q-input v-model="store.form.negative_styles" outlined dark dense label="Negative styles" />
              </div>

              <div v-if="store.mode === 'remix'" class="col-12 col-md-6">
                <div class="text-caption text-grey-5">Cover strength (keep structure)</div>
                <q-slider v-model="store.form.audio_cover_strength" :min="0" :max="1" :step="0.05" label dark color="secondary" />
              </div>
              <div v-if="store.mode === 'remix'" class="col-12 col-md-6">
                <div class="text-caption text-grey-5">Remix strength (more change)</div>
                <q-slider v-model="store.form.cover_noise_strength" :min="0" :max="1" :step="0.05" label dark color="accent" />
              </div>
              <div v-if="store.mode === 'edit'" class="col-6">
                <q-input v-model.number="store.form.repainting_start" type="number" outlined dark dense label="Edit start (sec)" />
              </div>
              <div v-if="store.mode === 'edit'" class="col-6">
                <q-input v-model.number="store.form.repainting_end" type="number" outlined dark dense label="Edit end (0=end)" />
              </div>

              <div v-if="store.mode === 'custom'" class="col-12">
                <q-file
                  v-model="store.refFile"
                  outlined
                  dark
                  dense
                  label="Reference audio (optional style guide)"
                  accept="audio/*,.mp3,.wav,.flac,.m4a"
                  clearable
                  max-files="1"
                />
              </div>
            </div>
          </q-expansion-item>

          <div class="row q-gutter-sm items-center">
            <q-btn
              unelevated
              color="primary"
              icon="play_arrow"
              label="Generate"
              class="q-px-lg"
              :loading="store.generating"
              :disable="!store.engineOnline"
              @click="onGenerate"
            />
            <q-btn
              v-if="store.generating"
              flat
              color="negative"
              icon="stop"
              label="Cancel wait"
              @click="store.cancelGenerate()"
            />
            <div v-if="store.jobStatus" class="text-caption text-grey-4">{{ store.jobStatus }}</div>
          </div>
        </div>
      </div>

      <div class="col-12 col-lg-4">
        <div class="ace-panel q-pa-md q-mb-md">
          <div class="ace-panel-title q-mb-sm">Now playing</div>
          <div v-if="currentAudioUrl" class="q-mb-sm">
            <div class="text-subtitle2 q-mb-xs">{{ currentTitle }}</div>
            <div v-if="metaLine" class="text-caption text-grey-5 q-mb-sm">{{ metaLine }}</div>
            <audio :src="currentAudioUrl" controls style="width: 100%" />
            <div class="row q-gutter-sm q-mt-sm">
              <q-btn
                dense
                outline
                color="grey-5"
                icon="download"
                label="Download"
                :href="currentAudioUrl"
                target="_blank"
              />
            </div>
          </div>
          <div v-else class="text-grey-6 text-body2">
            {{ emptyPlayerHint }}
          </div>
        </div>

        <div class="ace-panel q-pa-md">
          <div class="row items-center justify-between q-mb-sm">
            <div class="ace-panel-title">Recent</div>
            <q-btn flat dense size="sm" icon="refresh" @click="store.refreshLibrary()" />
          </div>
          <q-list dark separator>
            <q-item
              v-for="item in store.library.slice(0, 8)"
              :key="item.id"
              clickable
              class="library-item rounded-borders"
              @click="playItem(item)"
            >
              <q-item-section>
                <q-item-label>{{ item.title }}</q-item-label>
                <q-item-label caption class="text-grey-5">{{ item.mode }} · {{ item.created_at?.slice(0, 19) }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-btn flat dense round icon="edit" @click.stop="reuseItem(item)" />
              </q-item-section>
            </q-item>
            <q-item v-if="!store.library.length">
              <q-item-section class="text-grey-6">No songs yet</q-item-section>
            </q-item>
          </q-list>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { computed } from 'vue'
import { useQuasar } from 'quasar'
import { useStudioStore } from '@/stores/studio'
import { api } from '@/api/client'
import StructureTags from '@/components/StructureTags.vue'

const $q = useQuasar()
const store = useStudioStore()

const modeOptions = [
  { label: 'Remix MP3', value: 'remix' },
  { label: 'Custom', value: 'custom' },
  { label: 'Simple', value: 'simple' },
  { label: 'Edit', value: 'edit' },
]

const timeOptions = [
  { label: 'Auto', value: '' },
  { label: '2/4', value: '2' },
  { label: '3/4', value: '3' },
  { label: '4/4', value: '4' },
  { label: '6/8', value: '6' },
]

const modeHint = computed(() => {
  switch (store.mode) {
    case 'remix':
      return 'Upload a demo MP3 and restyle it. Keep placeholder lyrics if you care about phrasing/timing.'
    case 'edit':
      return 'Repaint a time range of an existing track (fix a section, swap lyrics).'
    case 'simple':
      return 'Album / style experiments from one description (needs ACE language model).'
    default:
      return 'Full control: styles + lyrics from scratch (or after drafting lyrics).'
  }
})

const capabilityBanner = computed(() => {
  if (!store.engineOnline) {
    return 'Engine offline — start ACE-Step (`uv run acestep-api` or scripts/start.ps1) before generating.'
  }
  if (!store.lmAvailable && (store.mode === 'simple' || store.form.use_format)) {
    return 'Language model is off (ACESTEP_INIT_LLM=false). Simple / Draft lyrics / Format need it. Remix with your own lyrics still works.'
  }
  return ''
})

const emptyPlayerHint = computed(() => {
  if (!store.engineOnline) return 'Start the ACE-Step engine, then generate a song to hear it here.'
  return 'Generate a remix or track to hear it here.'
})

const currentAudioUrl = computed(() => {
  const id = store.lastResult?.id
  return id ? api.audioUrl(id) : null
})

const currentTitle = computed(() => store.lastResult?.title || 'Result')

const metaLine = computed(() => {
  const m = store.lastResult?.metas || {}
  const parts = []
  if (m.bpm) parts.push(`${m.bpm} BPM`)
  if (m.keyscale || m.key_scale) parts.push(m.keyscale || m.key_scale)
  if (m.duration) parts.push(`${m.duration}s`)
  return parts.join(' · ')
})

function playItem(item) {
  store.lastResult = item
}

function reuseItem(item) {
  store.loadFromLibrary(item)
  $q.notify({ type: 'info', message: 'Loaded settings into Create' })
}

async function onDraftLyrics() {
  try {
    $q.loading.show({ message: 'Drafting lyrics…' })
    await store.formatLyrics({ fromConcept: true })
    $q.notify({ type: 'positive', message: 'Lyrics drafted — edit placeholders as needed' })
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
    $q.notify({ type: 'positive', message: 'Lyrics / caption formatted' })
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
</script>

<style scoped>
.mode-toggle :deep(.q-btn) {
  font-size: 12px;
  padding: 0 10px;
}
@media (max-width: 600px) {
  .mode-toggle {
    width: 100%;
  }
}
</style>
