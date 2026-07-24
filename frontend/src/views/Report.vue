<template>
  <div class="report-page">
    <div class="report-header">
      <h2>学习报告</h2>
      <el-radio-group v-model="period" @change="loadReport">
        <el-radio-button label="day">今日</el-radio-button>
        <el-radio-button label="week">本周</el-radio-button>
        <el-radio-button label="month">本月</el-radio-button>
      </el-radio-group>
    </div>

    <div class="stats-grid">
      <el-card class="stat-card">
        <div class="stat-icon words-icon">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ report.word_stats.total_words }}</div>
          <div class="stat-label">已学单词</div>
        </div>
        <div class="stat-rate">掌握率 {{ report.word_stats.mastery_rate }}%</div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon mistake-icon">
          <el-icon><Warning /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ report.mistake_stats.total_mistakes }}</div>
          <div class="stat-label">错题总数</div>
        </div>
        <div class="stat-rate">掌握率 {{ report.mistake_stats.mastery_rate }}%</div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon rec-icon">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ report.recommendation_stats.completed_this_period }}</div>
          <div class="stat-label">本期完成推荐</div>
        </div>
        <div class="stat-rate">正确率 {{ report.recommendation_stats.success_rate }}%</div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-icon time-icon">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ report.overall_stats.avg_daily_time }}</div>
          <div class="stat-label">日均学习(分钟)</div>
        </div>
        <div class="stat-rate">累计 {{ report.overall_stats.total_study_days }} 天</div>
      </el-card>
    </div>

    <div class="chart-section">
      <el-card>
        <template #header>
          <span>本周学习趋势</span>
        </template>
        <div ref="trendChart" class="chart-container"></div>
      </el-card>
    </div>

    <div class="detail-section">
      <el-card>
        <template #header>
          <span>错题科目分布</span>
        </template>
        <div class="subject-list">
          <div v-for="item in report.mistake_stats.by_subject" :key="item.subject" class="subject-item">
            <span class="subject-name">{{ item.subject }}</span>
            <el-progress :percentage="(item.count / Math.max(report.mistake_stats.total_mistakes, 1) * 100).toFixed(0)" />
            <span class="subject-count">{{ item.count }} 题</span>
          </div>
          <div v-if="report.mistake_stats.by_subject.length === 0" class="empty-text">暂无错题数据</div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { Document, Warning, DataAnalysis, Clock } from '@element-plus/icons-vue'
import { getStudyReport, getWeeklyTrend, type StudyReport } from '../api/report'

const period = ref('week')
const report = ref<StudyReport>({
  period: 'week',
  start_date: '',
  end_date: '',
  word_stats: { total_words: 0, mastered_count: 0, learned_this_period: 0, today_review: 0, mastery_rate: 0 },
  mistake_stats: { total_mistakes: 0, added_this_period: 0, mastered_mistakes: 0, today_review: 0, mastery_rate: 0, by_subject: [] },
  recommendation_stats: { total_recommendations: 0, completed_this_period: 0, total_completed: 0, completion_rate: 0, success_rate: 0 },
  overall_stats: { total_study_days: 0, avg_daily_time: 0 }
})

const trendChart = ref<HTMLElement | null>(null)

async function loadReport() {
  try {
    report.value = await getStudyReport(period.value)
    await nextTick()
    renderChart()
  } catch {
    // ignore
  }
}

function drawRoundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  r = Math.min(r, w / 2, h / 2)
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.quadraticCurveTo(x + w, y, x + w, y + r)
  ctx.lineTo(x + w, y + h - r)
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
  ctx.lineTo(x + r, y + h)
  ctx.quadraticCurveTo(x, y + h, x, y + h - r)
  ctx.lineTo(x, y + r)
  ctx.quadraticCurveTo(x, y, x + r, y)
  ctx.closePath()
}

async function renderChart() {
  try {
    const trend = await getWeeklyTrend()
    if (!trendChart.value) return

    const labels = trend.map(t => t.date.slice(5))
    const data = trend.map(t => t.total_time)

    const canvas = document.createElement('canvas')
    trendChart.value.innerHTML = ''
    trendChart.value.appendChild(canvas)

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = trendChart.value.clientWidth
    canvas.height = 200

    const maxValue = Math.max(...data, 1)
    const barWidth = canvas.width / labels.length * 0.6
    const gap = canvas.width / labels.length * 0.4
    const padding = 40

    ctx.fillStyle = '#f5f5f5'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    for (let i = 0; i <= 4; i++) {
      const y = padding + (canvas.height - padding * 2) * (i / 4)
      ctx.strokeStyle = '#ddd'
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(padding, y)
      ctx.lineTo(canvas.width - 10, y)
      ctx.stroke()

      ctx.fillStyle = '#999'
      ctx.font = '12px Arial'
      ctx.textAlign = 'right'
      ctx.fillText(Math.round(maxValue * (1 - i / 4)) + '', padding - 5, y + 4)
    }

    for (let i = 0; i < labels.length; i++) {
      const x = padding + i * (barWidth + gap) + gap / 2
      const height = data[i] > 0 ? (data[i] / maxValue) * (canvas.height - padding * 2) : 0
      const y = canvas.height - padding - height

      if (height > 0) {
        const gradient = ctx.createLinearGradient(x, y, x, canvas.height - padding)
        gradient.addColorStop(0, '#667eea')
        gradient.addColorStop(1, '#764ba2')

        ctx.fillStyle = gradient
        drawRoundRect(ctx, x, y, barWidth, height, Math.min(4, height / 2))
        ctx.fill()

        ctx.fillStyle = '#303133'
        ctx.font = '11px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(String(data[i]), x + barWidth / 2, y - 5)
      }

      ctx.fillStyle = '#666'
      ctx.font = '12px Arial'
      ctx.textAlign = 'center'
      ctx.fillText(labels[i], x + barWidth / 2, canvas.height - 15)
    }
  } catch {
    // ignore
  }
}

onMounted(() => {
  loadReport()
})

watch(period, () => {
  loadReport()
})
</script>

<style scoped>
.report-page {
  padding: 20px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.report-header h2 {
  font-size: 24px;
  font-weight: bold;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
}

.words-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.mistake-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.rec-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.time-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.stat-rate {
  font-size: 12px;
  color: #67c23a;
  margin-left: 10px;
}

.chart-section {
  margin-bottom: 20px;
}

.chart-container {
  width: 100%;
  height: 200px;
}

.detail-section {
  margin-bottom: 20px;
}

.subject-list {
  padding: 10px;
}

.subject-item {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.subject-name {
  width: 100px;
  font-size: 14px;
  color: #606266;
}

.subject-count {
  width: 60px;
  font-size: 14px;
  color: #909399;
  text-align: right;
  margin-left: 10px;
}

.empty-text {
  text-align: center;
  color: #909399;
  padding: 20px;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>