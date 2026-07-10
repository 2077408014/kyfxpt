<template>
  <div class="ai-chat">
    <div class="chat-container">
      <div class="chat-messages">
        <div v-for="msg in messages" :key="msg.id" class="message" :class="msg.role">
          <div class="avatar">
            <el-icon v-if="msg.role === 'user'"><User /></el-icon>
            <el-icon v-else><Service /></el-icon>
          </div>
          <div class="content">
            <p>{{ msg.content }}</p>
            <span v-if="msg.source" class="source">{{ msg.source }}</span>
          </div>
        </div>
      </div>
      <div class="chat-input">
        <el-input v-model="inputMessage" placeholder="输入你的问题或指令..." type="textarea" :rows="2" @keyup.enter="handleSend">
          <template #append>
            <el-button type="primary" @click="handleSend">发送</el-button>
          </template>
        </el-input>
      </div>
    </div>
    <div class="quick-commands">
      <h3>快捷指令</h3>
      <div class="command-buttons">
        <el-button @click="sendCommand('打开错题模块')">打开错题模块</el-button>
        <el-button @click="sendCommand('开始今日单词复习')">开始今日单词复习</el-button>
        <el-button @click="sendCommand('推荐10道高数微分方程题目')">推荐10道高数微分方程题目</el-button>
        <el-button @click="sendCommand('分析我的薄弱知识点')">分析我的薄弱知识点</el-button>
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
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Service } from '@element-plus/icons-vue'

const router = useRouter()
const messages = ref<any[]>([
  { id: 1, role: 'ai', content: '你好！我是考研复习平台的AI助手。请问有什么我可以帮你的？', source: 'AI系统' }
])
const inputMessage = ref('')

function handleSend() {
  if (!inputMessage.value.trim()) {
    ElMessage.warning('请输入内容')
    return
  }
  
  messages.value.push({
    id: messages.value.length + 1,
    role: 'user',
    content: inputMessage.value
  })
  
  const userMsg = inputMessage.value
  inputMessage.value = ''
  
  setTimeout(() => {
    const response = getAIResponse(userMsg)
    messages.value.push({
      id: messages.value.length + 1,
      role: 'ai',
      content: response.content,
      source: response.source
    })
  }, 1000)
}

function sendCommand(cmd: string) {
  inputMessage.value = cmd
  handleSend()
}

function getAIResponse(msg: string) {
  if (msg.includes('打开错题') || msg.includes('错题模块')) {
    setTimeout(() => router.push('/dashboard/mistakes'), 500)
    return { content: '正在为你打开错题管理模块...', source: 'AI系统' }
  }
  if (msg.includes('单词复习') || msg.includes('背单词')) {
    setTimeout(() => router.push('/dashboard/words'), 500)
    return { content: '正在为你打开单词背诵模块...', source: 'AI系统' }
  }
  if (msg.includes('推荐') || msg.includes('题目')) {
    setTimeout(() => router.push('/dashboard/recommend'), 500)
    return { content: '正在为你生成推荐题目...', source: 'AI系统' }
  }
  if (msg.includes('薄弱') || msg.includes('分析')) {
    return { content: '根据你的学习数据，你的薄弱知识点主要集中在：微分方程、阅读理解、马原辩证法。建议重点复习这些内容。', source: '本地数据分析' }
  }
  if (msg.includes('微积分')) {
    return { content: '微积分是高等数学的核心内容，主要包括极限、导数、积分等部分。考研数学中微积分占比约56%，是得分的关键。建议重点掌握：1. 极限的计算方法；2. 导数的应用（单调性、极值、凹凸性）；3. 定积分和不定积分的计算；4. 微分方程的求解。', source: '考研资料' }
  }
  return { content: '这是一个模拟回答。在实际应用中，AI系统会根据你的问题进行智能分析，可以回答知识点解析、题目解答、学习方法建议等。如果本地资料中有相关内容，会优先使用本地资料进行回答。', source: 'AI系统' }
}
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

.source {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}

.message.user .source {
  color: rgba(255, 255, 255, 0.7);
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
</style>