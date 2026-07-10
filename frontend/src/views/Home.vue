<template>
  <div class="home">
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon mistake-icon">
          <el-icon><DocumentError /></el-icon>
        </div>
        <div class="stat-info">
          <p class="stat-value">{{ mistakeCount }}</p>
          <p class="stat-label">错题总数</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon review-icon">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <p class="stat-value">{{ todayReviewCount }}</p>
          <p class="stat-label">今日待复习</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon word-icon">
          <el-icon><Reading /></el-icon>
        </div>
        <div class="stat-info">
          <p class="stat-value">{{ wordCount }}</p>
          <p class="stat-label">已学单词</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon resource-icon">
          <el-icon><FolderOpened /></el-icon>
        </div>
        <div class="stat-info">
          <p class="stat-value">{{ resourceCount }}</p>
          <p class="stat-label">资料数量</p>
        </div>
      </div>
    </div>
    <div class="quick-actions">
      <h3>快捷操作</h3>
      <div class="action-buttons">
        <el-button type="primary" @click="$router.push('/dashboard/mistakes')">
          <el-icon><Plus /></el-icon>
          添加错题
        </el-button>
        <el-button type="success" @click="$router.push('/dashboard/mistakes')">
          <el-icon><Refresh /></el-icon>
          开始复习
        </el-button>
        <el-button type="warning" @click="$router.push('/dashboard/words')">
          <el-icon><BookOpen /></el-icon>
          学习单词
        </el-button>
        <el-button type="info" @click="$router.push('/dashboard/ai')">
          <el-icon><Message /></el-icon>
          AI问答
        </el-button>
      </div>
    </div>
    <div class="recent-section">
      <h3>最近添加的错题</h3>
      <el-table :data="recentMistakes" border>
        <el-table-column prop="subject" label="科目" width="100" />
        <el-table-column prop="knowledge_point" label="知识点" />
        <el-table-column prop="difficulty" label="难度" width="80" />
        <el-table-column prop="mastery_level" label="掌握程度" width="100" />
        <el-table-column prop="created_at" label="添加时间" width="180" />
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { DocumentError, Clock, Reading, FolderOpened, Plus, Refresh, BookOpen, Message } from '@element-plus/icons-vue'
import { getMistakes, getTodayReviews } from '../api/mistakes'

const mistakeCount = ref(0)
const todayReviewCount = ref(0)
const wordCount = ref(0)
const resourceCount = ref(0)
const recentMistakes = ref<any[]>([])

onMounted(async () => {
  try {
    const mistakes = await getMistakes()
    mistakeCount.value = mistakes.length
    recentMistakes.value = mistakes.slice(0, 5)
    
    const todayReviews = await getTodayReviews()
    todayReviewCount.value = todayReviews.length
  } catch {
    mistakeCount.value = 0
    todayReviewCount.value = 0
  }
})
</script>

<style scoped>
.home {
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.mistake-icon {
  background: #fee2e2;
  color: #ef4444;
}

.review-icon {
  background: #dbeafe;
  color: #3b82f6;
}

.word-icon {
  background: #dcfce7;
  color: #22c55e;
}

.resource-icon {
  background: #fef3c7;
  color: #f59e0b;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  margin: 0;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin: 4px 0 0;
}

.quick-actions {
  background: white;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.quick-actions h3 {
  margin: 0 0 16px;
  font-size: 16px;
  color: #333;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.recent-section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.recent-section h3 {
  margin: 0 0 16px;
  font-size: 16px;
  color: #333;
}
</style>