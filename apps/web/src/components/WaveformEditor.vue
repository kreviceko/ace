<template>
  <div class="waveform-editor">
    <div ref="host" class="wave-host" />
    <div class="row items-center q-gutter-sm q-mt-sm">
      <q-btn dense flat icon="play_arrow" :disable="!ready" @click="togglePlay" />
      <div class="text-caption text-grey-5">
        Select a region to set Edit start/end
        <span v-if="ready"> · {{ start.toFixed(1) }}s – {{ endDisplay }}</span>
      </div>
      <q-space />
      <q-btn dense flat label="Clear region" :disable="!ready" @click="clearRegion" />
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.esm.js'

const props = defineProps({
  url: { type: String, default: '' },
  start: { type: Number, default: 0 },
  end: { type: Number, default: 0 },
})

const emit = defineEmits(['update:start', 'update:end'])

const host = ref(null)
const ready = ref(false)
const duration = ref(0)
let ws = null
let regions = null
let region = null

const endDisplay = ref('end')

function syncEndLabel() {
  endDisplay.value = props.end > 0 ? `${props.end.toFixed(1)}s` : 'end'
}

watch(() => props.end, syncEndLabel)

async function mountWave(url) {
  destroyWave()
  ready.value = false
  if (!url || !host.value) return

  regions = RegionsPlugin.create()
  ws = WaveSurfer.create({
    container: host.value,
    url,
    height: 96,
    waveColor: '#64748b',
    progressColor: '#8b5cf6',
    cursorColor: '#22d3ee',
    normalize: true,
    plugins: [regions],
  })

  ws.on('ready', () => {
    duration.value = ws.getDuration() || 0
    ready.value = true
    const s = Math.max(0, Number(props.start) || 0)
    const e = props.end > 0 ? Math.min(duration.value, Number(props.end)) : Math.min(duration.value, s + 8)
    region = regions.addRegion({
      start: s,
      end: Math.max(s + 0.5, e),
      color: 'rgba(139, 92, 246, 0.25)',
      drag: true,
      resize: true,
    })
    emitRange(region.start, region.end)
  })

  regions.on('region-updated', (r) => {
    region = r
    emitRange(r.start, r.end)
  })
}

function emitRange(start, end) {
  emit('update:start', Number(start.toFixed(2)))
  const atEnd = duration.value > 0 && end >= duration.value - 0.05
  emit('update:end', atEnd ? 0 : Number(end.toFixed(2)))
  syncEndLabel()
}

function clearRegion() {
  if (!regions) return
  regions.clearRegions()
  emit('update:start', 0)
  emit('update:end', 0)
  syncEndLabel()
}

function togglePlay() {
  ws?.playPause()
}

function destroyWave() {
  try {
    ws?.destroy()
  } catch {
    /* ignore */
  }
  ws = null
  regions = null
  region = null
  ready.value = false
}

watch(
  () => props.url,
  (url) => {
    mountWave(url)
  },
)

onMounted(() => mountWave(props.url))
onBeforeUnmount(destroyWave)
</script>

<style scoped>
.wave-host {
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
