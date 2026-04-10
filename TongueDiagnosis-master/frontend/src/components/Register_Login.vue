<template>
  <div class="back_ground">
    <div class="top-bar">
    </div>
    <div class="center-container">
      <div class="decorations">
        <div class="circle c1"></div>
        <div class="circle c2"></div>
        <div class="circle c3"></div>
        <div class="circle c4"></div>
        <div class="circle c5"></div>
        <div class="circle c6"></div>
        <div class="circle c7"></div>
      </div>
      <div class="container">
        <div class="form-box" :style="refstyle" v-loading="loading_tip" element-loading-background="#d3b7d8">
          <div class="register-box" v-show="show_change">
            <h1>{{ t('register.title') }}</h1>
            <registerBlock @change="change_style"/>
          </div>
          <div class="login-box" v-show="!show_change">
            <h1>{{ t('login.title') }}</h1>
            <loginBlock/>
          </div>
        </div>
        <div class="con-box left">
          <h2><span>{{ t('app.tongue') }}</span></h2>
          <h2><span>{{ t('app.diagnosis') }}</span></h2>
          <p></p>
          <img src="@/assets/Chat_Tongue.webp" alt="" class="logo">
          <p>{{ t('login.alreadyHave') }}</p>
          <button id="login" @click="change_style">{{ t('login.title') }}</button>
        </div>
        <div class="con-box right">
          <h2><span>{{ t('app.tongue') }}</span></h2>
          <h2><span>{{ t('app.diagnosis') }}</span></h2>
          <p></p>
          <img src="@/assets/Chat_Tongue.webp" alt="" class="logo">
          <p>{{ t('login.noAccount') }}</p>
          <button id="register" @click="change_style">{{ t('register.title') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import registerBlock from '@/components/Registerblock.vue';
import loginBlock from '@/components/Loginblock.vue';
import {ref} from 'vue'
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

let slide_tip = false
let refstyle = ref({
  transform: 'translateX(0%)'
})
let kf = ref({
  'background-color': "#d3b7d8"
})
let show_change = ref(false)
let loading_tip = ref(false)
let useless = true

function loading_seconds(seconds) {
  setTimeout(function () {
    loading_tip.value = false
  }, seconds * 1000);
}

function waiting_change(seconds) {
  setTimeout(function () {
    show_change.value = !show_change.value
  }, seconds * 1000)
}

const change_style = () => {
  loading_tip.value = true
  waiting_change(0.2)

  //show_change = !show_change
  slide_tip = !slide_tip
  refstyle.value.transform = slide_tip ? 'translateX(80%)' : 'translateX(0%)'

  loading_seconds(0.4)
}

</script>

<style scoped>
.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

[data-theme='dark'] .top-bar {
  background: rgba(30, 30, 30, 0.1);
  backdrop-filter: blur(10px);
}

.center-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100%;
  background: linear-gradient(45deg, #d6bdfc 0%, #f8d7da 50%, #b3d9ff 100%);
  transition: background 0.3s;
}

[data-theme='dark'] .center-container {
  background: linear-gradient(45deg, #2a1a2c 0%, #1e1a2c 50%, #1a1e2c 100%);
}

.back_ground {
  overflow: hidden;
}

.container {
  background-color: #ffffff;
  width: 650px;
  height: 415px;
  border-radius: 5px;
  box-shadow: 5px 5px 5px var(--shadow-color);
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  transition: background-color 0.3s, box-shadow 0.3s;
}

[data-theme='dark'] .container {
  background-color: #1a1a2a;
  box-shadow: 5px 5px 5px rgba(0, 0, 0, 0.7);
}

.form-box {
  position: absolute;
  top: -10%;
  left: 5%;
  background: linear-gradient(45deg, #d6bdfc, rgba(179, 209, 255, 0.8));
  width: 320px;
  height: 500px;
  border-radius: 5px;
  box-shadow: 2px 0 10px var(--shadow-color);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2;
  transition: 0.5s ease-in-out, background 0.3s;
}

[data-theme='dark'] .form-box {
  background: linear-gradient(45deg, #3a2a4c, rgba(30, 30, 50, 0.9));
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.7);
}

.register-box,
.login-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

h1 {
  text-align: center;
  margin-bottom: 25px;
  text-transform: uppercase;
  color: #fff;
  letter-spacing: 5px;
}

.con-box {
  width: 50%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
}

.con-box.left {
  left: -2%;
}

.con-box.right {
  right: -2%;
}

.con-box h2 {
  color: var(--accent-color);
  font-size: 25px;
  font-weight: bold;
  letter-spacing: 3px;
  text-align: center;
  margin-bottom: 4px;
  transition: color 0.3s;
}

.con-box p {
  font-size: 12px;
  letter-spacing: 2px;
  color: var(--text-secondary);
  text-align: center;
  transition: color 0.3s;
}

.con-box span {
  color: var(--accent-color);
  transition: color 0.3s;
}

.con-box img {
  width: 150px;
  height: 150px;
  opacity: 0.9;
  margin: 40px 0;
}

.con-box button {
  margin-top: 3%;
  background-color: var(--card-bg);
  color: var(--accent-color);
  border: 1px solid var(--accent-color);
  padding: 6px 10px;
  border-radius: 5px;
  letter-spacing: 1px;
  outline: none;
  cursor: pointer;
  transition: all 0.3s;
}

.con-box button:hover {
  background-color: var(--accent-color);
  color: #fff;
}

.logo {
  border-radius: 50%;
  height: 150px;
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
  transition: all 0.3s;
}

[data-theme='dark'] .circle {
  box-shadow: 
    0 15px 40px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.c1 {
  width: 200px;
  height: 200px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
  background: rgba(179, 209, 252, 0.4);
}

[data-theme='dark'] .c1 {
  background: rgba(100, 80, 120, 0.4);
}

.c2 {
  width: 150px;
  height: 150px;
  bottom: 15%;
  right: 15%;
  animation-delay: 2s;
  background: rgba(248, 215, 218, 0.4);
}

[data-theme='dark'] .c2 {
  background: rgba(120, 80, 80, 0.4);
}

.c3 {
  width: 100px;
  height: 100px;
  top: 40%;
  right: 20%;
  animation-delay: 4s;
  background: rgba(214, 189, 252, 0.4);
}

[data-theme='dark'] .c3 {
  background: rgba(120, 100, 140, 0.4);
}

.c4 {
  width: 80px;
  height: 80px;
  top: 60%;
  left: 15%;
  animation-delay: 1s;
  background: rgba(179, 209, 252, 0.4);
}

[data-theme='dark'] .c4 {
  background: rgba(80, 100, 120, 0.4);
}

.c5 {
  width: 120px;
  height: 120px;
  top: 20%;
  right: 30%;
  animation-delay: 3s;
  background: rgba(248, 215, 218, 0.4);
}

[data-theme='dark'] .c5 {
  background: rgba(120, 80, 90, 0.4);
}

.c6 {
  width: 60px;
  height: 60px;
  bottom: 25%;
  left: 30%;
  animation-delay: 5s;
  background: rgba(214, 189, 252, 0.4);
}

[data-theme='dark'] .c6 {
  background: rgba(100, 80, 110, 0.4);
}

.c7 {
  width: 140px;
  height: 140px;
  bottom: 10%;
  left: 30%;
  animation-delay: 6s;
  background: rgba(179, 209, 252, 0.4);
}

[data-theme='dark'] .c7 {
  background: rgba(80, 90, 110, 0.4);
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

/* 移动端响应式样式 */
@media (max-width: 768px) {
  .container {
    width: 90%;
    height: 380px;
  }
  
  .form-box {
    width: 90%;
    height: 450px;
    top: -5%;
  }
  
  .con-box {
    width: 100%;
    padding: 0 10px;
  }
  
  .con-box.left,
  .con-box.right {
    position: relative;
    top: auto;
    left: auto;
    right: auto;
    transform: none;
    margin: 10px 0;
  }
  
  .con-box h2 {
    font-size: 20px;
    margin-bottom: 3px;
  }
  
  .con-box p {
    font-size: 11px;
    margin-bottom: 3px;
  }
  
  .con-box img {
    width: 100px;
    height: 100px;
    margin: 20px 0;
  }
  
  .con-box button {
    padding: 4px 8px;
    font-size: 14px;
  }
  
  .decorations {
    display: none;
  }
  
  .circle {
    display: none;
  }
  
  h1 {
    font-size: 18px;
    margin-bottom: 20px;
  }
}

@media (max-width: 480px) {
  .container {
    width: 95%;
    height: 350px;
  }
  
  .form-box {
    width: 95%;
    height: 400px;
    top: -3%;
  }
  
  .con-box {
    flex-direction: column;
    padding: 15px;
    gap: 20px;
  }
  
  .con-box.left,
  .con-box.right {
    width: 100%;
    margin: 10px 0;
  }
  
  .con-box h2 {
    font-size: 18px;
    margin-bottom: 3px;
  }
  
  .con-box p {
    font-size: 11px;
    margin-bottom: 3px;
  }
  
  .con-box img {
    width: 80px;
    height: 80px;
    margin: 15px 0;
  }
  
  .con-box button {
    padding: 3px 6px;
    font-size: 13px;
  }
}
</style>