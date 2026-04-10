<template>
  <div class="login-container">
    <el-card class="login-card" shadow="hover">
      <el-form ref="Email_Password_login" style="max-width: 210px" :model="user" status-icon :rules="rules"
               label-width="auto" class="Email_Password_form" v-loading="loading" element-loading-background="#ffffff"
               size="large">
        <el-form-item label="" prop="Email">
          <el-input v-model="user.Email" :placeholder="t('login.email')" id="l_email" size="large"/>
        </el-form-item>
        <el-form-item label="" prop="Password">
          <el-input v-model="user.Password" :placeholder="t('login.password')" id="l_password" type="password" show-password size="large"/>
          <br>
        </el-form-item>
        <el-form-item>
          <el-button class="login_b" type="primary" @click="login(Email_Password_login)" size="large">{{ t('login.signIn') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import {reactive, ref} from 'vue'
import {ElMessage, type FormInstance, type FormRules} from 'element-plus'
import router from '@/router';
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import i18n from '@/i18n';

const emit = defineEmits(["login-success"])

const { t } = useI18n();

const Email_Password_login = ref<FormInstance>()
let loading = ref(false)
let token = ''
let not_register = ref<boolean>(false)

const validatePassword = (_rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error(t('login.password')))
  } else {
    if (value.length < 6) {
      callback(new Error(t('login.passwordTooShort')))
    } else {
      if (value.length > 20) {
        callback(new Error(t('login.passwordTooLong')))
      } else {
        callback()
      }
    }
  }
}

const validateEmail = (_rule: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error(t('login.email')))
  } else {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      callback(new Error(t('login.validEmail')))
    } else {
      callback()
    }
  }
};

let user = reactive({
  Email: '',
  Password: '',
})

const rules = reactive<FormRules<typeof user>>({
  Email: [{validator: validateEmail, trigger: ['blur']}],
  Password: [{validator: validatePassword, trigger: ['blur']}],
})

const login = (formEl: FormInstance | undefined) => {
  if (!formEl) return
  formEl.validate((valid) => {
    if (valid) {
      loading.value = true
      set_Login_put()
    } else {
      fail_message("Please fill in as required.")
      return false
    }
  })
}

const generate_form = () => {
  let dataform = new FormData()
  dataform.append('email', user.Email)
  dataform.append('password', user.Password)
  return dataform
}

const set_Login_put = () => {
  axios({
    method: 'put',
    data: generate_form(),
    url: '/api/user/login',
    timeout: 20000
  })
      .then(response => {
        loading.value = false
        analyze_response(response.data)

      })
      .catch(error => {
        loading.value = false
        if (error === 'ECONNABORTED') {
          loading.value = false
          fail_message('request timeout')
        } else {
          loading.value = false
          fail_message("Encounter an error, please try again")
          console.error(error);
        }
      });
}

const success_message = (message: string) => {
  ElMessage({
    showClose: true,
    message: message,
    type: 'success',
    duration: 1500
  })
}

const fail_message = (message: string) => {
  ElMessage({
    showClose: true,
    message: message,
    type: 'error',
    duration: 3000
  })
}

const analyze_response = (data: any) => {
     if (data.code === 0) {
       success_message(t('login.signIn'))
       token = data.data.token
       deliver_token(token)
       emit('login-success')
       fetchUserInfo(token)
       router.push('/home')
     } else {
       if (data.code === 101) {
         fail_message(t('login.userNotFound'))
         not_register.value = true
       } else {
         if (data.code === 102) {
           fail_message(t('login.wrongPassword'))
         } else {
           fail_message("Encounter an error, please try again")
         }
       }
     }
   }
  const fetchUserInfo = async (token: string) => {
     try {
       const res = await axios.get('/api/user/info', {
         headers: { Authorization: `Bearer ${token}` }
       })
       const resData = res.data as { code: number; data?: { language?: string } }
       if (resData.code === 0 && resData.data) {
         const language = resData.data.language
         if (language) {
           localStorage.setItem('language', language)
           i18n.global.locale.value = language as 'en' | 'zh' | 'es' | 'fr' | 'de' | 'ja' | 'ko'
         }
       }
     } catch (error) {
       console.error('Failed to fetch user info:', error)
     }
   }
  const deliver_token = (t: string) => {
    localStorage.setItem('token', t)
    axios.defaults.headers.common['Authorization'] = `Bearer ${t}`;
  }
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-card {
  padding: 5px;
  border-radius: 12px;
  max-height: 20%;
  background-color: transparent;
}

.login_b {
  width: 100%;
  margin-top: 20px;
}

.reset_l {
  justify-content: flex-end;
}

/* Element Plus 组件深色模式支持 */
[data-theme='dark'] :deep(.el-button--primary) {
  --el-button-bg-color: var(--accent-color);
  --el-button-border-color: var(--accent-color);
  --el-button-text-color: #ffffff;
  --el-button-hover-bg-color: var(--accent-hover);
  --el-button-hover-border-color: var(--accent-hover);
  --el-button-hover-text-color: #ffffff;
  --el-button-active-bg-color: var(--accent-hover);
  --el-button-active-border-color: var(--accent-hover);
  --el-button-active-text-color: #ffffff;
}

[data-theme='dark'] :deep(.el-input__wrapper) {
  --el-input-bg-color: var(--input-bg);
  --el-input-text-color: var(--text-primary);
  --el-input-border-color: var(--border-color);
  --el-input-hover-border-color: var(--accent-color);
  --el-input-focus-border-color: var(--accent-color);
  --el-input-placeholder-color: var(--text-tertiary);
}

[data-theme='dark'] :deep(.el-input__inner) {
  background-color: var(--input-bg);
  color: var(--text-primary);
}

[data-theme='dark'] :deep(.el-input__inner::placeholder) {
  color: var(--text-tertiary);
}

[data-theme='dark'] :deep(.el-form-item__label) {
  color: var(--text-primary);
}

[data-theme='dark'] :deep(.el-form-item__error) {
  color: #f56c6c;
}

[data-theme='dark'] :deep(.el-loading-mask) {
  background-color: rgba(0, 0, 0, 0.7);
}

[data-theme='dark'] :deep(.el-loading-spinner .circular) {
  stroke: var(--accent-color);
}

[data-theme='dark'] :deep(.el-card) {
  --el-card-bg-color: transparent;
  background-color: transparent;
  border-color: transparent;
}

[data-theme='dark'] :deep(.el-card__body) {
  background-color: transparent;
  color: var(--text-primary);
}
</style>
