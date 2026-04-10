<script setup>
import axios from "axios";
import {ref, onMounted} from 'vue'
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const emit = defineEmits(["getRecord"])
const props = defineProps(['isupstate'])
const size = 'small'

function reverseArray1(arr) {
  for (let index = 0; index < Math.floor(arr.length / 2); index++) {
    let temp = arr[index];
    arr[index] = arr[arr.length - 1 - index];
    arr[arr.length - 1 - index] = temp
  }
  return arr;
}

let rec = ref([0]);
let isEmpty = ref(false)

onMounted(function () {
  axios.get("/api/user/record", {
    headers: {
      'Authorization': 'Bearer ' + localStorage.getItem('token')
    }
  }).then(res => {
    rec.value = res.data.data
    console.log(rec.value)
    if (Object.keys(rec.value).length !== 0) {
      console.log('rec is not null')
      isEmpty.value = true
      reverseArray1(rec.value)
    }
  }).catch(error => {
    console.log(error);
  })
})

onMounted(function () {
  const timer = window.setInterval(() => {
    setTimeout(function () {
      console.log(("开始轮询"))
      console.log(props.isupstate)
      if (props.isupstate === true || rec.value[0].state === 0) {
        console.log(("开始轮询加上向后端发送请求"))
        axios.get("/api/user/record", {
          headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('token')
          }
        })
            .then(function (res) {
              console.log(res.data)
              rec.value = res.data.data
              reverseArray1(rec.value)
              console.log(rec.value)
              console.log(rec.value[0].state)
              if (Object.keys(rec.value).length !== 0) {
                console.log('rec is not null')
                isEmpty.value = true
              }
            })
            .catch(function (error) {
              console.log(error);
            })
            .then(res => {
              if (rec.value.length === 0 || (rec.value.length > 0 && rec.value[0].state !== 0)) {
                console.log("轮询停止")
                emit("getRecord", false)
              }
            })
      }
    }, 0)
  }, 2000)
});
</script>

<template>
  <div class="card" v-for="item in rec" :key="item.id" v-if="isEmpty === true">
    <el-descriptions
        :title="t('result.title')"
        direction="vertical"
        :column="4"
        :size="size"
        border
    >
      <el-descriptions-item :label="t('result.image')" width="450px">
        <el-tag size="small"><a :href=item.img_src>{{ t('result.clickToView') }}</a></el-tag>
      </el-descriptions-item>
      <el-descriptions-item :label="t('result.diagnosisResult')" v-if="item.state === 0">
        {{ t('result.wait') }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('result.diagnosisResult')" v-if="item.state === 1">
        {{ t('result.tongueColor') }}：{{ t('result.tongueColors.' + item.result.tongue_color) }}<br>
        {{ t('result.coatingColor') }}：{{ t('result.coatingColors.' + item.result.coating_color) }}<br>
        {{ t('result.rotGreasy') }}：{{ t('result.rotGreasyTypes.' + item.result.rot_greasy) }}<br>
        {{ t('result.tongueThickness') }}：{{ t('result.tongueThickness.' + item.result.tongue_thickness) }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('result.diagnosisResult')" v-if="item.state === 201">
        {{ t('result.noTongue') }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('result.diagnosisResult')" v-if="item.state === 202">
        {{ t('result.multipleTongues') }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('result.diagnosisResult')" v-if="item.state === 203">
        {{ t('result.fileTypeError') }}
      </el-descriptions-item>
    </el-descriptions>
  </div>
  <div v-else><h1 class="nores">{{ t('result.noResults') }}</h1></div>
</template>

<style>
.nores {
  text-align: center;
  color: var(--accent-color);
  transition: color 0.3s;
}
</style>
