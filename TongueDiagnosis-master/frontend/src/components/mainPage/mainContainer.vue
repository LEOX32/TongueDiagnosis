<script setup lang="ts">
import Bottom from "./dialogBox.vue";
import Main from "./main.vue";
import {ref} from 'vue'

let sharedInput = ref('');
const mainRef = ref<InstanceType<typeof Main> | null>(null)
const dialogRef = ref<InstanceType<typeof Bottom> | null>(null)
const tempName = ref('新会话')

const handleSendToMain = (id: number, input: string) => {
  // 先确保对话框显示文本输入框，而不是上传照片按钮
  dialogRef.value?.startChat();
  // 然后设置 sharedInput，触发 main.vue 中的 watch 函数
  sharedInput.value = `${id},${input}`;
};

const handleSendPicture = async (info: any) => {
  await initPage(info, tempName.value);
};

const initPage = async (basePic: any, sessionName: string) => {
  await mainRef.value?.initPage(basePic, sessionName);
}

const inputData = (data: any, id: any) => {
  dialogRef.value?.startChat()
  mainRef.value?.inputData(data, id);
}

const resetPage = () => {
  mainRef.value?.resetPage();
  dialogRef.value?.backUploading();
}

const setTempName = (name: string) => {
  console.log(name);
  tempName.value = name;
}

const activateSession = (id: string | number) => {
  mainRef.value?.activateSession(id);
  dialogRef.value?.startChat(); // 确保对话框显示文本输入框，而不是上传照片按钮
}

const getAllSessions = () => {
  return mainRef.value?.getAllSessions();
}

const scrollToMessage = (sessionId: string | number, messageIndex: number) => {
  mainRef.value?.scrollToMessage(sessionId, messageIndex);
}

const resetSessionState = () => {
  mainRef.value?.resetSessionState();
}

defineExpose({inputData, resetPage, setTempName, activateSession, getAllSessions, scrollToMessage, resetSessionState})

const handleGetReturn = (data: any) => {
  dialogRef.value?.getReturn(data);
}

const backIdToCheck = (id: any) => {
  emit("back-id", id);
}

const handleJumpToSession = (sessionId: string | number) => {
  emit("jump-to-session", sessionId);
}

const emit = defineEmits(["back-id", "jump-to-session"]);
</script>

<template>
  <div class="back-ground">
    <div class="common-layout">
      <Main :receivedInput="sharedInput" ref="mainRef" @get-return="handleGetReturn" @back-id="backIdToCheck" @jump-to-session="handleJumpToSession"/>
      <Bottom @send-to-main="handleSendToMain" @send-picture="handleSendPicture" ref="dialogRef"/>
    </div>
  </div>
</template>

<style scoped>
.back-ground {
  height: 80vh;
  background: linear-gradient(135deg, #4facfe, rgba(90, 224, 231, 0.9), #00d4a9, #00cba9);
  background-size: 200% 200%;
}
</style>