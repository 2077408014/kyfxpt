<template>
  <div class="mistakes">
    <div class="toolbar">
      <el-button type="primary" @click="showAddDialog = true">
        <el-icon><Plus /></el-icon>
        添加错题
      </el-button>
      <div class="filters">
        <el-select v-model="filters.subject" placeholder="科目" class="filter-select">
          <el-option label="数学" value="数学" />
          <el-option label="英语" value="英语" />
          <el-option label="政治" value="政治" />
          <el-option label="专业课" value="专业课" />
        </el-select>
        <el-select v-model="filters.mastery_level" placeholder="掌握程度" class="filter-select">
          <el-option label="生疏" value="生疏" />
          <el-option label="熟悉" value="熟悉" />
          <el-option label="掌握" value="掌握" />
        </el-select>
        <el-button @click="loadMistakes">筛选</el-button>
      </div>
    </div>
    <el-table :data="mistakes" border>
      <el-table-column prop="subject" label="科目" width="100" />
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
          <el-button @click="reviewMistake(scope.row)">重做</el-button>
          <el-button type="danger" @click="deleteMistake(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog title="添加错题" v-model="showAddDialog" width="600px">
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="100px">
        <el-form-item label="科目" prop="subject">
          <el-select v-model="addForm.subject">
            <el-option label="数学" value="数学" />
            <el-option label="英语" value="英语" />
            <el-option label="政治" value="政治" />
            <el-option label="专业课" value="专业课" />
          </el-select>
        </el-form-item>
        <el-form-item label="知识点" prop="knowledge_point">
          <el-input v-model="addForm.knowledge_point" />
        </el-form-item>
        <el-form-item label="错误类型" prop="error_type">
          <el-select v-model="addForm.error_type">
            <el-option label="概念错误" value="概念错误" />
            <el-option label="计算错误" value="计算错误" />
            <el-option label="审题错误" value="审题错误" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度" prop="difficulty">
          <el-select v-model="addForm.difficulty">
            <el-option label="简单" value="简单" />
            <el-option label="中等" value="中等" />
            <el-option label="困难" value="困难" />
          </el-select>
        </el-form-item>
        <el-form-item label="题目内容" prop="question_text">
          <el-input v-model="addForm.question_text" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="正确答案" prop="answer">
          <el-input v-model="addForm.answer" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="解析">
          <el-input v-model="addForm.analysis" type="textarea" :rows="3" />
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
    <el-dialog title="错题详情" v-model="showDetailDialog" width="600px">
      <div v-if="selectedMistake">
        <div class="detail-item">
          <span class="label">科目：</span>
          <span>{{ selectedMistake.subject }}</span>
        </div>
        <div class="detail-item">
          <span class="label">知识点：</span>
          <span>{{ selectedMistake.knowledge_point }}</span>
        </div>
        <div class="detail-item">
          <span class="label">错误类型：</span>
          <span>{{ selectedMistake.error_type }}</span>
        </div>
        <div class="detail-item">
          <span class="label">难度：</span>
          <span>{{ selectedMistake.difficulty }}</span>
        </div>
        <div class="detail-item">
          <span class="label">题目：</span>
          <p>{{ selectedMistake.question_text }}</p>
        </div>
        <div class="detail-item">
          <span class="label">答案：</span>
          <p>{{ selectedMistake.answer }}</p>
        </div>
        <div class="detail-item">
          <span class="label">解析：</span>
          <p>{{ selectedMistake.analysis || '暂无解析' }}</p>
        </div>
        <div class="detail-item">
          <span class="label">错误原因：</span>
          <p>{{ selectedMistake.error_reason || '暂无' }}</p>
        </div>
      </div>
    </el-dialog>
    <el-dialog title="重做错题" v-model="showReviewDialog" width="500px">
      <div v-if="reviewingMistake">
        <p class="question">{{ reviewingMistake.question_text }}</p>
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
import { Plus } from '@element-plus/icons-vue'
import { getMistakes, createMistake, deleteMistake, reviewMistake } from '../api/mistakes'

const mistakes = ref<any[]>([])
const showAddDialog = ref(false)
const showDetailDialog = ref(false)
const showReviewDialog = ref(false)
const selectedMistake = ref<any>(null)
const reviewingMistake = ref<any>(null)
const reviewResult = ref('')
const reviewNotes = ref('')
const addFormRef = ref()

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
  error_reason: ''
})

const addRules = {
  subject: [{ required: true, message: '请选择科目', trigger: 'change' }],
  knowledge_point: [{ required: true, message: '请输入知识点', trigger: 'blur' }],
  error_type: [{ required: true, message: '请选择错误类型', trigger: 'change' }],
  difficulty: [{ required: true, message: '请选择难度', trigger: 'change' }],
  question_text: [{ required: true, message: '请输入题目内容', trigger: 'blur' }],
  answer: [{ required: true, message: '请输入正确答案', trigger: 'blur' }]
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

async function handleAdd() {
  if (!addFormRef.value) return
  await addFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return
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
  showDetailDialog.value = true
}

function reviewMistake(mistake: any) {
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
    await reviewMistake(reviewingMistake.value.id, {
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

async function deleteMistake(mistake: any) {
  try {
    await ElMessageBox.confirm('确定要删除这个错题吗？', '提示', {
      type: 'warning'
    })
    await deleteMistake(mistake.id)
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

.question {
  font-size: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
}
</style>