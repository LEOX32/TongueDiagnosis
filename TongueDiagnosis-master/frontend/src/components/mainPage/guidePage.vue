<script setup>
import {ref} from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const showWelcome = ref(true)
const guideText = ref('')

const handleChatStart = () => {
  showWelcome.value = false
}

const changeGuideText = (text) => {
  guideText.value = text
}

defineExpose({handleChatStart, changeGuideText})
</script>

<template>
  <div class="main-container">
    <div v-if="showWelcome" class="welcome-container">
      <div class="content-wrapper">
        <div class="icon-box">
          <img src="@/assets/Chat_Tongue.webp" alt="" class="fas fa-comment-medical floating-icon"
               style="height: 20vh;border-radius: 50%;">
        </div>
        <div class="text-content">
          <h1 class="title">{{ t('guide.welcome') }} 👋</h1>
          <p class="subtitle">{{ t('guide.clickLeft') }}{{ guideText }}<br>{{ t('guide.obtainAnalysis') }}</p>
        </div>
      </div>
      <div class="decorations">
        <div class="circle c1"></div>
        <div class="circle c2"></div>
        <div class="circle c3"></div>
        <div class="circle c4"></div>
        <div class="circle c5"></div>
        <div class="circle c6"></div>
        <div class="circle c7"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.main-container {
  position: relative;
  flex: 1;
  height: 100%;
  overflow: hidden;
}

.welcome-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(45deg, #d6bdfc 0%, #f8d7da 50%, #b3d9ff 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.5s ease;
}

.content-wrapper {
  text-align: center;
  z-index: 10;
  animation: fadeInUp 1s ease-out;
}

.icon-box {
  margin-bottom: 2rem;
  animation: bounce 2s infinite;
}

.floating-icon {
  height: 20vh;
  border-radius: 50%;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  animation: float 3s ease-in-out infinite;
}

.text-content {
  max-width: 600px;
  margin: 0 auto;
}

.title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  color: #333;
  animation: fadeInUp 1s ease-out 0.3s both;
}

.subtitle {
  font-size: 1.2rem;
  line-height: 1.6;
  color: #666;
  margin-bottom: 2rem;
  animation: fadeInUp 1s ease-out 0.6s both;
}

.decorations {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.circle {
  position: absolute;
  border-radius: 50%;
  backdrop-filter: blur(120px);
  filter: blur(2px);
  animation: float 6s ease-in-out infinite;
  box-shadow: 
    0 15px 40px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.c1 {
  width: 200px;
  height: 200px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
  background: rgba(179, 209, 255, 0.4);
}

.c2 {
  width: 150px;
  height: 150px;
  bottom: 15%;
  right: 15%;
  animation-delay: 2s;
  background: rgba(248, 215, 218, 0.4);
}

.c3 {
  width: 100px;
  height: 100px;
  top: 40%;
  right: 20%;
  animation-delay: 4s;
  background: rgba(214, 189, 252, 0.4);
}

.c4 {
  width: 80px;
  height: 80px;
  top: 60%;
  left: 15%;
  animation-delay: 1s;
  background: rgba(179, 209, 252, 0.4);
}

.c5 {
  width: 120px;
  height: 120px;
  top: 20%;
  right: 30%;
  animation-delay: 3s;
  background: rgba(248, 215, 218, 0.4);
}

.c6 {
  width: 60px;
  height: 60px;
  bottom: 25%;
  left: 30%;
  animation-delay: 5s;
  background: rgba(214, 189, 252, 0.4);
}

.c7 {
  width: 140px;
  height: 140px;
  bottom: 10%;
  left: 30%;
  animation-delay: 6s;
  background: rgba(179, 209, 252, 0.4);
}

/* 深色模式样式 */
[data-theme='dark'] .welcome-container {
  background: linear-gradient(45deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
}

[data-theme='dark'] .title {
  color: #ffffff;
}

[data-theme='dark'] .subtitle {
  color: #e0e0e0;
}

[data-theme='dark'] .floating-icon {
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}

[data-theme='dark'] .circle {
  box-shadow: 
    0 15px 40px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

[data-theme='dark'] .c1 {
  background: rgba(102, 126, 234, 0.2);
}

[data-theme='dark'] .c2 {
  background: rgba(247, 127, 0, 0.2);
}

[data-theme='dark'] .c3 {
  background: rgba(168, 85, 247, 0.2);
}

[data-theme='dark'] .c4 {
  background: rgba(102, 126, 234, 0.2);
}

[data-theme='dark'] .c5 {
  background: rgba(247, 127, 0, 0.2);
}

[data-theme='dark'] .c6 {
  background: rgba(168, 85, 247, 0.2);
}

[data-theme='dark'] .c7 {
  background: rgba(102, 126, 234, 0.2);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

@media (max-width: 768px) {
  .title {
    font-size: 2rem;
  }
  
  .subtitle {
    font-size: 1rem;
  }
  
  .floating-icon {
    height: 15vh;
  }
}
</style>
