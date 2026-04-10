<script setup>
import {nextTick, onBeforeMount, onMounted, ref, shallowRef, triggerRef, watch, computed} from 'vue';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import 'github-markdown-css';
import {useStateStore} from "@/stores/stateStore";
import 'highlight.js/styles/github.css';
import axios from 'axios';
import emojiRegex from 'emoji-regex';
import {ElMessage} from "element-plus";
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

// 用于控制消息列表的过渡动画
const isTransitioning = ref(false);
const transitionDuration = 300; // 过渡动画持续时间（毫秒）

// 会话记录缓存，避免重复处理
const sessionCache = ref(new Map());

// 会话状态管理器
const sessions = ref(new Map());
const currentSessionId = ref(null);

// 从本地存储加载会话数据
const loadSessionsFromStorage = () => {
  try {
    const storedSessions = localStorage.getItem('tongueKit_sessions');
    if (storedSessions) {
      const parsedSessions = JSON.parse(storedSessions);
      parsedSessions.forEach(sessionData => {
        sessions.value.set(sessionData.id, sessionData);
        // 同时更新缓存
        const cacheKey = `session_${sessionData.id}`;
        sessionCache.value.set(cacheKey, [...sessionData.messages]);
      });
      console.log('从本地存储加载了会话数据:', parsedSessions.length);
    }
    
    const storedCurrentSessionId = localStorage.getItem('tongueKit_currentSessionId');
    if (storedCurrentSessionId) {
      currentSessionId.value = storedCurrentSessionId;
      console.log('从本地存储加载了当前会话ID:', storedCurrentSessionId);
    }
  } catch (error) {
    console.error('加载会话数据失败:', error);
  }
};

// 保存会话数据到本地存储
const saveSessionsToStorage = () => {
  try {
    const sessionsArray = [];
    sessions.value.forEach(session => {
      sessionsArray.push(session);
    });
    localStorage.setItem('tongueKit_sessions', JSON.stringify(sessionsArray));
    if (currentSessionId.value) {
      localStorage.setItem('tongueKit_currentSessionId', currentSessionId.value);
    } else {
      // 当currentSessionId为null时，清除localStorage中的tongueKit_currentSessionId
      localStorage.removeItem('tongueKit_currentSessionId');
    }
    console.log('会话数据已保存到本地存储:', sessionsArray.length);
  } catch (error) {
    console.error('保存会话数据失败:', error);
  }
};

// 获取当前会话状态
const getCurrentSession = () => {
  if (!currentSessionId.value) return undefined;
  const session = sessions.value.get(currentSessionId.value);
  return session || undefined;
};

// 创建新会话
const createSession = (id) => {
  const newSession = {
    id,
    messages: [
      {
        text: t('chat.welcome'),
        isUser: false,
        time: new Date().toLocaleString('default', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        }),
        loading: false,
        isPicture: false
      }
    ],
    abortController: null,
    isActive: false
  };
  sessions.value.set(id, newSession);
  triggerRef(sessions); // 触发更新
  return newSession;
};

// 激活会话
const activateSession = (id) => {
  // 先取消当前会话的激活状态和正在进行的请求
  if (currentSessionId.value) {
    const currentSession = sessions.value.get(currentSessionId.value);
    if (currentSession) {
      // 取消当前会话正在进行的请求
      if (currentSession.abortController) {
        currentSession.abortController.abort();
        currentSession.abortController = null;
      }
      currentSession.isActive = false;
    }
  }
  
  // 激活新会话
  let session = sessions.value.get(id);
  if (!session) {
    session = createSession(id);
  }
  session.isActive = true;
  currentSessionId.value = id;
  triggerRef(sessions); // 触发更新
  
  // 保存会话数据到本地存储
  saveSessionsToStorage();
};

// 当前会话的消息列表，使用计算属性获取
const messages = computed(() => {
  const currentSession = getCurrentSession();
  return currentSession && currentSession.messages ? currentSession.messages : [];
});

const initPage = async (basePic, sessionName) => {
  console.log('initPage 被调用:', basePic, sessionName);
  
  // 直接创建一个新会话，无论是否已有激活会话
  const sessionId = 'session_' + Date.now();
  console.log('创建新会话:', sessionId);
  
  // 直接创建会话并添加到 sessions Map
  const newSession = {
    id: sessionId,
    messages: [
      {
        text: t('chat.welcome'),
        isUser: false,
        time: new Date().toLocaleString('default', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        }),
        loading: false,
        isPicture: false
      }
    ],
    abortController: null,
    isActive: true
  };
  
  // 清空当前会话状态
  if (currentSessionId.value) {
    const oldSession = sessions.value.get(currentSessionId.value);
    if (oldSession) {
      oldSession.isActive = false;
    }
  }
  
  // 添加新会话到 Map
  sessions.value.set(sessionId, newSession);
  
  // 设置当前会话 ID
  currentSessionId.value = sessionId;
  
  // 确保触发 Vue 响应式更新
  sessions.value = new Map(sessions.value);
  
  console.log('会话创建后 currentSessionId:', currentSessionId.value);
  console.log('sessions 大小:', sessions.value.size);
  console.log('sessions 内容:', Array.from(sessions.value.entries()));
  
  // 等待 Vue 响应式更新完成
  await nextTick();
  
  // 再次检查会话状态
  console.log('nextTick 后 currentSessionId:', currentSessionId.value);
  console.log('nextTick 后 sessions 大小:', sessions.value.size);
  
  // 等待更长时间确保所有更新完成
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // 直接使用新创建的会话，而不是通过 getCurrentSession 获取
  let currentSession = newSession;
  
  // 双重保险：如果直接引用有问题，尝试从 sessions Map 中获取
  if (!currentSession) {
    currentSession = sessions.value.get(sessionId);
  }
  
  if (!currentSession) {
    console.error('无法获取当前会话');
    console.error('sessionId:', sessionId);
    console.error('currentSessionId:', currentSessionId.value);
    console.error('sessions 内容:', Array.from(sessions.value.entries()));
    return;
  }
  
  console.log('成功获取当前会话:', currentSession.id);
  
  const base64 = basePic.base64;
  console.log('图片 base64 长度:', base64 ? base64.length : 0);
  
  if (!base64) {
    console.error('base64 数据为空');
    return;
  }
  
  currentSession.messages.push({
    text: base64,
    isUser: true,
    time: new Date().toLocaleString('default', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }),
    loading: false,
    isPicture: true
  });
  
  console.log('添加图片消息后，消息列表长度:', currentSession.messages.length);
  
  // 触发响应式更新，确保图片立即显示
  sessions.value = new Map(sessions.value); // 这会触发响应式更新
  
  console.log('触发更新后，准备调用 getPictureAnswer');
  getPictureAnswer(basePic.fileData, sessionName, base64);
}

const inputData = async (data, id) => {
  // 激活目标会话
  activateSession(id);
  
  // 获取当前会话
  const currentSession = getCurrentSession();
  if (!currentSession) return;
  
  // 检查会话是否仍在处理中（有加载中的消息）
  const isProcessing = currentSession.messages.some(msg => msg.loading);
  
  // 如果会话仍在处理中，不替换消息
  if (isProcessing) {
    await nextTick();
    scrollToBottom();
    return;
  }
  
  // 检查会话缓存
  const cacheKey = `session_${id}`;
  if (sessionCache.value.has(cacheKey)) {
    // 使用缓存数据，快速切换
    currentSession.messages = sessionCache.value.get(cacheKey);
    // 触发响应式更新，确保会话数据变化能被 Vue 追踪到
    triggerRef(sessions);
    await nextTick();
    scrollToBottom();
    return;
  }
  
  // 显示过渡动画
  isTransitioning.value = true;
  
  // 使用nextTick确保DOM更新
  await nextTick();
  
  // 异步处理记录数据，避免阻塞主线程
  setTimeout(() => {
    // 再次获取当前会话，确保引用仍然有效
    const session = getCurrentSession();
    if (!session) return;
    
    // 再次检查会话是否仍在处理中
    const stillProcessing = session.messages.some(msg => msg.loading);
    if (stillProcessing) {
      isTransitioning.value = false;
      return;
    }
    
    // 从 localStorage 获取图片 base64 数据，使用会话 ID 作为键
    const pictureBase64 = localStorage.getItem(`picture_${id}`);
    console.log(`从 localStorage 读取图片数据，key=picture_${id}, 是否存在: ${!!pictureBase64}`);
    
    // 处理聊天记录，将"Descript it"替换为图片或占位符
    const processedMessages = data.map(item => {
      if (item.isUser && item.text === 'Descript it') {
        // 这是用户发送的"Descript it"消息，应该显示为图片
        if (pictureBase64) {
          // 有 localStorage 中的图片数据，使用它
          console.log('成功从 localStorage 加载图片数据');
          return {
            ...item,
            text: pictureBase64,
            isPicture: true
          };
        } else {
          // 没有图片数据，显示为 [图片] 占位符
          console.warn(`未找到图片数据，key=picture_${id}`);
          return {
            ...item,
            text: '',  // 空文本，避免显示"图片加载失败"
            isPicture: true,
            placeholder: '[图片]'  // 占位符标记
          };
        }
      }
      return item;
    });
    
    // 存入缓存
    sessionCache.value.set(cacheKey, processedMessages);
    
    // 更新消息列表
    session.messages = processedMessages;
    triggerRef(sessions); // 触发更新
    
    // 等待DOM更新后滚动到底部
    nextTick().then(() => {
      scrollToBottom();
      // 隐藏过渡动画
      setTimeout(() => {
        isTransitioning.value = false;
      }, transitionDuration);
    });
  }, 50);
}

async function getRecordData() {
  try {
    const response = await axios.get('/api/user/record', {
      headers: {
        'Authorization': 'Bearer ' + localStorage.getItem('token')
      }
    });
    console.log(response.data.data[response.data.data.length - 1].state);
  } catch (error) {
    console.error('获取 /user/record 失败:', error);
    return null;
  }
}

const resetPage = () => {
  const currentSession = getCurrentSession();
  if (!currentSession) return;
  
  // 重置消息列表，保留会话的AbortController和其他状态
  currentSession.messages = [
    {
      text: t('chat.welcome'),
      isUser: false,
      time: new Date().toLocaleString('default', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }),
      loading: false,
      isPicture: false
    }
  ];
  triggerRef(sessions); // 触发更新
}

const getAllSessions = () => {
  const allSessions = [];
  sessions.value.forEach((session, sessionId) => {
    session.messages.forEach((message, messageIndex) => {
      if (!message.isPicture && message.text) {
        allSessions.push({
          sessionId,
          sessionName: session.name || '会话',
          messageIndex,
          text: message.text,
          isUser: message.isUser,
          time: message.time
        });
      }
    });
  });
  return allSessions;
};

// 重置会话状态，用于当用户关闭记录时调用
const resetSessionState = () => {
  // 先取消当前会话的激活状态和正在进行的请求
  if (currentSessionId.value) {
    const currentSession = sessions.value.get(currentSessionId.value);
    if (currentSession) {
      // 取消当前会话正在进行的请求
      if (currentSession.abortController) {
        currentSession.abortController.abort();
        currentSession.abortController = null;
      }
      currentSession.isActive = false;
    }
  }
  
  // 重置当前会话ID
  currentSessionId.value = null;
  triggerRef(sessions); // 触发更新
  
  // 保存会话数据到本地存储
  saveSessionsToStorage();
};

const scrollToMessage = (sessionId, messageIndex) => {
  // 激活会话
  activateSession(sessionId);
  
  // 通知父组件（Check.vue）更新活跃项和关闭引导页
  emit('jump-to-session', sessionId);
  
  // 等待更长时间确保DOM完全更新
  setTimeout(() => {
    nextTick(() => {
      const messageElements = document.querySelectorAll('.message-item');
      console.log('Message elements found:', messageElements.length);
      console.log('Target message index:', messageIndex);
      
      if (messageElements.length > 0) {
        // 确保索引在有效范围内
        const targetIndex = Math.min(messageIndex, messageElements.length - 1);
        console.log('Adjusted target index:', targetIndex);
        
        if (messageElements[targetIndex]) {
          messageElements[targetIndex].scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
          messageElements[targetIndex].classList.add('highlight');
          setTimeout(() => {
            messageElements[targetIndex].classList.remove('highlight');
          }, 2000);
        }
      }
    });
  }, 300);
};

defineExpose({initPage, inputData, resetPage, activateSession, getAllSessions, scrollToMessage, resetSessionState})

const userAvatar = ref("/static/userDefault.jpg");
const aiAvatar = ref("/static/aiDefault.jpg");

let newMessage = ref('');
const chatContainer = ref(null);
const stateStore = useStateStore();

const md = new MarkdownIt({
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, {language: lang}).value}</code></pre>`;
      } catch (__) {
      }
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`;
  },
});

function org(input) {
  const noMarkdown = input
      .replace(/!\[.*?\]\(.*?\)/g, '')
      .replace(/\[(.*?)\]\(.*?\)/g, '$1')
      .replace(/[`_*~#>]/g, '')
      .replace(/\n+/g, ' ');
  const regex = emojiRegex();
  return noMarkdown.replace(regex, '')
}

const sendMessage = async () => {
  if (newMessage.value.trim() !== '') {
    const messageContent = newMessage.value;
    const targetSession = getCurrentSession();
    if (!targetSession) return;
    
    // 检查是否是快捷指令
    if (messageContent.startsWith('/')) {
      await handleCommand(messageContent, targetSession);
      newMessage.value = '';
      return;
    }
    
    targetSession.messages.push({
      text: messageContent,
      isUser: true,
      time: new Date().toLocaleString('default', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }),
      loading: false,
      isPicture: false
    });
    sessions.value = new Map(sessions.value); // 确保触发Vue响应式更新
    saveHistory(targetSession);
    await nextTick();
    scrollToBottom();
    await sendAIMessage(messageContent);
  }
};

const sendAIMessage = async (messageContent) => {
  // 保存当前会话的引用，确保即使会话切换也能正确处理
  const targetSession = getCurrentSession();
  const sessionId = currentSessionId.value;
  if (!targetSession || !sessionId) return;
  
  // 保存会话的ID和引用，确保即使会话切换也能正确处理
  const sessionIdToUse = sessionId;
  const sessionToUse = targetSession;
  
  setTimeout(async () => {
    // 使用保存的会话引用，而不是再次获取
    if (!sessionToUse) return;
    
    const newMessage = {
      text: '',
      isUser: false,
      time: new Date().toLocaleString('default', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }),
      loading: true,
      isPicture: false,
      receivedContent: false // 标记是否已接收到内容
    };
    
    sessionToUse.messages.push(newMessage);
    sessions.value = new Map(sessions.value); // 确保触发Vue响应式更新
    await nextTick(); // 确保DOM更新
    scrollToBottom();
    await getAnswer(messageContent, sessionToUse, sessionIdToUse);
  }, 500);
};


const getAnswer = async (messageContent, sessionToUse, sessionIdToUse) => {
     // 检查参数是否有效
     if (!messageContent || !sessionToUse || !sessionIdToUse) return;
     
     // 使用传递的会话引用和ID，确保即使会话切换也能正确处理
     
     const timeout = 120000;
     let token = localStorage.getItem('token');
     const timeoutPromise = new Promise((_, reject) =>
         setTimeout(() => reject(new Error("请求超时")), timeout)
     );

     // 创建新的AbortController，取消该会话之前的请求
     if (sessionToUse.abortController) {
       sessionToUse.abortController.abort();
     }
     sessionToUse.abortController = new AbortController();
     const signal = sessionToUse.abortController.signal;

     try {
       scrollToBottom();
       console.log(baseURL);
      const response = await Promise.race([
        fetch(`${baseURL}/session/${sessionIdToUse}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
            "Accept-Language": stateStore.language
          },
          body: JSON.stringify({
            input: personalPrompt + messageContent,
            language: stateStore.language
          }),
          signal: signal // 添加signal参数
        }),
        timeoutPromise,
      ]);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error("流式返回没有body");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let done = false;

    // 不立即解除加载，而是保持Thinking状态直到收到第一块数据

    while (!done) {
      const {value, done: readerDone} = await reader.read();
      done = readerDone;

      if (value) {
        const chunk = decoder.decode(value, {stream: true});
        const lines = chunk.split("\n");
        lines.forEach((line) => {
          if (line.trim()) {
            try {
              const parsedChunk = JSON.parse(line);
              if (!parsedChunk.is_complete && parsedChunk.token) {
                // 第一次收到有效token时，才停止thinking状态
                const currentMessage = sessionToUse.messages[sessionToUse.messages.length - 1];
                if (!currentMessage.receivedContent) {
                  currentMessage.receivedContent = true;
                  currentMessage.loading = false; // 解除加载
                }
                // 过滤掉可能导致URL错误的base64数据
                let token = parsedChunk.token;
                // 移除可能的base64图片数据URL，避免net::ERR_INVALID_URL错误
                if (token.includes('data:image') && token.includes('base64,')) {
                  token = '[图片数据]';
                }
                currentMessage.text += token;
                sessions.value = new Map(sessions.value); // 确保触发Vue响应式更新
              }
              if (parsedChunk.session_id) {
                // 使用原始会话ID，确保即使会话切换也能正确更新
                const oldSessionId = sessionIdToUse;
                
                // 如果会话ID发生变化，更新sessions Map
                if (oldSessionId && oldSessionId !== parsedChunk.session_id) {
                  // 从sessions Map中删除旧ID的会话
                  sessions.value.delete(oldSessionId);
                  // 用新ID重新添加会话
                  sessions.value.set(parsedChunk.session_id, sessionToUse);
                  // 更新会话对象的ID属性
                  sessionToUse.id = parsedChunk.session_id;
                  triggerRef(sessions); // 触发更新
                  
                  // 更新会话缓存键，确保缓存数据与新ID关联
                  const oldCacheKey = `session_${oldSessionId}`;
                  const newCacheKey = `session_${parsedChunk.session_id}`;
                  if (sessionCache.value.has(oldCacheKey)) {
                    const cachedMessages = sessionCache.value.get(oldCacheKey);
                    sessionCache.value.delete(oldCacheKey);
                    sessionCache.value.set(newCacheKey, cachedMessages);
                  }
                }
                
                // 只在当前会话是活动会话时更新currentSessionId
                if (sessionToUse.isActive) {
                  currentSessionId.value = parsedChunk.session_id;
                }
                // 通知父组件会话ID变化
                emit("back-id", parsedChunk.session_id);
              }
              scrollToBottom();
            } catch (parseError) {
              console.warn("JSON解析失败，跳过该行: ", line);
            }
          }
        });
      }

    }
    scrollToBottom();
    console.log("流结束");
    sessionToUse.abortController = null; // 请求结束，重置 AbortController
    // 通知父组件处理成功，切换到聊天输入框状态
    emit("get-return", {success: true});
    // 更新会话缓存
    const cacheKey = `session_${sessionToUse.id}`;
    sessionCache.value.set(cacheKey, sessionToUse.messages);
    
    // 触发健康跟踪页面刷新（通知有新分析完成）
    window.dispatchEvent(new CustomEvent('tongue-analysis-complete'));
    localStorage.setItem('tongue_analysis_complete', Date.now().toString());
  } catch (error) {
    // 如果是AbortError，说明请求被取消，不需要显示错误信息
    if (error.name === 'AbortError') {
      console.log("请求被取消");
      sessionToUse.abortController = null;
      // 通知父组件处理失败，切换回上传照片状态
      emit("get-return", {success: false});
      return;
    }
    
    // 忽略网络错误，如ERR_ABORTED
    if (error.message && error.message.includes('ERR_ABORTED')) {
      console.log("网络请求被中止，忽略错误");
      sessionToUse.abortController = null;
      // 通知父组件处理失败，切换回上传照片状态
      emit("get-return", {success: false});
      return;
    }
    
    console.error("错误: ", error);
    // 错误时处理最后一条消息
    if (sessionToUse.messages.length > 0) {
      const lastMessage = sessionToUse.messages[sessionToUse.messages.length - 1];
      if (lastMessage.loading) {
        // 替换为错误消息，而不是删除
        lastMessage.loading = false;
        lastMessage.receivedContent = true;
        lastMessage.text = error.message === "请求超时" ? t('chat.requestTimeout') : t('chat.errorOccurred');
        sessions.value = new Map(sessions.value); // 确保触发Vue响应式更新
      }
    }
    sessionToUse.abortController = null; // 重置AbortController
    // 通知父组件处理失败，切换回上传照片状态
    emit("get-return", {success: false});
  }
  saveHistory(sessionToUse);
};

function logFormData(formData) {
  for (let pair of formData.entries()) {
    console.log(pair[0] + ':', pair[1]);
  }
}

const getPictureAnswer = async (fileData, sessionName, base64) => {
  // Ensure sessionName is provided
  if (!sessionName || sessionName.trim() === '') {
    console.error('Error: sessionName is required but not provided');
    ErrorPop('会话名称不能为空');
    emit("get-return", {success: false});
    return;
  }
  
  console.log('getPictureAnswer 被调用');
  console.log('currentSessionId:', currentSessionId.value);
  console.log('sessions 大小:', sessions.value.size);
  
  // 存储当前会话的引用，确保回调函数始终使用正确的会话
  const targetSession = getCurrentSession();
  if (!targetSession) {
    console.error('无法获取当前会话');
    console.error('currentSessionId:', currentSessionId.value);
    console.error('sessions 内容:', Array.from(sessions.value.entries()));
    emit("get-return", {success: false});
    return;
  }
  
  console.log('成功获取当前会话:', targetSession.id);
  
  // 保存会话的引用和原始ID，确保即使会话切换也能正确处理
  const sessionToUse = targetSession;
  const originalSessionId = currentSessionId.value;
  
  console.log('使用会话:', originalSessionId);
  
  // 创建新的AbortController，取消该会话之前的请求
  if (sessionToUse.abortController) {
    sessionToUse.abortController.abort();
  }
  sessionToUse.abortController = new AbortController();
  const signal = sessionToUse.abortController.signal;
  
  // 只在开始时调用一次emit，并且设置success为true，表示处理开始
  emit("get-return", {success: true});
  
  // 不使用setTimeout，直接添加消息
  const newMessage = {
    text: '',
    isUser: false,
    time: new Date().toLocaleString('default', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }),
    loading: true,
    isPicture: false,
    receivedContent: false // 标记是否已接收到内容
  };
  sessionToUse.messages.push(newMessage);
  sessions.value = new Map(sessions.value); // 确保触发Vue响应式更新
  await nextTick();
  
  console.log('添加消息后，消息列表长度:', sessionToUse.messages.length);
  const timeout = 120000;

  let token = localStorage.getItem('token');

  const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error("请求超时")), timeout)
  );

  try {
    const response = await Promise.race([
      (async () => {
        const formData = new FormData();
        formData.append('file_data', fileData, fileData.name);
        formData.append('user_input', "Descript it");
        formData.append('name', sessionName);
        formData.append('session_id', originalSessionId.toString());
        
        // 确保使用正确的认证头
        const authToken = localStorage.getItem('token');
        return await fetch(`${baseURL}/session`, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${authToken}`
          },
          body: formData,
          signal: signal // 添加signal参数
        });
      })(),
      timeoutPromise,
    ]);


    if (!response.ok) {
      emit("get-return", {success: false});
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error("流式返回没有body");
    }
    emit("get-return", {success: true});

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let done = false;

    // 不立即解除加载，而是保持Thinking状态直到收到第一块数据

    while (!done) {
      const {value, done: readerDone} = await reader.read();
      done = readerDone;

      if (value) {
        const chunk = decoder.decode(value, {stream: true});
        const lines = chunk.split("\n");

        lines.forEach((line) => {
          if (line.trim()) {
            try {
              const parsedChunk = JSON.parse(line);
              if (!parsedChunk.is_complete && parsedChunk.token) {
                // 第一次收到有效token时，才停止thinking状态
                const currentMessage = sessionToUse.messages[sessionToUse.messages.length - 1];
                if (!currentMessage.receivedContent) {
                  currentMessage.receivedContent = true;
                  currentMessage.loading = false; // 解除加载
                }
                // 过滤掉可能导致URL错误的base64数据
                let token = parsedChunk.token;
                // 移除可能的base64图片数据URL，避免net::ERR_INVALID_URL错误
                if (token.includes('data:image') && token.includes('base64,')) {
                  token = '[图片数据]';
                }
                currentMessage.text += token;
                sessions.value = new Map(sessions.value); // 确保触发Vue响应式更新
              }
              if (parsedChunk.session_id) {
                // 使用原始会话ID，确保即使会话切换也能正确更新
                const oldSessionId = originalSessionId;
                
                // 如果会话ID发生变化，更新sessions Map
                if (oldSessionId && oldSessionId !== parsedChunk.session_id) {
                  // 从sessions Map中删除旧ID的会话
                  sessions.value.delete(oldSessionId);
                  // 用新ID重新添加会话
                  sessions.value.set(parsedChunk.session_id, sessionToUse);
                  // 更新会话对象的ID属性
                  sessionToUse.id = parsedChunk.session_id;
                  triggerRef(sessions); // 触发更新
                  
                  // 更新会话缓存键，确保缓存数据与新ID关联
                  const oldCacheKey = `session_${oldSessionId}`;
                  const newCacheKey = `session_${parsedChunk.session_id}`;
                  if (sessionCache.value.has(oldCacheKey)) {
                    const cachedMessages = sessionCache.value.get(oldCacheKey);
                    sessionCache.value.delete(oldCacheKey);
                    sessionCache.value.set(newCacheKey, cachedMessages);
                  }
                }
                
                // 只在当前会话是活动会话时更新currentSessionId
                if (sessionToUse.isActive) {
                  currentSessionId.value = parsedChunk.session_id;
                }
                // 保存图片base64到localStorage，以便刷新后恢复显示
                localStorage.setItem(`picture_${parsedChunk.session_id}`, base64);
                emit("back-id", parsedChunk.session_id);
              }
              scrollToBottom();
            } catch (parseError) {
              console.warn("JSON解析失败，跳过该行: ", line);
            }
          }
        });
      }
    }

    // 确保在流结束时停止最后一条消息的加载状态
    if (sessionToUse.messages.length > 0 && sessionToUse.messages[sessionToUse.messages.length - 1].loading) {
      const currentMessage = sessionToUse.messages[sessionToUse.messages.length - 1];
      currentMessage.loading = false;
      // 如果没有接收到内容，标记为已接收，这样就不会在UI上显示空白
      if (!currentMessage.receivedContent) {
        currentMessage.receivedContent = true;
      }
    }
    scrollToBottom();
    console.log("流结束");
    sessionToUse.abortController = null; // 请求结束，重置AbortController
    // 通知父组件处理成功，切换到聊天输入框状态
    emit("get-return", {success: true});
    // 更新会话缓存
    const cacheKey = `session_${sessionToUse.id}`;
    sessionCache.value.set(cacheKey, sessionToUse.messages);
  } catch (error) {
    // 如果是AbortError，说明请求被取消，不需要显示错误信息
    if (error.name === 'AbortError') {
      console.log("请求被取消");
      sessionToUse.abortController = null;
      // 通知父组件处理失败，切换回上传照片状态
      emit("get-return", {success: false});
      return;
    }
    
    // 忽略网络错误，如ERR_ABORTED
    if (error.message && error.message.includes('ERR_ABORTED')) {
      console.log("网络请求被中止，忽略错误");
      sessionToUse.abortController = null;
      // 通知父组件处理失败，切换回上传照片状态
      emit("get-return", {success: false});
      return;
    }
    
    emit("get-return", {success: false});
    console.error("错误: ", error);
    // 错误时处理最后一条消息
    if (sessionToUse.messages.length > 0) {
      const lastMessage = sessionToUse.messages[sessionToUse.messages.length - 1];
      if (lastMessage.loading) {
        // 替换为错误消息，而不是删除
        lastMessage.loading = false;
        lastMessage.receivedContent = true;
        lastMessage.text = error.message === "请求超时" ? t('chat.requestTimeout') : t('chat.errorOccurred');
        sessions.value = new Map(sessions.value); // 确保触发Vue响应式更新
      }
    }
    if (error.message === "请求超时") {
      ErrorPop(t('chat.requestTimeout'));
    } else {
      ErrorPop(t('chat.errorOccurred'));
    }
    sessionToUse.abortController = null; // 错误时，重置AbortController
  }
};

const getPictureId = () => {
  return currentSessionId.value;
}

// Markdown渲染缓存，避免重复渲染相同内容
const markdownCache = new Map();

const renderedText = (text) => {
  // 检查缓存
  if (markdownCache.has(text)) {
    return markdownCache.get(text);
  }
  
  // 渲染并缓存结果
  const result = md.render(text);
  markdownCache.set(text, result);
  
  return result;
};

// 防抖函数，减少频繁调用scrollToBottom
const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(null, args), delay);
  };
};

const scrollToBottom = debounce(() => {
  if (chatContainer.value) {
    // 使用requestAnimationFrame优化滚动性能
    requestAnimationFrame(() => {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    });
  }
}, 50);

const handleCommand = async (command, session) => {
  const commands = {
    '/help': () => {
      session.messages.push({
        text: '可用快捷指令：\n/help - 显示帮助信息\n/clear - 清空当前对话\n/export - 导出当前对话',
        isUser: false,
        time: new Date().toLocaleString('default', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        }),
        loading: false,
        isPicture: false
      });
    },
    '/clear': async () => {
      // 显示加载状态
      session.messages = [
        {
          text: '正在清空对话...',
          isUser: false,
          time: new Date().toLocaleString('default', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
          }),
          loading: true,
          isPicture: false
        }
      ];
      // 确保Vue响应式更新
      sessions.value = new Map(sessions.value);
      
      try {
        // 调用后端API删除会话记录
        const response = await axios.delete(`/api/model/record/${session.id}`, {
          headers: {
            'Authorization': 'Bearer ' + localStorage.getItem('token')
          }
        });
        
        console.log('删除会话API响应:', response);
        
        // 后端删除成功后，更新前端状态
        session.messages = [
          {
            text: '对话已清空',
            isUser: false,
            time: new Date().toLocaleString('default', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            }),
            loading: false,
            isPicture: false
          }
        ];
        
        // 清空stateStore中的聊天历史
        stateStore.setChatHistory(session.messages);
        // 清空会话缓存
        const cacheKey = `session_${session.id}`;
        sessionCache.value.delete(cacheKey);
        // 从sessions Map中删除会话
        sessions.value.delete(session.id);
        // 重置当前会话ID
        currentSessionId.value = null;
        // 确保Vue响应式更新
        sessions.value = new Map(sessions.value);
        
        // 显示成功消息
        ElMessage({
          showClose: true,
          message: '对话已彻底清空，刷新后不会再显示',
          type: 'success',
          duration: 2000
        });
        
      } catch (error) {
        console.error('删除会话失败:', error);
        
        // 错误时的处理
        session.messages = [
          {
            text: '对话已清空（本地）',
            isUser: false,
            time: new Date().toLocaleString('default', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            }),
            loading: false,
            isPicture: false
          }
        ];
        
        // 清空stateStore中的聊天历史
        stateStore.setChatHistory(session.messages);
        // 清空会话缓存
        const cacheKey = `session_${session.id}`;
        sessionCache.value.delete(cacheKey);
        // 确保Vue响应式更新
        sessions.value = new Map(sessions.value);
        
        // 显示错误消息
        ElMessage({
          showClose: true,
          message: '本地清空成功，但服务器删除失败，刷新后可能仍会显示',
          type: 'warning',
          duration: 2000
        });
      }
    },
    '/export': () => {
      exportConversation(session);
    }
  };
  
  const cmd = command.toLowerCase();
  if (commands[cmd]) {
    await commands[cmd]();
  } else {
    session.messages.push({
      text: `未知指令: ${command}\n输入 /help 查看可用指令`,
      isUser: false,
      time: new Date().toLocaleString('default', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }),
      loading: false,
      isPicture: false
    });
  }
};

const exportConversation = async (session) => {
  try {
    const content = session.messages
      .filter(msg => !msg.loading && msg.receivedContent)
      .map(msg => {
        const role = msg.isUser ? '用户' : 'AI';
        const time = msg.time;
        // 处理图片消息，避免导出 base64 乱码
        if (msg.isPicture || (msg.text && msg.text.length > 1000 && msg.text.startsWith('data:image'))) {
          return `[${time}] ${role}:\n[图片]\n`;
        }
        return `[${time}] ${role}:\n${msg.text}\n`;
      })
      .join('\n');
    
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `对话记录_${new Date().getTime()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    session.messages.push({
      text: '对话已导出',
      isUser: false,
      time: new Date().toLocaleString('default', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }),
      loading: false,
      isPicture: false
    });
  } catch (error) {
    console.error('导出失败:', error);
    session.messages.push({
      text: '导出失败，请重试',
      isUser: false,
      time: new Date().toLocaleString('default', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }),
      loading: false,
      isPicture: false
    });
  }
};

let audioType = "De";
watch(
    () => stateStore.audioType,
    (newValue, oldValue) => {
      audioType = newValue;
    }
);

const isPlaying = ref(false);
const fetchAndPlayAudio = async (text) => {
  text = org(text);

  if (audioType === "De") {
    if (isPlaying.value) {
      stopAudio();
    } else {
      playAudio(text);
    }
  }
};

const voices = ref([]);
const loadVoices = () => {
  voices.value = window.speechSynthesis.getVoices().filter(voice => voice.lang.startsWith("zh"));
};

onMounted(() => {
  loadVoices();
  window.speechSynthesis.onvoiceschanged = loadVoices;
});

const stopAudio = () => {
  window.speechSynthesis.cancel();
  isPlaying.value = false;
};

const playAudio = (text) => {
  if (!text) {
    return;
  }
  const synth = window.speechSynthesis;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "zh-CN";
  if (voices.value.length > 6) {
    utterance.voice = voices.value[6];
  }
  utterance.onstart = () => {
    isPlaying.value = true;
  };
  utterance.onend = () => {
    isPlaying.value = false;
  };
  utterance.onerror = () => {
    isPlaying.value = false;
  };
  synth.speak(utterance);
};

let baseURL = ""
let personalPrompt = ""
onBeforeMount(() => {
  aiAvatar.value = stateStore.aiImagePath;
  userAvatar.value = stateStore.userImagePath;
  stateStore.setaudioType("De");
  baseURL = stateStore.baseUrl;
  personalPrompt = stateStore.personalPrompt;
  
  // 从本地存储加载会话数据
  loadSessionsFromStorage();
  
  stateStore.setMainComponent({
    handleCommand: handleCommand,
    getCurrentSession: getCurrentSession,
    getAllSessions: getAllSessions,
    scrollToMessage: scrollToMessage
  });
});

const saveHistory = (sessionToUse) => {
  // 如果提供了会话引用，使用它；否则使用当前会话
  const session = sessionToUse || getCurrentSession();
  if (session) {
    stateStore.setChatHistory(session.messages);
    // 更新会话缓存，确保切换会话后能保持状态
    const cacheKey = `session_${session.id}`;
    sessionCache.value.set(cacheKey, [...session.messages]);
    
    // 保存会话数据到本地存储
    saveSessionsToStorage();
  }
};

const props = defineProps({
  receivedInput: String
});

watch(() => props.receivedInput, (newValue) => {
  if (newValue !== undefined && newValue !== '') {
    // 检查 newValue 是否包含逗号，如果包含，取逗号后面的部分
    const commaIndex = newValue.indexOf(',');
    if (commaIndex !== -1) {
      const firstValue = newValue.slice(commaIndex + 1);
      handleReceivedInput(firstValue);
    } else {
      handleReceivedInput(newValue);
    }
  }
});

const handleReceivedInput = (inputValue) => {
  newMessage.value = inputValue;
  sendMessage();
};

const ErrorPop = (info, time = 3000) => {
  ElMessage({
    showClose: true,
    message: info,
    type: 'error',
    duration: time
  })
}

const SuccessPop = (info, time = 2000) => {
  ElMessage({
    showClose: true,
    message: info,
    type: 'success',
    duration: time
  })
}

const deleteMessage = (index) => {
  const currentSession = getCurrentSession();
  if (currentSession) {
    currentSession.messages.splice(index, 1);
    triggerRef(sessions); // 触发更新
    saveHistory();
  }
};

const emit = defineEmits(['get-return', 'back-id', 'jump-to-session']);
</script>

<template>
  <div class="chat-page" ref="chatContainer" :class="{ 'transitioning': isTransitioning }">
    <transition-group
        name="message-fade"
        tag="div"
        class="message-list"
    >
      <div
          v-for="(message, index) in messages"
          :key="index"
          class="message-item"
          :class="message.isUser ? 'user-message' : 'ai-message'"
      >
        <div class="avatar" @dblclick="deleteMessage(index)">
          <img v-if="message.isUser" :src="userAvatar" alt="Image"/>
          <img v-else :src="aiAvatar" alt="Image"/>
        </div>
        <div class="message-content">
          <div v-if="message.loading" class="loading-text-gradient">
            {{ t('chat.thinking') }}
          </div>
          <div v-else>
            <div v-if="!message.isUser" class="message-text markdown-body" v-html="renderedText(message.text)"></div>
            <div v-else class="message-text">
              <div v-if="message.isPicture">
              <img v-if="message.text && message.text.startsWith('data:image')" :src="message.text" alt="舌头图片"
                   style="width: 200px; border: 1px solid #ddd; border-radius: 10px;"/>
              <div v-else-if="message.placeholder" class="placeholder-message">{{ message.placeholder }}</div>
              <div v-else class="placeholder-message">[图片]</div>
            </div>
              <div v-else>
                {{ message.text }}
              </div>
            </div>
          </div>
          <div class="message-time">{{ message.time }}
            <button v-if="!message.isUser && !message.loading" class="speech-button right-aligned"
                    @click="fetchAndPlayAudio(message.text)">🔊
              {{ t('chat.playAudio') }}
            </button>
          </div>
        </div>
      </div>
    </transition-group>
    
    <!-- 加载遮罩 -->
    <div v-if="isTransitioning" class="transition-mask">
      <div class="transition-spinner"></div>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  padding: 0px;
  margin-top: 20px;
  height: calc(100vh - 100px);
  overflow-y: auto;
  flex-grow: 1;
  scroll-behavior: smooth;
}

.message-item {
  display: flex;
  align-items: flex-end;
  margin-bottom: 10px;
}

.user-message {
  flex-direction: row-reverse;
  text-align: left;
}

.ai-message {
  flex-direction: row;
}

.avatar {
  width: 40px;
  height: 40px;
  margin: 0 10px;
}

.avatar img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.message-content {
  max-width: 60%;
  background-color: var(--card-bg);
  border-radius: 10px;
  padding: 10px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  font-family: 'Arial', 'Helvetica', sans-serif;
  font-size: 16px;
  line-height: 1.0;
  color: var(--text-primary);
  transition: background-color 0.3s, color 0.3s;
}

.message-text {
  color: var(--text-primary);
  transition: color 0.3s;
}

.user-message .message-content {
  background-color: #8fefdd;
}

.ai-message .message-content {
  font-size: 16px;
}

.message-time {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 7px;
  transition: color 0.3s;
}

.markdown-body {
  box-sizing: border-box;
  min-width: 200px;
  max-width: 980px;
  margin: 0 auto;
  padding: 15px;
  background-color: var(--card-bg);
  border-radius: 8px;
  transition: background-color 0.3s;
}

[data-theme='dark'] .message-content {
  color: #ffffff;
}

[data-theme='dark'] .message-text {
  color: #ffffff;
}

[data-theme='dark'] .user-message .message-content {
  background-color: #1e4b3b;
  color: #ffffff;
}

@media (max-width: 767px) {
  .markdown-body {
    padding: 15px;
  }
}

.loading-text-gradient {
  font-size: 18px;
  font-family: 'Times New Roman', serif;
  font-style: italic;
  position: relative;
  color: var(--text-tertiary);
  overflow: hidden;
  padding-bottom: 5px;
  transition: color 0.3s;
}

.loading-text-gradient::before {
  content: "生成中...";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(120deg, rgba(0, 0, 255, 0.1), var(--card-bg), rgba(0, 0, 255, 0.1));
  background-size: 1000% 100%;
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shine 3.0s ease-in-out infinite;
}

@keyframes shine {
  0% {
    background-position: -150% 0;
  }
  100% {
    background-position: 150% 0;
  }
}

.speech-button.right-aligned {
  float: right;
  margin-left: 10px;
  font-size: 12px;
  color: var(--text-secondary);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.3s;
}

.speech-button.right-aligned:hover {
  color: var(--accent-color);
}
/* 消息过渡动画 */
.message-fade-enter-active,
.message-fade-leave-active {
  transition: all 0.3s ease;
}

.message-fade-enter-from,
.message-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.message-fade-move {
  transition: transform 0.3s ease;
}

/* 消息列表容器 */
.message-list {
  flex-grow: 1;
}

/* 过渡状态样式 */
.chat-page.transitioning {
  position: relative;
  overflow: hidden;
}

/* 加载遮罩 */
.transition-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.3);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
  border-radius: 10px;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.transition-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-color);
  border-top: 4px solid var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.message-item.highlight {
  animation: highlight-pulse 2s ease-in-out;
}

@keyframes highlight-pulse {
  0%, 100% {
    background-color: transparent;
  }
  50% {
    background-color: rgba(102, 126, 234, 0.2);
  }
}
</style>
