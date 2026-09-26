import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { Quasar, Notify, Dialog, Loading } from 'quasar'
import quasarLang from 'quasar/lang/en-US'
import iconSet from 'quasar/icon-set/material-icons'

import '@quasar/extras/material-icons/material-icons.css'
import '@quasar/extras/roboto-font/roboto-font.css'
import 'quasar/src/css/index.sass'
import './css/app.scss'

import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Quasar, {
  plugins: { Notify, Dialog, Loading },
  lang: quasarLang,
  iconSet,
  config: {
    brand: {
      primary: '#8b5cf6',
      secondary: '#22d3ee',
      accent: '#f472b6',
      dark: '#0b0f19',
      'dark-page': '#070a12',
    },
    dark: true,
  },
})
app.mount('#app')
