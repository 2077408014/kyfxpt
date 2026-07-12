<template>
  <div class="mistakes">
    <div class="toolbar">
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        添加错题
      </el-button>
      <div class="filters">
        <el-select v-model="filters.subject" placeholder="科目" class="filter-select" clearable>
          <el-option label="数学" value="数学" />
          <el-option label="英语" value="英语" />
          <el-option label="政治" value="政治" />
          <el-option label="专业课" value="专业课" />
        </el-select>
        <el-select v-model="filters.mastery_level" placeholder="掌握程度" class="filter-select" clearable>
          <el-option label="生疏" value="生疏" />
          <el-option label="熟悉" value="熟悉" />
          <el-option label="掌握" value="掌握" />
        </el-select>
        <el-button @click="loadMistakes">筛选</el-button>
      </div>
    </div>
    <el-table :data="mistakes" border>
      <el-table-column prop="subject" label="科目" width="100" />
      <el-table-column label="图片" width="80">
        <template #default="scope">
          <el-image
            v-if="scope.row.image_path"
            :src="'/uploads/' + scope.row.image_path"
            :preview-src-list="['/uploads/' + scope.row.image_path]"
            fit="cover"
            style="width: 50px; height: 50px; border-radius: 4px"
          />
          <span v-else style="color: #ccc">无</span>
        </template>
      </el-table-column>
      <el-table-column prop="knowledge_point" label="知识点" />
      <el-table-column prop="error_type" label="错误类型" width="100" />
      <el-table-column prop="difficulty" label="难度" width="80" />
      <el-table-column prop="mastery_level" label="掌握程度" width="100">
        <template #default="scope">
          <el-tag :type="getMasteryTagType(scope.row.mastery_level)">
            {{ scope.row.mastery_level }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="next_review_date" label="下次复习" width="120" />
      <el-table-column prop="review_count" label="复习次数" width="100" />
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button @click="viewMistake(scope.row)">查看</el-button>
          <el-button @click="openReviewDialog(scope.row)">重做</el-button>
          <el-button type="danger" @click="handleDelete(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog title="添加错题" v-model="showAddDialog" width="650px">
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="100px">
        <el-form-item label="题目图片">
          <div class="upload-area" @paste="handlePaste">
            <el-upload
              :show-file-list="false"
              :before-upload="handleImageSelect"
              accept="image/jpeg,image/png,image/webp"
            >
              <div v-if="!addForm.image_path" class="upload-placeholder">
                <el-icon><Picture /></el-icon>
                <span>点击上传或粘贴题目图片</span>
              </div>
              <div v-else class="image-preview">
                <el-image
                  :src="'/uploads/' + addForm.image_path + '?t=' + Date.now()"
                  fit="contain"
                  class="preview-img"
                />
                <el-button size="small" type="danger" @click.stop="removeImage">移除</el-button>
              </div>
            </el-upload>
            <el-button
              v-if="addForm.image_path"
              type="primary"
              :loading="recognizing"
              @click="handleRecognize"
              style="margin-left: 12px"
            >
              AI识别
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="科目" prop="subject">
          <el-select v-model="addForm.subject" placeholder="请选择科目">
            <el-option label="数学" value="数学" />
            <el-option label="英语" value="英语" />
            <el-option label="政治" value="政治" />
            <el-option label="专业课" value="专业课" />
          </el-select>
        </el-form-item>
        <el-form-item label="知识点">
          <el-input v-model="addForm.knowledge_point" placeholder="可选，AI可自动识别" />
        </el-form-item>
        <el-form-item label="错误类型">
          <el-select v-model="addForm.error_type" placeholder="可选" clearable>
            <el-option label="概念错误" value="概念错误" />
            <el-option label="计算错误" value="计算错误" />
            <el-option label="审题错误" value="审题错误" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="addForm.difficulty" placeholder="可选" clearable>
            <el-option label="简单" value="简单" />
            <el-option label="中等" value="中等" />
            <el-option label="困难" value="困难" />
          </el-select>
        </el-form-item>
        <el-form-item label="题目内容">
          <el-input v-model="addForm.question_text" type="textarea" :rows="3" placeholder="可选，上传图片后点击AI识别可自动填充" />
        </el-form-item>
        <el-form-item label="正确答案">
          <el-input v-model="addForm.answer" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
        <el-form-item label="解析">
          <el-input v-model="addForm.analysis" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="错误原因">
          <el-input v-model="addForm.error_reason" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAdd">确认添加</el-button>
      </template>
    </el-dialog>
    <el-dialog title="错题详情" v-model="showDetailDialog" width="700px">
      <div v-if="selectedMistake">
        <div class="detail-item" v-if="selectedMistake.image_path">
          <span class="label">题目图片：</span>
          <el-image
            :src="'/uploads/' + selectedMistake.image_path"
            :preview-src-list="['/uploads/' + selectedMistake.image_path]"
            fit="contain"
            style="max-width: 100%; max-height: 300px; margin-top: 8px"
          />
        </div>
        <div class="detail-item">
          <span class="label">科目：</span>
          <span>{{ selectedMistake.subject }}</span>
        </div>
        <div class="detail-item">
          <span class="label">知识点：</span>
          <span>{{ selectedMistake.knowledge_point || '未填写' }}</span>
        </div>
        <div class="detail-item">
          <span class="label">错误类型：</span>
          <span>{{ selectedMistake.error_type || '未填写' }}</span>
        </div>
        <div class="detail-item">
          <span class="label">难度：</span>
          <span>{{ selectedMistake.difficulty || '未填写' }}</span>
        </div>
        <div class="detail-item">
          <span class="label">题目：</span>
          <p>{{ selectedMistake.question_text || '无' }}</p>
        </div>
        <div class="detail-item">
          <span class="label">答案：</span>
          <p>{{ selectedMistake.answer || '暂无' }}</p>
        </div>
        <div class="detail-item">
          <span class="label">解析：</span>
          <p>{{ selectedMistake.analysis || '暂无解析' }}</p>
        </div>
        <div class="detail-item">
          <span class="label">错误原因：</span>
          <p>{{ selectedMistake.error_reason || '暂无' }}</p>
        </div>
        <el-divider />
        <div class="similar-section">
          <div class="similar-header">
            <h4>同类题推荐</h4>
            <el-button size="small" @click="loadSimilarQuestions" :loading="loadingSimilar">
              加载推荐
            </el-button>
          </div>
          <div v-if="similarQuestions.length > 0" class="similar-list">
            <div v-for="item in similarQuestions" :key="item.id" class="similar-item">
              <div class="similar-info">
                <el-tag size="small">{{ item.subject }}</el-tag>
                <el-tag size="small" type="info" v-if="item.knowledge_point">
                  {{ item.knowledge_point }}
                </el-tag>
                <span class="similarity">
                  相似度: {{ (item.similarity_score * 100).toFixed(0) }}%
                </span>
              </div>
              <p class="similar-question">{{ item.question_text || '无题目文本' }}</p>
            </div>
          </div>
          <el-empty v-else-if="!loadingSimilar && hasLoadedSimilar" description="暂无同类题" />
        </div>
      </div>
    </el-dialog>
    <el-dialog title="重做错题" v-model="showReviewDialog" width="500px">
      <div v-if="reviewingMistake">
        <div v-if="reviewingMistake.image_path" class="review-image">
          <el-image
            :src="'/uploads/' + reviewingMistake.image_path"
            :preview-src-list="['/uploads/' + reviewingMistake.image_path]"
            fit="contain"
            style="max-width: 100%; max-height: 200px"
          />
        </div>
        <p class="question">{{ reviewingMistake.question_text || '无题目文本，请查看图片' }}</p>
        <el-form-item label="答题结果">
          <el-radio-group v-model="reviewResult">
            <el-radio label="正确" />
            <el-radio label="错误" />
            <el-radio label="部分正确" />
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="reviewNotes" type="textarea" :rows="2" />
        </el-form-item>
      </div>
      <template #footer>
        <el-button @click="showReviewDialog = false">取消</el-button>
        <el-button type="primary" @click="handleReview">确认提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Picture } from '@element-plus/icons-vue'
import {
  getMistakes, createMistake, deleteMistake as deleteMistakeApi,
  reviewMistake as reviewMistakeApi, uploadMistakeImage, recognizeMistake, getSimilarMistakes
} from '../api/mistakes'

const mistakes = ref<any[]>([])
const showAddDialog = ref(false)
const showDetailDialog = ref(false)
const showReviewDialog = ref(false)
const selectedMistake = ref<any>(null)
const reviewingMistake = ref<any>(null)
const reviewResult = ref('')
const reviewNotes = ref('')
const addFormRef = ref()
const recognizing = ref(false)
const similarQuestions = ref<any[]>([])
const loadingSimilar = ref(false)
const hasLoadedSimilar = ref(false)

const filters = reactive({
  subject: '',
  mastery_level: ''
})

const addForm = reactive({
  subject: '',
  knowledge_point: '',
  error_type: '',
  difficulty: '',
  question_text: '',
  answer: '',
  analysis: '',
  error_reason: '',
  image_path: ''
})

const addRules = {
  subject: [{ required: true, message: '请选择科目', trigger: 'change' }]
}

function getMasteryTagType(level: string) {
  switch (level) {
    case '生疏': return 'danger'
    case '熟悉': return 'warning'
    case '掌握': return 'success'
    default: return 'info'
  }
}

async function loadMistakes() {
  const params: Record<string, string> = {}
  if (filters.subject) params.subject = filters.subject
  if (filters.mastery_level) params.mastery_level = filters.mastery_level
  mistakes.value = await getMistakes(params)
}

onMounted(loadMistakes)

async function handleImageSelect(file: File): Promise<boolean> {
  try {
    const result = await uploadMistakeImage(file)
    addForm.image_path = result.image_path
    ElMessage.success('图片上传成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '图片上传失败')
  }
  return false
}

async function handlePaste(event: ClipboardEvent) {
  const items = event.clipboardData?.items
  if (!items) return

  for (const item of items) {
    if (item.type.startsWith('image/')) {
      event.preventDefault()
      const file = item.getAsFile()
      if (file) {
        await handleImageSelect(file)
        return
      }
    }
  }

  const files = event.clipboardData?.files
  if (files && files.length > 0) {
    const imageFile = Array.from(files).find(f => f.type.startsWith('image/'))
    if (imageFile) {
      event.preventDefault()
      await handleImageSelect(imageFile)
    }
  }
}

function removeImage() {
  addForm.image_path = ''
}

async function handleRecognize() {
  if (!addForm.image_path) {
    ElMessage.warning('请先上传题目图片')
    return
  }
  recognizing.value = true
  try {
    const result = await recognizeMistake(addForm.image_path)
    if (result.question_text) addForm.question_text = result.question_text
    if (result.subject) addForm.subject = result.subject
    if (result.knowledge_point) addForm.knowledge_point = result.knowledge_point
    ElMessage.success(`AI识别完成，置信度: ${(result.confidence * 100).toFixed(0)}%`)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'AI识别失败')
  } finally {
    recognizing.value = false
  }
}

async function handleAdd() {
  if (!addFormRef.value) return
  await addFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    if (!addForm.question_text && !addForm.image_path) {
      ElMessage.warning('请输入题目内容或上传题目图片')
      return
    }
    try {
      await createMistake(addForm)
      ElMessage.success('添加成功')
      showAddDialog.value = false
      loadMistakes()
      Object.keys(addForm).forEach(key => addForm[key as keyof typeof addForm] = '')
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '添加失败')
    }
  })
}

function viewMistake(mistake: any) {
  selectedMistake.value = mistake
  similarQuestions.value = []
  hasLoadedSimilar.value = false
  showDetailDialog.value = true
}

async function loadSimilarQuestions() {
  if (!selectedMistake.value) return
  loadingSimilar.value = true
  try {
    similarQuestions.value = await getSimilarMistakes(selectedMistake.value.id)
    hasLoadedSimilar.value = true
  } catch (error: any) {
    ElMessage.error('加载推荐失败')
  } finally {
    loadingSimilar.value = false
  }
}

function openReviewDialog(mistake: any) {
  reviewingMistake.value = mistake
  reviewResult.value = ''
  reviewNotes.value = ''
  showReviewDialog.value = true
}

async function handleReview() {
  if (!reviewResult.value) {
    ElMessage.warning('请选择答题结果')
    return
  }
  try {
    await reviewMistakeApi(reviewingMistake.value.id, {
      result: reviewResult.value,
      notes: reviewNotes.value
    })
    ElMessage.success('提交成功')
    showReviewDialog.value = false
    loadMistakes()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '提交失败')
  }
}

async function handleDelete(mistake: any) {
  try {
    await ElMessageBox.confirm('确定要删除这个错题吗？', '提示', {
      type: 'warning'
    })
    await deleteMistakeApi(mistake.id)
    ElMessage.success('删除成功')
    loadMistakes()
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.mistakes {
  padding: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filters {
  display: flex;
  gap: 12px;
}

.filter-select {
  width: 120px;
}

.upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.upload-placeholder {
  width: 200px;
  height: 120px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #909399;
  cursor: pointer;
}

.upload-placeholder .el-icon {
  font-size: 28px;
}

.image-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.preview-img {
  width: 200px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
}

.detail-item {
  margin-bottom: 12px;
}

.detail-item .label {
  font-weight: bold;
  color: #666;
}

.detail-item p {
  margin: 4px 0 0;
  color: #333;
}

.similar-section {
  margin-top: 8px;
}

.similar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.similar-header h4 {
  margin: 0;
  font-size: 15px;
  color: #333;
}

.similar-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.similar-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.similar-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.similarity {
  font-size: 12px;
  color: #999;
}

.similar-question {
  margin: 0;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

.review-image {
  margin-bottom: 16px;
  text-align: center;
}

.question {
  font-size: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
}
</style>
