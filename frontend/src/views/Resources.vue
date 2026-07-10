<template>
  <div class="resources">
    <div class="toolbar">
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>
        上传资料
      </el-button>
      <div class="search-box">
        <el-input v-model="searchQuery" placeholder="搜索资料" @keyup.enter="handleSearch">
          <template #append>
            <el-icon @click="handleSearch"><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>
    <div class="resources-grid">
      <el-empty v-if="resources.length === 0" description="暂无资料" />
      <div v-else class="resource-cards">
        <div v-for="item in resources" :key="item.id" class="resource-card">
          <div class="card-icon">
            <el-icon><FileText /></el-icon>
          </div>
          <div class="card-info">
            <p class="filename">{{ item.filename }}</p>
            <p class="file-info">{{ item.file_type }} · {{ formatSize(item.file_size) }}</p>
            <p class="upload-date">{{ item.upload_date }}</p>
          </div>
          <div class="card-actions">
            <el-button size="small" @click="downloadResource(item)">下载</el-button>
            <el-button size="small" type="danger" @click="deleteResource(item)">删除</el-button>
          </div>
        </div>
      </div>
    </div>
    <div class="qa-section">
      <h3>智能问答</h3>
      <div class="qa-form">
        <el-input v-model="qaQuestion" placeholder="输入你的问题，系统将在资料中查找答案" type="textarea" :rows="3">
          <template #append>
            <el-button type="primary" @click="handleQA">提问</el-button>
          </template>
        </el-input>
      </div>
      <div class="qa-result" v-if="qaAnswer">
        <div class="answer-header">
          <span class="answer-label">答案：</span>
          <span class="answer-source">来源：{{ qaAnswer.source }}</span>
        </div>
        <p class="answer-content">{{ qaAnswer.content }}</p>
      </div>
    </div>
    <el-dialog title="上传资料" v-model="showUploadDialog" width="500px">
      <el-form>
        <el-form-item label="文件">
          <el-upload
            class="upload-demo"
            action="/api/resources/upload"
            :on-success="handleUploadSuccess"
            :on-error="handleUploadError"
          >
            <el-button type="primary">点击上传</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Search, FileText } from '@element-plus/icons-vue'

const resources = ref<any[]>([])
const showUploadDialog = ref(false)
const searchQuery = ref('')
const qaQuestion = ref('')
const qaAnswer = ref<any>(null)

function formatSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function handleSearch() {
  ElMessage.info('搜索功能开发中')
}

function downloadResource(item: any) {
  ElMessage.info(`下载 ${item.filename}`)
}

async function deleteResource(item: any) {
  try {
    await ElMessageBox.confirm('确定要删除这个文件吗？', '提示', { type: 'warning' })
    ElMessage.success('删除成功')
  } catch {
    // 用户取消
  }
}

function handleQA() {
  if (!qaQuestion.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  qaAnswer.value = {
    content: '这是一个模拟回答。根据你的问题，系统会在上传的资料中进行全文检索，查找相关知识点并生成答案。如果本地资料中找不到答案，系统会自动触发网络查询。',
    source: '本地资料'
  }
}

function handleUploadSuccess() {
  ElMessage.success('上传成功')
  showUploadDialog.value = false
}

function handleUploadError() {
  ElMessage.error('上传失败')
}
</script>

<style scoped>
.resources {
  padding: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.search-box {
  width: 400px;
}

.resource-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.resource-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-icon {
  width: 50px;
  height: 50px;
  background: #f0f9ff;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #3b82f6;
}

.card-info {
  flex: 1;
}

.filename {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: bold;
  color: #333;
}

.file-info,
.upload-date {
  margin: 0;
  font-size: 12px;
  color: #999;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.qa-section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-top: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.qa-section h3 {
  margin: 0 0 20px;
  font-size: 16px;
  color: #333;
}

.qa-form {
  margin-bottom: 20px;
}

.qa-result {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.answer-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.answer-label {
  font-weight: bold;
  color: #333;
}

.answer-source {
  font-size: 12px;
  color: #666;
}

.answer-content {
  margin: 0;
  color: #333;
  line-height: 1.6;
}
</style>