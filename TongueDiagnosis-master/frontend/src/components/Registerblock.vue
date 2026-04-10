<template>
  <div class="register-container">
    <el-card class="register-card" shadow="hover">
      <el-form ref="Email_Password_register" style="max-width: 210px;margin-top: 10px" :model="user" status-icon :rules="rules"
               label-width="auto" class="Email_Password_form" v-loading="loading" element-loading-background="#ffffff"
               size="large">
        <el-form-item label="" prop="Email">
          <el-input v-model="user.Email" :placeholder="t('register.email')" id="r_email" size="large"/>
        </el-form-item>
        <el-form-item label="" prop="Password">
          <el-input v-model="user.Password" :placeholder="t('register.password')" id="r_password" type="password"
                    show-password size="large"/>
        </el-form-item>
        <el-form-item label="" prop="checkPassword">
          <el-input v-model="user.checkPassword" :placeholder="t('register.confirmPassword')" id="r_cpassword" type="password" show-password
                    size="large"/>
          <br>
        </el-form-item>
        <el-form-item>
          <br>
          <el-button class="register_b" type="primary" @click="register(Email_Password_register)" size="large">{{ t('register.signUp') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import {reactive, ref} from 'vue'
import {ElMessage, type FormInstance, type FormRules} from 'element-plus'
const emit = defineEmits(["change", "register-success"])
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const Email_Password_register = ref<FormInstance>()
let loading = ref(false)
const timeout = 20000
let finish_register = ref<boolean>(false)

const validatePassword = (_: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error(t('register.password')))
  } else {
    const pattern = /^[a-zA-Z0-9]+$/;
    if (value.length < 6) {
      callback(new Error(t('register.passwordTooShort')))
    } else {
      if (value.length > 20) {
        callback(new Error(t('register.passwordTooLong')))
      } else {
        if (pattern.test(value)) {
          callback()
        } else {
          callback(new Error(t('register.noSpecialChars')))
        }
      }
    }
  }
}

const validateEmail = (_: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error(t('register.email')))
  } else {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      callback(new Error(t('register.validEmail')))
    } else {
      callback();
    }
  }
};

const validatecheckPassword = (_: any, value: any, callback: any) => {
  if (value === '') {
    callback(new Error(t('register.confirmPassword')))
  } else {
    if (value !== user.Password) {
      callback(new Error(t('register.passwordsDoNotMatch')))
    } else {
      callback()
    }
  }
}

const user = reactive({
  Email: '',
  Password: '',
  checkPassword: '',
})

const rules = reactive<FormRules<typeof user>>({
  Email: [{validator: validateEmail, trigger: ['blur']}],
  Password: [{validator: validatePassword, trigger: ['blur']}],
  checkPassword: [{validator: validatecheckPassword, trigger: 'change'}],
})

const register = (formEl: FormInstance | undefined) => {
  if (!formEl) return
  formEl.validate((valid) => {
    if (valid) {

      set_Register_post()
      loading.value = true
    } else {
      fail_message("Please fill in as required.")
      return false
    }
  })
}

import axios from 'axios';

const set_Register_post = () => {
  axios.post('/api/user/register', {
    email: user.Email,
    password: user.Password
  }, {timeout: timeout})
      .then(response => {
        analyze_response(response.data)
        loading.value = false
      })
      .catch(error => {
        loading.value = false
        if (error === 'ECONNABORTED') {

          fail_message('request timeout')
        } else {

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
    success_message(t('register.signUp'))

    finish_register.value = true

    jump_login(1)
  } else {
    if (data.code === 101) {
      fail_message("This account has been registered")
    } else {
      fail_message("Registration failed, please try again.")
    }
  }
}

function jump_login(seconds) {
  setTimeout(function () {
    emit('change');
    emit('register-success');
  }, seconds * 1000);
}
</script>

<style scoped>
.register_b {
  width: 100%;
  margin-top: 10px;
}

.reset_r {
  justify-content: flex-end;
}

.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.register-card {
  padding: 5px;
  border-radius: 12px;
  max-height: 30%;
  background-color: transparent;
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
