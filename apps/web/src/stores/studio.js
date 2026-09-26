import { defineStore } from 'pinia'
import { api } from '@/api/client'

const SECTION_TAGS = ['[Intro]', '[Verse]', '[Pre-Chorus]', '[Chorus]', '[Bridge]', '[Outro]', '[Instrumental]']

function asFile(value) {
  if (!value) return null
  if (value instanceof File) return value
  if (Array.isArray(value) && value[0] instanceof File) return value[0]
  if (typeof FileList !== 'undefined' && value instanceof FileList && value[0]) return value[0]
  return null
}

function normalizeSong(jobOrSong) {
  if (!jobOrSong) return null
  if (jobOrSong.song) {
    return { ...jobOrSong.song, id: jobOrSong.song.id || jobOrSong.id }
  }
  if (jobOrSong.id && (jobOrSong.title || jobOrSong.audio_path || jobOrSong.prompt !== undefined)) {
    return jobOrSong
  }
  return null
}

export const useStudioStore = defineStore('studio', {
  state: () => ({
    engine: { ok: false, loading: true, detail: null, error: null },
    library: [],
    // Remix-first: primary workflow is upload an MP3 idea
    mode: 'remix',
    form: {
      sample_query: '',
      prompt: '',
      lyric_concept: '',
      lyrics: '',
      instrumental: false,
      thinking: false,
      use_format: false,
      duration: 120,
      bpm: 0,
      key: '',
      time_signature: '',
      vocal_language: 'en',
      negative_styles: '',
      audio_cover_strength: 0.85,
      cover_noise_strength: 0.15,
      repainting_start: 0,
      repainting_end: 0,
      seed: -1,
      batch_size: 1,
    },
    srcFile: null,
    refFile: null,
    generating: false,
    jobStatus: '',
    lastResult: null,
    pollAbort: false,
    sectionTags: SECTION_TAGS,
  }),
  getters: {
    needsSource(state) {
      return state.mode === 'remix' || state.mode === 'edit'
    },
    lmConfigured(state) {
      return Boolean(state.engine.detail?.models?.init_llm)
    },
    lmAvailable(state) {
      return Boolean(state.engine.ok && state.engine.detail?.models?.init_llm)
    },
    engineOnline(state) {
      return Boolean(state.engine.ok)
    },
  },
  actions: {
    async refreshHealth() {
      this.engine.loading = true
      try {
        const data = await api.health()
        this.engine = {
          ok: Boolean(data?.ace?.ok),
          loading: false,
          detail: data,
          error: data?.ace?.ok ? null : data?.ace?.error || 'ACE-Step unreachable',
        }
      } catch (err) {
        this.engine = { ok: false, loading: false, detail: null, error: err.message }
      }
    },
    async refreshLibrary() {
      this.library = await api.library()
    },
    insertTag(tag) {
      const current = this.form.lyrics || ''
      const sep = !current || current.endsWith('\n') ? '' : '\n'
      this.form.lyrics = `${current}${sep}${tag}\n`
    },
    validateForGenerate() {
      if (!this.engineOnline) {
        return 'ACE-Step engine is offline. Start it before generating.'
      }
      if (this.mode === 'simple') {
        if (!this.form.sample_query.trim()) return 'Describe the song for Simple mode.'
        if (!this.lmAvailable) {
          return 'Simple mode needs the ACE language model. Set ACESTEP_INIT_LLM=true in ACE-Step-1.5/.env (or use Custom / Remix).'
        }
      }
      if (this.mode === 'custom') {
        if (!this.form.prompt.trim() && !this.form.lyrics.trim() && !this.form.instrumental) {
          return 'Add a style caption, lyrics, or enable Instrumental.'
        }
      }
      if (this.mode === 'remix') {
        if (!asFile(this.srcFile)) return 'Upload a source MP3 (or audio file) for Remix.'
        if (!this.form.prompt.trim() && !this.form.lyric_concept.trim()) {
          return 'Add a style caption (and optional lyric concept) for the remix.'
        }
      }
      if (this.mode === 'edit') {
        if (!asFile(this.srcFile)) return 'Upload source audio for Edit.'
      }
      if (this.form.use_format && !this.lmAvailable) {
        return 'Format with LM needs ACESTEP_INIT_LLM=true and an online engine.'
      }
      return null
    },
    async formatLyrics({ fromConcept = false } = {}) {
      if (!this.lmAvailable) {
        throw new Error('Lyric formatting needs the ACE LM online (ACESTEP_INIT_LLM=true).')
      }
      let prompt = this.form.prompt
      let lyrics = this.form.lyrics
      if (fromConcept && this.form.lyric_concept.trim()) {
        prompt = prompt || this.form.lyric_concept
        if (!lyrics.trim()) {
          lyrics = `Write structured song lyrics for this concept:\n${this.form.lyric_concept}\n\nUse [Verse] / [Chorus] tags.`
        }
      }
      const data = await api.formatLyrics({
        prompt,
        lyrics,
        duration: this.form.duration || null,
        language: this.form.vocal_language || 'en',
      })
      if (data.caption || data.prompt) this.form.prompt = data.caption || data.prompt
      if (data.lyrics) this.form.lyrics = data.lyrics
      return data
    },
    cancelGenerate() {
      this.pollAbort = true
      this.jobStatus = 'Cancelled'
      this.generating = false
    },
    async generate() {
      const validationError = this.validateForGenerate()
      if (validationError) throw new Error(validationError)

      this.generating = true
      this.pollAbort = false
      this.jobStatus = 'Submitting…'
      this.lastResult = null
      try {
        const prompt =
          this.form.prompt.trim() ||
          (this.mode === 'remix' ? this.form.lyric_concept.trim() : '') ||
          this.form.sample_query.trim()

        const payload = {
          mode: this.mode,
          ...this.form,
          prompt,
          bpm: this.form.bpm > 0 ? this.form.bpm : null,
          duration: this.form.duration > 0 ? this.form.duration : null,
          repainting_end: this.form.repainting_end > 0 ? this.form.repainting_end : -1,
          seed: this.form.seed >= 0 ? this.form.seed : null,
          batch_size: Math.max(1, Math.min(4, Number(this.form.batch_size) || 1)),
          allow_lm: this.lmAvailable,
        }
        const files = {}
        const src = asFile(this.srcFile)
        const ref = asFile(this.refFile)
        if (src) files.src_audio = src
        if (ref) files.reference_audio = ref

        const submitted = await api.create(payload, files)
        const taskId = submitted.task_id
        this.jobStatus = `Queued ${taskId?.slice(0, 8) || ''}…`

        const started = Date.now()
        while (Date.now() - started < 600000) {
          if (this.pollAbort) {
            throw new Error('Generation cancelled')
          }
          let job
          try {
            job = await api.job(taskId)
          } catch (err) {
            await this.refreshHealth()
            throw new Error(
              err.message ||
                'Lost connection to ACE-Step while generating. The engine may have crashed loading the model.',
            )
          }
          if (job.status === 1) {
            this.jobStatus = 'Done'
            const song = normalizeSong(job)
            this.lastResult = song
            await this.refreshLibrary()
            return { ...job, song }
          }
          if (job.status === 2) {
            await this.refreshHealth()
            throw new Error(job.error || 'Generation failed')
          }
          this.jobStatus = `Generating… (${job.stage || 'running'})`
          await new Promise((r) => setTimeout(r, 1500))
        }
        throw new Error('Timed out waiting for generation')
      } finally {
        this.generating = false
        this.pollAbort = false
      }
    },
    loadFromLibrary(item) {
      this.form.prompt = item.prompt || ''
      this.form.lyrics = item.lyrics || ''
      this.mode = item.mode === 'simple' ? 'custom' : item.mode || 'custom'
      this.lastResult = normalizeSong(item)
    },
  },
})
