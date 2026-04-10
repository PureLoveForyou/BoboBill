<script setup>
defineOptions({ name: 'AIAssistant' })
import { ref, computed, watch, nextTick, onMounted, onActivated, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAiApi } from '../composables/useAiApi'
import { marked } from 'marked'

const { t } = useI18n()
const {
  chatStream, isConfigured, aiConfigs, activeConfigId, activeConfig,
  activeModelName, fetchConfigs, selectConfig,
  chats, activeChatId, activeChat, currentMessages,
  fetchChats, createChatSession, switchChatSession,
  deleteChatSession: deleteChat, clearChatSession, addMessage, updateMessage,
  streamAbortController,
} = useAiApi()

// ====== EVA 眼睛跟踪 ======
const evaContainerRef = ref(null)
const eyeLeftRef = ref(null)
const eyeRightRef = ref(null)
const eyeOffsetX = ref(0)
const eyeOffsetY = ref(0)

const updateEyePosition = (clientX, clientY) => {
  if (!evaContainerRef.value) return
  const rect = evaContainerRef.value.getBoundingClientRect()
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2
  const maxMove = 6
  const dx = clientX - centerX
  const dy = clientY - centerY
  const dist = Math.sqrt(dx * dx + dy * dy)
  const clampDist = Math.min(dist, 200)
  eyeOffsetX.value = (dx / (dist || 1)) * (clampDist / 200) * maxMove
  eyeOffsetY.value = (dy / (dist || 1)) * (clampDist / 200) * maxMove
}

const onMouseMove = (e) => updateEyePosition(e.clientX, e.clientY)
const onTouchMove = (e) => {
  if (e.touches.length > 0) updateEyePosition(e.touches[0].clientX, e.touches[0].clientY)
}

onMounted(() => {
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('touchmove', onTouchMove, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('touchmove', onTouchMove)
})

// ====== 聊天功能 ======
const inputText = ref('')
const isLoading = ref(false)
const chatContainer = ref(null)
const showSidebar = ref(false)
const showScrollDownBtn = ref(false)

// 监听滚动位置，决定是否显示"回到底部"按钮
let scrollCheckTimeout = null
const onChatScroll = () => {
  clearTimeout(scrollCheckTimeout)
  scrollCheckTimeout = setTimeout(() => {
    if (chatContainer.value) {
      const { scrollTop, scrollHeight, clientHeight } = chatContainer.value
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight
      showScrollDownBtn.value = distanceFromBottom > 100
    }
  }, 50)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

watch(activeChatId, () => scrollToBottom())

// 当 EchoAssistant 流式传输时，同步滚动到底部（共享 currentMessages）
watch(currentMessages, () => {
  if (isLoading.value) scrollToBottom()
}, { deep: true })

const handleSend = async () => {
  const text = inputText.value.trim().replace(/\n+$/, '')
  if (!text || isLoading.value || !isConfigured.value) return

  // 确保有活跃会话
  if (!activeChatId.value) {
    const session = await createChatSession()
    if (!session) return
  }

  const sid = activeChatId.value
  if (!sid) return

  // 添加用户消息到内存和数据库（去除尾部多余换行）
  const cleanText = text.replace(/\n+$/, '')
  currentMessages.value.push({ role: 'user', content: cleanText })
  addMessage(sid, 'user', cleanText).catch(() => {})

  inputText.value = ''
  isLoading.value = true
  scrollToBottom()

  // AI 占位消息（内存）
  const placeholderIdx = currentMessages.value.length
  currentMessages.value.push({ role: 'assistant', content: '', reasoning: '', loading: true, reasoningExpanded: true })

  // 构建发送给后端的历史
  const historyToSend = currentMessages.value.filter(m => !m.loading && m.role !== undefined).slice(0, -1)

  let curContent = ''
  let curReasoning = ''

  // 创建 AbortController 用于中断请求
  const controller = new AbortController()
  streamAbortController.value = controller

  try {
    const result = await chatStream(cleanText, historyToSend, (event) => {
      const msg = currentMessages.value[placeholderIdx]
      if (!msg || msg.role !== 'assistant') return

      if (event.type === 'reasoning') {
        curReasoning += event.content
        msg.reasoning = curReasoning
        scrollToBottom()
      } else if (event.type === 'tool_start') {
        // AI 开始调用工具
        if (!msg.toolCalls) msg.toolCalls = []
        msg.toolCalls.push({
          name: event.content.name,
          description: event.content.description,
          status: 'running' // running | done
        })
        scrollToBottom()
      } else if (event.type === 'tool_end') {
        // 工具执行完成
        if (msg.toolCalls) {
          const tc = msg.toolCalls.find(t => t.name === event.content.name)
          if (tc) tc.status = 'done'
        }
        scrollToBottom()
      } else if (event.type === 'content') {
        curContent += event.content
        msg.content = curContent
        msg.loading = false
        scrollToBottom()
      } else if (event.type === 'done') {
        msg.loading = false
        if (curReasoning) msg.reasoningExpanded = false
      } else if (event.type === 'error') {
        msg.content = `[错误] ${event.content}`
        msg.loading = false
        msg.toolStatus = ''
      }
    }, controller.signal)

    // 流结束后更新
    const finalMsg = currentMessages.value[placeholderIdx]
    if (finalMsg && finalMsg.role === 'assistant') {
      finalMsg.loading = false
      if (!finalMsg.content && !result.success && !result.aborted) {
        finalMsg.content = `[错误] ${result.message}`
      }
      // 如果是中断，标记中断
      if (result.aborted && curContent) {
        finalMsg.content = curContent + '\n\n*[回答已中断]*'
      }
    }

    // 流完成后才保存 AI 消息到数据库（避免存入空消息导致空气泡）
    const finalContent = finalMsg?.content || null
    const finalReasoning = finalMsg?.reasoning || null
    const finalToolCalls = finalMsg?.toolCalls || null
    if (finalContent || finalReasoning || finalToolCalls) {
      addMessage(sid, 'assistant', finalContent, finalReasoning, finalToolCalls).catch(() => {})
    }

    // 更新会话标题（取第一条用户消息前30字）
    const newTitle = cleanText.slice(0, 30).replace(/\n/g, ' ') || '新对话'
    updateChatTitle(activeChatId.value, newTitle).catch(() => {})
    fetchChats().catch(() => {})

    // 移动到列表顶部
    const idx = chats.value.findIndex(c => c.id === sid)
    if (idx > 0) {
      const [item] = chats.value.splice(idx, 1)
      chats.value.unshift(item)
    }
  } finally {
    isLoading.value = false
    streamAbortController.value = null
    scrollToBottom()
  }
}

// 中断 AI 回答
const stopGeneration = () => {
  if (streamAbortController.value) {
    streamAbortController.value.abort()
    streamAbortController.value = null
  }
  // 立即重置 loading 状态，让用户可以立即发新消息
  isLoading.value = false
}

const clearCurrentChat = async () => {
  await clearChatSession()
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// 格式化时间
const formatTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts * 1000) // 后端存的是 Unix timestamp
  if (isNaN(d.getTime())) d = new Date(ts)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

// Markdown 渲染
marked.setOptions({ breaks: true, gfm: true })
const renderMarkdown = (text) => { if (!text) return ''; return marked.parse(text) }

// 初始化（首次挂载）
onMounted(async () => {
  await Promise.all([fetchConfigs(), fetchChats()])
  if (chats.value.length > 0) {
    await switchChatSession(chats.value[0].id)
  } else {
    await createChatSession()
  }
  scrollToBottom()
})

// 从其他页面返回时激活
onActivated(async () => {
  await fetchChats()
  // 如果正在流式传输中，不要重新加载（会覆盖掉实时流式消息）
  if (isLoading.value) {
    scrollToBottom()
    return
  }
  // 如果当前有活跃会话，刷新其消息（从悬浮窗聊的可能有新内容）
  if (activeChatId.value) {
    await switchChatSession(activeChatId.value, true)
  } else if (chats.value.length > 0) {
    await switchChatSession(chats.value[0].id, true)
  }
  scrollToBottom()
})
</script>

<template>
  <div class="h-[calc(100vh-2rem)] flex">
    <!-- 对话历史侧栏 -->
    <div class="w-64 flex-shrink-0 border-r border-base-200/60 flex flex-col bg-base-100/50"
         :class="{ 'hidden': !showSidebar, 'lg:flex': showSidebar }">
      <div class="p-3 border-b border-base-200/60 flex items-center justify-between">
        <h2 class="font-semibold text-sm">{{ t('ai.chatHistory') }}</h2>
        <button @click="createChatSession()" class="btn btn-primary btn-xs gap-1" :title="t('ai.newChat')">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/>
          </svg>
          {{ t('ai.newChat') }}
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-2 space-y-1">
        <div
          v-for="item in chats"
          :key="item.id"
          @click="switchChatSession(item.id)"
          class="group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all text-sm truncate"
          :class="item.id === activeChatId
            ? 'bg-primary/10 text-primary font-medium'
            : 'hover:bg-base-200/80 text-base-content/70 hover:text-base-content'"
        >
          <svg class="w-4 h-4 flex-shrink-0 opacity-50 group-hover:opacity-70"
               :class="{ '!opacity-100': item.id === activeChatId }"
               fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8 818 8 0 01-6.95-4.06L3 13l3.05-.94A8 8 0 1112 21z"/>
          </svg>
          <div class="flex-1 min-w-0">
            <span class="truncate block">{{ item.title }}</span>
            <span v-if="item.preview" class="truncate block text-[10px] opacity-40 mt-0.5">{{ item.preview }}</span>
          </div>
          <span class="text-[10px] flex-shrink-0 opacity-40">{{ formatTime(item.updated_at) }}</span>
          <button @click.stop="deleteChat(item.id)" class="opacity-0 group-hover:opacity-50 hover:!opacity-100 text-error transition-all p-0.5 rounded">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div v-if="!chats.length" class="text-center text-xs text-base-content/30 py-8">
          {{ t('ai.noChats') }}
        </div>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 pb-0">
        <div class="flex items-center gap-2">
          <button @click="showSidebar = !showSidebar" class="btn btn-ghost btn-sm lg:hidden p-1">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16"/></svg>
          </button>
          <button @click="showSidebar = !showSidebar" class="btn btn-ghost btn-sm p-1 hidden lg:flex" :title="t('ai.toggleHistory')">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16"/></svg>
          </button>
          <div>
            <h1 class="text-xl font-bold">{{ t('ai.title') }}</h1>
            <p class="text-xs text-base-content/40 mt-0.5" v-if="!isConfigured">{{ t('ai.notConfigured') }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <div v-if="isConfigured" class="relative">
            <select :value="activeConfigId" @change="selectConfig(parseInt($event.target.value))"
              class="select select-sm select-bordered bg-base-200 pr-8 text-xs">
              <option v-for="cfg in aiConfigs" :key="cfg.id" :value="cfg.id">
                {{ cfg.name }} ({{ cfg.model }})
              </option>
            </select>
          </div>
          <button @click="createChatSession()" class="btn btn-ghost btn-sm text-base-content/50 hover:text-primary gap-1" :title="t('ai.newChat')">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/></svg>
            <span class="hidden sm:inline">{{ t('ai.newChat') }}</span>
          </button>
          <button @click="clearCurrentChat" class="btn btn-ghost btn-sm text-base-content/50 hover:text-error gap-1" v-if="currentMessages.length" :title="t('ai.clearChat')">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/></svg>
            <span class="hidden sm:inline">{{ t('ai.clearChat') }}</span>
          </button>
        </div>
      </div>

      <!-- Messages -->
      <div ref="chatContainer" @scroll="onChatScroll" class="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth relative">
        <div v-if="!currentMessages.length" class="flex flex-col items-center justify-center h-full text-center px-8">
          <div ref="evaContainerRef" class="eva-avatar mb-6 relative">
            <div class="eva-glow"></div>
            <div class="eva-ring eva-ring-1"></div>
            <div class="eva-ring eva-ring-2"></div>
            <div class="eva-ring eva-ring-3"></div>
            <div class="eva-body">
              <div class="eva-highlight"></div>
              <div class="eva-eyes">
                <div ref="eyeLeftRef" class="eva-eye" :style="{ transform: `translate(${eyeOffsetX}px, ${eyeOffsetY}px)` }">
                  <div class="eva-eye-inner"></div>
                </div>
                <div ref="eyeRightRef" class="eva-eye" :style="{ transform: `translate(${eyeOffsetX}px, ${eyeOffsetY}px)` }">
                  <div class="eva-eye-inner"></div>
                </div>
              </div>
            </div>
            <div class="eva-shadow"></div>
          </div>
          <h2 class="text-lg font-semibold mb-2">{{ t('ai.welcome') }}</h2>
          <p class="text-sm text-base-content/50 leading-relaxed max-w-md">{{ t('ai.welcomeHint') }}</p>
          <div class="mt-8 grid gap-2 w-full max-w-md">
            <button v-for="suggestion in ['ai.suggest1', 'ai.suggest2', 'ai.suggest3']" :key="suggestion"
              @click="inputText = t(suggestion); handleSend()"
              class="text-left p-3 rounded-xl bg-base-200/60 hover:bg-base-200 transition-all text-sm text-base-content/70 hover:text-base-content">
              {{ t(suggestion) }}
            </button>
          </div>
        </div>

        <template v-else>
          <div v-for="(msg, index) in currentMessages" :key="msg.id || index"
            class="flex gap-3 max-w-[85%] animate-fade-in"
            :class="msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''">
            <div class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-1"
              :class="msg.role === 'user' ? 'bg-primary/80 text-white' : 'eva-avatar-mini'">
              <span v-if="msg.role === 'user'" class="text-xs font-bold">你</span>
              <div v-else class="eva-mini-body">
                <div class="eva-mini-highlight"></div>
                <div class="eva-mini-eyes">
                  <div class="eva-mini-eye"></div>
                  <div class="eva-mini-eye"></div>
                </div>
              </div>
            </div>
            <div class="rounded-2xl px-4 py-2.5 text-sm leading-relaxed break-words"
              :class="msg.role === 'user' ? 'bg-primary text-white rounded-tr-sm whitespace-pre-wrap' : 'bg-base-200/80 rounded-tl-sm'">
              <div v-if="msg.loading && !msg.content && !msg.reasoning && (!msg.toolCalls || !msg.toolCalls.length)" class="flex items-center gap-1.5 py-1">
                <span class="w-2 h-2 rounded-full bg-base-content/40 animate-bounce" style="animation-delay:0ms"></span>
                <span class="w-2 h-2 rounded-full bg-base-content/40 animate-bounce" style="animation-delay:150ms"></span>
                <span class="w-2 h-2 rounded-full bg-base-content/40 animate-bounce" style="animation-delay:300ms"></span>
              </div>
              <!-- 工具调用记录（用户可见，分阶段展示） -->
              <div v-if="msg.toolCalls && msg.toolCalls.length" class="space-y-1.5 py-1">
                <div v-for="(tc, tcIdx) in msg.toolCalls" :key="tcIdx"
                  class="flex items-center gap-2 text-xs rounded-lg px-3 py-1.5 transition-all"
                  :class="tc.status === 'done'
                    ? 'bg-success/5 border border-success/10 text-success/80'
                    : 'bg-primary/5 border border-primary/10 text-primary/70'">
                  <!-- 运行中：转圈 -->
                  <span v-if="tc.status === 'running'" class="loading loading-spinner loading-xs"></span>
                  <!-- 已完成：勾选 -->
                  <svg v-else class="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
                  </svg>
                  <span>{{ tc.description }}</span>
                </div>
              </div>
              <div v-if="msg.reasoning" class="mb-2">
                <button @click="msg.reasoningExpanded = !msg.reasoningExpanded"
                  class="flex items-center gap-1.5 text-xs text-primary/70 hover:text-primary transition-colors py-0.5">
                  <svg class="w-3.5 h-3.5 transition-transform duration-200" :class="{ 'rotate-90': msg.reasoningExpanded }"
                    fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
                  <span class="font-medium">{{ t('ai.thinking') }}</span>
                  <span v-if="msg.loading && !msg.content" class="loading loading-spinner loading-xs text-primary/50"></span>
                </button>
                <div v-show="msg.reasoningExpanded"
                  class="mt-1.5 pl-3 border-l-2 border-primary/20 text-xs text-base-content/50 leading-relaxed whitespace-pre-wrap break-words">{{ msg.reasoning }}</div>
              </div>
              <template v-if="msg.content">
                <div v-if="msg.content.startsWith('[错误]')" class="text-error">{{ msg.content }}</div>
                <div v-else-if="msg.role === 'user'" class="whitespace-pre-wrap break-words">{{ msg.content }}</div>
                <div v-else class="markdown-body" v-html="renderMarkdown(msg.content) + (msg.loading ? '<span class=\'cursor-blink\'>▌</span>' : '')"></div>
              </template>
              <template v-else-if="!msg.loading && !msg.reasoning"></template>
            </div>
          </div>
        </template>
        <!-- 回到底部按钮 -->
        <Transition name="fade">
          <button v-if="showScrollDownBtn" @click="scrollToBottom"
            class="absolute bottom-4 right-6 btn btn-circle btn-sm bg-base-100 shadow-lg border border-base-300 hover:border-primary/50 z-10">
            <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3"/></svg>
          </button>
        </Transition>
      </div>

      <!-- Input Area -->
      <div class="p-4 pt-2 border-t border-base-200/50">
        <div class="flex items-end gap-2">
          <textarea v-model="inputText" @keydown="handleKeydown" rows="1"
            :placeholder="t('ai.inputPlaceholder')" :disabled="isLoading || !isConfigured"
            class="flex-1 resize-none rounded-2xl border-0 bg-base-200/60 focus:bg-base-200 focus:outline-none focus:ring-2 focus:ring-primary/30 px-4 py-3 text-sm placeholder:text-base-content/30 transition-all disabled:opacity-50"
            style="max-height:120px;min-height:48px;"
            @input="$event.target.style.height='auto'; $event.target.style.height=$event.target.scrollHeight+'px'" />
          <button v-if="isLoading" @click="stopGeneration"
            class="btn btn-error btn-circle btn-sm self-end flex-shrink-0" title="中断回答">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
          </button>
          <button v-else @click="handleSend" :disabled="!inputText.trim() || !isConfigured"
            class="btn btn-primary btn-circle btn-sm self-end flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"/></svg>
          </button>
        </div>
        <p v-if="!isConfigured" class="text-xs text-warning mt-2 text-center">{{ t('ai.configHint') }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes fade-in { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
.animate-fade-in { animation: fade-in 0.25s ease-out; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(6px); }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.cursor-blink { display:inline; animation:blink .8s step-end infinite; color:hsl(var(--p)/.6); font-weight:normal; }

/* ====== EVA Avatar - 欢迎区域大头像 ====== */
.eva-avatar {
  width: 160px;
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.eva-glow {
  position: absolute;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(56,189,248,0.15) 0%, transparent 70%);
  animation: eva-glow-pulse 3s ease-in-out infinite;
  filter: blur(20px);
}

@keyframes eva-glow-pulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.15); opacity: 1; }
}

.eva-ring {
  position: absolute;
  border-radius: 50%;
  border: 1.5px solid rgba(56,189,248,0.2);
  animation: eva-ring-expand 3s ease-out infinite;
}

.eva-ring-1 { width: 190px; height: 190px; animation-delay: 0s; }
.eva-ring-2 { width: 220px; height: 220px; animation-delay: 0.8s; }
.eva-ring-3 { width: 250px; height: 250px; animation-delay: 1.6s; }

@keyframes eva-ring-expand {
  0% { transform: scale(0.85); opacity: 0.8; }
  100% { transform: scale(1.15); opacity: 0; }
}

.eva-body {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #4a4a4a 0%, #1a1a1a 40%, #0a0a0a 70%, #000000 100%);
  box-shadow:
    0 20px 60px rgba(0,0,0,0.5),
    0 8px 25px rgba(0,0,0,0.3),
    inset 0 -15px 30px rgba(0,0,0,0.4),
    inset 0 10px 20px rgba(255,255,255,0.05),
    0 0 40px rgba(56,189,248,0.1);
  position: relative;
  z-index: 2;
  overflow: hidden;
}

.eva-highlight {
  position: absolute;
  top: 12%;
  left: 18%;
  width: 35%;
  height: 22%;
  background: radial-gradient(ellipse at center, rgba(255,255,255,0.25) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(3px);
  transform: rotate(-25deg);
}

.eva-highlight::after {
  content: '';
  position: absolute;
  top: 120%;
  left: 60%;
  width: 18%;
  height: 10%;
  background: radial-gradient(ellipse at center, rgba(255,255,255,0.1) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(2px);
}

.eva-eyes {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -45%);
  display: flex;
  gap: 22px;
  z-index: 3;
}

.eva-eye {
  width: 28px;
  height: 14px;
  position: relative;
  transition: transform 0.08s ease-out;
}

.eva-eye-inner {
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, #67e8f9 0%, #06b6d4 40%, #0891b2 100%);
  border-radius: 50%;
  box-shadow:
    0 0 15px rgba(56,189,248,0.8),
    0 0 30px rgba(56,189,248,0.4),
    inset 0 -2px 4px rgba(0,0,0,0.2),
    inset 0 2px 3px rgba(255,255,255,0.4);
  clip-path: ellipse(50% 48% at 50% 52%);
  animation: eva-eye-shimmer 3s ease-in-out infinite;
  position: relative;
  overflow: hidden;
}

.eva-eye-inner::before {
  content: '';
  position: absolute;
  top: 15%;
  left: 15%;
  width: 35%;
  height: 40%;
  background: rgba(255,255,255,0.5);
  border-radius: 50%;
  filter: blur(1.5px);
}

.eva-eye-inner::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(255,255,255,0.15) 45%,
    rgba(255,255,255,0.3) 50%,
    rgba(255,255,255,0.15) 55%,
    transparent 100%
  );
  animation: eva-eye-scan 4s ease-in-out infinite;
}

@keyframes eva-eye-shimmer {
  0%, 100% { opacity: 1; filter: brightness(1); }
  50% { opacity: 0.85; filter: brightness(1.15); }
}

@keyframes eva-eye-scan {
  0%, 100% { transform: translateX(-100%); }
  50% { transform: translateX(100%); }
}

.eva-shadow {
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  width: 90px;
  height: 16px;
  background: radial-gradient(ellipse at center, rgba(56,189,248,0.25) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(6px);
  z-index: 1;
}

/* ====== EVA Mini Avatar - 聊天消息小头像 ====== */
.eva-avatar-mini {
  background: linear-gradient(135deg, #1a1a1a 0%, #0a0a0a 100%) !important;
  box-shadow:
    0 2px 8px rgba(0,0,0,0.3),
    inset 0 1px 2px rgba(255,255,255,0.05) !important;
}

.eva-mini-body {
  width: 100%;
  height: 100%;
  border-radius: inherit;
  background: radial-gradient(circle at 35% 30%, #3a3a3a 0%, #151515 50%, #080808 100%);
  position: relative;
  overflow: hidden;
}

.eva-mini-highlight {
  position: absolute;
  top: 15%;
  left: 20%;
  width: 30%;
  height: 18%;
  background: radial-gradient(ellipse at center, rgba(255,255,255,0.2) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(1px);
}

.eva-mini-eyes {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -42%);
  display: flex;
  gap: 5px;
}

.eva-mini-eye {
  width: 9px;
  height: 5px;
  background: linear-gradient(180deg, #67e8f9 0%, #06b6d4 50%, #0891b2 100%);
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(56,189,248,0.7);
  clip-path: ellipse(50% 48% at 50% 52%);
  animation: eva-eye-shimmer 3s ease-in-out infinite;
  position: relative;
  overflow: hidden;
}

.eva-mini-eye::before {
  content: '';
  position: absolute;
  top: 10%;
  left: 15%;
  width: 30%;
  height: 35%;
  background: rgba(255,255,255,0.5);
  border-radius: 50%;
  filter: blur(0.5px);
}

.markdown-body { line-height:1.7; }
.markdown-body :deep(p) { margin:.4em 0; }
.markdown-body :deep(p:first-child) { margin-top:0; }
.markdown-body :deep(p:last-child) { margin-bottom:0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { margin:.4em 0; padding-left:1.5em; }
.markdown-body :deep(ul) { list-style-type:disc; }
.markdown-body :deep(ol) { list-style-type:decimal; }
.markdown-body :deep(li) { margin:.15em 0; }
.markdown-body :deep(li>ul), .markdown-body :deep(li>ol) { margin:.1em 0; }
.markdown-body :deep(strong) { font-weight:700; }
.markdown-body :deep(code) { background:hsl(var(--b3)/.8); padding:.15em .35em; border-radius:4px; font-size:.85em; font-family:'Menlo','Monaco','Courier New',monospace; }
.markdown-body :deep(pre) { background:hsl(var(--b3)); border-radius:8px; padding:.8em 1em; overflow-x:auto; margin:.6em 0; }
.markdown-body :deep(pre code) { background:none; padding:0; font-size:.82em; line-height:1.6; }
.markdown-body :deep(blockquote) { border-left:3px solid hsl(var(--p)/.3); padding-left:.8em; margin:.5em 0; color:hsl(var(--bc)/.6); }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { font-weight:700; margin:.6em 0 .3em; }
.markdown-body :deep(h1){ font-size:1.2em; }
.markdown-body :deep(h2){ font-size:1.1em; }
.markdown-body :deep(h3){ font-size:1em; }
.markdown-body :deep(table) { border-collapse:collapse; margin:.5em 0; font-size:.9em; width:100%; }
.markdown-body :deep(th), .markdown-body :deep(td) { border:1px solid hsl(var(--bc)/.15); padding:.35em .6em; text-align:left; }
.markdown-body :deep(th) { background:hsl(var(--b3)/.5); font-weight:600; }
.markdown-body :deep(hr) { border:none; border-top:1px solid hsl(var(--bc)/.15); margin:.6em 0; }
</style>
