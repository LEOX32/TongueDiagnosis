<script lang="ts" setup>
import {nextTick, onMounted, ref} from 'vue';
import { useRouter } from 'vue-router';
import Main from "@/components/mainPage/mainContainer.vue";
import GuidePage from "@/components/mainPage/guidePage.vue";
import axios from "axios";
import { useI18n } from 'vue-i18n';
import { useStateStore } from '@/stores/stateStore';
import { ElMessage, ElMessageBox } from 'element-plus';

const router = useRouter();

interface Item {
  id: string | number;
  label: string;
  temp: boolean;
}

const { t } = useI18n();
const stateStore = useStateStore();

const showGuide = ref(true);
const guidePageRef = ref<InstanceType<typeof GuidePage> | null>(null);
const activeItem = ref<string | null | number>(null);
const mainPageRef = ref<InstanceType<typeof Main> | null>(null);
const items = ref<Item[]>([]);
const newItemLabel = ref('');
let itemIdCounter = 10000000;

const toggleSidebar = () => {
  stateStore.toggleSidebar();
};

const handleItemClick = async (id: string | number) => {
  // 检查是否点击了当前活跃的记录
  if (activeItem.value === id) {
    // 如果是当前活跃记录，关闭它并返回引导页
    // 先重置会话状态，确保搜索功能切换到全局搜索模式
    mainPageRef.value?.resetSessionState();
    // 然后再设置引导页显示，避免组件卸载后方法调用失败
    showGuide.value = true;
    activeItem.value = null;
    console.log("关闭当前记录，返回引导页");
    return;
  }
  
  showGuide.value = false;
  await nextTick();
  console.log(`选中项: ${id}`);
  const item = items.value.find(item => item.id === id);
  if (!item) return;
  const tempTip = item.temp;
  
  // Always set the temp name for the session, regardless of whether it's temporary or not
  mainPageRef.value?.setTempName(item.label);
  
  activeItem.value = id;
  
  // 先激活会话，确保会话存在
  mainPageRef.value?.activateSession(id);
  
  if (tempTip) {
    console.log("临时页面");
    mainPageRef.value?.resetPage();
    return;
  }
  
  // 确保对话框显示文本输入框，而不是上传照片按钮
  setTimeout(() => {
    mainPageRef.value?.activateSession(id);
  }, 100);
  
  // 在后台加载会话数据，不阻塞会话切换
  axios.get("/api/model/record/" + id, {
    headers: {
      'Authorization': 'Bearer ' + localStorage.getItem('token')
    }, timeout: 20000
  }).then((res: any) => {

    console.log("选中页面的数据", res.data.data.records);
    const data = res.data.data.records;
    mainPageRef.value?.inputData(data.map((item: any) => {
          return {
            text: item.content,
            isUser: item.role == 1,
            loading: false,
            isPicture: false,
            time: new Date(item.create_at).toLocaleString('default', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            }),
          };
        }), id
    );
  }).catch((error: any) => {
    console.log(error);
  });
};

// 移除未使用的watch函数
// watch(activeItem, () => {
// });

const addItem = () => {
  const label = newItemLabel.value.trim();
  if (!label) {
    return;
  }
  
  // 检查记录名称是否已存在
  const isDuplicate = items.value.some(item => item.label === label);
  if (isDuplicate) {
    // 显示错误提示
    ElMessage({
      showClose: true,
      message: t('check.duplicateNameError'),
      type: 'error',
      duration: 3000
    });
    return;
  }
  
  const newItemId = ++itemIdCounter;
  const newItem: Item = {
    id: newItemId,
    label: label,
    temp: true
  };
  items.value.push(newItem);
  
  // 立即切换到新会话，不管当前会话是否在处理中
  // 这样可以避免多个会话同时被激活的问题
  handleItemClick(newItemId);
  newItemLabel.value = '';
};

const deletingItems = ref(new Set<string | number>());

// 清空所有记录
const clearAllItems = async () => {
  if (items.value.length === 0) {
    return;
  }
  
  // 使用 Element Plus 的确认对话框，确保在确认后才执行删除
  try {
    await ElMessageBox.confirm(
      t('check.clearConfirm'),
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
  } catch {
    // 用户点击取消，直接返回
    return;
  }
  
  console.log('开始清空所有记录');
  
  // 获取所有需要删除的 ID
  const idsToDelete = items.value.map(item => item.id);
  
  // 批量删除
  const deletePromises = idsToDelete.map(id => {
    deletingItems.value.add(id);
    return axios.delete(`/api/model/record/${id}`, {
      headers: {
        'Authorization': 'Bearer ' + localStorage.getItem('token')
      }
    });
  });
  
  try {
    await Promise.all(deletePromises);
    console.log('所有记录删除成功');
    
    // 等待动画完成后清空数组
    setTimeout(() => {
      items.value = [];
      activeItem.value = null;
      showGuide.value = true;
      deletingItems.value.clear();
      
      // 显示成功提示
      ElMessage({
        showClose: true,
        message: t('check.clearSuccess'),
        type: 'success',
        duration: 2000
      });
    }, 300);
  } catch (error) {
    console.error('批量删除失败:', error);
    ElMessage({
      showClose: true,
      message: t('check.clearFailed'),
      type: 'error',
      duration: 3000
    });
    // 清空删除中集合
    deletingItems.value.clear();
  }
};

// 跳转到健康跟踪页面
const goToHealthTrack = () => {
  router.push('/health');
};

const removeItem = (targetId: string | number) => {
  // 调用后端API删除记录
  console.log(`尝试删除记录，ID: ${targetId}`);
  
  // 添加到删除中集合，触发动画
  deletingItems.value.add(targetId);
  
  axios.delete(`/api/model/record/${targetId}`, {
    headers: {
      'Authorization': 'Bearer ' + localStorage.getItem('token')
    }
  }).then(response => {
    console.log('删除API响应:', response);
    
    // 等待动画完成后从数组中移除（300ms是动画持续时间）
    setTimeout(() => {
      const index = items.value.findIndex(item => item.id === targetId);
      if (index !== -1) {
        items.value.splice(index, 1);
        
        // 更新活跃项
        if (activeItem.value === targetId) {
          activeItem.value = items.value.length ? items.value[0].id : null;
          // 如果还有其他项，切换到第一项
          if (activeItem.value) {
            handleItemClick(activeItem.value);
          } else {
            // 如果没有项了，显示引导页
            showGuide.value = true;
          }
        }
      }
      
      // 从删除中集合移除
      deletingItems.value.delete(targetId);
      
      // 显示成功消息
      ElMessage({
        showClose: true,
        message: t('check.deleteSuccess'),
        type: 'success',
        duration: 2000
      });
      
      console.log('记录删除成功');
    }, 300);
  }).catch(error => {
    console.error('删除记录失败:', error);
    console.error('错误详情:', error.response?.data || error.message);
    
    // 从删除中集合移除
    deletingItems.value.delete(targetId);
    
    // 显示错误消息
    ElMessage({
      showClose: true,
      message: t('check.deleteFailed'),
      type: 'error',
      duration: 3000
    });
  });
};

const formatData = (data: any) => {
  return data.map((item: any) => {
    return {
      id: item.session_id,
      label: item.name,
      temp: false
    } as Item;
  });
};

onMounted(() => {
  axios.get("/api/model/session", {
    headers: {
      'Authorization': 'Bearer ' + localStorage.getItem('token')
    }, timeout: 40000
  }).then((res: any) => {
    console.log("初始化数据", res.data.data);
    items.value = formatData(res.data.data);
    if (items.value.length) {
      guidePageRef.value?.changeGuideText(t('check.viewDetails'));
    } else {
      guidePageRef.value?.changeGuideText(t('check.addNew'));
    }
  }).catch((error: any) => {
    console.log(error);
  });
});

const handleBackId = (id: string) => {
  // 找到当前活跃的项，更新其 ID
  const activeItemIndex = items.value.findIndex(item => item.id === activeItem.value);
  if (activeItemIndex !== -1) {
    items.value[activeItemIndex].id = id;
    activeItem.value = id;
    items.value[activeItemIndex].temp = false;
  } else {
    // 如果没有找到活跃项，尝试更新最后一个项（保持原有行为作为后备）
    const lastItem = items.value[items.value.length - 1];
    if (lastItem) {
      lastItem.id = id;
      activeItem.value = id;
      lastItem.temp = false;
    }
  }
};

// 处理从搜索结果跳转会话的事件
const handleJumpToSession = (sessionId: string) => {
  // 关闭引导页
  showGuide.value = false;
  // 找到对应的项并设置为活跃项
  const item = items.value.find(item => item.id === sessionId);
  if (item) {
    activeItem.value = sessionId;
  }
  console.log('从搜索结果跳转到会话:', sessionId);
};

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter') {
    addItem();
  }
};
</script>

<template>
  <div class="back-ground">
    <div class="content" :class="{ 'sidebar-expanded': !stateStore.isSidebarCollapsed, 'sidebar-collapsed': stateStore.isSidebarCollapsed }">
      <div class="sidebar-wrapper" :class="{ 'collapsed': stateStore.isSidebarCollapsed }">
        <div class="sidebar-container">
          <div class="sidebar-header">
            <el-input v-model="newItemLabel" :placeholder="t('check.recordName')" size="large" @keydown="handleKeyDown" />
            <div class="header-buttons">
              <el-button type="primary" size="large" @click="clearAllItems" :disabled="items.length === 0" class="clear-btn">{{ t('check.clear') }}</el-button>
              <el-button type="success" size="large" @click="goToHealthTrack" class="health-btn">📊 {{ t('health.title') }}</el-button>
            </div>
          </div>
          <div class="sidebar-list">
            <div
                v-for="item in items"
                :key="item.id"
                :class="['sidebar-item', { active: activeItem === item.id, deleting: deletingItems.has(item.id) }]"
                @click="!deletingItems.has(item.id) && handleItemClick(item.id)"
            >
              <span>{{ item.label }}</span>
              <el-icon 
                class="delete-icon" 
                @click.stop="removeItem(item.id)"
                :style="{ opacity: deletingItems.has(item.id) ? 0.5 : 1, cursor: deletingItems.has(item.id) ? 'not-allowed' : 'pointer' }"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
              </el-icon>
            </div>
          </div>
        </div>
        <el-button size="small" class="collapse-btn" @click="toggleSidebar">
          {{ stateStore.isSidebarCollapsed ? '>' : '<' }}
        </el-button>
      </div>
      <div class="main-container">
        <GuidePage v-show="showGuide" ref="guidePageRef" />
        <Main v-show="!showGuide" ref="mainPageRef" @back-id="handleBackId" @jump-to-session="handleJumpToSession" />
      </div>
    </div>
  </div>
</template>

<style scoped>
@import '@/assets/theme.css';

.back-ground {
  background: var(--bg-primary);
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: background-color 0.3s;
}

.content {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
  --sidebar-width: 250px;
  --sidebar-collapsed-width: 40px;
  --dialogbox-left-collapsed: 60px;
  --dialogbox-left-expanded: 280px;
  --dialogbox-width-collapsed: calc(100% - 80px);
  --dialogbox-width-expanded: calc(100% - 300px);
}

.content.sidebar-collapsed {
  --dialogbox-left: var(--dialogbox-left-collapsed);
  --dialogbox-width: var(--dialogbox-width-collapsed);
}

.content.sidebar-expanded {
  --dialogbox-left: var(--dialogbox-left-expanded);
  --dialogbox-width: var(--dialogbox-width-expanded);
}

.sidebar-wrapper {
  position: relative;
  width: 250px;
  transition: width 0.3s ease;
  overflow: visible;
  display: flex;
  align-items: stretch;
}

.sidebar-wrapper.collapsed {
  width: 40px;
}

.sidebar-container {
  width: 100%;
  height: 100%;
  background-color: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  padding: 10px;
  display: flex;
  flex-direction: column;
  z-index: 3;
  transition: all 0.3s ease;
  transform: translateX(0);
}

.sidebar-wrapper.collapsed .sidebar-container {
  display: none;
}

.collapse-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50% 0 0 50%;
  background: linear-gradient(145deg, var(--card-bg), var(--bg-secondary)) !important;
  color: var(--text-secondary);
  border: none !important;
  cursor: pointer;
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
  align-self: center;
  margin-left: -40px;
  z-index: 4;
  flex-shrink: 0;
  font-weight: 500;
  font-size: 0.9rem;
}

.sidebar-wrapper.collapsed .collapse-btn {
  border-radius: 0 50% 50% 0;
  margin-left: 0;
  z-index: 6;
}

.collapse-btn:hover {
  background: linear-gradient(145deg, var(--hover-bg), var(--bg-tertiary)) !important;
  color: var(--accent-color);
  transform: translateY(-2px);
  box-shadow: 
    0 8px 25px rgba(79, 172, 254, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.sidebar-header {
  display: flex;
  gap: 5px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.header-buttons {
  display: flex;
  gap: 5px;
}

/* 清空按钮的特殊样式 - 与添加按钮一致的立体效果 */
.clear-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  font-weight: 600;
  box-shadow: 
    0 4px 15px rgba(102, 126, 234, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 2px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.clear-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: left 0.5s;
}

.clear-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 6px 20px rgba(102, 126, 234, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 2px 0 rgba(0, 0, 0, 0.1);
}

.clear-btn:hover::before {
  left: 100%;
}

.clear-btn:active {
  transform: translateY(1px);
  box-shadow: 
    0 2px 10px rgba(102, 126, 234, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 1px 0 rgba(0, 0, 0, 0.1);
}

.clear-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: 
    0 2px 10px rgba(102, 126, 234, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

/* 健康跟踪按钮样式 - 绿色渐变 */
.health-btn {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  border: none;
  color: white;
  font-weight: 600;
  box-shadow: 
    0 4px 15px rgba(17, 153, 142, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 2px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.health-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: left 0.5s;
}

.health-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 6px 20px rgba(17, 153, 142, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 2px 0 rgba(0, 0, 0, 0.1);
}

.health-btn:hover::before {
  left: 100%;
}

.health-btn:active {
  transform: translateY(1px);
  box-shadow: 
    0 2px 10px rgba(17, 153, 142, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 1px 0 rgba(0, 0, 0, 0.1);
}

.sidebar-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
}

.sidebar-item {
  background: linear-gradient(145deg, var(--bg-tertiary), var(--bg-secondary));
  padding: 10px 25px 10px 15px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.3s ease;
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  margin-right: 0;
  width: calc(100% - 10px);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.sidebar-item.active {
  background: var(--card-bg);
  transform: translateX(8px) translateY(-2px);
  box-shadow:
    0 8px 25px var(--shadow-color),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  z-index: 10;
}

.sidebar-item:hover {
  background: linear-gradient(145deg, var(--hover-bg), var(--bg-tertiary));
  transform: translateX(2px) translateY(-1px);
  box-shadow: 
    0 6px 20px rgba(79, 172, 254, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.delete-icon {
  font-size: 18px;
  cursor: pointer;
  transition: all 0.3s ease;
  transform-origin: center;
  color: var(--text-secondary);
}

.delete-icon:hover {
  color: #e74c3c;
  transform: scale(1.2);
  filter: drop-shadow(0 0 3px rgba(231, 76, 60, 0.5));
}

.delete-icon:active {
  transform: scale(0.9);
  transition: all 0.1s ease;
}

/* 添加删除项的淡出动画 */
.sidebar-item {
  background: #ffffff;
  padding: 10px 25px 10px 15px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.3s ease;
  box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
  margin-right: 0;
  width: calc(100% - 10px);
  animation: slideIn 0.3s ease-out;
  overflow: hidden;
}

/* 定义删除动画 */
@keyframes slideOut {
  0% {
    opacity: 1;
    transform: translateX(0);
    max-height: 100px;
    padding: 10px 25px 10px 15px;
    margin: 0;
  }
  100% {
    opacity: 0;
    transform: translateX(-100%);
    max-height: 0;
    padding: 0 25px 0 15px;
    margin: 0;
    box-shadow: none;
  }
}

/* 添加进入动画 */
@keyframes slideIn {
  0% {
    opacity: 0;
    transform: translateX(-10px);
    max-height: 0;
    padding: 0 25px 0 15px;
  }
  100% {
    opacity: 1;
    transform: translateX(0);
    max-height: 100px;
    padding: 10px 25px 10px 15px;
  }
}

/* 应用删除动画的类 */
.sidebar-item.deleting {
  animation: slideOut 0.3s ease-out forwards;
}

.main-container {
  flex: 1;
  padding: 0;
  transition: margin-left 0.3s ease;
  position: relative;
}

/* 侧边栏展开时的样式 */
.sidebar-expanded :deep(.draggable-container) {
  left: 280px;
  width: calc(100% - 300px);
}

/* 侧边栏收起时的样式 */
.sidebar-collapsed :deep(.draggable-container) {
  left: 60px;
  width: calc(100% - 80px);
}

/* Element Plus 组件样式覆盖 */
:deep(.el-button--primary) {
  background: linear-gradient(145deg, var(--card-bg), var(--bg-secondary)) !important;
  border: none !important;
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
}

:deep(.el-button--primary span),
:deep(.el-button--primary) {
  color: var(--text-secondary) !important;
  font-weight: 500 !important;
  font-size: 0.9rem !important;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(145deg, var(--hover-bg), var(--bg-tertiary)) !important;
  color: var(--accent-color) !important;
  transform: translateY(-2px);
  box-shadow: 
    0 8px 25px rgba(79, 172, 254, 0.25),
    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
}

:deep(.el-button--primary:hover span) {
  color: var(--accent-color) !important;
}

:deep(.el-button--primary:active) {
  background: linear-gradient(145deg, var(--bg-secondary), var(--hover-bg)) !important;
  transform: translateY(0);
  box-shadow: 
    0 2px 10px rgba(0, 0, 0, 0.1),
    inset 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}

/* Element Plus 组件深色模式支持 */
[data-theme='dark'] :deep(.el-button--primary) {
  background: linear-gradient(145deg, var(--card-bg), var(--bg-secondary)) !important;
  border: none !important;
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

[data-theme='dark'] :deep(.el-button--primary span),
[data-theme='dark'] :deep(.el-button--primary) {
  color: var(--text-secondary) !important;
  font-weight: 500 !important;
  font-size: 0.9rem !important;
}

[data-theme='dark'] :deep(.el-button--primary:hover) {
  background: linear-gradient(145deg, var(--hover-bg), var(--bg-tertiary)) !important;
  color: var(--accent-color) !important;
  transform: translateY(-2px);
  box-shadow: 
    0 8px 25px rgba(79, 172, 254, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

[data-theme='dark'] :deep(.el-button--primary:hover span) {
  color: var(--accent-color) !important;
}

[data-theme='dark'] :deep(.el-button--primary:active) {
  background: linear-gradient(145deg, var(--bg-secondary), var(--hover-bg)) !important;
  transform: translateY(0);
  box-shadow: 
    0 2px 10px rgba(0, 0, 0, 0.2),
    inset 0 2px 4px rgba(0, 0, 0, 0.2) !important;
}

[data-theme='dark'] :deep(.el-input__wrapper) {
  --el-input-bg-color: var(--input-bg);
  --el-input-text-color: var(--text-primary);
  --el-input-border-color: var(--border-color);
  --el-input-hover-border-color: var(--accent-color);
  --el-input-focus-border-color: var(--accent-color);
  --el-input-placeholder-color: var(--text-tertiary);
  background: linear-gradient(145deg, var(--input-bg), var(--bg-secondary)) !important;
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
  border: 1px solid var(--border-color) !important;
}

:deep(.el-input__wrapper) {
  background: linear-gradient(145deg, var(--bg-tertiary), var(--bg-secondary)) !important;
  box-shadow: 
    0 4px 6px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 
    0 6px 20px rgba(79, 172, 254, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
  transform: translateY(-1px);
}

:deep(.el-input__wrapper:focus-within) {
  box-shadow: 
    0 8px 25px rgba(79, 172, 254, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
  border-color: var(--accent-color) !important;
  transform: translateY(-1px);
}

[data-theme='dark'] :deep(.el-input__inner) {
  background-color: var(--input-bg);
  color: var(--text-primary);
}

[data-theme='dark'] :deep(.el-input__inner::placeholder) {
  color: var(--text-tertiary);
}

[data-theme='dark'] :deep(.el-card) {
  --el-card-bg-color: var(--card-bg);
  --el-card-border-color: var(--border-color);
  background-color: var(--card-bg);
  border-color: var(--border-color);
}

[data-theme='dark'] :deep(.el-card__body) {
  background-color: var(--card-bg);
  color: var(--text-primary);
}

[data-theme='dark'] :deep(.el-dropdown-menu) {
  --el-dropdown-bg-color: var(--card-bg);
  --el-dropdown-border-color: var(--border-color);
  background-color: var(--card-bg);
  border-color: var(--border-color);
}

[data-theme='dark'] :deep(.el-dropdown-menu__item) {
  color: var(--text-primary);
}

[data-theme='dark'] :deep(.el-dropdown-menu__item:hover) {
  background-color: var(--hover-bg);
  color: var(--accent-color);
}

[data-theme='dark'] :deep(.el-descriptions) {
  --el-descriptions-table-border-color: var(--border-color);
}

[data-theme='dark'] :deep(.el-descriptions__label) {
  color: var(--text-primary);
}

[data-theme='dark'] :deep(.el-descriptions__content) {
  color: var(--text-primary);
}

[data-theme='dark'] :deep(.el-descriptions__body) {
  background-color: var(--card-bg);
  color: var(--text-primary);
}

[data-theme='dark'] :deep(.el-tag) {
  --el-tag-bg-color: rgba(102, 126, 234, 0.1);
  --el-tag-border-color: var(--accent-color);
  --el-tag-text-color: var(--accent-color);
  background-color: rgba(102, 126, 234, 0.1);
  border-color: var(--accent-color);
  color: var(--accent-color);
}

[data-theme='dark'] :deep(.el-tag a) {
  color: var(--accent-color);
}

/* 深色模式下的自定义按钮样式 */
[data-theme='dark'] .collapse-btn {
  background-color: var(--accent-color);
  box-shadow: 2px 0 5px var(--shadow-color);
}

[data-theme='dark'] .collapse-btn:hover {
  background-color: var(--accent-hover);
}

[data-theme='dark'] .sidebar-item {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  box-shadow: 0 2px 10px var(--shadow-color);
}

[data-theme='dark'] .sidebar-item.active {
  background: var(--accent-color);
  color: white;
}

[data-theme='dark'] .sidebar-item:hover {
  background: var(--hover-bg);
  transform: translateX(2px);
}

[data-theme='dark'] .delete-icon {
  color: var(--text-secondary);
}

[data-theme='dark'] .delete-icon:hover {
  color: #e74c3c !important;
  transform: scale(1.2);
  filter: drop-shadow(0 0 3px rgba(231, 76, 60, 0.5));
}

[data-theme='dark'] .sidebar-item.active {
  background: var(--card-bg) !important;
  transform: translateX(8px) translateY(-2px) !important;
  box-shadow:
    0 8px 25px var(--shadow-color),
    inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
  z-index: 10;
}

[data-theme='dark'] .sidebar-item.active:hover {
  transform: translateX(10px) translateY(-3px) !important;
}
</style>
