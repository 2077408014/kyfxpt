<template>
  <div class="recommend-page">
    <div class="page-header">
      <h2>智能推荐</h2>
      <el-button type="primary" @click="handleGenerate">
        <el-icon><Refresh /></el-icon>生成推荐题目
      </el-button>
    </div>

    <div class="stats-row">
      <el-card class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-info">
          <div class="stat-value">{{ report.total_recommendations }}</div>
          <div class="stat-label">推荐总数</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-value">{{ report.completed_recommendations }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-icon">🎯</div>
        <div class="stat-info">
          <div class="stat-value">{{ report.accuracy_rate }}%</div>
          <div class="stat-label">正确率</div>
        </div>
      </el-card>
    </div>

    <div class="section">
      <h3>薄弱知识点分析</h3>
      <div v-if="weakPoints.length > 0" class="weak-points-list">
        <el-tag
          v-for="wp in weakPoints"
          :key="`${wp.subject}-${wp.knowledge_point}`"
          :type="getWeakLevelType(wp.weak_level)"
          class="weak-point-tag"
        >
          {{ wp.subject }} - {{ wp.knowledge_point }}
          <span class="weak-count">错误{{ wp.mistake_count }}次</span>
        </el-tag>
      </div>
      <div v-else class="empty-tip">
        <el-icon><InfoFilled /></el-icon>暂无薄弱知识点数据，请先添加错题
      </div>
    </div>

    <div class="section">
      <h3>待做推荐题目</h3>
      <div v-if="pendingRecommendations.length > 0" class="recommendation-list">
        <el-card
          v-for="rec in pendingRecommendations"
          :key="rec.id"
          class="recommendation-card"
        >
          <div class="rec-header">
            <el-tag>{{ rec.subject }}</el-tag>
            <el-tag :type="getDifficultyType(rec.difficulty)">{{ rec.difficulty }}</el-tag>
            <el-tag size="small">{{ rec.source }}</el-tag>
          </div>
          <div class="rec-question">
            <span class="question-label">题目：</span>
            {{ rec.question_text }}
          </div>
          <div class="rec-answer" v-if="showAnswers[rec.id]">
            <div class="answer-section">
              <span class="answer-label">答案：</span>
              {{ rec.answer }}
            </div>
            <div class="analysis-section" v-if="rec.analysis">
              <span class="analysis-label">解析：</span>
              {{ rec.analysis }}
            </div>
          </div>
          <div class="rec-actions">
            <el-button
              v-if="!showAnswers[rec.id]"
              type="primary"
              @click="showAnswers[rec.id] = true"
            >
              查看答案
            </el-button>
            <div v-else class="result-buttons">
              <el-button type="success" @click="handleComplete(rec.id, '正确')">
                <el-icon><Check /></el-icon>正确
              </el-button>
              <el-button type="danger" @click="handleComplete(rec.id, '错误')">
                <el-icon><Close /></el-icon>错误
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
      <div v-else class="empty-tip">
        <el-icon><InfoFilled /></el-icon>暂无待做推荐题目，点击上方按钮生成
      </div>
    </div>

    <div class="section">
      <h3>已完成题目</h3>
      <div v-if="completedRecommendations.length > 0" class="completed-list">
        <el-table :data="completedRecommendations" border>
          <el-table-column prop="subject" label="科目" width="100" />
          <el-table-column prop="knowledge_point" label="知识点" width="120" />
          <el-table-column prop="question_text" label="题目" show-overflow-tooltip />
          <el-table-column prop="result" label="结果" width="80">
            <template #default="scope">
              <el-tag :type="scope.row.result === '正确' ? 'success' : 'danger'">
                {{ scope.row.result }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="source" label="来源" width="80" />
        </el-table>
      </div>
      <div v-else class="empty-tip">
        <el-icon><InfoFilled /></el-icon>暂无已完成题目
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, InfoFilled, Check, Close } from '@element-plus/icons-vue'
import {
  analyzeWeakPoints, generateRecommendations, getRecommendations,
  completeRecommendation, getRecommendationReport,
  type Recommendation, type WeakPoint, type RecommendationReport
} from '../api/recommendation'

const weakPoints = ref<WeakPoint[]>([])
const recommendations = ref<Recommendation[]>([])
const report = reactive<RecommendationReport>({
  total_recommendations: 0,
  completed_recommendations: 0,
  correct_recommendations: 0,
  accuracy_rate: 0,
  weak_points: []
})
const showAnswers = reactive<Record<number, boolean>>({})

const pendingRecommendations = computed(() => recommendations.value.filter((r: Recommendation) => !r.completed))
const completedRecommendations = computed(() => recommendations.value.filter((r: Recommendation) => r.completed))

function getWeakLevelType(level: number) {
  if (level >= 4) return 'danger'
  if (level >= 3) return 'warning'
  return 'info'
}

function getDifficultyType(difficulty: string) {
  switch (difficulty) {
    case '困难': return 'danger'
    case '中等': return 'warning'
    default: return 'success'
  }
}

async function loadData() {
  try {
    weakPoints.value = await analyzeWeakPoints()
    recommendations.value = await getRecommendations()
    const data = await getRecommendationReport()
    Object.assign(report, data)
  } catch {
    recommendations.value = []
  }
}

async function handleGenerate() {
  try {
    const newRecs = await generateRecommendations(5)
    recommendations.value = [...newRecs, ...recommendations.value]
    const data = await getRecommendationReport()
    Object.assign(report, data)
    ElMessage.success(`成功生成 ${newRecs.length} 道推荐题目`)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '生成失败')
  }
}

async function handleComplete(id: number, result: string) {
  try {
    await completeRecommendation(id, result)
    showAnswers[id] = false
    await loadData()
    ElMessage.success(`已标记为${result}`)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.recommend-page {
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

.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 32px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.section {
  margin-bottom: 24px;
}

.section h3 {
  margin: 0 0 16px;
  font-size: 16px;
  color: #333;
}

.weak-points-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.weak-point-tag {
  padding: 8px 16px;
}

.weak-count {
  margin-left: 8px;
  font-size: 12px;
  opacity: 0.8;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recommendation-card {
  padding: 16px;
}

.rec-header {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.rec-question {
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 12px;
}

.question-label {
  font-weight: 600;
  color: #333;
}

.rec-answer {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 12px;
}

.answer-section, .analysis-section {
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.answer-section:last-child, .analysis-section:last-child {
  margin-bottom: 0;
}

.answer-label, .analysis-label {
  font-weight: 600;
  color: #333;
}

.rec-actions {
  display: flex;
  justify-content: flex-end;
}

.result-buttons {
  display: flex;
  gap: 8px;
}

.completed-list {
  max-height: 400px;
  overflow-y: auto;
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
</style>