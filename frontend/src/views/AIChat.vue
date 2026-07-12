<template>
  <div class="ai-chat">
    <div class="chat-container">
      <div class="chat-header">
        <h2>AI智能助手</h2>
        <div class="header-actions">
          <el-button type="text" @click="showConfigDialog = true">
            <el-icon><Tools /></el-icon>AI配置
          </el-button>
          <el-button type="text" @click="handleClearHistory">
            <el-icon><Delete /></el-icon>清除记录
          </el-button>
        </div>
      </div>
      <div ref="chatContainerRef" class="chat-messages">
        <div v-for="msg in messages" :key="msg.id" class="message" :class="msg.role">
          <div class="avatar">
            <el-icon v-if="msg.role === 'user'"><User /></el-icon>
            <el-icon v-else><Message /></el-icon>
          </div>
          <div class="content">
            <p v-if="msg.role === 'user'">{{ msg.content }}</p>
            <div v-else class="ai-content" v-html="renderMarkdown(msg.content)"></div>
            <span v-if="msg.source" class="source">{{ msg.source }}</span>
          </div>
        </div>
        <div v-if="suggestions.length > 0" class="suggestions">
          <el-tag
            v-for="(suggestion, index) in suggestions"
            :key="index"
            size="small"
            type="info"
            @click="sendSuggestion(suggestion)"
          >
            {{ suggestion }}
          </el-tag>
        </div>
      </div>
      <div class="chat-input">
        <el-input
          v-model="inputMessage"
          placeholder="输入你的问题或指令..."
          type="textarea"
          :rows="2"
          :disabled="loading"
          @keyup.enter="handleSend"
        >
          <template #append>
            <el-button type="primary" @click="handleSend" :loading="loading">
              <el-icon><Refresh /></el-icon>发送
            </el-button>
          </template>
        </el-input>
      </div>
    </div>
    <div class="sidebar">
      <div class="quick-commands">
        <h3>快捷指令</h3>
        <div class="command-buttons">
          <el-button @click="sendCommand('打开错题模块')">打开错题模块</el-button>
          <el-button @click="sendCommand('开始今日单词复习')">开始今日单词复习</el-button>
          <el-button @click="sendCommand('推荐10道高数微分方程题目')">推荐10道题目</el-button>
          <el-button @click="sendCommand('分析我的薄弱知识点')">分析薄弱知识点</el-button>
        </div>
      </div>
      <div class="usage-tips">
        <h3>使用提示</h3>
        <ul>
          <li>支持自然语言指令，如："打开错题模块"、"开始复习"</li>
          <li>可以提问考研相关问题，如："什么是微积分？"</li>
          <li>支持多轮对话，系统会记住上下文</li>
          <li>答案来源会标注（本地资料/网络资源）</li>
        </ul>
      </div>
    </div>

    <el-dialog v-model="showConfigDialog" title="AI配置" width="500px">
      <el-form :model="aiConfig" label-width="120px">
        <el-form-item label="AI服务提供商">
          <el-select v-model="aiConfig.provider" @change="handleProviderChange">
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="智谱AI" value="zhipu" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="aiConfig.apiKey" type="password" placeholder="请输入您的API Key" />
        </el-form-item>
        <el-form-item label="API Base URL">
          <el-input v-model="aiConfig.baseUrl" placeholder="API接口地址" />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="aiConfig.model" placeholder="模型名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showConfigDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAIConfig">保存配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Message, Delete, Refresh, Tools } from '@element-plus/icons-vue'
import { chat, command, getHistory, clearHistory } from '../api/ai'
import { getMe, updateAIConfig, type User as UserType } from '../api/auth'
import { marked } from 'marked'
import katex from 'katex'
import 'katex/dist/katex.min.css'

marked.setOptions({
  breaks: true,
  gfm: true,
  sanitize: false,
  mangle: false
})

const router = useRouter()
const messages = ref<any[]>([])
const inputMessage = ref('')
const loading = ref(false)
const suggestions = ref<string[]>([])
const showConfigDialog = ref(false)
const chatContainerRef = ref<HTMLElement | null>(null)

const aiConfig = reactive({
  provider: '',
  apiKey: '',
  baseUrl: '',
  model: ''
})

const providerDefaults: Record<string, { baseUrl: string; model: string }> = {
  deepseek: {
    baseUrl: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat'
  },
  zhipu: {
    baseUrl: 'https://open.bigmodel.cn/api/paas/v4',
    model: 'glm-4'
  },
  openai: {
    baseUrl: 'https://api.openai.com/v1',
    model: 'gpt-3.5-turbo'
  },
  custom: {
    baseUrl: '',
    model: ''
  }
}

function handleProviderChange() {
  const defaults = providerDefaults[aiConfig.provider]
  if (defaults) {
    aiConfig.baseUrl = defaults.baseUrl
    aiConfig.model = defaults.model
  }
}

async function loadAIConfig() {
  try {
    const user: UserType = await getMe()
    if (user.ai_api_provider) {
      aiConfig.provider = user.ai_api_provider
      handleProviderChange()
    }
  } catch {
    // ignore
  }
}

async function saveAIConfig() {
  try {
    await updateAIConfig({
      ai_api_provider: aiConfig.provider || undefined,
      ai_api_key: aiConfig.apiKey || undefined,
      ai_api_base_url: aiConfig.baseUrl || undefined,
      ai_api_model: aiConfig.model || undefined
    })
    ElMessage.success('AI配置保存成功')
    showConfigDialog.value = false
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}

function renderMathFormula(formula: string, displayMode: boolean): string {
  try {
    return katex.renderToString(formula.trim(), {
      displayMode,
      throwOnError: false,
      strict: false,
      trust: true
    })
  } catch {
    return `<span class="math-error">${displayMode ? '$$' : '$'}${formula.trim()}${displayMode ? '$$' : '$'}</span>`
  }
}

function renderMarkdown(text: string): string {
  let result = text || ''
  
  const mathBlocks: { placeholder: string; html: string }[] = []
  
  const addMathBlock = (formula: string, displayMode: boolean): string => {
    const html = renderMathFormula(formula, displayMode)
    const placeholder = `@@MATH_${displayMode ? 'BLOCK' : 'INLINE'}_${mathBlocks.length}@@`
    mathBlocks.push({ placeholder, html })
    return placeholder
  }
  
  result = result.replace(/\$\$(.*?)\$\$/gms, (_, formula) => {
    const trimmedFormula = formula.trim()
    if (!trimmedFormula) return '$$'
    return addMathBlock(trimmedFormula, true)
  })
  
  result = result.replace(/(?<!\\)\$(.*?)(?<!\\)\$/g, (_, formula) => {
    const trimmedFormula = formula.trim()
    if (!trimmedFormula) return '$'
    if (trimmedFormula.length > 100) {
      return addMathBlock(trimmedFormula, true)
    }
    return addMathBlock(trimmedFormula, false)
  })
  
  const standaloneMathPatterns = [
    /lim_{[^}]+}\s+[^$]+/g,
    /\\frac{[^}]+}{[^}]+}/g,
    /\\int[^$]+/g,
    /\\sum_{[^}]+}[^$]+/g,
    /\\frac{d[^}]+}{d[^}]+}/g,
    /\\frac{\\partial[^}]+}{\\partial[^}]+}/g,
    /\\sqrt{[^}]+}/g,
    /\\sin\s*\([^)]+\)/g,
    /\\cos\s*\([^)]+\)/g,
    /\\tan\s*\([^)]+\)/g,
    /\\ln\s*\([^)]+\)/g,
    /\\log\s*\([^)]+\)/g,
    /\\exp\s*\([^)]+\)/g,
    /\\alpha|\\beta|\\gamma|\\delta|\\epsilon|\\zeta|\\eta|\\theta|\\iota|\\kappa|\\lambda|\\mu|\\nu|\\xi|\\pi|\\rho|\\sigma|\\tau|\\upsilon|\\phi|\\chi|\\psi|\\omega/gi,
    /\\Delta|\\Gamma|\\Theta|\\Lambda|\\Xi|\\Pi|\\Sigma|\\Upsilon|\\Phi|\\Psi|\\Omega/gi,
    /\\frac\{[^\}]+\}\{[^\}]+\}/g,
    /\\sum\{[^\}]+\}[^$]+/g,
    /\\int\{[^\}]+\}[^$]+/g,
    /\\lim\{[^\}]+\}\s+[^$]+/g
  ]
  
  standaloneMathPatterns.forEach((pattern) => {
    result = result.replace(pattern, (match) => {
      if (match.includes('@@MATH_')) return match
      return addMathBlock(match, false)
    })
  })
  
  const parsedMarkdown = marked.parse(result)
  if (parsedMarkdown) {
    result = parsedMarkdown as string
  }
  
  mathBlocks.forEach(({ placeholder, html }) => {
    result = result.split(placeholder).join(html)
  })
  
  return result
}

async function loadHistory() {
  try {
    const history = await getHistory()
    messages.value = history.map(msg => ({
      id: msg.id,
      role: msg.message_type === 'question' ? 'user' : 'ai',
      content: msg.content,
      source: msg.source
    }))
    
    if (messages.value.length === 0) {
      messages.value.push({
        id: 1,
        role: 'ai',
        content: '你好！我是考研复习平台的AI助手。请问有什么我可以帮你的？',
        source: 'AI系统'
      })
    }
  } catch {
    messages.value.push({
      id: 1,
      role: 'ai',
      content: '你好！我是考研复习平台的AI助手。请问有什么我可以帮你的？',
      source: 'AI系统'
    })
  }
}

async function handleSend() {
  if (!inputMessage.value.trim() || loading.value) {
    if (!inputMessage.value.trim()) {
      ElMessage.warning('请输入内容')
    }
    return
  }
  
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: inputMessage.value
  })
  
  const userMsg = inputMessage.value
  inputMessage.value = ''
  suggestions.value = []
  loading.value = true
  
  try {
    const result = await chat(userMsg)
    
    messages.value.push({
      id: Date.now() + 1,
      role: 'ai',
      content: result.answer,
      source: result.category
    })
    
    if (result.suggestions && result.suggestions.length > 0) {
      suggestions.value = result.suggestions
    }
    
    handleRouteNavigation(result.answer)
  } catch (error: any) {
    messages.value.push({
      id: Date.now() + 1,
      role: 'ai',
      content: error.response?.data?.detail || '抱歉，我暂时无法回答这个问题。',
      source: 'AI系统'
    })
  } finally {
    loading.value = false
  }
}

function handleRouteNavigation(answer: string) {
  const routes: Record<string, string> = {
    '错题': '/dashboard/mistakes',
    '单词': '/dashboard/words',
    '推荐': '/dashboard/recommend',
    '薄弱': '/dashboard/recommend',
    '计划': '/dashboard/words',
    '报告': '/dashboard/report'
  }
  
  for (const [keyword, route] of Object.entries(routes)) {
    if (answer.includes(keyword)) {
      setTimeout(() => router.push(route), 1500)
      break
    }
  }
}

async function sendCommand(cmd: string) {
  inputMessage.value = cmd
  handleSend()
  
  try {
    const result = await command(cmd)
    
    if (result.action === 'open_mistakes') {
      setTimeout(() => router.push('/dashboard/mistakes'), 1000)
    } else if (result.action === 'start_recitation') {
      setTimeout(() => router.push('/dashboard/words'), 1000)
    } else if (result.action === 'generate_recommendation') {
      setTimeout(() => router.push('/dashboard/recommend'), 1000)
    } else if (result.action === 'analyze_weak_points') {
      setTimeout(() => router.push('/dashboard/recommend'), 1000)
    } else if (result.action === 'generate_report') {
      setTimeout(() => router.push('/dashboard/report'), 1000)
    }
  } catch {
    // ignore
  }
}

function sendSuggestion(suggestion: string) {
  inputMessage.value = suggestion
  handleSend()
}

async function handleClearHistory() {
  try {
    await clearHistory()
    messages.value = [{
      id: 1,
      role: 'ai',
      content: '你好！我是考研复习平台的AI助手。请问有什么我可以帮你的？',
      source: 'AI系统'
    }]
    ElMessage.success('聊天记录已清除')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '清除失败')
  }
}

onMounted(() => {
  loadHistory()
  loadAIConfig()
})
</script>

<style scoped>
.ai-chat {
  padding: 20px;
  display: flex;
  gap: 20px;
  height: calc(100vh - 80px);
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.chat-header h2 {
  margin: 0;
  font-size: 18px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.message.user .avatar {
  background: #667eea;
  color: white;
}

.message.ai .avatar {
  background: #f0f0f0;
  color: #666;
}

.content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
}

.message.user .content {
  background: #667eea;
  color: white;
  border-radius: 12px 0 12px 12px;
}

.message.ai .content {
  background: #f5f7fa;
  color: #333;
  border-radius: 0 12px 12px 12px;
}

.content p {
  margin: 0;
  line-height: 1.6;
}

.ai-content {
  line-height: 1.8;
}

.ai-content h1,
.ai-content h2,
.ai-content h3 {
  margin: 12px 0 8px;
  font-weight: 600;
}

.ai-content h1 {
  font-size: 18px;
}

.ai-content h2 {
  font-size: 16px;
}

.ai-content h3 {
  font-size: 14px;
}

.ai-content ul,
.ai-content ol {
  margin: 8px 0;
  padding-left: 24px;
}

.ai-content li {
  margin-bottom: 4px;
}

.ai-content strong {
  font-weight: 600;
  color: #667eea;
}

.ai-content code {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.ai-content pre {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.ai-content pre code {
  background: none;
  padding: 0;
}

.source {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}

.message.user .source {
  color: rgba(255, 255, 255, 0.7);
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  padding-left: 52px;
}

.suggestions .el-tag {
  cursor: pointer;
}

.chat-input {
  padding: 20px;
  border-top: 1px solid #e0e0e0;
}

.sidebar {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.quick-commands,
.usage-tips {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.quick-commands h3,
.usage-tips h3 {
  margin: 0 0 16px;
  font-size: 16px;
  color: #333;
}

.command-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.command-buttons .el-button {
  text-align: left;
}

.usage-tips ul {
  margin: 0;
  padding-left: 20px;
}

.usage-tips li {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.ai-content .katex {
  font-size: 1.1em;
}

.ai-content .katex-display {
  margin: 12px 0;
  overflow-x: auto;
  overflow-y: hidden;
}

.ai-content .katex-display::-webkit-scrollbar {
  height: 6px;
}

.ai-content .katex-display::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.ai-content .katex-display::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.ai-content .katex-display::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}

.math-error {
  color: #e74c3c;
  font-family: monospace;
  background: #fef5f5;
  padding: 2px 4px;
  border-radius: 3px;
}
</style>