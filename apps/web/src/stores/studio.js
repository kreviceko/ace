import { defineStore } from 'pinia'
import { api } from '@/api/client'

const SECTION_TAGS = ['[Intro]', '[Verse]', '[Pre-Chorus]', '[Chorus]', '[Bridge]', '[Outro]', '[Instrumental]']

export const useStudioStore = defineStore('studio', {
  state: () => ({
    engine: { ok: false, loading: true, detail: null, error: null },
    library: [],
    mode: 'custom',
    form: {
      sample_query: '',
      prompt: '',
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
      audio_cover_strength: 1,
      cover_noise_strength: 0,
      repainting_start: 0,
      repainting_end: 0,
    },
    srcFile: null,
    refFile: null,
    generating: false,
    jobStatus: '',
    lastResult: null,
    sectionTags: SECTION_TAGS,
  }),
  getters: {
    needsSource(state) {
      return state.mode === 'remix' || state.mode === 'edit'
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
    async formatLyrics() {
      const data = await api.formatLyrics({
        prompt: this.form.prompt,
        lyrics: this.form.lyrics,
        duration: this.form.duration || null,
        language: this.form.vocal_language || 'en',
      })
      if (data.caption || data.prompt) this.form.prompt = data.caption || data.prompt
      if (data.lyrics) this.form.lyrics = data.lyrics
      return data
    },
    async generate() {
      this.generating = true
      this.jobStatus = 'Submitting…'
      this.lastResult = null
      try {
        const payload = {
          mode: this.mode,
          ...this.form,
          bpm: this.form.bpm > 0 ? this.form.bpm : null,
          duration: this.form.duration > 0 ? this.form.duration : null,
          repainting_end: this.form.repainting_end > 0 ? this.form.repainting_end : -1,
        }
        const files = {}
        if (this.srcFile) files.src_audio = this.srcFile
        if (this.refFile) files.reference_audio = this.refFile

        const submitted = await api.create(payload, files)
        const taskId = submitted.task_id
        this.jobStatus = `Queued ${taskId?.slice(0, 8) || ''}…`

        // Poll until done
        const started = Date.now()
        while (Date.now() - started < 600000) {
          const job = await api.job(taskId)
          if (job.status === 1) {
            this.jobStatus = 'Done'
            this.lastResult = job
            await this.refreshLibrary()
            return job
          }
          if (job.status === 2) {
            throw new Error(job.error || 'Generation failed')
          }
          this.jobStatus = `Generating… (${job.stage || 'running'})`
          await new Promise((r) => setTimeout(r, 1500))
        }
        throw new Error('Timed out waiting for generation')
      } finally {
        this.generating = false
      }
    },
    loadFromLibrary(item) {
      this.form.prompt = item.prompt || ''
      this.form.lyrics = item.lyrics || ''
      this.mode = item.mode || 'custom'
      this.lastResult = item
    },
  },
})
