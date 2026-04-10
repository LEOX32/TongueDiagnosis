<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isLoginMode ? t('login.title') : t('register.title')"
    width="500px"
    :close-on-click-modal="false"
    class="auth-dialog"
  >
    <div class="auth-content">
      <div class="form-box" v-loading="loading" element-loading-background="#d3b7d8">
        <div class="login-box" v-if="isLoginMode">
          <loginBlock @login-success="handleLoginSuccess"/>
        </div>
        <div class="register-box" v-else>
          <registerBlock @register-success="handleRegisterSuccess"/>
        </div>
      </div>
      <div class="switch-text">
        <span v-if="isLoginMode">{{ t('login.noAccount') }}</span>
        <span v-else>{{ t('login.alreadyHave') }}</span>
        <el-button type="primary" link @click="toggleMode">
          {{ isLoginMode ? t('register.title') : t('login.title') }}
        </el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import registerBlock from '@/components/Registerblock.vue'
import loginBlock from '@/components/Loginblock.vue'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'login-success'])

const dialogVisible = ref(props.modelValue)
const isLoginMode = ref(true)
const loading = ref(false)

watch(() => props.modelValue, (newVal) => {
  dialogVisible.value = newVal
})

watch(dialogVisible, (newVal) => {
  emit('update:modelValue', newVal)
})

const toggleMode = () => {
  isLoginMode.value = !isLoginMode.value
}

const handleLoginSuccess = () => {
  dialogVisible.value = false
  emit('login-success')
  
  // 登录成功后，清除 localStorage 中的会话缓存和图片数据，避免显示已删除的记录
  localStorage.removeItem('tongueKit_sessions')
  localStorage.removeItem('tongueKit_currentSessionId')
  
  // 清除所有图片缓存
  const keysToRemove = Object.keys(localStorage).filter(key => key.startsWith('picture_'))
  keysToRemove.forEach(key => localStorage.removeItem(key))
  
  console.log('已清除本地会话缓存和图片数据，将从后端重新加载最新记录')
  
  // 延迟刷新页面，确保登录状态已保存
  setTimeout(() => {
    location.reload()
  }, 500)
}

const handleRegisterSuccess = () => {
  isLoginMode.value = true
}
</script>

<style scoped>
.auth-content {
  padding: 20px 0;
}

.form-box {
  min-height: 200px;
}

.switch-text {
  text-align: center;
  margin-top: 20px;
  color: var(--text-secondary);
}

.switch-text span {
  margin-right: 8px;
}
</style>

<style>
.auth-dialog .el-dialog__header {
  background: linear-gradient(135deg, var(--accent-color), rgba(118, 75, 162, 0.8));
  color: white;
  padding: 20px;
  margin: 0;
}

.auth-dialog .el-dialog__title {
  color: white;
  font-size: 1.25rem;
  font-weight: 600;
}

.auth-dialog .el-dialog__headerbtn .el-dialog__close {
  color: white;
}

.auth-dialog .el-dialog__body {
  padding: 30px 40px;
}

[data-theme='dark'] .auth-dialog .el-dialog__header {
  background: linear-gradient(135deg, var(--accent-color), rgba(118, 75, 162, 0.8));
}

[data-theme='dark'] .auth-dialog .el-dialog__title {
  color: white;
}

[data-theme='dark'] .auth-dialog .el-dialog__headerbtn .el-dialog__close {
  color: white;
}

[data-theme='dark'] .switch-text {
  color: var(--text-secondary);
}
</style>
