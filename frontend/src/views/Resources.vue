<template>
  <div class="resources-page">
    <div class="page-header">
      <h2>资料管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="triggerUpload">
          <el-icon><Plus /></el-icon>上传资料
        </el-button>
        <input
          ref="fileInput"
          type="file"
          accept=".pdf,.doc,.docx,.txt,.md"
          class="hidden-input"
          @change="handleFileSelect"
        />
      </div>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索文件名..."
        clearable
        @keyup.enter="handleSearch"
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button @click="handleSearch">搜索</el-button>
    </div>

    <div v-if="resources.length > 0" class="resources-grid">
      <el-card
        v-for="resource in resources"
        :key="resource.id"
        class="resource-card"
        @click="openResourceDetail(resource)"
      >
        <div class="resource-icon">
          {{ getFileIcon(resource.file_type) }}
        </div>
        <div class="resource-info">
          <div class="resource-name">{{ resource.filename }}</div>
          <div class="resource-meta">
            <span>{{ getFileSize(resource.file_size) }}</span>
            <span>{{ formatDate(resource.upload_date) }}</span>
          </div>
        </div>
        <div class="resource-actions">
          <el-button type="text" size="small" @click.stop="handleQA(resource)">
            <el-icon><Message /></el-icon>
          </el-button>
          <el-button type="text" size="small" @click.stop="handleDelete(resource.id)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </el-card>
    </div>
    <div v-else class="empty-tip">
      <el-icon><FolderOpened /></el-icon>暂无资料，点击上方按钮上传
    </div>

    <el-dialog
      v-model="showDetail"
      :title="selectedResource?.filename || '资料详情'"
      width="600px"
    >
      <div v-if="selectedResource" class="detail-content">
        <div class="detail-row">
          <span class="detail-label">文件类型：</span>
          <span>{{ selectedResource.file_type.toUpperCase() }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">文件大小：</span>
          <span>{{ getFileSize(selectedResource.file_size) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">上传时间：</span>
          <span>{{ formatDate(selectedResource.upload_date) }}</span>
        </div>
        <div class="qa-section">
          <h4>智能问答</h4>
          <el-input
            v-model="qaQuestion"
            placeholder="输入您的问题..."
            clearable
          >
            <template #append>
              <el-button @click="handleAskQA">提问</el-button>
            </template>
          </el-input>
          <div v-if="qaAnswer" class="qa-answer">
            <div class="answer-header">回答</div>
            <div class="answer-content">{{ qaAnswer }}</div>
            <div v-if="qaSource" class="answer-source">来源：{{ qaSource }}</div>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="showUploadDialog"
      title="确认上传"
      width="400px"
    >
      <div v-if="selectedFile" class="upload-dialog-content">
        <div class="upload-icon">📁</div>
        <div class="upload-info">
          <div class="upload-filename">{{ selectedFile.name }}</div>
          <div class="upload-size">{{ getFileSize(selectedFile.size) }}</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="cancelUpload">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="confirmUpload">
          {{ uploading ? '上传中...' : '确认上传' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Message, Delete, FolderOpened } from '@element-plus/icons-vue'
import {
  uploadResource, getResources, deleteResource, searchResources, resourceQA,
  type Resource
} from '../api/resources'

const resources = ref<Resource[]>([])
const searchQuery = ref('')
const showDetail = ref(false)
const selectedResource = ref<Resource | null>(null)
const qaQuestion = ref('')
const qaAnswer = ref('')
const qaSource = ref('')

const fileInput = ref<HTMLInputElement | null>(null)
const showUploadDialog = ref(false)
const selectedFile = ref<File | null>(null)
const uploading = ref(false)

function getFileIcon(fileType: string) {
  const icons: Record<string, string> = {
    pdf: '📄',
    doc: '📝',
    docx: '📝',
    txt: '📄',
    md: '📝'
  }
  return icons[fileType] || '📁'
}

function getFileSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function loadResources() {
  try {
    resources.value = await getResources()
  } catch {
    resources.value = []
  }
}

function triggerUpload() {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0]
    showUploadDialog.value = true
  }
}

async function confirmUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  try {
    await uploadResource(selectedFile.value)
    ElMessage.success('上传成功')
    await loadResources()
    showUploadDialog.value = false
    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || 
                     error.message || 
                     '上传失败，请检查网络连接或文件大小'
    ElMessage.error(errorMsg)
    console.error('上传错误:', error)
  } finally {
    uploading.value = false
  }
}

function cancelUpload() {
  showUploadDialog.value = false
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

async function handleSearch() {
  try {
    if (searchQuery.value.trim()) {
      resources.value = await searchResources(searchQuery.value.trim())
    } else {
      await loadResources()
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '搜索失败')
  }
}

function openResourceDetail(resource: Resource) {
  selectedResource.value = resource
  qaQuestion.value = ''
  qaAnswer.value = ''
  qaSource.value = ''
  showDetail.value = true
}

async function handleQA(resource: Resource) {
  selectedResource.value = resource
  qaQuestion.value = ''
  qaAnswer.value = ''
  qaSource.value = ''
  showDetail.value = true
}

async function handleAskQA() {
  if (!selectedResource.value || !qaQuestion.value.trim()) {
    ElMessage.warning('请先选择资料并输入问题')
    return
  }
  try {
    const result = await resourceQA(selectedResource.value.id, qaQuestion.value.trim())
    qaAnswer.value = result.answer
    qaSource.value = result.source || ''
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提问失败')
  }
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除该资料吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteResource(id)
    ElMessage.success('删除成功')
    await loadResources()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

loadResources()
</script>

<style scoped>
.resources-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input {
  width: 300px;
}

.resources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.resource-card {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.resource-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.resource-icon {
  font-size: 32px;
}

.resource-info {
  flex: 1;
  min-width: 0;
}

.resource-name {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.resource-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.resource-actions {
  display: flex;
  gap: 8px;
}

.empty-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 40px;
  background: #f5f7fa;
  border-radius: 8px;
  color: #909399;
  justify-content: center;
}

.detail-content {
  padding: 10px 0;
}

.detail-row {
  display: flex;
  margin-bottom: 12px;
  font-size: 14px;
}

.detail-label {
  font-weight: 600;
  width: 100px;
  color: #666;
}

.qa-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.qa-section h4 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #333;
}

.qa-answer {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.answer-header {
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.answer-content {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

.answer-source {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.hidden-input {
  display: none;
}

.upload-dialog-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 0;
}

.upload-icon {
  font-size: 48px;
}

.upload-info {
  flex: 1;
}

.upload-filename {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.upload-size {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}
</style>