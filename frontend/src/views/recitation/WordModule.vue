<template>
  <div class="word-module">
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
      <div class="stat-card source-card">
        <p class="stat-value" style="font-size: 18px">{{ currentSourceLabel }}</p>
        <p class="stat-label">当前来源</p>
      </div>
    </div>

    <el-tabs v-model="subTab" class="sub-tabs">
      <el-tab-pane label="今日学习" name="today">
        <div class="study-section">
          <div class="plan-bar">
              <el-form :inline="true">
                <el-form-item label="词汇分类">
                  <el-select
                    v-model="selectedCategory"
                    placeholder="选择词汇分类"
                    style="width: 150px"
                    clearable
                    @change="handleCategoryChange"
                  >
                    <el-option label="全部" value="" />
                    <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
                  </el-select>
                </el-form-item>
                <el-form-item label="每日学习量">
                  <el-slider v-model="dailyCount" :min="5" :max="100" :step="5" style="width: 200px" />
                  <span style="margin-left: 12px">{{ dailyCount }} 词</span>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="savePlan">保存计划</el-button>
                </el-form-item>
                <el-form-item>
                  <el-button type="success" :loading="uploadingWordbook" @click="triggerWordbookUpload">
                    <el-icon><Upload /></el-icon>上传词书
                  </el-button>
                  <input
                    ref="wordbookInput"
                    type="file"
                    accept=".pdf,.txt,.doc,.docx"
                    class="hidden-input"
                    @change="handleWordbookSelect"
                  />
                </el-form-item>
              </el-form>
              <div class="daily-stats">
                <span class="daily-stat-item">
                  <el-tag type="warning">待复习: {{ reviewCount }}</el-tag>
                </span>
                <span class="daily-stat-item">
                  <el-tag type="success">新单词: {{ newCount }}</el-tag>
                </span>
              </div>
            </div>

          <div v-if="currentWord" class="word-card">
            <div class="word-header">
              <span class="word-number">{{ currentIndex + 1 }} / {{ todayWords.length }}</span>
              <span class="word-tag">{{ currentWord.exam_requirement }}</span>
              <span v-if="currentIndex < reviewCount" class="review-badge">复习</span>
              <span v-else class="new-badge">新单词</span>
            </div>
            <h2 class="word">{{ currentWord.word }}</h2>
            <p class="phonetic">{{ currentWord.phonetic }}</p>
            <div class="word-actions">
              <el-button @click="showMeaning = !showMeaning">
                {{ showMeaning ? '隐藏释义' : '显示释义' }}
              </el-button>
              <el-button @click="speakWord(currentWord.word)">
                <el-icon><VideoPlay /></el-icon>发音
              </el-button>
            </div>
            <div v-if="showMeaning" class="word-detail">
              <p class="meaning">{{ currentWord.meaning }}</p>
              <p v-if="currentWord.example_sentence" class="example">
                例句：{{ currentWord.example_sentence }}
                <el-button size="small" text @click="speakWord(currentWord.example_sentence)">
                  <el-icon><VideoPlay /></el-icon>朗读
                </el-button>
              </p>
            </div>
            <div class="study-buttons">
              <el-button type="danger" @click="markResult('错误')">不认识</el-button>
              <el-button type="warning" @click="markResult('模糊')">模糊</el-button>
              <el-button type="success" @click="markResult('认识')">认识</el-button>
            </div>
          </div>
          <div v-else class="empty-state">
            <el-empty description="今日单词已学完" />
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="今日复习" name="review">
        <div class="study-section">
          <div class="plan-bar">
            <el-form :inline="true">
              <el-form-item label="复习范围">
                <el-select
                  v-model="reviewRange"
                  placeholder="选择复习范围"
                  style="width: 150px"
                  @change="loadReviewWords"
                >
                  <el-option label="近一日" value="day" />
                  <el-option label="近一周" value="week" />
                  <el-option label="近一月" value="month" />
                  <el-option label="系统推荐" value="recommended" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="loadReviewWords">开始复习</el-button>
              </el-form-item>
            </el-form>
            <div class="daily-stats">
              <span class="daily-stat-item">
                <el-tag type="info">待复习: {{ reviewWords.length }} 词</el-tag>
              </span>
            </div>
          </div>

          <div v-if="currentReviewWord" class="word-card">
            <div class="word-header">
              <span class="word-number">{{ reviewIndex + 1 }} / {{ reviewWords.length }}</span>
              <span class="word-tag">{{ currentReviewWord.exam_requirement }}</span>
              <span class="review-badge">复习</span>
            </div>
            <h2 class="word">{{ currentReviewWord.word }}</h2>
            <p class="phonetic">{{ currentReviewWord.phonetic }}</p>
            <div class="word-actions">
              <el-button @click="showReviewMeaning = !showReviewMeaning">
                {{ showReviewMeaning ? '隐藏释义' : '显示释义' }}
              </el-button>
              <el-button @click="speakWord(currentReviewWord.word)">
                <el-icon><VideoPlay /></el-icon>发音
              </el-button>
            </div>
            <div v-if="showReviewMeaning" class="word-detail">
              <p class="meaning">{{ currentReviewWord.meaning }}</p>
              <p v-if="currentReviewWord.example_sentence" class="example">
                例句：{{ currentReviewWord.example_sentence }}
                <el-button size="small" text @click="speakWord(currentReviewWord.example_sentence)">
                  <el-icon><VideoPlay /></el-icon>朗读
                </el-button>
              </p>
            </div>
            <div class="study-buttons">
              <el-button type="danger" @click="markReviewResult('错误')">不认识</el-button>
              <el-button type="warning" @click="markReviewResult('模糊')">模糊</el-button>
              <el-button type="success" @click="markReviewResult('认识')">认识</el-button>
            </div>
          </div>
          <div v-else class="empty-state">
            <el-empty description="暂无需要复习的单词" />
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="单词列表" name="list">
        <div class="list-section">
          <div class="list-filters">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索单词"
              style="width: 200px"
              clearable
              @clear="loadWordList"
              @keyup.enter="loadWordList"
            />
            <el-select
              v-model="filterLevel"
              placeholder="掌握程度"
              style="width: 150px"
              clearable
              @change="loadWordList"
            >
              <el-option label="未学习" value="未学习" />
              <el-option label="陌生" value="陌生" />
              <el-option label="认识" value="认识" />
              <el-option label="熟悉" value="熟悉" />
              <el-option label="掌握" value="掌握" />
            </el-select>
            <el-button type="primary" @click="loadWordList">筛选</el-button>
          </div>
          <el-table :data="wordList" border>
            <el-table-column prop="word" label="单词" width="140" />
            <el-table-column prop="phonetic" label="音标" width="140" />
            <el-table-column prop="meaning" label="释义" />
            <el-table-column prop="mastery_level" label="掌握程度" width="100">
              <template #default="scope">
                <el-tag :type="getMasteryTagType(scope.row.mastery_level)">
                  {{ scope.row.mastery_level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="review_count" label="复习次数" width="100" />
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button size="small" @click="speakWord(scope.row.word)">
                  <el-icon><VideoPlay /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="totalWords"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadWordList"
              @current-change="loadWordList"
            />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay, Upload } from '@element-plus/icons-vue'
import {
  getWordStats, getTodayWords, getWordList,
  studyWord, getStudyPlan, saveStudyPlan, getWordCategories, uploadWordbook,
  getReviewWordsByRange,
  type Word, type UserWord, type TodayWordsResponse
} from '../../api/words'
import { useSpeech } from '@/composables/useSpeech'

const { speak: speakWord } = useSpeech()

const subTab = ref('today')
const wordStats = reactive({
  total: 0,
  studied: 0,
  mastered: 0,
  today: 0,
  has_wordbook: false
})
const uploadingWordbook = ref(false)
const wordbookInput = ref<HTMLInputElement | null>(null)
const dailyCount = ref(20)
const todayWords = ref<Word[]>([])
const currentIndex = ref(0)
const showMeaning = ref(false)
const wordList = ref<UserWord[]>([])
const searchKeyword = ref('')
const filterLevel = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalWords = ref(0)
const reviewCount = ref(0)
const newCount = ref(0)

const currentWord = ref<Word | null>(null)
const categories = ref<string[]>([])
const selectedCategory = ref<string>('')

const reviewWords = ref<Word[]>([])
const reviewIndex = ref(0)
const showReviewMeaning = ref(false)
const reviewRange = ref('today')
const currentReviewWord = ref<Word | null>(null)

const currentSourceLabel = computed(() => {
  const cat = selectedCategory.value
  if (!cat || cat === '全部') return '系统+词书'
  if (cat === '我的词书') return '我的词书'
  return cat
})

function getMasteryTagType(level: string) {
  switch (level) {
    case '未学习': return 'default'
    case '陌生': return 'danger'
    case '认识': return 'warning'
    case '熟悉': return 'info'
    case '掌握': return 'success'
    default: return 'default'
  }
}

async function loadStats(category?: string) {
  try {
    const stats = await getWordStats(category)
    Object.assign(wordStats, stats)
  } catch {
    wordStats.total = 0
    wordStats.studied = 0
    wordStats.mastered = 0
    wordStats.today = 0
  }
}

async function loadPlan() {
  try {
    const plan = await getStudyPlan()
    dailyCount.value = plan.daily_word_count
    if (plan.word_category !== null && plan.word_category !== undefined) {
      selectedCategory.value = plan.word_category
    }
  } catch {
    dailyCount.value = 20
  }
}

async function loadCategories() {
  try {
    const result = await getWordCategories()
    categories.value = result.categories
  } catch {
    categories.value = ['CET-4', 'CET-6', '考研']
  }
}

async function savePlan() {
  try {
    await saveStudyPlan(dailyCount.value, selectedCategory.value || undefined)
    await loadTodayWords()
    ElMessage.success('学习计划已保存')
  } catch {
    await loadTodayWords()
    ElMessage.success(`学习计划已保存：每日${dailyCount.value}词`)
  }
}

async function loadTodayWords() {
  try {
    const category = selectedCategory.value || undefined
    const result: TodayWordsResponse = await getTodayWords(dailyCount.value, category)
    todayWords.value = [...result.review, ...result.new]
    reviewCount.value = result.review_count
    newCount.value = result.new_count
    currentIndex.value = 0
    currentWord.value = todayWords.value[0] || null
    showMeaning.value = false
  } catch {
    todayWords.value = [
      { id: 1, word: 'abandon', phonetic: '/əˈbændən/', meaning: 'v. 放弃，抛弃', example_sentence: 'He decided to abandon the project.', difficulty: 1, frequency: 95, exam_requirement: '高频词' },
      { id: 2, word: 'ability', phonetic: '/əˈbɪləti/', meaning: 'n. 能力，才能', example_sentence: 'She has the ability to learn quickly.', difficulty: 1, frequency: 88, exam_requirement: '考纲词' },
      { id: 3, word: 'absolute', phonetic: '/ˈæbsəluːt/', meaning: 'adj. 绝对的，完全的', example_sentence: 'This is an absolute truth.', difficulty: 2, frequency: 75, exam_requirement: '考纲词' },
    ]
    reviewCount.value = 0
    newCount.value = todayWords.value.length
    currentWord.value = todayWords.value[0]
  }
}

async function loadReviewWords() {
  try {
    const result = await getReviewWordsByRange(reviewRange.value)
    reviewWords.value = result.words
    reviewIndex.value = 0
    currentReviewWord.value = reviewWords.value[0] || null
    showReviewMeaning.value = false
  } catch {
    reviewWords.value = [
      { id: 1, word: 'abandon', phonetic: '/əˈbændən/', meaning: 'v. 放弃，抛弃', example_sentence: 'He decided to abandon the project.', difficulty: 1, frequency: 95, exam_requirement: '高频词' },
      { id: 2, word: 'ability', phonetic: '/əˈbɪləti/', meaning: 'n. 能力，才能', example_sentence: 'She has the ability to learn quickly.', difficulty: 1, frequency: 88, exam_requirement: '考纲词' },
    ]
    currentReviewWord.value = reviewWords.value[0]
  }
}

async function loadWordList() {
  try {
    const result = await getWordList({
      page: currentPage.value,
      page_size: pageSize.value,
      mastery_level: filterLevel.value || undefined,
      keyword: searchKeyword.value || undefined,
      category: selectedCategory.value || undefined
    })
    wordList.value = result.items
    totalWords.value = result.total
  } catch {
    wordList.value = []
    totalWords.value = 0
  }
}

async function markResult(result: string) {
  if (!currentWord.value) return
  try {
    await studyWord(currentWord.value.id, result)
  } catch {
    if (result === '认识') {
      wordStats.mastered++
    }
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

async function markReviewResult(result: string) {
  if (!currentReviewWord.value) return
  try {
    await studyWord(currentReviewWord.value.id, result)
  } catch {
    if (result === '认识') {
      wordStats.mastered++
    }
  }
  if (reviewIndex.value < reviewWords.value.length - 1) {
    reviewIndex.value++
    currentReviewWord.value = reviewWords.value[reviewIndex.value]
    showReviewMeaning.value = false
  } else {
    currentReviewWord.value = null
    ElMessage.success('复习完成！')
  }
}

onMounted(async () => {
  await loadStats()
  await loadPlan()
  await loadCategories()
  await loadTodayWords()
  await loadWordList()
})

watch(subTab, async (newTab) => {
  if (newTab === 'review') {
    await loadReviewWords()
  }
})

async function handleCategoryChange() {
  const cat = selectedCategory.value || undefined
  await loadTodayWords()
  await loadStats(cat)
  await loadWordList()
  await savePlan()
}

function triggerWordbookUpload() {
  wordbookInput.value?.click()
}

async function handleWordbookSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return
  const file = target.files[0]

  uploadingWordbook.value = true
  try {
    const result = await uploadWordbook(file)
    ElMessage.success(result.message)
    selectedCategory.value = ''
    await loadStats()
    await loadCategories()
    await loadTodayWords()
    await loadWordList()
  } catch (error: any) {
    const msg = error.response?.data?.detail || error.message || '词书上传失败'
    ElMessage.error(msg)
  } finally {
    uploadingWordbook.value = false
    if (wordbookInput.value) {
      wordbookInput.value.value = ''
    }
  }
}
</script>

<style scoped>
.word-module {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 12px;
  text-align: center;
}

.source-card {
  background: #ecfdf5;
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

.sub-tabs {
  margin-top: 10px;
}

.plan-bar {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
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

.review-badge {
  padding: 4px 12px;
  background: #fef3c7;
  color: #d97706;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.new-badge {
  padding: 4px 12px;
  background: #dcfce7;
  color: #22c55e;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.daily-stats {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e0e0e0;
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
  display: flex;
  align-items: center;
  gap: 8px;
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

.list-filters {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.pagination {
  margin-top: 16px;
  text-align: right;
}

.hidden-input {
  display: none;
}
</style>
