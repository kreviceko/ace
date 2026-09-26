<template>
  <q-page class="q-pa-md">
    <div class="row q-col-gutter-md">
      <div class="col-12 col-md-8">
        <div class="ace-panel q-pa-md">
          <div class="text-h6 q-mb-xs">Lyrics lab</div>
          <div class="text-caption text-grey-5 q-mb-md">
            Draft from a concept, keep syllable placeholders for melody timing, then send to Create (usually Remix).
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

          <StructureTags :tags="store.sectionTags" class="q-mb-sm" @insert="store.insertTag" />

          <q-input
            v-model="store.form.lyrics"
            type="textarea"
            outlined
            dark
            input-style="min-height: 360px"
            class="lyrics-editor q-mb-md"
            label="Lyrics / placeholders"
            hint="Placeholder lines (da-da / la-la) help the model match your melody’s phrasing in Remix"
          />

          <div class="row q-gutter-sm">
            <q-btn
              outline
              color="secondary"
              icon="auto_awesome"
              label="Draft from concept"
              :loading="busy"
              :disable="!store.lmAvailable"
              @click="draft"
            />
            <q-btn
              outline
              color="grey-5"
              icon="auto_fix"
              label="Format"
              :loading="busy"
              :disable="!store.lmAvailable"
              @click="format"
            />
            <q-btn unelevated color="primary" icon="arrow_forward" label="Use in Remix" @click="toRemix" />
            <q-btn flat color="grey-5" label="Use in Custom" @click="toCustom" />
          </div>

          <q-banner v-if="!store.lmAvailable" dense rounded class="bg-grey-10 text-grey-4 q-mt-md">
            Draft/Format need ACESTEP_INIT_LLM=true. You can still paste or write placeholders here and remix without the LM.
          </q-banner>
        </div>
      </div>

      <div class="col-12 col-md-4">
        <div class="ace-panel q-pa-md q-mb-md">
          <div class="ace-panel-title q-mb-sm">Your usual flow</div>
          <ol class="text-body2 text-grey-4 q-pl-md">
            <li>Upload a demo MP3 in Remix</li>
            <li>Sketch a lyric concept (or placeholders)</li>
            <li>Draft / format lyrics if LM is on</li>
            <li>Generate the cover/remix</li>
          </ol>
        </div>

        <div class="ace-panel q-pa-md">
          <div class="ace-panel-title q-mb-sm">Tips</div>
          <ul class="text-body2 text-grey-4 q-pl-md">
            <li>Keep section tags on their own lines.</li>
            <li>Match placeholder syllable counts to your melody.</li>
            <li>Put style words in caption, not inside lyrics.</li>
          </ul>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useStudioStore } from '@/stores/studio'
import StructureTags from '@/components/StructureTags.vue'

const store = useStudioStore()
const router = useRouter()
const $q = useQuasar()
const busy = ref(false)

async function draft() {
  busy.value = true
  try {
    await store.formatLyrics({ fromConcept: true })
    $q.notify({ type: 'positive', message: 'Draft ready' })
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message })
  } finally {
    busy.value = false
  }
}

async function format() {
  busy.value = true
  try {
    await store.formatLyrics()
    $q.notify({ type: 'positive', message: 'Formatted' })
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message })
  } finally {
    busy.value = false
  }
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
