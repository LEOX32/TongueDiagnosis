// i18n 调试脚本
import i18n from './i18n/index.js'

console.log('=== i18n 调试信息 ===')
console.log('当前语言:', i18n.global.locale.value)
console.log('fallbackLocale:', i18n.global.fallbackLocale.value)
console.log('可用语言:', Object.keys(i18n.global.messages.value))
console.log('中文翻译是否存在:', !!i18n.global.messages.value.zh)
console.log('home.hero.title1 的翻译:', i18n.global.messages.value.zh?.home?.hero?.title1)
console.log('home.hero.title2 的翻译:', i18n.global.messages.value.zh?.home?.hero?.title2)
console.log('home.hero.title3 的翻译:', i18n.global.messages.value.zh?.home?.hero?.title3)

// 测试 t 函数
const { t } = i18n.global
console.log('使用 t 函数翻译 home.hero.title1:', t('home.hero.title1'))
