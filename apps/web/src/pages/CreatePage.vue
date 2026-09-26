<template>
  <q-page class="q-pa-md">
    <div class="row q-col-gutter-md">
      <!-- Left: Create form -->
      <div class="col-12 col-lg-8">
        <div class="ace-panel q-pa-md">
          <div class="row items-center justify-between q-mb-md">
            <div class="ace-panel-title">Create</div>
            <q-btn-toggle
              v-model="store.mode"
              toggle-color="primary"
              unelevated
              dense
              :options="modeOptions"
              class="bg-grey-10"
            />
          </div>

          <div class="text-caption text-grey-5 q-mb-md">{{ modeHint }}</div>

          <q-input
            v-if="store.mode === 'simple'"
            v-model="store.form.sample_query"
            type="textarea"
            autogrow
            outlined
            dark
            label="Describe the song"
            placeholder="a soft indie love song for a rainy evening"
            class="q-mb-md"
          />

          <template v-else>
            <q-input
              v-model="store.form.prompt"
              type="textarea"
              autogrow
              outlined
              dark
              label="Styles / caption"
              placeholder="Describe the styles of the song..."
              class="q-mb-md"
            />
          </template>

          <div class="row items-center justify-between q-mb-xs">
            <div class="text-subtitle2">Lyrics</div>
            <div class="row q-gutter-xs">
              <q-btn
                v-for="tag in store.sectionTags"
                :key="tag"
                dense
                outline
                size="sm"
                color="grey-6"
                :label="tag"
                @click="store.insertTag(tag)"
              />
            </div>
          </div>

          <q-input
            v-model="store.form.lyrics"
            type="textarea"
            outlined
            dark
            :disable="store.form.instrumental"
            placeholder="Write lyrics, or leave blank for instrumental..."
            input-style="min-height: 220px"
            class="lyrics-editor q-mb-md"
          />

          <div class="row q-col-gutter-md q-mb-md">
            <div class="col-12 col-sm-4">
              <q-checkbox v-model="store.form.instrumental" dark label="Instrumental" />
            </div>
            <div class="col-12 col-sm-4">
              <q-checkbox
                v-model="store.form.thinking"
                dark
                label="Thinking (LM)"
                :disable="store.mode === 'remix' || store.mode === 'edit'"
              />
            </div>
            <div class="col-12 col-sm-4">
              <q-checkbox v-model="store.form.use_format" dark label="Format with LM" />
            </div>
          </div>

          <q-expansion-item
            dense
            dark
            label="Advanced controls"
            header-class="text-grey-4"
            class="q-mb-md"
          >
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
                  :options="['', '2', '3', '4', '6']"
                  outlined
                  dark
                  dense
                  label="Time signature"
                  emit-value
                  map-options
                />
              </div>
              <div class="col-6 col-md-3">
                <q-input v-model="store.form.vocal_language" outlined dark dense label="Language" />
              </div>
              <div class="col-12 col-md-9">
                <q-input v-model="store.form.negative_styles" outlined dark dense label="Negative styles" />
              </div>

              <div v-if="store.mode === 'remix'" class="col-12 col-md-6">
                <div class="text-caption text-grey-5">Cover Strength</div>
                <q-slider v-model="store.form.audio_cover_strength" :min="0" :max="1" :step="0.05" label dark color="secondary" />
              </div>
              <div v-if="store.mode === 'remix'" class="col-12 col-md-6">
                <div class="text-caption text-grey-5">Remix Strength</div>
                <q-slider v-model="store.form.cover_noise_strength" :min="0" :max="1" :step="0.05" label dark color="accent" />
              </div>
              <div v-if="store.mode === 'edit'" class="col-6">
                <q-input v-model.number="store.form.repainting_start" type="number" outlined dark dense label="Edit start (sec)" />
              </div>
              <div v-if="store.mode === 'edit'" class="col-6">
                <q-input v-model.number="store.form.repainting_end" type="number" outlined dark dense label="Edit end (0=end)" />
              </div>
            </div>
          </q-expansion-item>

          <div class="row q-col-gutter-md q-mb-md">
            <div v-if="store.needsSource" class="col-12 col-md-6">
              <q-file
                v-model="store.srcFile"
                outlined
                dark
                dense
                label="Source audio (required)"
                accept="audio/*,.mp3,.wav,.flac,.m4a"
                clearable
              >
                <template #prepend><q-icon name="upload_file" /></template>
              </q-file>
            </div>
            <div v-if="store.mode === 'custom'" class="col-12 col-md-6">
              <q-file
                v-model="store.refFile"
                outlined
                dark
                dense
                label="Reference audio (optional)"
                accept="audio/*,.mp3,.wav,.flac,.m4a"
                clearable
              >
                <template #prepend><q-icon name="library_music" /></template>
              </q-file>
            </div>
          </div>

          <div class="row q-gutter-sm">
            <q-btn
              outline
              color="grey-5"
              icon="auto_fix"
              label="Format lyrics"
              :disable="store.generating"
              @click="onFormat"
            />
            <q-btn
              unelevated
              color="primary"
              icon="play_arrow"
              label="Generate"
              class="q-px-lg"
              :loading="store.generating"
              @click="onGenerate"
            />
            <div v-if="store.jobStatus" class="self-center text-caption text-grey-4">
              {{ store.jobStatus }}
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Player + recent -->
      <div class="col-12 col-lg-4">
        <div class="ace-panel q-pa-md q-mb-md">
          <div class="ace-panel-title q-mb-sm">Now playing</div>
          <div v-if="currentAudioUrl" class="q-mb-sm">
            <div class="text-subtitle2 q-mb-sm">{{ currentTitle }}</div>
            <audio :src="currentAudioUrl" controls style="width: 100%" />
          </div>
          <div v-else class="text-grey-6 text-body2">
            Generate a song to hear it here. On this laptop, the ACE engine may stay offline until you run it on a machine with more RAM.
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
              @click="store.loadFromLibrary(item)"
            >
              <q-item-section>
                <q-item-label>{{ item.title }}</q-item-label>
                <q-item-label caption class="text-grey-5">{{ item.mode }} · {{ item.created_at?.slice(0, 19) }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-btn flat dense round icon="play_arrow" @click.stop="playItem(item)" />
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

const $q = useQuasar()
const store = useStudioStore()

const modeOptions = [
  { label: 'Simple', value: 'simple' },
  { label: 'Custom', value: 'custom' },
  { label: 'Remix', value: 'remix' },
  { label: 'Edit', value: 'edit' },
]

const modeHint = computed(() => {
  switch (store.mode) {
    case 'simple':
      return 'One description → full song (sample mode).'
    case 'remix':
      return 'Upload audio and restyle it (cover).'
    case 'edit':
      return 'Repaint a time range of an existing track.'
    default:
      return 'Styles + lyrics with full creative control.'
  }
})

const currentAudioUrl = computed(() => {
  const id = store.lastResult?.id || store.lastResult?.song_id
  return id ? api.audioUrl(id) : null
})

const currentTitle = computed(() => store.lastResult?.title || store.lastResult?.song?.title || 'Result')

function playItem(item) {
  store.lastResult = item
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
  if (store.needsSource && !store.srcFile) {
    $q.notify({ type: 'warning', message: 'Upload a source audio file for Remix/Edit' })
    return
  }
  try {
    const job = await store.generate()
    $q.notify({ type: 'positive', message: 'Song ready' })
    if (job?.song) store.lastResult = job.song
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message, timeout: 8000 })
  }
}
</script>
