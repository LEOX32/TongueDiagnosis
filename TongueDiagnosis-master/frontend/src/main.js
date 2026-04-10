import './assets/main.css'
import {createApp} from 'vue'
import {createPinia} from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import VueAxios from 'vue-axios'
import settings from './config/config.js'
import i18n from './i18n'
import { useStateStore } from './stores/stateStore'

let token = localStorage.getItem('token');

axios.defaults.headers.common['Authorization'] = "Bearer " + token

const app = createApp(App)
app.use(createPinia())

const store = useStateStore()
store.initialize()

// 使用 localStorage 中存储的语言，如果没有则使用中文
const storedLang = localStorage.getItem('language')
const validLangs = ['zh', 'en', 'es', 'fr', 'de', 'ja', 'ko']
const initialLang = validLangs.includes(storedLang) ? storedLang : 'zh'
store.language = initialLang
// 只在语言改变时才更新 localStorage
if (storedLang !== initialLang) {
  localStorage.setItem('language', initialLang)
}
i18n.global.locale.value = initialLang

app.use(i18n)
app.use(router)
app.use(VueAxios, axios)
app.config.globalProperties.$axios = axios

app.use(ElementPlus, {
  size: 'small', 
  zIndex: 3000,
  locale: initialLang === 'zh' ? zhCn : {}
})

app.mount('#app')

router.beforeEach((to, from, next) => {
    // Using the route guard, if the user is not logged in, they will be redirected to the login page.
    if (to.matched.some((auth) => auth.meta.requireAuth)) {
        let token = localStorage.getItem("token");
        if (token) {
            next();
        } else {
            next({
                path: '/register'
            });
        }
    } else {
        next();
    }
})
