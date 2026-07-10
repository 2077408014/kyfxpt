<template>
  <div class="recommend">
    <div class="section">
      <h3>薄弱知识点分析</h3>
      <div class="weak-points">
        <el-empty v-if="weakPoints.length === 0" description="暂无薄弱知识点数据" />
        <el-table v-else :data="weakPoints" border>
          <el-table-column prop="subject" label="科目" width="100" />
          <el-table-column prop="knowledge_point" label="知识点" />
          <el-table-column prop="weak_level" label="薄弱等级" width="100">
            <template #default="scope">
              <el-tag :type="getWeakLevelType(scope.row.weak_level)">
                Lv.{{ scope.row.weak_level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="mistake_count" label="错误次数" width="100" />
        </el-table>
      </div>
    </div>
    <div class="section">
      <h3>智能推荐题目</h3>
      <div class="recommend-form">
        <el-form :inline="true" :model="recommendForm">
          <el-form-item label="科目">
            <el-select v-model="recommendForm.subject" placeholder="全部">
              <el-option label="数学" value="数学" />
              <el-option label="英语" value="英语" />
              <el-option label="政治" value="政治" />
              <el-option label="专业课" value="专业课" />
            </el-select>
          </el-form-item>
          <el-form-item label="难度">
            <el-select v-model="recommendForm.difficulty" placeholder="全部">
              <el-option label="基础" value="基础" />
              <el-option label="强化" value="强化" />
              <el-option label="冲刺" value="冲刺" />
            </el-select>
          </el-form-item>
          <el-form-item label="数量">
            <el-select v-model="recommendForm.count">
              <el-option label="5道" :value="5" />
              <el-option label="10道" :value="10" />
              <el-option label="20道" :value="20" />
              <el-option label="30道" :value="30" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="generateRecommend">生成推荐</el-button>
          </el-form-item>
        </el-form>
      </div>
      <div class="recommend-list">
        <el-empty v-if="recommendations.length === 0" description="暂无推荐题目" />
        <div v-else class="question-cards">
          <div v-for="item in recommendations" :key="item.id" class="question-card">
            <div class="card-header">
              <span class="tag subject">{{ item.subject }}</span>
              <span class="tag difficulty">{{ item.difficulty }}</span>
              <span class="tag source">{{ item.source }}</span>
              <span v-if="item.completed" class="tag completed">已完成</span>
            </div>
            <p class="question-text">{{ item.question_text }}</p>
            <div class="card-actions">
              <el-button @click="showAnswer(item)">查看答案</el-button>
              <el-button v-if="!item.completed" type="primary" @click="completeQuestion(item)">标记完成</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="section">
      <h3>学习报告</h3>
      <div class="report-cards">
        <div class="report-card">
          <p class="report-value">{{ report.total || 0 }}</p>
          <p class="report-label">推荐题目总数</p>
        </div>
        <div class="report-card">
          <p class="report-value">{{ report.completed || 0 }}</p>
          <p class="report-label">已完成</p>
        </div>
        <div class="report-card">
          <p class="report-value">{{ report.rate || '0' }}%</p>
          <p class="report-label">正确率</p>
        </div>
      </div>
    </div>
    <el-dialog title="答案解析" v-model="showAnswerDialog" width="600px">
      <div v-if="currentAnswer">
        <p class="question">{{ currentAnswer.question_text }}</p>
        <div class="answer-section">
          <h4>参考答案：</h4>
          <p>{{ currentAnswer.answer }}</p>
        </div>
        <div class="analysis-section">
          <h4>解析：</h4>
          <p>{{ currentAnswer.analysis || '暂无解析' }}</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const weakPoints = ref<any[]>([])
const recommendations = ref<any[]>([])
const showAnswerDialog = ref(false)
const currentAnswer = ref<any>(null)

const recommendForm = reactive({
  subject: '',
  difficulty: '',
  count: 10
})

const report = reactive({
  total: 0,
  completed: 0,
  rate: '0'
})

function getWeakLevelType(level: number) {
  if (level >= 4) return 'danger'
  if (level >= 2) return 'warning'
  return 'info'
}

function generateRecommend() {
  recommendations.value = [
    { id: 1, subject: '数学', knowledge_point: '微分方程', difficulty: '中等', source: '真题', question_text: '求微分方程 y\' + 2y = e^(-x) 的通解', answer: 'y = (x + C)e^(-2x)', analysis: '这是一阶线性微分方程，使用积分因子法求解...', completed: false },
    { id: 2, subject: '数学', knowledge_point: '微分方程', difficulty: '困难', source: '模拟题', question_text: '求解方程 y\'\' - 3y\' + 2y = e^x 的特解', answer: 'y* = (x^2/2)e^x', analysis: '这是二阶常系数非齐次线性微分方程...', completed: false },
    { id: 3, subject: '英语', knowledge_point: '阅读理解', difficulty: '中等', source: '真题', question_text: 'According to the passage, what is the main idea of the third paragraph?', answer: 'The importance of environmental protection', analysis: '根据第三段首句的主题句...', completed: false },
    { id: 4, subject: '政治', knowledge_point: '马克思主义原理', difficulty: '基础', source: '专项练习', question_text: '矛盾的普遍性和特殊性的关系是什么？', answer: '普遍性寓于特殊性之中，特殊性包含普遍性', analysis: '矛盾的普遍性即矛盾无处不在...', completed: false },
    { id: 5, subject: '数学', knowledge_point: '微积分', difficulty: '中等', source: '真题', question_text: '计算不定积分 ∫x^2 e^x dx', answer: '(x^2 - 2x + 2)e^x + C', analysis: '使用分部积分法...', completed: false }
  ]
  report.total = recommendations.value.length
  report.completed = recommendations.value.filter(r => r.completed).length
  ElMessage.success('推荐题目已生成')
}

function showAnswer(item: any) {
  currentAnswer.value = item
  showAnswerDialog.value = true
}

function completeQuestion(item: any) {
  item.completed = true
  report.completed++
  report.rate = Math.round((report.completed / report.total) * 100).toString()
  ElMessage.success('已标记完成')
}
</script>

<style scoped>
.recommend {
  padding: 20px;
}

.section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section h3 {
  margin: 0 0 20px;
  font-size: 16px;
  color: #333;
}

.recommend-form {
  margin-bottom: 20px;
}

.question-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.question-card {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
}

.card-header {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.tag {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.tag.subject {
  background: #dbeafe;
  color: #3b82f6;
}

.tag.difficulty {
  background: #fef3c7;
  color: #f59e0b;
}

.tag.source {
  background: #dcfce7;
  color: #22c55e;
}

.tag.completed {
  background: #e0e7ff;
  color: #6366f1;
}

.question-text {
  margin: 0 0 16px;
  font-size: 14px;
  line-height: 1.6;
}

.card-actions {
  display: flex;
  gap: 10px;
}

.report-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.report-card {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 12px;
}

.report-value {
  font-size: 32px;
  font-weight: bold;
  margin: 0;
  color: #333;
}

.report-label {
  font-size: 14px;
  color: #999;
  margin: 8px 0 0;
}

.question {
  font-size: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.answer-section,
.analysis-section {
  margin-bottom: 16px;
}

.answer-section h4,
.analysis-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #666;
}

.answer-section p,
.analysis-section p {
  margin: 0;
  padding: 8px;
  background: #f0f9ff;
  border-radius: 4px;
}
</style>