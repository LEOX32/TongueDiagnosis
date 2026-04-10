<script setup lang="ts">
import {UploadFilled} from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const emit = defineEmits(["success"])

let e;
let base64String = "";
let fileReaderPromise: Promise<string | null> | null = null;

function PicOnLoad(file: any) {
  e = file;
  // 创建一个Promise来等待FileReader完成
  fileReaderPromise = new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = function (event) {
      base64String = event.target?.result as string;
      console.log('FileReader 完成，base64 长度:', base64String.length);
      resolve(base64String);
    };
    reader.onerror = function (error) {
      console.error('FileReader 错误:', error);
      resolve(null);
    };
    reader.readAsDataURL(file.raw);
  });
}

async function handleSuccess(_event: any) {
  if (!e || !e.raw) {
    console.error("未找到要上传的文件");
    return;
  }

  // 等待FileReader完成读取
  if (fileReaderPromise) {
    await fileReaderPromise;
    console.log('等待FileReader完成后，base64长度:', base64String.length);
  }

  console.log("上传的文件：", e.raw);
  emit("success", {success: true, base64: base64String, fileData: e.raw});
}
</script>

<template>
  <el-upload
      class="upload-demo"
      drag
      multiple
      :on-change="PicOnLoad"
      :http-request="handleSuccess"
      accept=".jpg,.jpeg,.png,.bmp"
      :show-file-list="false"
  >
    <el-icon class="el-icon--upload">
      <upload-filled/>
    </el-icon>
    <div class="el-upload__text">
      {{ t('upload.drag') }} <em>{{ t('upload.click') }}</em>
    </div>
  </el-upload>
</template>

<style scoped>
.upload-demo {
  width: 400px;
  height: 180px;
}

:deep(.el-upload-dragger) {
  background-color: var(--bg-secondary);
  border: 2px dashed var(--accent-color);
  border-radius: 8px;
  color: var(--text-primary);
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  transition: background-color 0.3s, border-color 0.3s, color 0.3s;
}

:deep(.el-icon--upload) {
  font-size: 50px;
  color: var(--accent-color);
  transition: color 0.3s;
}

:deep(.el-upload__text) {
  font-size: 16px;
  font-weight: bold;
  color: var(--text-secondary);
  transition: color 0.3s;
}
</style>
