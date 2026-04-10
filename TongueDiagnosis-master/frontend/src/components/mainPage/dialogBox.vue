<template>
  <div
      class="draggable-container"
      :style="dialogBoxStyle"
  >
    <div v-if="sendPic" class="upload-wrapper">
      <el-icon class="arrow-left">
        <ArrowRightBold/>
      </el-icon>
      <div v-if="isUploading">
        <Steps ref="stepRef"/>
      </div>
      <div v-else>
        <UploadPicture @success="startQuest" style="margin-top: 5px"/>
      </div>
      <el-icon class="arrow-right">
        <ArrowLeftBold/>
      </el-icon>
    </div>

    <input @keydown="handleKeyDown" class="message-input" v-model="inputValue" :placeholder="t('input.placeholder')"
           style="height: auto;" v-if="!sendPic">
    <el-button type="success" :icon="Promotion" @click="sendToMain" size="large" style="font-size: 20px;" circle
               v-if="!sendPic"/>
    <el-button
        :type="isRecording ? 'warning' : 'primary'"
        :icon="isRecording ? CircleClose:Microphone"
        @click="toggleVoiceRecognition"
        size="large"
        :loading="isLoading"
        style="font-size: 20px;"
        circle
        v-if="!sendPic"
    />
  </div>
</template>

<script setup lang="ts">
import {ref, onBeforeMount, computed, nextTick} from 'vue'
import {Promotion, Microphone, CircleClose, ArrowLeftBold, ArrowRightBold} from "@element-plus/icons-vue";
import {ElMessage} from "element-plus";
import {useStateStore} from '@/stores/stateStore';
import UploadPicture from '@/components/UploadPicture.vue';
import Steps from "@/components/Steps.vue";
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const stateStore = useStateStore();
let sendPic = ref(true);
let isUploading = ref(false);
const stepRef = ref<any>(null);
const emit = defineEmits(['send-to-main', 'send-picture']);
let inputValue = ref('');
let ask_tip = 0;
const sendToMain = () => {
  emit('send-to-main', ask_tip, inputValue.value);
  ask_tip += 1;
  inputValue.value = '';
};

const isRecording = ref(false);
const isLoading = ref(false);

// 计算dialogBox的动态样式
const dialogBoxStyle = computed(() => {
  const isCollapsed = stateStore.isSidebarCollapsed;
  return {
    left: isCollapsed ? '60px' : '280px',
    width: isCollapsed ? 'calc(100% - 80px)' : 'calc(100% - 300px)'
  };
});

onBeforeMount(() => {
  if (stateStore.baseUrl == "0") {
    ErrorPop("Please set an url", 5000)
  }
});
let recognition: any = null;

const toggleVoiceRecognition = () => {
  if (isRecording.value) {
    stopRecognition();
  } else {
    startRecognition();
  }
};

const resetLoading = (attempt = 0) => {
  // 添加存在性检查，避免组件未渲染时调用
  if (stepRef.value && typeof stepRef.value.resetCountdown === 'function') {
    try {
      stepRef.value.resetCountdown()
      console.log('成功重置倒计时');
    } catch (error) {
      console.error('重置倒计时失败:', error);
      // 即使有错误也继续重试
      if (attempt < 10) {
        setTimeout(() => {
          resetLoading(attempt + 1);
        }, 200);
      }
    }
  } else {
    // 如果组件未渲染，尝试重试几次
    if (attempt < 10) {
      setTimeout(() => {
        resetLoading(attempt + 1);
      }, 200);
    } else {
      console.warn('Steps组件未渲染，无法重置倒计时');
    }
  }
}

// 使用更安全的方式访问语音识别API
const recognitionClass = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

if (recognitionClass) {
  recognition = new recognitionClass();
  recognition.continuous = false; // 设为非连续模式
  recognition.interimResults = false; // 只返回最终结果
  recognition.lang = 'zh-CN'; // 设定语言为中文

  recognition.onstart = () => {
    isRecording.value = true;
  };

  recognition.onresult = (event: any) => {
    inputValue.value += event.results[0][0].transcript;
  };

  recognition.onerror = () => {
    ErrorPop('语音识别出错，请重试');
  };

  recognition.onend = () => {
    isRecording.value = false;
  };
} else {
  console.warn('当前浏览器不支持语音识别');
}

const startRecognition = () => {
  if (recognition && typeof recognition.start === 'function') {
    recognition.start();
    console.log("开始语音识别")
  } else {
    ErrorPop('您的浏览器不支持语音识别');
  }
};

const stopRecognition = () => {
  if (recognition && typeof recognition.stop === 'function') {
    console.log("停止语音识别")
    recognition.stop();
  }
};

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    sendToMain();
  }
};

const ErrorPop = (info: string, time = 3000) => {
  ElMessage({
    showClose: true,
    message: info,
    type: 'error',
    duration: time
  })
}

let pic64 = ref("")

const startQuest = async (info: any) => {
  if (info.success) {
    pic64.value = info.base64
  }

  console.log("开始");
  emit("send-picture", {base64: pic64.value, fileData: info.fileData});
  
  // 等待父组件处理完 initPage 后再开始加载
  await new Promise(resolve => setTimeout(resolve, 100));
  startLoading();
}

const backUploading = () => {
  sendPic.value = true
  isUploading.value = false
}

const startLoading = async () => {
  isUploading.value = true
  await nextTick()
  // 添加额外的延迟确保Steps组件完全渲染
  await new Promise(resolve => setTimeout(resolve, 300))
  resetLoading();
}

const startChat = () => {
  sendPic.value = false
  isUploading.value = false
}

const getReturn = (data: any) => {
  if (data.success) startChat()
  else backUploading()
}
defineExpose({startChat, startLoading, backUploading, getReturn})
</script>

<style scoped>
.draggable-container {
  display: flex;
  align-items: center;
  min-width: 550px;
  background-color: var(--bg-secondary);
  border-radius: 30px 30px 0 0;
  padding: 10px;
  box-shadow: 0 -4px 8px var(--shadow-color);
  border: 1px solid var(--border-color);
  border-bottom: none;
  transition: left 0.3s ease, width 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease, background-color 0.3s, border-color 0.3s;
  justify-content: center;
  position: fixed;
  bottom: 0;
  z-index: 100;
}

.draggable-container:hover {
  box-shadow: 0 8px 16px var(--shadow-color);
  transform: translateY(-2px);
}

.send-button svg {
  fill: var(--text-primary);
}

.message-input {
  flex: 1;
  border: none;
  padding: 10px;
  outline: none;
  border-radius: 20px;
  font-size: 16px;
  font-family: 'Roboto', sans-serif;
  line-height: 1.5;
  background-color: var(--input-bg);
  color: var(--text-primary);
  transition: background-color 0.3s, color 0.3s;
}

.send-button svg {
  fill: var(--text-primary);
}

.upload-wrapper {
  display: flex;
  align-items: center;
  gap: 20px;
}

.arrow-left, .arrow-right {
  font-size: 24px;
  color: var(--accent-color);
  cursor: pointer;
  transition: color 0.3s;
}

.arrow-left:hover, .arrow-right:hover {
  color: var(--accent-hover);
}

.input-container {
  display: flex;
  align-items: center;
  gap: 10px;
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

[data-theme='dark'] :deep(.el-button--warning) {
  --el-button-bg-color: #e6a23c;
  --el-button-border-color: #e6a23c;
  --el-button-text-color: #ffffff;
  --el-button-hover-bg-color: #f78c2c;
  --el-button-hover-border-color: #f78c2c;
  --el-button-hover-text-color: #ffffff;
  --el-button-active-bg-color: #d97706;
  --el-button-active-border-color: #d97706;
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

[data-theme='dark'] :deep(.el-loading-mask) {
  background-color: rgba(0, 0, 0, 0.7);
}

[data-theme='dark'] :deep(.el-loading-spinner .circular) {
  stroke: var(--accent-color);
}
</style>