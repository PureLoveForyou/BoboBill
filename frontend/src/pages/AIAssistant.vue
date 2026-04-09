<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAiApi } from '../composables/useAiApi'
import { marked } from 'marked'

const { t } = useI18n()
const { chatStream, isConfigured, reloadConfig } = useAiApi()

// ====== 对话历史管理 ======
const CHATS_KEY = 'bobobill_ai_chats'
const ACTIVE_CHAT_KEY = 'bobobill_ai_active_chat'

function loadChats() {
  try {
    return JSON.parse(localStorage.getItem(CHATS_KEY) || '[]')
  } catch {
    return []
  }
}

function saveChats(chats) {
  localStorage.setItem(CHATS_KEY, JSON.stringify(chats))
}

const chats = ref(loadChats())
const activeChatId = ref(localStorage.getItem(ACTIVE_CHAT_KEY) || '')

// 当前消息（从活跃对话中读取）
const messages = computed(() => {
  const chatItem = chats.value.find(c => c.id === activeChatId.value)
  return chatItem ? chatItem.messages : []
})

// 自动生成对话标题（取第一条用户消息的前20字）
function autoTitle(msgs) {
  const firstUserMsg = msgs.find(m => m.role === 'user')
  if (!firstUserMsg) return t('ai.newChat')
  return firstUserMsg.content.slice(0, 20).replace(/\n/g, ' ') || t('ai.newChat')
}

// 创建新对话
const createNewChat = () => {
  const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 7)
  chats.value.unshift({ id, title: t('ai.newChat'), messages: [], createdAt: Date.now(), updatedAt: Date.now() })
  activeChatId.value = id
  persistState()
}

// 切换对话
const switchChat = (chatId) => {
  activeChatId.value = chatId
  persistState()
}

// 删除对话
const deleteChat = (chatId, e) => {
  e.stopPropagation()
  const idx = chats.value.findIndex(c => c.id === chatId)
  if (idx !== -1) {
    chats.value.splice(idx, 1)
    if (activeChatId.value === chatId) {
      if (chats.value.length > 0) {
        activeChatId.value = chats.value[0].id
      } else {
        createNewChat()
      }
    }
    persistState()
  }
}

// 持久化到 localStorage
const persistState = () => {
  // 只保留最近50条对话
  if (chats.value.length > 50) {
    chats.value = chats.value.slice(0, 50)
  }
  saveChats(chats.value)
  localStorage.setItem(ACTIVE_CHAT_KEY, activeChatId.value)
}

// 保存当前对话消息到历史
const persistMessages = () => {
  const idx = chats.value.findIndex(c => c.id === activeChatId.value)
  if (idx !== -1) {
    chats.value[idx].messages = [...messages.value]
    chats.value[idx].updatedAt = Date.now()
    if (messages.value.some(m => m.role === 'user')) {
      chats.value[idx].title = autoTitle(messages.value)
    }
    persistState()
  }
}

// 初始化：如果没有对话就创建一个
if (!chats.value.length || !chats.value.find(c => c.id === activeChatId.value)) {
  if (chats.value.length > 0) {
    activeChatId.value = chats.value[0].id
  } else {
    createNewChat()
  }
}

reloadConfig()

// ====== 聊天功能 ======
const inputText = ref('')
const isLoading = ref(false)
const chatContainer = ref(null)
const showSidebar = ref(false)

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

watch(activeChatId, () => {
  scrollToBottom()
})

const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || isLoading.value || !isConfigured.value) return

  // 确保有活跃对话
  let chatIdx = chats.value.findIndex(c => c.id === activeChatId.value)
  if (chatIdx === -1) {
    createNewChat()
    chatIdx = 0
  }

  // 添加用户消息到当前对话
  chats.value[chatIdx].messages.push({ role: 'user', content: text })
  inputText.value = ''
  isLoading.value = true
  scrollToBottom()

  // AI 占位消息（包含 reasoning 和 content）
  chats.value[chatIdx].messages.push({ role: 'assistant', content: '', reasoning: '', loading: true, reasoningExpanded: true })
  persistState()
  scrollToBottom()

  // 构建发送给后端的历史（不含占位和当前消息，后端会单独 append 当前消息）
  const historyToSend = messages.value.filter(m => !m.loading && m.role !== undefined).slice(0, -1)

  let currentContent = ''
  let currentReasoning = ''

  const result = await chatStream(text, historyToSend, (event) => {
    // 找到当前活跃对话的占位消息
    const idx = chats.value.findIndex(c => c.id === activeChatId.value)
    if (idx === -1) return
    const msgs = chats.value[idx].messages
    const lastMsg = msgs[msgs.length - 1]
    if (!lastMsg || lastMsg.role !== 'assistant') return

    if (event.type === 'reasoning') {
      currentReasoning += event.content
      lastMsg.reasoning = currentReasoning
      scrollToBottom()
    } else if (event.type === 'content') {
      currentContent += event.content
      lastMsg.content = currentContent
      lastMsg.loading = false
      scrollToBottom()
    } else if (event.type === 'done') {
      lastMsg.loading = false
      // 如果有思考内容，默认收起
      if (currentReasoning) {
        lastMsg.reasoningExpanded = false
      }
    } else if (event.type === 'error') {
      lastMsg.content = `[错误] ${event.content}`
      lastMsg.loading = false
    }
  })

  // 流结束后最终更新
  const currentIdx = chats.value.findIndex(c => c.id === activeChatId.value)
  if (currentIdx !== -1) {
    const lastMsg = chats.value[currentIdx].messages[chats.value[currentIdx].messages.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.loading = false
      if (!lastMsg.content && !result.success) {
        lastMsg.content = `[错误] ${result.message}`
      }
      // 如果没有收到任何内容但也没错误，用结果
      if (!currentContent && result.success) {
        lastMsg.content = ''
      }
    }
    chats.value[currentIdx].title = autoTitle(chats.value[currentIdx].messages)
    persistState()
  }

  isLoading.value = false
  scrollToBottom()
  // 移动到列表顶部
  if (currentIdx !== -1 && currentIdx !== 0) {
    const [item] = chats.value.splice(currentIdx, 1)
    chats.value.unshift(item)
  }
  persistState()
}

const clearCurrentChat = () => {
  const idx = chats.value.findIndex(c => c.id === activeChatId.value)
  if (idx !== -1) {
    chats.value[idx].messages = []
    chats.value[idx].title = t('ai.newChat')
    chats.value[idx].updatedAt = Date.now()
    persistState()
  }
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// 格式化时间
const formatTime = (ts) => {
  const d = new Date(ts)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

// Markdown 渲染
marked.setOptions({
  breaks: true,
  gfm: true,
})

const renderMarkdown = (text) => {
  if (!text) return ''
  return marked.parse(text)
}
</script>

<template>
  <div class="h-[calc(100vh-2rem)] flex">
    <!-- 对话历史侧栏 -->
    <div class="w-64 flex-shrink-0 border-r border-base-200/60 flex flex-col bg-base-100/50"
         :class="{ 'hidden': !showSidebar, 'lg:flex': showSidebar }">

      <!-- 侧栏头部 -->
      <div class="p-3 border-b border-base-200/60 flex items-center justify-between">
        <h2 class="font-semibold text-sm">{{ t('ai.chatHistory') }}</h2>
        <button @click="createNewChat" class="btn btn-primary btn-xs gap-1" :title="t('ai.newChat')">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/>
          </svg>
          {{ t('ai.newChat') }}
        </button>
      </div>

      <!-- 对话列表 -->
      <div class="flex-1 overflow-y-auto p-2 space-y-1">
        <div
          v-for="item in chats"
          :key="item.id"
          @click="switchChat(item.id)"
          class="group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all text-sm truncate"
          :class="item.id === activeChatId
            ? 'bg-primary/10 text-primary font-medium'
            : 'hover:bg-base-200/80 text-base-content/70 hover:text-base-content'"
        >
          <!-- 图标 -->
          <svg class="w-4 h-4 flex-shrink-0 opacity-50 group-hover:opacity-70"
               :class="{ '!opacity-100': item.id === activeChatId }"
               fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8 818 8 0 01-6.95-4.06L3 13l3.05-.94A8 8 0 1112 21z"/>
          </svg>
          <!-- 标题 -->
          <span class="truncate flex-1 min-w-0">{{ item.title }}</span>
          <!-- 时间 -->
          <span class="text-[10px] flex-shrink-0 opacity-40">{{ formatTime(item.updatedAt) }}</span>
          <!-- 删除按钮 -->
          <button @click="deleteChat(item.id, $event)" class="opacity-0 group-hover:opacity-50 hover:!opacity-100 text-error transition-all p-0.5 rounded">
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
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>
          <button @click="showSidebar = !showSidebar" class="btn btn-ghost btn-sm p-1 hidden lg:flex" :title="t('ai.toggleHistory')">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>
          <div>
            <h1 class="text-xl font-bold">{{ t('ai.title') }}</h1>
            <p class="text-xs text-base-content/40 mt-0.5" v-if="!isConfigured">
              {{ t('ai.notConfigured') }}
            </p>
          </div>
        </div>
        <div class="flex items-center gap-1">
          <button @click="createNewChat" class="btn btn-ghost btn-sm text-base-content/50 hover:text-primary gap-1" :title="t('ai.newChat')">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/>
            </svg>
            <span class="hidden sm:inline">{{ t('ai.newChat') }}</span>
          </button>
          <button @click="clearCurrentChat" class="btn btn-ghost btn-sm text-base-content/50 hover:text-error gap-1" v-if="messages.length" :title="t('ai.clearChat')">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/>
            </svg>
            <span class="hidden sm:inline">{{ t('ai.clearChat') }}</span>
          </button>
        </div>
      </div>

      <!-- Messages -->
      <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth">
        <!-- Welcome -->
        <div v-if="!messages.length" class="flex flex-col items-center justify-center h-full text-center px-8">
          <div class="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary via-primary to-primary/60 flex items-center justify-center shadow-xl shadow-primary/30 mb-6 relative overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent"></div>
            <svg class="w-10 h-10 text-base-100 relative z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z"/>
            </svg>
          </div>
          <h2 class="text-lg font-semibold mb-2">{{ t('ai.welcome') }}</h2>
          <p class="text-sm text-base-content/50 leading-relaxed max-w-md">{{ t('ai.welcomeHint') }}</p>

          <div class="mt-8 grid gap-2 w-full max-w-md">
            <button
              v-for="suggestion in ['ai.suggest1', 'ai.suggest2', 'ai.suggest3']"
              :key="suggestion"
              @click="inputText = t(suggestion); handleSend()"
              class="text-left p-3 rounded-xl bg-base-200/60 hover:bg-base-200 transition-all text-sm text-base-content/70 hover:text-base-content"
            >
              {{ t(suggestion) }}
            </button>
          </div>
        </div>

        <!-- Chat Messages -->
        <template v-else>
          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="flex gap-3 max-w-[85%] animate-fade-in"
            :class="msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''"
          >
            <!-- Avatar -->
            <div
              class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-1"
              :class="msg.role === 'user'
                ? 'bg-primary/80 text-white'
                : 'bg-gradient-to-br from-primary via-primary to-primary/60 text-white shadow-lg shadow-primary/20'"
            >
              <span v-if="msg.role === 'user'" class="text-xs font-bold">你</span>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z"/>
              </svg>
            </div>

            <!-- Message Bubble -->
            <div
              class="rounded-2xl px-4 py-2.5 text-sm leading-relaxed break-words"
              :class="msg.role === 'user'
                ? 'bg-primary text-white rounded-tr-sm whitespace-pre-wrap'
                : 'bg-base-200/80 rounded-tl-sm'"
            >
              <div v-if="msg.loading && !msg.content && !msg.reasoning" class="flex items-center gap-1.5 py-1">
                <span class="w-2 h-2 rounded-full bg-base-content/40 animate-bounce" style="animation-delay: 0ms"></span>
                <span class="w-2 h-2 rounded-full bg-base-content/40 animate-bounce" style="animation-delay: 150ms"></span>
                <span class="w-2 h-2 rounded-full bg-base-content/40 animate-bounce" style="animation-delay: 300ms"></span>
              </div>
              <!-- 思考过程（可折叠） -->
              <div v-if="msg.reasoning" class="mb-2">
                <button
                  @click="msg.reasoningExpanded = !msg.reasoningExpanded"
                  class="flex items-center gap-1.5 text-xs text-primary/70 hover:text-primary transition-colors py-0.5"
                >
                  <svg
                    class="w-3.5 h-3.5 transition-transform duration-200"
                    :class="{ 'rotate-90': msg.reasoningExpanded }"
                    fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
                  </svg>
                  <span class="font-medium">{{ t('ai.thinking') }}</span>
                  <span v-if="msg.loading && !msg.content" class="loading loading-spinner loading-xs text-primary/50"></span>
                </button>
                <div
                  v-show="msg.reasoningExpanded"
                  class="mt-1.5 pl-3 border-l-2 border-primary/20 text-xs text-base-content/50 leading-relaxed whitespace-pre-wrap break-words"
                >{{ msg.reasoning }}</div>
              </div>
              <!-- 正常内容（Markdown 渲染） -->
              <template v-if="msg.content">
                <div v-if="msg.content.startsWith('[错误]')" class="text-error">{{ msg.content }}</div>
                <div v-else class="markdown-body" v-html="renderMarkdown(msg.content) + (msg.loading ? '<span class=\'cursor-blink\'>▌</span>' : '')"></div>
              </template>
              <template v-else-if="!msg.loading && !msg.reasoning"></template>
            </div>
          </div>
        </template>
      </div>

      <!-- Input Area -->
      <div class="p-4 pt-2 border-t border-base-200/50">
        <div class="flex items-end gap-2">
          <textarea
            v-model="inputText"
            @keydown="handleKeydown"
            rows="1"
            :placeholder="t('ai.inputPlaceholder')"
            :disabled="isLoading || !isConfigured"
            class="flex-1 resize-none rounded-2xl border-0 bg-base-200/60 focus:bg-base-200 focus:outline-none focus:ring-2 focus:ring-primary/30 px-4 py-3 text-sm placeholder:text-base-content/30 transition-all disabled:opacity-50"
            style="max-height: 120px; min-height: 48px;"
            @input="$event.target.style.height='auto'; $event.target.style.height=$event.target.scrollHeight+'px'"
          ></textarea>
          <button
            @click="handleSend"
            :disabled="isLoading || !inputText.trim() || !isConfigured"
            class="btn btn-primary btn-circle btn-sm self-end flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="!isLoading" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"/>
            </svg>
            <span v-else class="loading loading-spinner loading-xs"></span>
          </button>
        </div>
        <p v-if="!isConfigured" class="text-xs text-warning mt-2 text-center">
          {{ t('ai.configHint') }}
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in {
  animation: fade-in 0.25s ease-out;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
.cursor-blink {
  display: inline;
  animation: blink 0.8s step-end infinite;
  color: hsl(var(--p) / 0.6);
  font-weight: normal;
}

/* Markdown 样式 */
.markdown-body {
  line-height: 1.7;
}
.markdown-body :deep(p) {
  margin: 0.4em 0;
}
.markdown-body :deep(p:first-child) {
  margin-top: 0;
}
.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.4em 0;
  padding-left: 1.5em;
}
.markdown-body :deep(ul) {
  list-style-type: disc;
}
.markdown-body :deep(ol) {
  list-style-type: decimal;
}
.markdown-body :deep(li) {
  margin: 0.15em 0;
}
.markdown-body :deep(li > ul),
.markdown-body :deep(li > ol) {
  margin: 0.1em 0;
}
.markdown-body :deep(strong) {
  font-weight: 700;
}
.markdown-body :deep(code) {
  background: hsl(var(--b3) / 0.8);
  padding: 0.15em 0.35em;
  border-radius: 4px;
  font-size: 0.85em;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
}
.markdown-body :deep(pre) {
  background: hsl(var(--b3));
  border-radius: 8px;
  padding: 0.8em 1em;
  overflow-x: auto;
  margin: 0.6em 0;
}
.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.82em;
  line-height: 1.6;
}
.markdown-body :deep(blockquote) {
  border-left: 3px solid hsl(var(--p) / 0.3);
  padding-left: 0.8em;
  margin: 0.5em 0;
  color: hsl(var(--bc) / 0.6);
}
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  font-weight: 700;
  margin: 0.6em 0 0.3em;
}
.markdown-body :deep(h1) { font-size: 1.2em; }
.markdown-body :deep(h2) { font-size: 1.1em; }
.markdown-body :deep(h3) { font-size: 1em; }
.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 0.5em 0;
  font-size: 0.9em;
  width: 100%;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid hsl(var(--bc) / 0.15);
  padding: 0.35em 0.6em;
  text-align: left;
}
.markdown-body :deep(th) {
  background: hsl(var(--b3) / 0.5);
  font-weight: 600;
}
.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid hsl(var(--bc) / 0.15);
  margin: 0.6em 0;
}
</style>
