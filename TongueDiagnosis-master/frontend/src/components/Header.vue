<script setup>
import axios from "axios";
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStateStore } from '@/stores/stateStore'
import { useI18n } from 'vue-i18n'
import i18n from '../i18n'
import LanguageSelector from './LanguageSelector.vue'
import { ElMessage } from 'element-plus'

const { t } = useI18n()

const store = useStateStore()
const router = useRouter()
const route = useRoute()
const activeIndex = ref('')
const isAuthenticated = ref(false)
const userInfo = ref({
  name: 'Test User',
  avatar: '/static/userDefault.jpg',
})
const isScrolled = ref(false)
const isMobileMenuOpen = ref(false)

const shouldShowSearchAndHelp = computed(() => {
  return route.path !== '/home' && route.path !== '/register'
})

const setActiveIndex = () => {
  activeIndex.value = route.path === '/check' ? '3' : '2'
}

const fetchUserInfo = async () => {
     const token = localStorage.getItem('token')
     if (!token) {
       isAuthenticated.value = false
       return
     }
     try {
       const res = await axios.get('/api/user/info', {
         headers: { Authorization: `Bearer ${token}` }
       })
       if (res.data.code === 0) {
         isAuthenticated.value = true
         if (res.data.data) {
           userInfo.value = { ...userInfo.value, ...res.data.data }
           // 注意：优先使用 localStorage 中用户选择的语言，而不是后端的语言设置
           // 只有当 localStorage 中没有设置时，才使用后端返回的语言
           const storedLang = localStorage.getItem('language')
           const validLangs = ['zh', 'en', 'es', 'fr', 'de', 'ja', 'ko']
           if (!storedLang || !validLangs.includes(storedLang)) {
             // localStorage 中没有有效语言设置，使用后端返回的
             if (res.data.data.language && validLangs.includes(res.data.data.language)) {
               store.language = res.data.data.language
               localStorage.setItem('language', res.data.data.language)
               i18n.global.locale.value = res.data.data.language
             }
           }
         }
       } else {
         localStorage.removeItem('token')
         isAuthenticated.value = false
       }
     } catch (error) {
       console.error('获取用户信息失败:', error)
       localStorage.removeItem('token')
       isAuthenticated.value = false
     }
   }

const handleScroll = () => {
  isScrolled.value = window.scrollY > 50
}

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const logout = () => {
  localStorage.removeItem('token')
  isAuthenticated.value = false
  isMobileMenuOpen.value = false
  router.push('/register')
}

const toggleTheme = () => {
  store.toggleTheme()
}

const handleExport = () => {
  const mainComponent = store.mainComponent
  if (mainComponent && mainComponent.getCurrentSession) {
    const currentSession = mainComponent.getCurrentSession()
    if (currentSession) {
      // 直接调用导出功能
      const content = currentSession.messages
        .filter(msg => !msg.loading && msg.text)
        .map(msg => {
          const role = msg.isUser ? '用户' : 'AI'
          const time = msg.time
          // 处理图片消息，避免导出 base64 乱码
          if (msg.isPicture || (msg.text && msg.text.length > 1000 && msg.text.startsWith('data:image'))) {
            return `[${time}] ${role}:\n[图片]\n`
          }
          return `[${time}] ${role}:\n${msg.text}\n`
        })
        .join('\n')
      
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `对话记录_${new Date().getTime()}.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      // 显示成功消息
      ElMessage({
        showClose: true,
        message: '对话已导出',
        type: 'success',
        duration: 2000
      })
    }
  }
}

const showSearchDialog = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const quickSearchQuery = ref('')
const searchIsLoading = ref(false)
const selectedRecords = ref([])

const closeSearchDialog = () => {
  showSearchDialog.value = false
}

const toggleRecordSelection = (record) => {
  const index = selectedRecords.value.findIndex(r => 
    r.sessionId === record.sessionId && r.messageIndex === record.messageIndex
  )
  
  if (index > -1) {
    // 取消选中
    selectedRecords.value.splice(index, 1)
  } else {
    // 选中记录
    selectedRecords.value.push(record)
  }
  
  console.log('Selected records:', selectedRecords.value)
}

const isRecordSelected = (record) => {
  return selectedRecords.value.some(r => 
    r.sessionId === record.sessionId && r.messageIndex === record.messageIndex
  )
}

const performQuickSearch = async () => {
  console.log('performQuickSearch called');
  console.log('quickSearchQuery.value:', quickSearchQuery.value);
  
  if (!quickSearchQuery.value.trim()) {
    console.log('Empty search query');
    return
  }
  
  searchIsLoading.value = true
  
  try {
    // 模拟搜索过程，确保对话框能显示
    setTimeout(async () => {
      console.log('Simulating search process');
      
      // 获取所有会话
      const allSessions = store.getAllSessions()
      console.log('allSessions length:', allSessions ? allSessions.length : 0);
      
      // 检查是否有活跃会话
      const hasActiveSession = store.mainComponent && store.mainComponent.getCurrentSession && store.mainComponent.getCurrentSession();
      console.log('Has active session:', !!hasActiveSession);
      
      // 执行搜索
      if (allSessions && Array.isArray(allSessions)) {
        const query = quickSearchQuery.value.toLowerCase()
        console.log('Search query:', query);
        
        if (hasActiveSession) {
          // 局部搜索：只在当前活跃会话中搜索
          const currentSessionId = hasActiveSession.id;
          searchResults.value = allSessions.filter(msg => {
            const text = msg.text.toLowerCase()
            return msg.sessionId === currentSessionId && text.includes(query)
          })
          console.log('Local search results length:', searchResults.value.length);
        } else {
          // 全局搜索：在所有记录中搜索
          searchResults.value = allSessions.filter(msg => {
            const text = msg.text.toLowerCase()
            return text.includes(query)
          })
          console.log('Global search results length:', searchResults.value.length);
        }
      } else {
        // 如果没有会话数据，使用模拟数据
        searchResults.value = [
          {
            sessionId: 'mock_session_1',
            sessionName: '模拟会话',
            messageIndex: 0,
            text: '这是一条模拟的搜索结果，用于测试搜索功能。',
            isUser: false,
            time: new Date().toLocaleString()
          }
        ]
        console.log('Using mock search results');
      }
      
      // 显示搜索对话框
      console.log('Showing search dialog');
      showSearchDialog.value = true
    }, 500);
  } catch (error) {
    console.error('Error in performQuickSearch:', error);
    searchResults.value = []
    showSearchDialog.value = true
  } finally {
    searchIsLoading.value = false
  }
}

const jumpToMessage = (sessionId, messageIndex) => {
  console.log('jumpToMessage called:', sessionId, messageIndex);
  store.scrollToMessage(sessionId, messageIndex)
  closeSearchDialog()
}

const highlightKeyword = (text, keyword) => {
  if (!keyword || !text) return text;
  
  // 分割句子
  const sentences = text.split(/[。！？.!?]/).filter(s => s.trim());
  
  // 找到所有包含关键词的句子
  const matchedSentences = sentences.filter(sentence => 
    sentence.toLowerCase().includes(keyword.toLowerCase())
  );
  
  if (matchedSentences.length === 0) return text;
  
  // 高亮所有匹配句子中的关键词并拼接
  const highlightedSentences = matchedSentences.map(sentence => {
    return sentence.replace(
      new RegExp(keyword, 'gi'),
      '<span style="color: red; font-weight: bold; cursor: pointer; text-decoration: underline;">$&</span>'
    );
  });
  
  // 用换行符连接所有匹配的句子，确保每句话下空一行
  return highlightedSentences.map(sentence => sentence + '。').join('<br><br>');
}

watch(() => route.path, () => {
  setActiveIndex()
  fetchUserInfo()
  isMobileMenuOpen.value = false
})

onMounted(() => {
  setActiveIndex()
  fetchUserInfo()
  window.addEventListener('scroll', handleScroll)
})
</script>

<template>
  <header class="modern-header" :class="{ 'scrolled': isScrolled }">
    <div class="header-container">
      <div class="logo-section">
        <div class="logo-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L15.09 8.26L22 9L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9L8.91 8.26L12 2Z"
                  fill="currentColor"/>
          </svg>
        </div>
        <div class="logo-text">
          <span class="logo-title">TongueKit</span>
          <span class="logo-subtitle">AI Diagnosis</span>
        </div>
      </div>
      <nav class="desktop-nav">
        <div class="nav-items">
          <router-link
                to="/home"
                class="nav-item"
                :class="{ 'active': activeIndex === '2' }"
            >
              <div class="nav-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z"
                        stroke="currentColor" stroke-width="2"/>
                  <path d="M9 22V12H15V22" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <span>{{ t('nav.home') }}</span>
            </router-link>
            <router-link
                to="/check"
                class="nav-item"
                :class="{ 'active': activeIndex === '3' }"
            >
              <div class="nav-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z"
                        stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <span>{{ t('nav.examination') }}</span>
            </router-link>
        </div>
      </nav>
      <div class="user-section">
        <!-- 搜索输入框 -->
        <div v-if="shouldShowSearchAndHelp" class="search-input-wrapper">
          <el-icon class="search-icon"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></el-icon>
          <input 
            v-model="quickSearchQuery" 
            :placeholder="t('searchPlaceholder')" 
            class="search-input"
            @keyup.enter="performQuickSearch"
          />
        </div>
        
        <!-- 导出按钮 -->
        <button v-if="shouldShowSearchAndHelp" class="language-dropdown help-dropdown" @click="handleExport" title="导出当前对话为文本文件">
          <el-icon><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg></el-icon>
          <span class="language-text">{{ t('export') }}</span>
        </button>
        
        <!-- 语言选择器 -->
        <LanguageSelector />
        
        <!-- 主题切换按钮 -->
        <button class="theme-toggle" @click="toggleTheme" :title="store.theme === 'light' ? '切换到深色模式' : '切换到浅色模式'">
          <svg v-if="store.theme === 'light'" width="20" height="20" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="12" y1="1" x2="12" y2="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="12" y1="21" x2="12" y2="23" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="1" y1="12" x2="3" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="21" y1="12" x2="23" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        
        <div v-if="isAuthenticated" class="user-menu">
          <el-dropdown trigger="click" popper-class="custom-dropdown">
            <div class="user-profile">
              <div class="user-avatar">
                <img :src="userInfo.avatar" :alt="userInfo.name" />
                <div class="user-status"></div>
              </div>
              <div class="user-info">
                <span class="user-name">{{ userInfo.name }}</span>
                <span class="user-role">{{ t('user.premium') }}</span>
              </div>
              <div class="dropdown-arrow">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
            </div>
            <template #dropdown>
              <el-dropdown-menu class="custom-dropdown-menu">
                <el-dropdown-item class="dropdown-header">
                  <div class="user-card">
                    <img :src="userInfo.avatar" :alt="userInfo.name" class="user-card-avatar" />
                    <div class="user-card-info">
                      <div class="user-card-name">{{ userInfo.name }}</div>
                      <div class="user-card-email">{{ userInfo.email }}</div>
                    </div>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item divided class="menu-item danger" @click="logout">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9M16 17L21 12M21 12L16 7M21 12H9"
                          stroke="currentColor" stroke-width="2"/>
                  </svg>
                  <span>{{ t('nav.logout') }}</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <div v-else class="auth-buttons">
          <router-link to="/register" class="auth-button">
            <span>{{ t('nav.signIn') }}</span>
          </router-link>
        </div>
        <button class="mobile-menu-button" @click="toggleMobileMenu">
          <svg v-if="!isMobileMenuOpen" width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M3 12H21M3 6H21M3 18H21" stroke="currentColor" stroke-width="2"/>
          </svg>
          <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2"/>
          </svg>
        </button>
      </div>
    </div>
    <div class="mobile-menu" :class="{ 'open': isMobileMenuOpen }">
      <div class="mobile-nav">
        <router-link
            to="/home"
            class="mobile-nav-item"
            :class="{ 'active': activeIndex === '2' }"
            @click="isMobileMenuOpen = false"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z"
                  stroke="currentColor" stroke-width="2"/>
            <path d="M9 22V12H15V22" stroke="currentColor" stroke-width="2"/>
          </svg>
          <span>{{ t('nav.home') }}</span>
        </router-link>
        <router-link
            to="/check"
            class="mobile-nav-item"
            :class="{ 'active': activeIndex === '3' }"
            @click="isMobileMenuOpen = false"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z"
                  stroke="currentColor" stroke-width="2"/>
          </svg>
          <span>{{ t('nav.examination') }}</span>
        </router-link>
        <div v-if="isAuthenticated" class="mobile-user-section">
          <div class="mobile-user-profile">
            <img :src="userInfo.avatar" :alt="userInfo.name" />
            <div class="mobile-user-info">
              <span class="mobile-user-name">{{ userInfo.name }}</span>
              <span class="mobile-user-role">{{ t('user.premium') }}</span>
            </div>
          </div>
          <div class="mobile-user-actions">
            <button class="mobile-action-item">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21M16 7C16 9.20914 14.2091 11 12 11C9.79086 11 8 9.20914 8 7C8 4.79086 9.79086 3 12 3C14.2091 3 16 4.79086 16 7Z"
                      stroke="currentColor" stroke-width="2"/>
              </svg>
              <span>{{ t('nav.profile') }}</span>
            </button>
            <button class="mobile-action-item" @click="logout">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9M16 17L21 12M21 12L16 7M21 12H9"
                      stroke="currentColor" stroke-width="2"/>
              </svg>
              <span>{{ t('nav.logout') }}</span>
            </button>
          </div>
        </div>
        <div v-else class="mobile-auth">
          <router-link to="/register" class="mobile-auth-button" @click="isMobileMenuOpen = false">
            {{ t('nav.signIn') }} / {{ t('login.register') }}
          </router-link>
        </div>
      </div>
    </div>
    
    <!-- 搜索对话框 -->
    <div v-if="showSearchDialog" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: flex-start; justify-content: center; padding-top: 80px; z-index: 9999;">
      <div style="background: white; padding: 20px; border-radius: 8px; width: 600px; max-width: 90vw;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
          <h2>搜索结果</h2>
          <button style="background: none; border: none; font-size: 20px; cursor: pointer;" @click="closeSearchDialog">&times;</button>
        </div>
        <div>
          <h3>搜索关键词: {{ quickSearchQuery }}</h3>
          <p>找到 {{ searchResults.length }} 条结果</p>
          <div style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">
            {{ store.mainComponent && store.mainComponent.getCurrentSession && store.mainComponent.getCurrentSession() ? '已打开记录，正在进行局部搜索' : '未打开记录，正在进行全局搜索' }}
          </div>
          <div 
            v-for="(result, index) in searchResults"
            :key="index"
            style="padding: 10px; margin: 10px 0; background: #f5f5f5; border-radius: 8px; cursor: pointer;"
            @click="jumpToMessage(result.sessionId, result.messageIndex)"
          >
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
              <strong>{{ result.isUser ? '用户' : 'AI' }}</strong>
              <span>{{ result.sessionName }}</span>
              <span style="color: #999;">{{ result.time }}</span>
            </div>
            <div style="font-size: 0.8rem; color: #666; margin-bottom: 5px;">
              记录位置: 会话 {{ result.sessionId }} - 消息 #{{ result.messageIndex }}
            </div>
            <div v-html="highlightKeyword(result.text, quickSearchQuery)"></div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.modern-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
}

.modern-header.scrolled {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.15);
}

.header-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 70px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 24px;
  color: var(--accent-color);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.logo-icon:hover {
  transform: scale(1.05);
  background: rgba(64, 158, 255, 0.2);
}

.logo-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.logo-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

.logo-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.desktop-nav {
  display: flex;
  align-items: center;
}

.nav-items {
  display: flex;
  gap: 2px;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  height: 70px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.3s ease;
  border-bottom: 2px solid transparent;
  position: relative;
  background: linear-gradient(145deg, #ffffff, #f0f0f0);
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  border-radius: 0 0 8px 8px;
  margin: 0 2px;
  transform: translateY(0);
}

.nav-item:hover {
  color: var(--accent-color);
  background: linear-gradient(145deg, #f0f8ff, #e6f2ff);
  box-shadow: 
    0 6px 12px rgba(64, 158, 255, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
}

.nav-item.active {
  color: var(--accent-color);
  border-bottom-color: var(--accent-color);
  background: linear-gradient(145deg, #e6f2ff, #d6e8ff);
  box-shadow: 
    0 8px 16px rgba(64, 158, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
}

.nav-icon {
  margin-bottom: 4px;
  font-size: 16px;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  background: linear-gradient(145deg, #ffffff, #f5f5f5);
  border-radius: 20px;
  padding: 0 12px;
  transition: all 0.3s ease;
  border: 1px solid #e0e0e0;
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  transform: translateY(0);
}

.search-input-wrapper:hover {
  background: linear-gradient(145deg, #f0f8ff, #e6f2ff);
  border-color: var(--accent-color);
  box-shadow: 
    0 6px 12px rgba(64, 158, 255, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}

.search-icon {
  color: var(--text-tertiary);
  margin-right: 8px;
  font-size: 14px;
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  padding: 8px 0;
  color: var(--text-primary);
  font-size: 14px;
  min-width: 200px;
  transition: all 0.3s ease;
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

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
  font-size: 14px;
  font-weight: 500;
}

.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(145deg, var(--card-bg), var(--bg-secondary));
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-color);
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
}

.theme-toggle:hover {
  background: linear-gradient(145deg, var(--hover-bg), var(--bg-tertiary));
  color: var(--accent-color);
  transform: scale(1.05) translateY(-2px);
  box-shadow: 
    0 8px 25px rgba(79, 172, 254, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.user-menu {
  display: flex;
  align-items: center;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(145deg, #ffffff, #f5f5f5);
  border: 1px solid #e0e0e0;
  box-shadow: 
    0 4px 8px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  transform: translateY(0);
}

.user-profile:hover {
  background: linear-gradient(145deg, #f0f8ff, #e6f2ff);
  border-color: var(--accent-color);
  box-shadow: 
    0 6px 16px rgba(64, 158, 255, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
}

.user-avatar {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid rgba(64, 158, 255, 0.2);
  transition: all 0.3s ease;
}

.user-profile:hover .user-avatar {
  border-color: var(--accent-color);
  transform: scale(1.05);
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-status {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #4caf50;
  border: 2px solid white;
  animation: pulse 2s infinite;
}

.user-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.user-role {
  font-size: 12px;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-arrow {
  font-size: 12px;
  color: var(--text-tertiary);
  transition: transform 0.3s ease;
}

.user-profile:hover .dropdown-arrow {
  transform: rotate(180deg);
  color: var(--accent-color);
}

.auth-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.auth-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  text-decoration: none;
  transition: all 0.3s ease;
  color: var(--accent-color);
  border: 1px solid var(--accent-color);
  font-size: 14px;
  font-weight: 500;
}

.auth-button:hover {
  background: var(--accent-color);
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.mobile-menu-button {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--bg-secondary);
  border: 1px solid transparent;
  color: var(--text-secondary);
}

.mobile-menu-button:hover {
  background: var(--bg-tertiary);
  border-color: var(--border-color);
  color: var(--text-primary);
  transform: scale(1.05);
}

.mobile-menu {
  position: fixed;
  top: 70px;
  left: 0;
  right: 0;
  height: 0;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-color);
  transition: all 0.3s ease;
  z-index: 999;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.mobile-menu.open {
  height: auto;
  max-height: 500px;
  overflow-y: auto;
}

.mobile-nav {
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 10px;
}

.mobile-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px 20px;
  border-radius: 10px;
  text-decoration: none;
  transition: all 0.3s ease;
  color: var(--text-secondary);
  border: 1px solid transparent;
}

.mobile-nav-item:hover {
  background: var(--bg-secondary);
  border-color: var(--border-color);
  color: var(--text-primary);
}

.mobile-nav-item.active {
  background: rgba(64, 158, 255, 0.1);
  border-color: var(--accent-color);
  color: var(--accent-color);
}

.mobile-user-section {
  margin-top: 10px;
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
}

.mobile-user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  border-radius: 10px;
  background: var(--bg-secondary);
  margin-bottom: 15px;
}

.mobile-user-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.mobile-user-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mobile-user-role {
  font-size: 13px;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mobile-user-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mobile-action-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-secondary);
  font-size: 14px;
}

.mobile-action-item:hover {
  background: var(--bg-secondary);
  border-color: var(--border-color);
  color: var(--text-primary);
}

.mobile-auth {
  margin-top: 10px;
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
}

.mobile-auth-button {
  display: block;
  text-align: center;
  padding: 15px;
  border-radius: 10px;
  text-decoration: none;
  transition: all 0.3s ease;
  color: var(--accent-color);
  border: 1px solid var(--accent-color);
  font-size: 15px;
  font-weight: 600;
}

.mobile-auth-button:hover {
  background: var(--accent-color);
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.custom-dropdown {
  border-radius: 10px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.custom-dropdown-menu {
  min-width: 280px;
  border-radius: 10px;
  overflow: hidden;
}

.dropdown-header {
  padding: 0 !important;
  border-bottom: 1px solid var(--border-color);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: var(--bg-secondary);
}

.user-card-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--accent-color);
}

.user-card-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.user-card-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-card-email {
  font-size: 13px;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 15px !important;
  transition: all 0.3s ease;
}

.menu-item:hover {
  background: var(--bg-secondary) !important;
}

.menu-item.danger:hover {
  background: rgba(245, 108, 108, 0.1) !important;
}

.menu-item.danger {
  color: #f56c6c;
}

@media (max-width: 1024px) {
  .header-container {
    padding: 0 15px;
  }
  
  .search-input {
    min-width: 160px;
  }
  
  .nav-item {
    padding: 0 16px;
  }
}

@media (max-width: 768px) {
  .desktop-nav {
    display: none;
  }
  
  .mobile-menu-button {
    display: flex;
  }
  
  .search-input {
    min-width: 120px;
    font-size: 13px;
  }
  
  .logo-title {
    font-size: 16px;
  }
  
  .logo-subtitle {
    font-size: 11px;
  }
  
  .language-dropdown .language-text {
    display: none;
  }
  
  .user-info {
    display: none;
  }
  
  .user-profile {
    padding: 6px;
  }
  
  .user-avatar {
    width: 32px;
    height: 32px;
  }
}

@media (max-width: 480px) {
  .header-container {
    height: 60px;
  }
  
  .mobile-menu {
    top: 60px;
  }
  
  .logo-section {
    gap: 8px;
  }
  
  .logo-icon {
    width: 32px;
    height: 32px;
  }
  
  .logo-title {
    font-size: 14px;
  }
  
  .logo-subtitle {
    display: none;
  }
  
  .search-input-wrapper {
    padding: 0 8px;
  }
  
  .search-input {
    min-width: 100px;
    font-size: 12px;
  }
  
  .user-section {
    gap: 6px;
  }
  
  .theme-toggle,
  .language-dropdown,
  .mobile-menu-button {
    width: 32px;
    height: 32px;
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 深色模式适配 */
[data-theme="dark"] .modern-header {
  background: rgba(26, 26, 26, 0.9);
  border-bottom-color: rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.3);
}

[data-theme="dark"] .modern-header.scrolled {
  background: rgba(26, 26, 26, 0.95);
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.4);
}

[data-theme="dark"] .logo-title {
  color: #e5e5e5;
}

[data-theme="dark"] .logo-subtitle {
  color: #b0b0b0;
}

[data-theme="dark"] .nav-item {
  color: #b0b0b0;
  background: linear-gradient(145deg, #333333, #2a2a2a);
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  border: 1px solid #404040;
}

[data-theme="dark"] .nav-item:hover {
  color: var(--accent-color);
  background: linear-gradient(145deg, #3a3a3a, #303030);
  box-shadow: 
    0 6px 12px rgba(64, 158, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  border-color: var(--accent-color);
}

[data-theme="dark"] .nav-item.active {
  color: var(--accent-color);
  background: linear-gradient(145deg, #303030, #2a2a2a);
  box-shadow: 
    0 8px 16px rgba(64, 158, 255, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  border-color: var(--accent-color);
}

[data-theme="dark"] .search-input-wrapper {
  background: linear-gradient(145deg, #333333, #2a2a2a);
  border: 1px solid #404040;
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

[data-theme="dark"] .search-input-wrapper:hover {
  background: linear-gradient(145deg, #3a3a3a, #303030);
  border-color: var(--accent-color);
  box-shadow: 
    0 6px 12px rgba(64, 158, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

[data-theme="dark"] .search-icon {
  color: #808080;
}

[data-theme="dark"] .search-input {
  color: #e5e5e5;
}

[data-theme="dark"] .search-input::placeholder {
  color: #808080;
}

[data-theme="dark"] .language-dropdown {
  color: #b0b0b0;
}

[data-theme="dark"] .language-dropdown:hover {
  background: #2d2d2d;
  border-color: #404040;
  color: #e5e5e5;
}

[data-theme="dark"] .theme-toggle {
  background: #2d2d2d;
  color: #b0b0b0;
}

[data-theme="dark"] .theme-toggle:hover {
  background: #3a3a3a;
  border-color: #404040;
  color: #e5e5e5;
}

[data-theme="dark"] .user-profile {
  background: linear-gradient(145deg, #333333, #2a2a2a);
  border: 1px solid #404040;
  box-shadow: 
    0 4px 8px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

[data-theme="dark"] .user-profile:hover {
  background: linear-gradient(145deg, #3a3a3a, #303030);
  border-color: var(--accent-color);
  box-shadow: 
    0 6px 16px rgba(64, 158, 255, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

[data-theme="dark"] .user-name {
  color: #e5e5e5;
}

[data-theme="dark"] .user-role {
  color: #808080;
}

[data-theme="dark"] .dropdown-arrow {
  color: #808080;
}

[data-theme="dark"] .user-profile:hover .dropdown-arrow {
  color: var(--accent-color);
}

[data-theme="dark"] .mobile-menu-button {
  background: #2d2d2d;
  color: #b0b0b0;
}

[data-theme="dark"] .mobile-menu-button:hover {
  background: #3a3a3a;
  border-color: #404040;
  color: #e5e5e5;
}

[data-theme="dark"] .mobile-menu {
  background: rgba(26, 26, 26, 0.95);
  border-bottom-color: #404040;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}

[data-theme="dark"] .mobile-nav-item {
  color: #b0b0b0;
}

[data-theme="dark"] .mobile-nav-item:hover {
  background: #2d2d2d;
  border-color: #404040;
  color: #e5e5e5;
}

[data-theme="dark"] .mobile-nav-item.active {
  background: rgba(64, 158, 255, 0.15);
  border-color: var(--accent-color);
  color: var(--accent-color);
}

[data-theme="dark"] .mobile-user-profile {
  background: #2d2d2d;
}

[data-theme="dark"] .mobile-user-name {
  color: #e5e5e5;
}

[data-theme="dark"] .mobile-user-role {
  color: #808080;
}

[data-theme="dark"] .mobile-action-item {
  color: #b0b0b0;
}

[data-theme="dark"] .mobile-action-item:hover {
  background: #2d2d2d;
  border-color: #404040;
  color: #e5e5e5;
}

[data-theme="dark"] .custom-dropdown {
  border-color: #404040;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

[data-theme="dark"] .user-card {
  background: #2d2d2d;
}

[data-theme="dark"] .user-card-name {
  color: #e5e5e5;
}

[data-theme="dark"] .user-card-email {
  color: #808080;
}

[data-theme="dark"] .menu-item:hover {
  background: #2d2d2d !important;
}

[data-theme="dark"] .menu-item.danger:hover {
  background: rgba(245, 108, 108, 0.15) !important;
}
</style>