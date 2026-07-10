<template>
  <div class="words">
    <div class="stats-section">
      <div class="stat-card">
        <p class="stat-value">{{ wordStats.total }}</p>
        <p class="stat-label">词汇总量</p>
      </div>
      <div class="stat-card">
        <p class="stat-value">{{ wordStats.studied }}</p>
        <p class="stat-label">已学单词</p>
      </div>
      <div class="stat-card">
        <p class="stat-value">{{ wordStats.mastered }}</p>
        <p class="stat-label">已掌握</p>
      </div>
      <div class="stat-card">
        <p class="stat-value">{{ wordStats.today }}</p>
        <p class="stat-label">今日学习</p>
      </div>
    </div>
    <div class="plan-section">
      <h3>学习计划</h3>
      <div class="plan-form">
        <el-form :inline="true">
          <el-form-item label="每日学习量">
            <el-slider v-model="dailyCount" :min="5" :max="100" :step="5" />
            <span>{{ dailyCount }} 词</span>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="savePlan">保存计划</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
    <div class="study-section">
      <h3>今日单词</h3>
      <div v-if="currentWord" class="word-card">
        <div class="word-header">
          <span class="word-number">{{ currentIndex + 1 }} / {{ todayWords.length }}</span>
          <span class="word-tag">{{ currentWord.exam_requirement }}</span>
        </div>
        <h2 class="word">{{ currentWord.word }}</h2>
        <p class="phonetic">{{ currentWord.phonetic }}</p>
        <div class="word-actions">
          <el-button @click="showMeaning = !showMeaning">{{ showMeaning ? '隐藏释义' : '显示释义' }}</el-button>
          <el-button @click="playAudio">发音</el-button>
        </div>
        <div v-if="showMeaning" class="word-detail">
          <p class="meaning">{{ currentWord.meaning }}</p>
          <p v-if="currentWord.example_sentence" class="example">例句：{{ currentWord.example_sentence }}</p>
        </div>
        <div class="study-buttons">
          <el-button type="danger" @click="markResult('错误')">不认识</el-button>
          <el-button type="warning" @click="markResult('模糊')">模糊</el-button>
          <el-button type="success" @click="markResult('认识')">认识</el-button>
        </div>
      </div>
      <div v-else class="empty-state">
        <el-empty description="今日单词已学完" />
        <el-button type="primary" @click="startReview">开始复习</el-button>
      </div>
    </div>
    <div class="review-section">
      <h3>待复习单词</h3>
      <el-table :data="reviewWords" border>
        <el-table-column prop="word" label="单词" />
        <el-table-column prop="mastery_level" label="掌握程度" width="120">
          <template #default="scope">
            <el-tag :type="getMasteryTagType(scope.row.mastery_level)">
              {{ scope.row.mastery_level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="next_review_date" label="下次复习" width="140" />
        <el-table-column prop="review_count" label="复习次数" width="100" />
      </el-table>
    </div>
    <div class="report-section">
      <h3>学习报告</h3>
      <div class="chart-container">
        <el-empty description="图表功能开发中" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const wordStats = reactive({
  total: 5500,
  studied: 1200,
  mastered: 450,
  today: 20
})

const dailyCount = ref(20)
const todayWords = ref<any[]>([])
const currentIndex = ref(0)
const showMeaning = ref(false)
const reviewWords = ref<any[]>([])

const currentWord = ref<any>(null)

function getMasteryTagType(level: string) {
  switch (level) {
    case '陌生': return 'danger'
    case '认识': return 'warning'
    case '熟悉': return 'info'
    case '掌握': return 'success'
    default: return 'info'
  }
}

function savePlan() {
  ElMessage.success(`学习计划已保存：每日${dailyCount.value}词`)
}

function playAudio() {
  ElMessage.info('发音功能开发中')
}

function markResult(result: string) {
  if (result === '认识') {
    wordStats.mastered++
  }
  wordStats.today++
  if (currentIndex.value < todayWords.value.length - 1) {
    currentIndex.value++
    currentWord.value = todayWords.value[currentIndex.value]
    showMeaning.value = false
  } else {
    currentWord.value = null
    ElMessage.success('今日单词学习完成！')
  }
}

function startReview() {
  ElMessage.info('复习功能开发中')
}

onMounted(() => {
  todayWords.value = [
    { id: 1, word: 'abandon', phonetic: '/əˈbændən/', meaning: 'v. 放弃，抛弃', example_sentence: 'He decided to abandon the project.', exam_requirement: '高频词' },
    { id: 2, word: 'ability', phonetic: '/əˈbɪləti/', meaning: 'n. 能力，才能', example_sentence: 'She has the ability to learn quickly.', exam_requirement: '考纲词' },
    { id: 3, word: 'absolute', phonetic: '/ˈæbsəluːt/', meaning: 'adj. 绝对的，完全的', example_sentence: 'This is an absolute truth.', exam_requirement: '考纲词' },
    { id: 4, word: 'absorb', phonetic: '/əbˈsɔːrb/', meaning: 'v. 吸收；吸引', example_sentence: 'Plants absorb carbon dioxide.', exam_requirement: '高频词' },
    { id: 5, word: 'abstract', phonetic: '/ˈæbstrækt/', meaning: 'adj. 抽象的 n. 摘要', example_sentence: 'Beauty is an abstract concept.', exam_requirement: '考纲词' }
  ]
  currentWord.value = todayWords.value[0]
  
  reviewWords.value = [
    { word: 'abandon', mastery_level: '熟悉', next_review_date: '2026-07-11', review_count: 3 },
    { word: 'ability', mastery_level: '掌握', next_review_date: '2026-07-14', review_count: 5 },
    { word: 'absolute', mastery_level: '认识', next_review_date: '2026-07-10', review_count: 2 },
    { word: 'absorb', mastery_level: '陌生', next_review_date: '2026-07-10', review_count: 1 }
  ]
})
</script>

<style scoped>
.words {
  padding: 20px;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  margin: 0;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin: 8px 0 0;
}

.plan-section,
.study-section,
.review-section,
.report-section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.plan-section h3,
.study-section h3,
.review-section h3,
.report-section h3 {
  margin: 0 0 20px;
  font-size: 16px;
  color: #333;
}

.word-card {
  text-align: center;
  padding: 40px;
  background: #fafafa;
  border-radius: 12px;
}

.word-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.word-number {
  font-size: 14px;
  color: #999;
}

.word-tag {
  padding: 4px 12px;
  background: #dbeafe;
  color: #3b82f6;
  border-radius: 4px;
  font-size: 12px;
}

.word {
  font-size: 48px;
  font-weight: bold;
  margin: 0 0 8px;
  color: #333;
}

.phonetic {
  font-size: 18px;
  color: #666;
  margin: 0 0 20px;
}

.word-actions {
  margin-bottom: 20px;
}

.word-detail {
  text-align: left;
  padding: 20px;
  background: white;
  border-radius: 8px;
  margin-bottom: 20px;
}

.meaning {
  font-size: 16px;
  color: #333;
  margin: 0 0 12px;
}

.example {
  font-size: 14px;
  color: #666;
  margin: 0;
  font-style: italic;
}

.study-buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.empty-state {
  text-align: center;
  padding: 40px;
}

.chart-container {
  height: 300px;
}
</style>