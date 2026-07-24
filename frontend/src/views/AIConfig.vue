<template>
  <div class="ai-config-page">
    <div class="page-header">
      <h2>AI配置</h2>
      <el-button type="primary" @click="goBack">返回AI问答</el-button>
    </div>

    <div class="config-card">
      <div class="config-section">
        <h3>AI服务提供商</h3>
        <div class="provider-options">
          <el-radio-group v-model="aiConfig.provider">
            <el-radio-button label="deepseek">DeepSeek</el-radio-button>
            <el-radio-button label="zhipu">智谱AI</el-radio-button>
            <el-radio-button label="openai">OpenAI</el-radio-button>
            <el-radio-button label="custom">自定义</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <div class="config-section">
        <h3>API配置</h3>
        <el-form :model="aiConfig" label-width="120px" class="config-form">
          <el-form-item label="API Key">
            <el-input 
              v-model="aiConfig.apiKey" 
              type="password" 
              placeholder="请输入您的API Key"
              show-password
            />
          </el-form-item>
          <el-form-item label="API Base URL">
            <el-input 
              v-model="aiConfig.baseUrl" 
              placeholder="API接口地址"
            />
          </el-form-item>
          <el-form-item label="模型名称">
            <el-input 
              v-model="aiConfig.model" 
              placeholder="模型名称"
            />
          </el-form-item>
        </el-form>
      </div>

      <div class="config-section" v-if="hasConfig">
        <h3>当前配置</h3>
        <div class="current-config">
          <div class="config-item">
            <span class="label">服务提供商：</span>
            <span class="value">{{ getProviderLabel(aiConfig.provider) }}</span>
          </div>
          <div class="config-item">
            <span class="label">API Key：</span>
            <span class="value">{{ maskApiKey(aiConfig.apiKey) }}</span>
          </div>
          <div class="config-item">
            <span class="label">API Base URL：</span>
            <span class="value">{{ aiConfig.baseUrl || '未设置' }}</span>
          </div>
          <div class="config-item">
            <span class="label">模型名称：</span>
            <span class="value">{{ aiConfig.model || '未设置' }}</span>
          </div>
        </div>
      </div>

      <div class="action-buttons">
        <el-button 
          v-if="hasConfig" 
          type="danger" 
          @click="clearAIConfig"
          :loading="clearing"
        >
          <el-icon><Delete /></el-icon>删除配置
        </el-button>
        <el-button 
          type="primary" 
          @click="saveAIConfig"
          :loading="saving"
        >
          <el-icon><Check /></el-icon>保存配置
        </el-button>
      </div>
    </div>

    <div class="tips-card">
      <h3>使用说明</h3>
      <ul>
        <li><strong>DeepSeek</strong>：默认配置即可使用，需在DeepSeek官网获取API Key</li>
        <li><strong>智谱AI</strong>：需在智谱AI官网注册并获取API Key</li>
        <li><strong>OpenAI</strong>：需在OpenAI官网注册并获取API Key</li>
        <li><strong>自定义</strong>：支持其他兼容OpenAI接口的AI服务</li>
        <li>API Key是您的个人密钥，请妥善保管，不要泄露给他人</li>
        <li>删除配置后将使用系统默认配置</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Delete, Check } from '@element-plus/icons-vue'
import { getMe, updateAIConfig, type User as UserType } from '../api/auth'

const router = useRouter()
const saving = ref(false)
const clearing = ref(false)

const aiConfig = reactive({
  provider: '',
  apiKey: '',
  baseUrl: '',
  model: ''
})

const providerDefaults: Record<string, { baseUrl: string; model: string; label: string }> = {
  deepseek: {
    baseUrl: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    label: 'DeepSeek'
  },
  zhipu: {
    baseUrl: 'https://open.bigmodel.cn/api/paas/v4',
    model: 'glm-4',
    label: '智谱AI'
  },
  openai: {
    baseUrl: 'https://api.openai.com/v1',
    model: 'gpt-3.5-turbo',
    label: 'OpenAI'
  },
  custom: {
    baseUrl: '',
    model: '',
    label: '自定义'
  }
}

const hasConfig = computed(() => {
  return aiConfig.apiKey
})

function getProviderLabel(provider: string) {
  return providerDefaults[provider]?.label || '未选择'
}

function maskApiKey(apiKey: string) {
  if (!apiKey) return '未设置'
  if (apiKey.length <= 8) return apiKey
  return apiKey.slice(0, 4) + '****' + apiKey.slice(-4)
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
    }
    if (user.ai_api_key) {
      aiConfig.apiKey = user.ai_api_key
    }
    if (user.ai_api_base_url) {
      aiConfig.baseUrl = user.ai_api_base_url
    }
    if (user.ai_api_model) {
      aiConfig.model = user.ai_api_model
    }
    if (aiConfig.provider && !aiConfig.baseUrl && !aiConfig.model) {
      handleProviderChange()
    }
  } catch {
    // ignore
  }
}

async function saveAIConfig() {
  if (!aiConfig.provider) {
    ElMessage.warning('请选择AI服务提供商')
    return
  }
  if (!aiConfig.apiKey) {
    ElMessage.warning('请输入API Key')
    return
  }

  saving.value = true
  try {
    await updateAIConfig({
      ai_api_provider: aiConfig.provider,
      ai_api_key: aiConfig.apiKey,
      ai_api_base_url: aiConfig.baseUrl,
      ai_api_model: aiConfig.model
    })
    ElMessage.success('AI配置保存成功')
    setTimeout(() => {
      router.push('/dashboard/ai')
    }, 1000)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function clearAIConfig() {
  clearing.value = true
  try {
    await updateAIConfig({
      ai_api_provider: '',
      ai_api_key: '',
      ai_api_base_url: '',
      ai_api_model: ''
    })
    aiConfig.provider = ''
    aiConfig.apiKey = ''
    aiConfig.baseUrl = ''
    aiConfig.model = ''
    ElMessage.success('AI配置已删除')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  } finally {
    clearing.value = false
  }
}

function goBack() {
  router.push('/dashboard/ai')
}

onMounted(() => {
  loadAIConfig()
})
</script>

<style scoped>
.ai-config-page {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.config-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 24px;
  margin-bottom: 20px;
}

.config-section {
  margin-bottom: 24px;
}

.config-section:last-child {
  margin-bottom: 0;
}

.config-section h3 {
  margin: 0 0 16px;
  font-size: 16px;
  color: #333;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 8px;
}

.provider-options {
  display: flex;
  gap: 8px;
}

.config-form {
  padding: 16px 0;
}

.current-config {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
}

.config-item {
  display: flex;
  margin-bottom: 12px;
  font-size: 14px;
}

.config-item:last-child {
  margin-bottom: 0;
}

.config-item .label {
  font-weight: 600;
  color: #666;
  width: 120px;
}

.config-item .value {
  color: #333;
  flex: 1;
  word-break: break-all;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e0e0e0;
}

.tips-card {
  background: #fef9f5;
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid #f5a623;
}

.tips-card h3 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #333;
}

.tips-card ul {
  margin: 0;
  padding-left: 20px;
}

.tips-card li {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.tips-card li:last-child {
  margin-bottom: 0;
}

.tips-card strong {
  color: #333;
}
</style>
