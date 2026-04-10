<template>
  <el-dropdown trigger="click" @command="handleLanguageChange" placement="bottom">
    <span class="language-dropdown" :title="'当前语言: ' + currentLanguageLabel">
      <el-icon><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></el-icon>
      <span class="language-text">{{ currentLanguageLabel }}</span>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item
          v-for="lang in languages"
          :key="lang.value"
          :command="lang.value"
          :disabled="lang.value === store.language"
          class="language-item"
        >
          <span>{{ lang.label }}</span>
          <el-icon v-if="lang.value === store.language" class="check-icon"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></el-icon>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useStore } from '../stores/stateStore'
import i18n from '../i18n'

const store = useStore()

const languages = [
  { value: 'en', label: 'English' },
  { value: 'zh', label: '中文' },
  { value: 'es', label: 'Español' },
  { value: 'fr', label: 'Français' },
  { value: 'de', label: 'Deutsch' },
  { value: 'ja', label: '日本語' },
  { value: 'ko', label: '한국어' }
]

const currentLanguageLabel = computed(() => {
  // 优先使用 i18n 的实际语言设置，如果没有则使用 store.language
  const lang = i18n.global.locale.value || store.language || 'zh'
  const current = languages.find(l => l.value === lang)
  return current ? current.label : '中文'
})

const handleLanguageChange = async (lang) => {
  if (lang === store.language) {
    return
  }
  
  store.language = lang
  localStorage.setItem('language', lang)
  
  // 更新 i18n 的全局语言设置
  i18n.global.locale.value = lang
  
  // 只有在用户登录后才发送请求到后端
  if (store.token) {
    try {
      const response = await fetch('http://localhost:5000/api/user/language', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${store.token}`
        },
        body: JSON.stringify({ language: lang })
      })
      
      const result = await response.json()
      
      if (result.code === 0) {
        // 使用浏览器内置的 alert 代替 ElMessage
        alert('Language updated successfully')
        location.reload()
      } else {
        alert(result.message || 'Failed to update language')
      }
    } catch (error) {
      console.error('Language update error:', error)
      // 仅在控制台记录错误，不打扰用户
    }
  } else {
    // 未登录用户，仅刷新页面以应用语言变化
    location.reload()
  }
}
</script>

<style scoped>
.language-dropdown {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  color: var(--text-secondary);
  transition: all 0.3s ease;
  background: linear-gradient(145deg, var(--card-bg), var(--bg-secondary));
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-color);
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.language-dropdown:hover {
  background: linear-gradient(145deg, var(--hover-bg), var(--bg-tertiary));
  color: var(--accent-color);
  transform: translateY(-2px);
  box-shadow: 
    0 8px 25px rgba(79, 172, 254, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.language-text {
  font-weight: 500;
}

.language-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  font-size: 0.9rem;
  color: var(--text-primary);
  transition: color 0.3s;
}

.check-icon {
  color: var(--accent-color);
  transition: color 0.3s;
}
</style>