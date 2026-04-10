<script setup>
defineOptions({ name: 'EchoAssistant' })
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAiApi } from '../composables/useAiApi'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const {
  chatStream, isConfigured,
  activeChatId, currentMessages, fetchChats, createChatSession, fetchConfigs,
  switchChatSession,
  addMessage, updateMessage, streamAbortController,
} = useAiApi()

// AI 助手页面不显示悬浮球
const isHidden = computed(() => ['/ai', '/settings'].includes(route.path))

// ====== 状态 ======
const isOpen = ref(false)
const isDragging = ref(false)
const position = ref({ x: window.innerWidth - 80, y: window.innerHeight - 120 })
const dragStart = ref({ x: 0, y: 0 })
const echoMood = ref('idle') // idle | happy | thinking | surprised | sleepy | love | mischievous | excited
const inputText = ref('')
const isLoading = ref(false)
const chatContainer = ref(null)
const mousePos = ref({ x: 0, y: 0 })
const showParticles = ref(false)
const windowWidth = ref(window.innerWidth)
const windowHeight = ref(window.innerHeight)
const panelMaxH = 480

// 面板位置：水平居中跟随球+clamp，垂直默认上方碰到边界才翻下方
const panelPosition = computed(() => {
  const ballX = position.value.x
  const ballY = position.value.y
  const gap = 12
  const ballH = 54
  const ballW = 54
  const panelW = 360
  const panelDefaultH = 480
  const margin = 10
  const vh = window.innerHeight
  const vw = windowWidth.value
  const style = {}

  // === 垂直：默认在球上方，上方空间太小才翻到下方 ===
  const spaceAbove = ballY - gap
  const spaceBelow = vh - ballY - ballH - gap
  const showBelow = spaceAbove < panelDefaultH && spaceBelow > spaceAbove

  if (showBelow) {
    style.top = (ballY + ballH + gap) + 'px'
    style.maxHeight = Math.min(panelDefaultH, spaceBelow - margin) + 'px'
  } else {
    style.bottom = (vh - ballY + gap) + 'px'
    style.maxHeight = Math.min(panelDefaultH, spaceAbove - margin) + 'px'
  }

  // === 水平：面板居中对齐球，碰到边界就 clamp，永远不翻转 ===
  let left = ballX + ballW / 2 - panelW / 2
  if (left < margin) left = margin
  if (left + panelW > vw - margin) left = vw - panelW - margin
  style.left = left + 'px'

  return style
})

// ====== 生命周期 ======
onMounted(() => {
  startMoodCycle()
  document.addEventListener('mousemove', onMouseTrack)
  document.addEventListener('click', onDocClick)
  window.addEventListener('resize', () => { windowWidth.value = window.innerWidth; windowHeight.value = window.innerHeight })
  // 自动加载 AI 配置和聊天记录（与 AI 助手 TAB 共享数据）
  fetchConfigs().then(() => { if (isConfigured.value) fetchChats().catch(() => {}) }).catch(() => {})
})
onUnmounted(() => {
  stopMoodCycle()
  document.removeEventListener('mousemove', onMouseTrack)
  document.removeEventListener('click', onDocClick)
})

function onMouseTrack(e) {
  if (!isDragging.value && !isOpen.value) {
    mousePos.value = { x: e.clientX, y: e.clientY }
  }
}

// ====== 表情循环 ======
let moodTimer = null
const moods = ['idle', 'happy', 'mischievous', 'sleepy', 'love', 'surprised']
function startMoodCycle() {
  stopMoodCycle()
  moodTimer = setInterval(() => {
    if (!isLoading.value && !isOpen.value) {
      switchMood(moods[Math.floor(Math.random() * moods.length)])
    }
  }, 5000 + Math.random() * 8000)
}
function stopMoodCycle() {
  if (moodTimer) { clearInterval(moodTimer); moodTimer = null }
}
function switchMood(m) { if (m !== echoMood.value) echoMood.value = m }

// 监听面板开关和加载状态
watch(isOpen, (val) => {
  if (val) { stopMoodCycle(); switchMood('happy') }
  else nextTick(() => startMoodCycle())
})
watch(isLoading, (v) => {
  switchMood(v ? 'thinking' : 'happy')
  if (!v) { showParticles.value = true; setTimeout(() => { showParticles.value = false }, 1200) }
})

// ====== 眼球跟踪 ======
const ballRef = ref(null)
const eyeOffset = computed(() => {
  if (!ballRef.value || echoMood.value === 'thinking' || echoMood.value === 'sleepy') return { x: 0, y: 0 }
  const rect = ballRef.value.getBoundingClientRect()
  const dx = mousePos.value.x - (rect.left + rect.width / 2)
  const dy = mousePos.value.y - (rect.top + rect.height / 2)
  const dist = Math.sqrt(dx * dx + dy * dy)
  const maxDist = 200
  const clamp = Math.min(dist / maxDist, 1) * 4
  return dist > 1 ? { x: (dx / dist) * clamp, y: (dy / dist) * clamp } : { x: 0, y: 0 }
})

// ====== 快捷提问 ======
const quickQuestions = computed(() => {
  const path = route.path
  if (path === '/dashboard') return [
    { text: t('echo.q1_dashboard') || '这个月花了多少？', icon: '\u{1F4B0}' },
    { text: t('echo.q2_dashboard') || '帮我分析一下消费趋势', icon: '\u{1F4CA}' },
    { text: t('echo.q3_dashboard') || '最近有什么大额支出？', icon: '\u{1F50D}' },
  ]
  if (path === '/bills') return [
    { text: t('echo.q1_bills') || '帮我整理一下最近的账单', icon: '\u{1F4CB}' },
    { text: t('echo.q2_bills') || '餐饮花了多少钱？', icon: '\u{1F35C}' },
    { text: t('echo.q3_bills') || '有没有重复的账单？', icon: '\u{1F504}' },
  ]
  if (path === '/settings') return [
    { text: t('echo.q1_settings') || '怎么配置 AI 助手？', icon: '\u2699\uFE0F' },
    { text: t('echo.q2_settings') || '我的预算合理吗？', icon: '\u{1F4DD}' },
    { text: t('echo.q3_settings') || '如何导出数据？', icon: '\u{1F4E4}' },
  ]
  return [
    { text: t('echo.q_default1') || '几点了？', icon: '\u{1F550}' },
    { text: t('echo.q_default2') || '今天心情怎么样？', icon: '\u{1F60A}' },
    { text: t('echo.q_default3') || '给我讲个笑话吧', icon: '\u2728' },
  ]
})

// ====== 拖拽 + 点击（最简实现）=====
const dragThreshold = 5
let _dragDist = 0 // 记录拖拽距离

function onPointerDown(e) {
  if (e.target.closest('.echo-panel')) return
  _dragDist = 0
  isDragging.value = true
  const pos = e.touches ? e.touches[0] : e
  dragStart.value = { x: pos.clientX - position.value.x, y: pos.clientY - position.value.y }
  document.addEventListener('mousemove', onPointerMove)
  document.addEventListener('mouseup', onPointerUp)
  document.addEventListener('touchmove', onPointerMove, { passive: false })
  document.addEventListener('touchend', onPointerUp)
}
function onPointerMove(e) {
  if (!isDragging.value) return
  if (e.cancelable) e.preventDefault()
  const pos = e.touches ? e.touches[0] : e
  const nx = pos.clientX - dragStart.value.x
  const ny = pos.clientY - dragStart.value.y
  _dragDist += Math.abs(nx - position.value.x + dragStart.value.x) + Math.abs(ny - position.value.y + dragStart.value.y)
  position.value = {
    x: Math.max(20, Math.min(nx, window.innerWidth - 56)),
    y: Math.max(20, Math.min(ny, window.innerHeight - 56)),
  }
}
function onPointerUp() {
  isDragging.value = false
  document.removeEventListener('mousemove', onPointerMove)
  document.removeEventListener('mouseup', onPointerUp)
  document.removeEventListener('touchmove', onPointerMove)
  document.removeEventListener('touchend', onPointerUp)
}

// 点击球：打开/关闭面板（纯 click，不依赖 mousedown 状态）
let _lastClickTime = 0
function onBallClick() {
  // 防抖 + 防止拖拽后误触
  if (_dragDist > dragThreshold * 2 || Date.now() - _lastClickTime < 300) return
  _lastClickTime = Date.now()
  _dragDist = 0
  console.log('[Echo] ball clicked, toggle:', !isOpen.value) // DEBUG
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    ensureSession(); scrollToBottom()
    switchMood('excited')
    setTimeout(() => { if (isOpen.value) switchMood('happy') }, 800)
  }
}

// 点击面板内关闭按钮
function closePanel() { isOpen.value = false }
let _panelInteractedAt = 0 // 面板内交互时间戳
function markPanelInteract() { _panelInteractedAt = Date.now() }
// 点击面板外部关闭
function onDocClick(e) {
  // 300ms 内有面板交互则不关闭（防止快捷按钮等操作误关）
  if (Date.now() - _panelInteractedAt < 300) return
  if (isOpen.value && !e.target.closest('.echo-panel') && !e.target.closest('.echo-ball')) {
    isOpen.value = false
  }
}

// 点击打开/关闭（保留作为备用，但主要靠 pointer up 判断）
let clickTime = 0
function toggleOpen() {
  if (Date.now() - clickTime < 200) return
  clickTime = Date.now()
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    ensureSession(); scrollToBottom()
    switchMood('excited')
    setTimeout(() => { if (isOpen.value) switchMood('happy') }, 800)
  }
}

// ====== 聊天功能 ======
async function ensureSession() {
  if (!activeChatId.value) await createChatSession(t('echo.newChat') || '\u548C\u5FF5\u6EAA\u804A\u5929')
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) chatContainer.value.scrollTo({ top: chatContainer.value.scrollHeight, behavior: 'smooth' })
  })
}

async function handleSend(text) {
  const msgText = (text || inputText.value).trim().replace(/\n+$/, '')
  if (!msgText || isLoading.value || !isConfigured.value) return
  await ensureSession()
  const sid = activeChatId.value; if (!sid) return

  currentMessages.value.push({ role: 'user', content: msgText })
  addMessage(sid, 'user', msgText).catch(() => {})
  inputText.value = ''
  isLoading.value = true

  const pIdx = currentMessages.value.length
  currentMessages.value.push({ role: 'assistant', content: '', reasoning: '', loading: true, reasoningExpanded: true })

  const history = currentMessages.value.filter(m => !m.loading && m.role !== undefined).slice(0, -1)
  let curContent = ''; let curReasoning = ''

  const controller = new AbortController()
  streamAbortController.value = controller

  try {
    const result = await chatStream(msgText, history, (event) => {
      const msg = currentMessages.value[pIdx]; if (!msg || msg.role !== 'assistant') return
      if (event.type === 'reasoning') {
        curReasoning += event.content; msg.reasoning = curReasoning; scrollToBottom()
      } else if (event.type === 'tool_start') {
        if (!msg.toolCalls) msg.toolCalls = []
        msg.toolCalls.push({ name: event.content.name, description: event.content.description, status: 'running' }); scrollToBottom()
      } else if (event.type === 'tool_end') {
        if (msg.toolCalls) { const tc = msg.toolCalls.find(t => t.name === event.content.name); if (tc) tc.status = 'done' }; scrollToBottom()
      } else if (event.type === 'content') {
        curContent += event.content; msg.content = curContent; msg.loading = false; scrollToBottom()
      } else if (event.type === 'done') {
        msg.loading = false; if (curReasoning) msg.reasoningExpanded = false
      } else if (event.type === 'error') {
        msg.content = `[错误] ${event.content}`; msg.loading = false
      }
    }, controller.signal)

    const finalMsg = currentMessages.value[pIdx]
    if (finalMsg && finalMsg.role === 'assistant') {
      finalMsg.loading = false
      if (!finalMsg.content && !result.success && !result.aborted) finalMsg.content = `[错误] ${result.message}`
      if (result.aborted && curContent) finalMsg.content = curContent + '\n\n*[回答已中断]*'
    }
    const fc = finalMsg?.content, fr = finalMsg?.reasoning, ft = finalMsg?.toolCalls
    if (fc || fr || ft) await addMessage(sid, 'assistant', fc, fr, ft).catch(() => {})

    switchMood(['happy','love','mischievous','excited'][Math.floor(Math.random()*4)])
    showParticles.value = true; setTimeout(() => { showParticles.value = false }, 1500)
  } finally {
    isLoading.value = false; streamAbortController.value = null; scrollToBottom()
  }
}

function handleQuickQuestion(q) { markPanelInteract(); handleSend(q.text) }
function handleKeydown(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }
function stopGeneration() { if (streamAbortController.value) { streamAbortController.value.abort(); streamAbortController.value = null } isLoading.value = false }
async function goToFullAI() {
  isOpen.value = false
  // 先刷新会话列表，确保 AI 助手 TAB 能看到最新会话
  await fetchChats().catch(() => {})
  router.push('/ai')
}

// Markdown
import { marked } from 'marked'
marked.setOptions({ breaks: true, gfm: true })
const renderMd = (text) => { if (!text) return ''; return marked.parse(text) }
</script>

<template>
  <Teleport to="body">
  <!-- 念溪 Echo -->
  <div v-if="!isHidden" class="echo-wrapper">

    <!-- 浮动球 -->
    <div
      ref="ballRef"
      class="echo-ball"
      :class="[`echo-mood-${echoMood}`, { 'echo-dragging': isDragging }]"
      :style="{ left: position.x + 'px', top: position.y + 'px' }"
      @mousedown="onPointerDown"
      @touchstart="onPointerDown"
      @click="onBallClick"
    >
      <!-- 外层光晕 -->
      <div class="echo-orbit"></div>
      <div class="echo-glow"></div>

      <!-- 主圆形 SVG 角色 - EVA Style -->
      <svg viewBox="0 0 100 100" class="echo-face">
        <defs>
          <radialGradient id="evaBodyG" cx="38%" cy="32%" r="65%">
            <stop offset="0%" stop-color="#4a4a4a"/>
            <stop offset="35%" stop-color="#1a1a1a"/>
            <stop offset="70%" stop-color="#0a0a0a"/>
            <stop offset="100%" stop-color="#000000"/>
          </radialGradient>
          <radialGradient id="evaEyeG" cx="50%" cy="45%" r="55%">
            <stop offset="0%" stop-color="#67e8f9"/>
            <stop offset="40%" stop-color="#06b6d4"/>
            <stop offset="100%" stop-color="#0891b2"/>
          </radialGradient>
          <linearGradient id="evaHighlightG" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#fff" stop-opacity="0.28"/>
            <stop offset="50%" stop-color="#fff" stop-opacity="0.06"/>
            <stop offset="100%" stop-color="#fff" stop-opacity="0"/>
          </linearGradient>
          <filter id="evaEyeGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2.5" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
          <filter id="evaBodyShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#000" flood-opacity="0.5"/>
            <feDropShadow dx="0" dy="1" stdDeviation="2" flood-color="#000" flood-opacity="0.3"/>
          </filter>
        </defs>

        <!-- EVA 黑色球体 -->
        <circle cx="50" cy="50" r="46" fill="url(#evaBodyG)" filter="url(#evaBodyShadow)"/>

        <!-- 高光 -->
        <ellipse cx="36" cy="32" rx="15" ry="10" fill="url(#evaHighlightG)" transform="rotate(-22 36 32)"/>

        <!-- idle: 微眯笑眼 -_- -->
        <g v-if="echoMood === 'idle'" class="echo-eyes-g">
          <ellipse :cx="34 + eyeOffset.x * 0.8" :cy="44 + eyeOffset.y * 0.8" rx="8" ry="4.5" fill="url(#evaEyeG)" filter="url(#evaEyeGlow)" class="eva-eye-ellipse"/>
          <ellipse :cx="66 + eyeOffset.x * 0.8" :cy="44 + eyeOffset.y * 0.8" rx="8" ry="4.5" fill="url(#evaEyeG)" filter="url(#evaEyeGlow)" class="eva-eye-ellipse"/>
          <ellipse cx="34" cy="44" rx="3" ry="1.5" fill="rgba(255,255,255,0.45)" transform="translate(-1,-0.5)"/>
          <ellipse cx="66" cy="44" rx="3" ry="1.5" fill="rgba(255,255,255,0.45)" transform="translate(-1,-0.5)"/>
        </g>

        <!-- happy: 弯弯笑眼 ^^ -->
        <g v-if="echoMood === 'happy'" class="echo-eyes-g">
          <path d="M27 43 Q34 36 41 43" stroke="url(#evaEyeG)" stroke-width="4" fill="none" stroke-linecap="round" filter="url(#evaEyeGlow)" class="eva-eye-happy"/>
          <path d="M59 43 Q66 36 73 43" stroke="url(#evaEyeG)" stroke-width="4" fill="none" stroke-linecap="round" filter="url(#evaEyeGlow)" class="eva-eye-happy"/>
          <path d="M43 62 Q50 68 57 62" stroke="#06b6d4" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.7"/>
        </g>

        <!-- excited: 兴奋大眼 OvO -->
        <g v-if="echoMood === 'excited'" class="echo-eyes-g">
          <ellipse :cx="34 + eyeOffset.x" :cy="43 + eyeOffset.y" rx="9" ry="6" fill="url(#evaEyeG)" filter="url(#evaEyeGlow)" class="eva-eye-excited"/>
          <ellipse :cx="66 + eyeOffset.x" :cy="43 + eyeOffset.y" rx="9" ry="6" fill="url(#evaEyeG)" filter="url(#evaEyeGlow)" class="eva-eye-excited"/>
          <ellipse :cx="33 + eyeOffset.x * 0.7" :cy="42 + eyeOffset.y * 0.7" rx="3.5" ry="2" fill="rgba(255,255,255,0.5)"/>
          <ellipse :cx="65 + eyeOffset.x * 0.7" :cy="42 + eyeOffset.y * 0.7" rx="3.5" ry="2" fill="rgba(255,255,255,0.5)"/>
          <ellipse cx="50" cy="64" rx="8" ry="5" fill="#06b6d4" opacity="0.6" class="eva-mouth-open"/>
          <circle cx="18" cy="26" r="2" fill="#22d3ee" class="echo-spark-dot"/><circle cx="84" cy="24" r="1.5" fill="#22d3ee" class="echo-spark-dot-d"/>
        </g>

        <!-- mischievous: 调皮眨眼 >_• -->
        <g v-if="echoMood === 'mischievous'" class="echo-eyes-g">
          <line x1="27" y1="44" x2="41" y2="44" stroke="url(#evaEyeG)" stroke-width="3.5" stroke-linecap="round" filter="url(#evaEyeGlow)"/>
          <ellipse :cx="66 + eyeOffset.x * 0.9" :cy="44 + eyeOffset.y * 0.9" rx="8" ry="5" fill="url(#evaEyeG)" filter="url(#evaEyeGlow)"/>
          <ellipse :cx="65 + eyeOffset.x * 0.6" :cy="43 + eyeOffset.y * 0.6" rx="3" ry="1.8" fill="rgba(255,255,255,0.45)"/>
          <path d="M42 61 Q50 56 58 62" stroke="#06b6d4" stroke-width="2.2" fill="none" stroke-linecap="round"/>
          <text x="76" y="30" font-size="13" fill="#22d3ee" font-weight="bold" class="echo-float-sym">~</text>
        </g>

        <!-- sleepy: 困困 💤 -->
        <g v-if="echoMood === 'sleepy'" class="echo-eyes-g">
          <ellipse cx="34" cy="44" rx="8" ry="4" fill="url(#evaEyeG)" opacity="0.35" filter="url(#evaEyeGlow)"/>
          <ellipse cx="66" cy="44" rx="8" ry="4" fill="url(#evaEyeG)" opacity="0.35" filter="url(#evaEyeGlow)"/>
          <text x="72" y="30" font-size="14" fill="#67e8f9" opacity="0.5" font-weight="300" letter-spacing="1" class="echo-zzz">💤</text>
          <text x="82" y="22" font-size="10" fill="#06b6d4" opacity="0.25" class="echo-zzz-d1">💤</text>
        </g>

        <!-- love: 心心眼 <3 -->
        <g v-if="echoMood === 'love'" class="echo-eyes-g">
          <path d="M34 42 C31 39 27 39 27 43 C27 47 31 49 34 52 C37 49 41 47 41 43 C41 39 37 39 34 42Z" fill="#22d3ee" class="echo-heart-pulse"/>
          <path d="M64 42 C61 39 57 39 57 43 C57 47 61 49 64 52 C67 49 71 47 71 43 C71 39 67 39 64 42Z" fill="#22d3ee" class="echo-heart-pulse"/>
          <path d="M44 61 Q50 66 56 61" stroke="#06b6d4" stroke-width="2" fill="none" stroke-linecap="round"/>
          <text x="14" y="25" font-size="12" class="echo-float-hrt">&hearts;</text>
          <text x="82" y="31" font-size="8" class="echo-float-hrt-d1">&hearts;</text>
        </g>

        <!-- surprised: 惊讶 O_O -->
        <g v-if="echoMood === 'surprised'" class="echo-eyes-g">
          <ellipse cx="34" cy="43" rx="10" ry="7" fill="url(#evaEyeG)" filter="url(#evaEyeGlow)" class="eva-eye-surprised"/>
          <ellipse cx="66" cy="43" rx="10" ry="7" fill="url(#evaEyeG)" filter="url(#evaEyeGlow)" class="eva-eye-surprised"/>
          <ellipse cx="33" cy="41" rx="4" ry="2.5" fill="rgba(255,255,255,0.55)"/>
          <ellipse cx="65" cy="41" rx="4" ry="2.5" fill="rgba(255,255,255,0.55)"/>
          <text x="79" y="27" font-size="15" fill="#22d3ee" font-weight="bold" class="echo-bang">!</text>
        </g>

        <!-- thinking: 思考中 •_• -->
        <g v-if="echoMood === 'thinking'" class="echo-eyes-g">
          <ellipse cx="34" cy="44" rx="7" ry="4.5" fill="url(#evaEyeG)" opacity="0.7" filter="url(#evaEyeGlow)"/>
          <ellipse cx="66" cy="44" rx="7" ry="4.5" fill="url(#evaEyeG)" opacity="0.7" filter="url(#evaEyeGlow)"/>
          <line x1="43" y1="63" x2="57" y2="63" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" opacity="0.6"/>
          <g class="echo-thought">
            <circle cx="82" cy="29" r="3" fill="#22d3ee" opacity="0.25"/>
            <circle cx="88" cy="21" r="5" fill="#22d3ee" opacity="0.16"/>
            <ellipse cx="78" cy="12" rx="10" ry="7.5" fill="#22d3ee" opacity="0.1"/>
          </g>
        </g>
      </svg>

      <!-- 未配置提示 -->
      <span v-if="!isOpen && !isConfigured" class="echo-badge"></span>

      <!-- 粒子特效 -->
      <div v-if="showParticles" class="echo-particles-layer">
        <span v-for="i in 8" :key="i" class="echo-p"
          :style="{ '--dx': ((Math.sin(i*0.8)*60)+'px'), '--dy': ((Math.cos(i*0.8)*-50)+'px'), '--d': (0.3+i*0.08)+'s', '--s': (1+i*0.25)+'em' }">&#x2728;</span>
      </div>
    </div>

    <!-- 展开面板 -->
    <div
      v-if="isOpen"
      class="echo-panel"
      :style="panelPosition"
      @mousedown.stop="markPanelInteract"
      @touchstart.stop="markPanelInteract"
    >
        <!-- 头部 -->
        <div class="echo-hdr">
          <div class="flex items-center gap-2.5">
            <div class="echo-ava">
              <svg viewBox="0 0 100 100"><defs><radialGradient id="avG" cx="38%" cy="32%" r="65%"><stop offset="0%" stop-color="#4a4a4a"/><stop offset="35%" stop-color="#1a1a1a"/><stop offset="70%" stop-color="#0a0a0a"/><stop offset="100%" stop-color="#000000"/></radialGradient><radialGradient id="avEyeG" cx="50%" cy="45%" r="55%"><stop offset="0%" stop-color="#67e8f9"/><stop offset="40%" stop-color="#06b6d4"/><stop offset="100%" stop-color="#0891b2"/></radialGradient></defs><circle cx="50" cy="50" r="46" fill="url(#avG)"/><ellipse cx="36" cy="32" rx="15" ry="10" fill="rgba(255,255,255,0.2)" transform="rotate(-22 36 32)"/><ellipse cx="34" cy="44" rx="8" ry="4.5" fill="url(#avEyeG)"/><ellipse cx="66" cy="44" rx="8" ry="4.5" fill="url(#avEyeG)"/><ellipse cx="34" cy="44" rx="3" ry="1.5" fill="rgba(255,255,255,0.45)" transform="translate(-1,-0.5)"/><ellipse cx="66" cy="44" rx="3" ry="1.5" fill="rgba(255,255,255,0.45)" transform="translate(-1,-0.5)"/></svg>
            </div>
            <div>
              <div class="font-semibold text-sm">{{ t('echo.title') || '念溪 Echo' }}</div>
              <div class="text-[10px] mt-0.5" :class="isLoading ? 'text-primary/70' : 'text-base-content/35'">
                {{ isLoading ? (t('echo.thinking') || '思考中...') : (t('echo.online') || '在线等你 ~') }}
              </div>
            </div>
          </div>
          <div class="flex items-center gap-0.5">
            <button @click.stop="goToFullAI" class="echo-btn" title="\u6253\u5F00\u5B8C\u6574\u5BF9\u8BDD"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"/></svg></button>
            <button @click.stop="isOpen=false" class="echo-btn echo-btn-close" title="\u5173\u95ED"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg></button>
          </div>
        </div>

        <!-- 消息区 -->
        <div ref="chatContainer" class="echo-msgs">
          <div v-if="!isConfigured" class="echo-empty">
            <div class="echo-empty-ic">\u2699\uFE0F</div>
            <div class="text-sm opacity-60 mb-3">{{ t('echo.notConfigured') || '\u8FD8\u6CA1\u914D\u7F6E AI \u5462~' }}</div>
            <button @click="goToFullAI" class="btn btn-primary btn-sm btn-xs gap-1.5 shadow-lg"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>{{ t('echo.goSettings') || '\u53BB\u8BBE\u7F6E' }}</button>
          </div>

          <template v-else>
            <template v-for="(msg, i) in currentMessages" :key="i">
              <div v-if="msg.role==='user'" class="echo-m echo-m-u"><div class="echo-bub-u">{{ msg.content }}</div></div>
              <div v-else class="echo-m echo-m-a">
                <div class="echo-av-sm"><svg viewBox="0 0 100 100"><defs><radialGradient id="smAvG" cx="38%" cy="32%" r="65%"><stop offset="0%" stop-color="#4a4a4a"/><stop offset="35%" stop-color="#1a1a1a"/><stop offset="70%" stop-color="#0a0a0a"/><stop offset="100%" stop-color="#000000"/></radialGradient><radialGradient id="smEyeG" cx="50%" cy="45%" r="55%"><stop offset="0%" stop-color="#67e8f9"/><stop offset="40%" stop-color="#06b6d4"/><stop offset="100%" stop-color="#0891b2"/></radialGradient></defs><circle cx="50" cy="50" r="46" fill="url(#smAvG)"/><ellipse cx="36" cy="32" rx="15" ry="10" fill="rgba(255,255,255,0.2)" transform="rotate(-22 36 32)"/><ellipse cx="34" cy="44" rx="8" ry="4.5" fill="url(#smEyeG)"/><ellipse cx="66" cy="44" rx="8" ry="4.5" fill="url(#smEyeG)"/></svg></div>
                <div class="echo-bub-a">
                  <div v-if="msg.toolCalls && msg.toolCalls.length" class="space-y-1 mb-1.5">
                    <div v-for="(tc, ti) in msg.toolCalls" :key="ti" class="flex items-center gap-1.5 text-[10px] px-2 py-0.5 rounded-full" :class="tc.status==='done'?'bg-success/8 text-success/70':'bg-primary/8 text-primary/70'">
                      <span v-if="tc.status==='running'" class="loading loading-spinner loading-[8px]"></span>
                      <svg v-else class="w-2.5 h-2.5 flex-shrink-0 text-success/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                      <span>{{ tc.description }}</span>
                    </div>
                  </div>
                  <div v-if="msg.reasoning" class="mb-1">
                    <details open class="group">
                      <summary class="cursor-pointer text-[10px] text-primary/50 hover:text-primary/70 select-none flex items-center gap-1"><span>{{ t('ai.thinking') || '\u601D\u8003\u8FC7\u7A0B' }}</span><span v-if="msg.loading&&!msg.content" class="loading loading-spinner loading-[8px] ml-1"></span></summary>
                      <p class="mt-0.5 pl-1.5 border-l-2 border-primary/12 text-[10px] text-base-content/40 whitespace-pre-wrap break-all leading-relaxed">{{ msg.reasoning }}</p>
                    </details>
                  </div>
                  <div v-if="msg.content" :class="msg.content.startsWith('[\u9519\u8BEF]')?'text-error text-xs':'echo-md text-xs'" v-html="msg.content.startsWith('[\u9519\u8BEF]')?msg.content:renderMd(msg.content)+(msg.loading?'<span class=\'echo-cursor\'>&#x258C;</span>':'')"></div>
                  <div v-if="msg.loading && !msg.content && !msg.reasoning && (!msg.toolCalls||!msg.toolCalls.length)" class="flex items-center gap-1 py-1.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce" style="animation-delay:0ms"></span>
                    <span class="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce" style="animation-delay:150ms"></span>
                    <span class="w-1.5 h-1.5 rounded-full bg-primary/40 animate-bounce" style="animation-delay:300ms"></span>
                  </div>
                </div>
              </div>
            </template>
            <!-- 欢迎空态 -->
            <div v-if="!currentMessages.length" class="echo-welcome">
              <div class="echo-wel-txt">{{ t('echo.welcome') || '\u55E8~ \u6211\u662F\u5FF5\u6EAA Echo \uD83D\uDC4B \u6709\u4EC0\u4E48\u53EF\u4EE5\u5E2E\u4F60\u7684\u5417?' }}</div>
            </div>
          </template>
        </div>

        <!-- 快捷建议 -->
        <div v-if="isConfigured && !currentMessages.length" class="echo-qks">
          <button v-for="(q, i) in quickQuestions" :key="i" @click="handleQuickQuestion(q)" class="echo-qk">
            <span>{{ q.icon }}</span><span>{{ q.text }}</span>
          </button>
        </div>

        <!-- 输入区 -->
        <div class="echo-input-row">
          <textarea v-model="inputText" @keydown="handleKeydown" :placeholder="isConfigured?(t('echo.placeholder')||'\u95EE\u5FF5\u6EAF\u70B9\u4EC0\u4E48...'):(t('echo.configFirst')||'\u5148\u914D\u7F6E AI \u5427')" :disabled="!isConfigured||isLoading" rows="1" class="echo-inp"/>
          <button v-if="isLoading" @click="stopGeneration" class="echo-go echo-go-stop" title="\u505C\u6B62\u751F\u6210"><svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2.5"/></svg></button>
          <button v-else @click="handleSend()" :disabled="!inputText.trim()||!isConfigured" class="echo-go" :title="t('echo.send')||'\u53D1\u9001'"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"/></svg></button>
        </div>
      </div>
  </div>
  </Teleport>
</template>

<style scoped>
/* ========== 浮动球 ========== */
.echo-wrapper { pointer-events: auto; }

.echo-ball {
  position: fixed;
  width: 54px;
  height: 54px;
  z-index: 9998;
  cursor: grab;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  transition: transform .35s cubic-bezier(.34,1.56,.64,1);
  filter: drop-shadow(0 4px 18px rgba(6,182,212,.3));
}
.echo-ball:hover { transform: scale(1.08) translateY(-2px); filter: drop-shadow(0 6px 24px rgba(6,182,212,.45)); }
.echo-ball:active { transform: scale(.92); cursor: grabbing; }
.echo-dragging { cursor: grabbing; transform: scale(1.05)!important; transition: transform .1s ease!important; }

/* EVA 光晕 - 青蓝色调 */
@keyframes orbit-spin { to { transform: rotate(360deg); } }
.echo-orbit {
  position:absolute; inset:-5px; border-radius:50%; border:1.5px solid rgba(6,182,212,.25);
  animation: orbit-spin 8s linear infinite;
}
@keyframes eva-glow-pulse { 0%,100%{opacity:.35;transform:scale(1)} 50%{opacity:.65;transform:scale(1.12)} }
.echo-glow {
  position:absolute; inset:-8px; border-radius:50%;
  background:radial-gradient(circle,rgba(6,182,212,.28) 0%,transparent 70%);
  animation: eva-glow-pulse 3s ease-in-out infinite;
  pointer-events:none;
}

/* SVG */
.echo-face { width:100%; height:100%; overflow:visible; }

/* 浮动呼吸 */
@keyframes float-y { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-3px)} }
.echo-face circle:first-of-type { animation: float-y 3.5s ease-in-out infinite; }

/* 眼睛通用过渡 */
.echo-eyes-g { transition: opacity .3s ease; }

/* EVA 眼睛动画 */
@keyframes eva-eye-shimmer {
  0%, 100% { opacity: 1; filter: brightness(1); }
  50% { opacity: 0.85; filter: brightness(1.2); }
}
@keyframes eva-eye-blink {
  0%, 90%, 100% { transform: scaleY(1); }
  95% { transform: scaleY(0.15); }
}
.eva-eye-ellipse { animation: eva-eye-shimmer 3s ease-in-out infinite, eva-eye-blink 5s ease-in-out infinite; }

@keyframes eva-happy-wiggle {
  0%, 100% { d: path('M27 43 Q34 36 41 43'); }
  50% { d: path('M27 43 Q34 34 41 43'); }
}
.eva-eye-happy { animation: eva-eye-shimmer 3s ease-in-out infinite; }

@keyframes eva-excited-pulse {
  0%, 100% { opacity: 1; rx: 9px; ry: 6px; }
  50% { opacity: 0.88; rx: 10px; ry: 6.5px; }
}
.eva-eye-excited { animation: eva-excited-pulse 2s ease-in-out infinite; }

@keyframes eva-mouth-open-bounce {
  0%, 100% { transform: scaleY(1); }
  50% { transform: scaleY(1.12); }
}
.eva-mouth-open { animation: eva-mouth-open-bounce 1.8s ease-in-out infinite; transform-origin: center top; }

@keyframes eva-surprised-pop {
  0%, 100% { rx: 10px; ry: 7px; }
  30% { rx: 11.5px; ry: 8px; }
}
.eva-eye-surprised { animation: eva-surprised-pop 1.2s ease-in-out infinite; }

/* 星星闪烁 */
@keyframes twinkle { 0%,100%{transform:scale(1);filter:brightness(1)} 50%{transform:scale(1.15);filter:brightness(1.3)} }
.echo-star { animation: twinkle 2s ease-in-out infinite; transform-origin:center; }
.echo-star:nth-last-child(2) { animation-delay:.35s; }
.echo-star-fast { animation: twinkle 1.4s ease-in-out infinite; transform-origin:center; }
.echo-star-fast:nth-last-child(2) { animation-delay:.2s; }

/* 嘴巴弹跳 */
@keyframes mouth-bounce { 0%,100%{transform:scaleY(1)} 50%{transform:scaleY(1.08)} }
.echo-mouth-w { animation: mouth-bounce 2.2s ease-in-out infinite; transform-origin:center top; }
.echo-mouth-bounce { animation: mouth-bounce 1.5s ease-in-out infinite; transform-origin:center top; }

/* 心跳 */
@keyframes hb { 0%,100%{transform:scale(1)} 15%{transform:scale(1.22)} 30%{transform:scale(1)} 45%{transform:scale(1.15)} 60%{transform:scale(1)} }
.echo-heart-pulse { animation: hb 1.1s ease-in-out infinite; }
.echo-heart-pulse:last-child { animation-delay:.15s; }

/* 飘浮符号 */
@keyframes float-sym { 0%{opacity:0;transform:translateY(4px) scale(.7)} 30%{opacity:.85;transform:translateY(0) scale(1)} 80%{opacity:.5;transform:translateY(-10px) scale(.88)} 100%{opacity:0;transform:translateY(-14px) scale(.65)} }
.echo-float-sym { animation:float-sym 2.5s ease-in-out infinite; display:inline-block; }
.echo-float-hrt { animation:float-sym 2.8s ease-in-out infinite .3s; display:inline-block; }
.echo-float-hrt-d1 { animation:float-sym 2.6s ease-in-out infinite 1s; display:inline-block; }

/* 火花点 */
@keyframes spark-fade { 0%{opacity:0;transform:scale(0)} 40%{opacity:1;transform:scale(1.2)} 100%{opacity:0;transform:scale(0)} }
.echo-spark-dot { animation:spark-fade 2s ease-in-out infinite; }
.echo-spark-dot-d { animation:spark-fade 2.2s ease-in-out infinite .5s; }

/* ZZZ */
@keyframes z-drift { 0%{opacity:0;transform:translate(0,0)} 40%{opacity:.7;transform:translate(4px,-5px)} 100%{opacity:0;transform:translate(10px,-14px)} }
.echo-z { animation:z-drift 2.5s ease-in-out infinite; display:inline-block; }
.echo-z-d1 { animation:z-drift 2.5s ease-in-out infinite .7s; display:inline-block; }

/* 💤 困困飘浮 */
@keyframes zzz-float {
  0% { opacity: 0; transform: translate(0, 2px) scale(0.8) rotate(-5deg); }
  25% { opacity: 0.6; transform: translate(3px, -3px) scale(1) rotate(3deg); }
  50% { opacity: 0.45; transform: translate(6px, -7px) scale(0.95) rotate(-2deg); }
  75% { opacity: 0.25; transform: translate(9px, -11px) scale(0.88) rotate(4deg); }
  100% { opacity: 0; transform: translate(12px, -15px) scale(0.75) rotate(-3deg); }
}
.echo-zzz { animation: zzz-float 3s ease-in-out infinite; display: inline-block; }
.echo-zzz-d1 { animation: zzz-float 3s ease-in-out infinite 1s; display: inline-block; }

/* 感叹号 */
@keyframes bang-pop { 0%,100%{transform:translateY(0) scale(1)} 25%{transform:translateY(-3px) scale(1.15)} 50%{transform:translateY(1px) scale(.93)} 75%{transform:translateY(-2px) scale(1.05)} }
.echo-bang { animation:bang-pop .6s ease-in-out infinite; display:inline-block; }

/* 思考泡泡 */
@keyframes thought-float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-3px)} }
.echo-thought { animation:thought-float 2.2s ease-in-out infinite; }

/* 腮红脉冲 */
@keyframes blush-p { 0%,100%{opacity:.35} 50%{opacity:.6} }
.echo-blush-group ellipse { animation:blush-p 3s ease-in-out infinite; }

/* 配置提示徽章 */
@keyframes badge-p { 0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,.5)} 50%{box-shadow:0 0 0 5px rgba(239,68,68,0)} }
.echo-badge {
  position:absolute; top:-2px; right:-2px; width:12px; height:12px;
  background:#ef4444; border-radius:50%; border:2px solid #fff;
  animation:badge-p 1.8s ease-in-out infinite; z-index:3;
}

/* 粒子 */
.echo-particles-layer { position:absolute; inset:0; pointer-events:none; overflow:visible; z-index:5; }
@keyframes p-burst { 0%{opacity:1;transform:translate(0,0) scale(1)} 100%{opacity:0;transform:translate(var(--dx),var(--dy)) scale(0)} }
.echo-p { position:absolute; top:50%;left:50%; animation:p-burst .7s ease-out forwards; color:#fbbf24; font-size:var(--s); margin-left:-.4em; margin-top:-.4em; }

/* ========== 面板 ========== */
.echo-panel {
  position: fixed;
  width:360px; max-height:calc(100vh - 90px);
  background: linear-gradient(165deg, hsl(var(--b1)/.88) 0%, hsl(var(--b2)/.82) 100%);
  backdrop-filter: blur(24px) saturate(1.5);
  -webkit-backdrop-filter: blur(24px) saturate(1.5);
  border: 1px solid hsl(var(--bc)/.1);
  border-radius: 20px;
  box-shadow:
    0 20px 60px rgba(0,0,0,.1),
    0 8px 25px rgba(0,0,0,.04),
    inset 0 1px 0 hsl(var(--bc)/.08);
  display:flex; flex-direction:column; z-index:9999; overflow:hidden;
  animation: panel-in .35s cubic-bezier(.34,1.56,.64,1) both;
}
@keyframes panel-in {
  from { opacity:0; transform:scale(.9) translateY(8px); }
  to { opacity:1; transform:scale(1) translateY(0); }
}

/* 面板动画 */
.ep-enter-active { transition: all .4s cubic-bezier(.34,1.56,.64,1); transition-property:opacity,transform; }
.ep-leave-active { transition: all .25s cubic-bezier(.4,0,1,1); transition-property:opacity,transform; }
.ep-enter-from { opacity:0; transform:scale(.86) translateY(10px); }
.ep-leave-to { opacity:0; transform:scale(.96) translateY(5px); }

/* 头部 */
.echo-hdr { display:flex; align-items:center; justify-content:space-between; padding:13px 16px 10px; border-bottom:1px solid hsl(var(--bc)/.06); flex-shrink:0; }

/* 头像 */
.echo-ava { width:36px; height:36px; flex-shrink:0; border-radius:50%; overflow:hidden; box-shadow:0 2px 10px rgba(6,182,212,.2); transition:transform .3s cubic-bezier(.34,1.56,.64,1); }
.echo-ava:hover { transform:scale(1.08) rotate(-5deg); }
.echo-ava svg { width:100%;height:100%;display:block; }

/* 按钮 */
.echo-btn { width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:hsl(var(--bc)/.5); background:transparent; border:none; cursor:pointer; transition:all .2s; }
.echo-btn:hover { color:hsl(var(--bc)/.75); background:hsl(var(--bc)/.06); }
.echo-btn-close:hover { color:#ef4444; background:rgba(239,68,68,.07); }

/* 消息区 */
.echo-msgs { flex:1; overflow-y:auto; padding:12px 16px; display:flex; flex-direction:column; gap:9px; min-height:140px; max-height:calc(100vh - 260px); scroll-behavior:smooth; }
.echo-msgs::-webkit-scrollbar{width:3px} .echo-msgs::-webkit-scrollbar-track{background:transparent} .echo-msgs::-webkit-scrollbar-thumb{background:hsl(var(--bc)/.12);border-radius:3px;}

/* 消息行 & 入场 */
.echo-m { display:flex; gap:7px; align-items:flex-start; animation:m-in .3s ease both; }
@keyframes m-in { from{opacity:0;transform:translateY(7px) scale(.96)} to{opacity:1;transform:translateY(0) scale(1)} }
.echo-m-u { justify-content:flex-end; animation-delay:.05s; }

/* 气泡 */
.echo-bub-u {
  max-width:80%; padding:9px 14px;
  background:hsl(var(--p)); color:#fff;
  border-radius:18px 18px 5px 18px; font-size:13px; line-height:1.5;
  word-break:break-word; box-shadow:0 2px 10px hsl(var(--p)/.2);
}
.echo-bub-a {
  max-width:82%; padding:9px 13px; background:hsl(var(--bc)/.03);
  border-radius:18px 18px 18px 5px; line-height:1.55; word-break:break-word;
  border:1px solid hsl(var(--bc)/.05);
}
.echo-av-sm { width:26px;height:26px; flex-shrink:0; border-radius:50%; margin-top:2px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.06); }
.echo-av-sm svg { width:100%;height:100%;display:block; }

/* Markdown */
.echo-md :deep(p){margin:.3em 0} .echo-md :deep(p:first-child){margin-top:0} .echo-md :deep(p:last-child){margin-bottom:0}
.echo-md :deep(strong){font-weight:600}
.echo-md :deep(code){background:hsl(var(--b3)/.65);padding:.12em .35em;border-radius:4px;font-size:.88em}
.echo-md :deep(ul),.echo-md :deep(ol){margin:.3em 0;padding-left:1.3em} .echo-md :deep(li){margin:.12em 0}

/* 光标闪烁 */
@keyframes cur-blink { 0%,100%{opacity:1} 50%{opacity:0} }
.echo-cursor { animation:cur-blink .7s step-end infinite; color:#8b5cf6; }

/* 空状态 */
.echo-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; height:180px; gap:10px; }
.echo-empty-ic { font-size:30px; animation:bob 3s ease-in-out infinite; }
@keyframes bob { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }

/* 欢迎 */
.echo-welcome { display:flex; flex-direction:column; align-items:center; min-height:130px; gap:12px; padding:10px 0; }
.echo-wel-av { width:52px;height:52px;border-radius:50%;overflow:hidden;box-shadow:0 4px 14px rgba(6,182,212,.15); animation:wpop .6s cubic-bezier(.34,1.56,.64,1) both; }
.echo-wel-av svg { width:100%;height:100%;display:block; }
@keyframes wpop { 0%{transform:scale(0) rotate(-18deg);opacity:0} 60%{transform:scale(1.12) rotate(3deg);opacity:1} 100%{transform:scale(1) rotate(0);opacity:1} }
.echo-wel-txt { font-size:13px;color:hsl(var(--bc)/.45);text-align:center;line-height:1.6;padding:0 12px; animation:fup .5s ease .2s both; }
@keyframes fup { from{opacity:0;transform:translateY(7px)} to{opacity:1;transform:translateY(0)} }

/* 快捷建议 */
.echo-qks { display:flex; flex-wrap:wrap; gap:6px; padding:8px 16px 4px; border-top:1px solid hsl(var(--bc)/.05); flex-shrink:0; }
.echo-qk {
  display:inline-flex; align-items:center; gap:5px; padding:6px 11px; font-size:11.5px;
  color:hsl(var(--p)); background:hsl(var(--p)/.06); border:1px solid hsl(var(--p)/.12);
  border-radius:999px; cursor:pointer; transition:all .25s cubic-bezier(.34,1.56,.64,1);
  white-space:nowrap; max-width:100%; overflow:hidden; text-overflow:ellipsis; font-weight:500;
}
.echo-qk:hover { background:hsl(var(--p)/.14); border-color:hsl(var(--p)/.28); transform:translateY(-2px) scale(1.02); box-shadow:0 3px 10px hsl(var(--p)/.12); }
.echo-qk:active { transform:translateY(0) scale(.97); }

/* 输入区 */
.echo-input-row { display:flex; align-items:flex-end; gap:7px; padding:10px 12px 12px; border-top:1px solid hsl(var(--bc)/.06); flex-shrink:0; }
.echo-inp {
  flex:1; resize:none; border:1.5px solid hsl(var(--bc)/.09); border-radius:17px;
  padding:9px 14px; font-size:13px; background:hsl(var(--b2)/.35);
  outline:none; transition:all .25s; line-height:1.4; max-height:80px; min-height:40px; font-family:inherit; color:inherit;
}
.echo-inp:focus { border-color:hsl(var(--p)/.45); box-shadow:0 0 0 3px hsl(var(--p)/.08); background:hsl(var(--b2)/.55); }
.echo-inp::placeholder { color:hsl(var(--bc)/.28); }
.echo-inp:disabled { opacity:.45; cursor:not-allowed; }

.echo-go {
  width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  background:hsl(var(--p));color:#fff;border:none;cursor:pointer;
  flex-shrink:0;transition:all .25s cubic-bezier(.34,1.56,.64,1);
  box-shadow:0 2px 10px hsl(var(--p)/.3);
}
.echo-go:not(:disabled):hover { filter:brightness(1.08); transform:scale(1.07) rotate(-3deg); box-shadow:0 4px 14px hsl(var(--p)/.4); }
.echo-go:not(:disabled):active { transform:scale(.93); }
.echo-go:disabled { opacity:.3;cursor:not-allowed;box-shadow:none; }
.echo-go-stop { background:linear-gradient(135deg,#ef4444,#dc2626); box-shadow:0 2px 10px rgba(239,68,68,.3); }
.echo-go-stop:hover { box-shadow:0 4px 14px rgba(239,68,68,.4); }

/* 移动端 */
@media(max-width:420px){
  .echo-panel{width:calc(100vw - 20px)!important;left:10px!important;right:10px!important;bottom:10px!important;max-height:calc(100vh - 90px);border-radius:18px;}
  .echo-ball{width:50px;height:50px;}
  .echo-msgs{max-height:calc(100vh - 270px);}
}
@supports(padding-top:env(safe-area-inset-bottom)){
  .echo-input-row{padding-bottom:calc(12px + env(safe-area-inset-bottom));}
  .echo-panel{maxHeight:calc(100vh - 90px - env(safe-area-inset-bottom));}
}
</style>
