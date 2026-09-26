<template>
  <q-page class="q-pa-md">
    <div class="row q-col-gutter-md">
      <div class="col-12 col-md-7">
        <div class="ace-panel q-pa-md">
          <div class="ace-page-title q-mb-xs">Lyrics lab</div>
          <div class="ace-page-sub q-mb-md">
            Draft from a concept, keep syllable placeholders for melody timing, then send to Remix.
          </div>

          <q-input
            v-model="store.form.lyric_concept"
            outlined
            dark
            type="textarea"
            autogrow
            label="Lyric concept"
            placeholder="Theme, story, emotional arc…"
            class="q-mb-md"
          />

          <q-input
            v-model="store.form.prompt"
            outlined
            dark
            dense
            label="Style cues (for assist)"
            class="q-mb-md"
          />

          <StructureTags :tags="store.sectionTags" class="q-mb-sm" @insert="store.insertTag" />

          <q-input
            v-model="store.form.lyrics"
            type="textarea"
            outlined
            dark
            input-style="min-height: 320px"
            class="lyrics-editor q-mb-md"
            label="Lyrics / placeholders"
            hint="Placeholder lines help Remix match your melody’s phrasing"
          />

          <q-input
            v-model="focusLine"
            outlined
            dark
            dense
            label="Focus line (for rhyme / rewrite)"
            class="q-mb-md"
            hint="Leave blank to use the last lyric line"
          />

          <div class="row q-gutter-sm q-mb-md">
            <q-btn
              outline
              color="secondary"
              icon="auto_awesome"
              label="Draft (ACE LM)"
              :loading="busy === 'draft'"
              :disable="!store.lmAvailable"
              @click="draftAce"
            />
            <q-btn
              outline
              color="grey-5"
              icon="auto_fix"
              label="Format (ACE LM)"
              :loading="busy === 'format'"
              :disable="!store.lmAvailable"
              @click="formatAce"
            />
            <q-btn unelevated color="primary" icon="arrow_forward" label="Use in Remix" class="ace-btn-primary" @click="toRemix" />
            <q-btn outline class="ace-btn-ghost" label="Custom" @click="toCustom" />
          </div>
        </div>
      </div>

      <div class="col-12 col-md-5">
        <div class="ace-panel q-pa-md q-mb-md">
          <div class="ace-panel-title q-mb-sm">SpaceXAI assist</div>
          <div class="text-caption text-grey-5 q-mb-md">
            Needs <code>XAI_API_KEY</code> in repo <code>.env</code>.
            Status:
            <span :class="assistReady ? 'text-positive' : 'text-grey-5'">
              {{ assistReady ? 'configured' : 'not configured' }}
            </span>
          </div>

          <div class="row q-gutter-sm q-mb-md">
            <q-btn dense outline color="primary" label="Rhymes" :loading="busy === 'rhyme'" :disable="!assistReady" @click="assist('rhyme')" />
            <q-btn dense outline color="primary" label="Rewrite line" :loading="busy === 'rewrite_line'" :disable="!assistReady" @click="assist('rewrite_line')" />
            <q-btn dense outline color="primary" label="Continue verse" :loading="busy === 'continue_verse'" :disable="!assistReady" @click="assist('continue_verse')" />
            <q-btn dense outline color="primary" label="Hooks" :loading="busy === 'suggest_hooks'" :disable="!assistReady" @click="assist('suggest_hooks')" />
            <q-btn dense outline color="primary" label="Polish all" :loading="busy === 'polish'" :disable="!assistReady" @click="assist('polish')" />
          </div>

          <q-input
            v-model="assistOut"
            type="textarea"
            outlined
            dark
            input-style="min-height: 220px"
            label="Assist output"
          />
          <div class="row q-gutter-sm q-mt-sm">
            <q-btn dense flat color="secondary" label="Append to lyrics" :disable="!assistOut" @click="appendAssist" />
            <q-btn dense flat color="grey-5" label="Replace lyrics" :disable="!assistOut" @click="replaceAssist" />
          </div>
        </div>

        <div class="ace-panel q-pa-md">
          <div class="ace-panel-title q-mb-sm">Your usual flow</div>
          <ol class="text-body2 text-grey-4 q-pl-md">
            <li>Upload a demo MP3 in Remix</li>
            <li>Sketch a lyric concept (or placeholders)</li>
            <li>Draft / assist lyrics</li>
            <li>Generate the cover/remix</li>
          </ol>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useStudioStore } from '@/stores/studio'
import { api } from '@/api/client'
import StructureTags from '@/components/StructureTags.vue'

const store = useStudioStore()
const router = useRouter()
const $q = useQuasar()
const busy = ref('')
const focusLine = ref('')
const assistOut = ref('')

const assistReady = computed(() => Boolean(store.engine.detail?.features?.lyric_assist))

async function draftAce() {
  busy.value = 'draft'
  try {
    await store.formatLyrics({ fromConcept: true })
    $q.notify({ type: 'positive', message: 'Draft ready' })
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message })
  } finally {
    busy.value = ''
  }
}

async function formatAce() {
  busy.value = 'format'
  try {
    await store.formatLyrics()
    $q.notify({ type: 'positive', message: 'Formatted' })
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message })
  } finally {
    busy.value = ''
  }
}

async function assist(action) {
  busy.value = action
  try {
    const data = await api.assistLyrics({
      action,
      lyrics: store.form.lyrics,
      concept: store.form.lyric_concept,
      style: store.form.prompt,
      line: focusLine.value,
    })
    assistOut.value = data.text || ''
    if (action === 'polish' && data.text) {
      // leave in output; user chooses replace
    }
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message, timeout: 8000 })
  } finally {
    busy.value = ''
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
