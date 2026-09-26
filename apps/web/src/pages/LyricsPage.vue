<template>
  <q-page class="q-pa-md">
    <div class="row q-col-gutter-md">
      <div class="col-12 col-md-8">
        <div class="ace-panel q-pa-md">
          <div class="text-h6 q-mb-xs">Lyric workspace</div>
          <div class="text-caption text-grey-5 q-mb-md">
            Structure tags for ACE-Step, local format via the engine LM, and optional SpaceXAI assist later.
          </div>

          <q-input
            v-model="brief"
            outlined
            dark
            type="textarea"
            autogrow
            label="Song brief"
            placeholder="Theme, mood, audience, story beats…"
            class="q-mb-md"
          />

          <div class="row q-gutter-xs q-mb-sm">
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

          <q-input
            v-model="store.form.lyrics"
            type="textarea"
            outlined
            dark
            input-style="min-height: 360px"
            class="lyrics-editor q-mb-md"
            label="Lyrics"
          />

          <div class="row q-gutter-sm">
            <q-btn outline color="grey-5" icon="auto_fix" label="Format with ACE" :loading="busy" @click="format" />
            <q-btn unelevated color="primary" icon="arrow_forward" label="Use in Create" to="/" />
          </div>
        </div>
      </div>

      <div class="col-12 col-md-4">
        <div class="ace-panel q-pa-md q-mb-md">
          <div class="ace-panel-title q-mb-sm">Assist</div>
          <div class="text-body2 text-grey-4 q-mb-md">
            Rhyme / line rewrite assist will use SpaceXAI when <code>XAI_API_KEY</code> is set. Core formatting works locally through ACE-Step.
          </div>
          <q-banner dense rounded class="bg-grey-10 text-grey-4">
            Coming next: rhyme suggestions, continue verse, rewrite line.
          </q-banner>
        </div>

        <div class="ace-panel q-pa-md">
          <div class="ace-panel-title q-mb-sm">Tips</div>
          <ul class="text-body2 text-grey-4 q-pl-md">
            <li>Keep section tags on their own lines.</li>
            <li>Shorter lines usually sing better.</li>
            <li>Put style words in caption, not inside lyrics.</li>
          </ul>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'
import { useQuasar } from 'quasar'
import { useStudioStore } from '@/stores/studio'

const store = useStudioStore()
const $q = useQuasar()
const brief = ref('')
const busy = ref(false)

async function format() {
  busy.value = true
  try {
    if (brief.value && !store.form.prompt) store.form.prompt = brief.value
    await store.formatLyrics()
    $q.notify({ type: 'positive', message: 'Formatted' })
  } catch (err) {
    $q.notify({ type: 'negative', message: err.message })
  } finally {
    busy.value = false
  }
}
</script>
