import { createI18n } from 'vue-i18n'
import en from './en'
import zh from './zh'
import es from './es'
import fr from './fr'
import de from './de'
import ja from './ja'
import ko from './ko'

const messages = {
  en,
  zh,
  es,
  fr,
  de,
  ja,
  ko
}

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  fallbackLocale: 'zh',
  messages,
  missingWarn: false,
  fallbackWarn: false
})

export default i18n