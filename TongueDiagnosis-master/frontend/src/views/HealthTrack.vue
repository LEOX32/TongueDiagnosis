<template>
  <div class="health-track">
    <div class="header">
      <h1>{{ t('health.title') }}</h1>
      <p class="subtitle">{{ t('health.subtitle') }}</p>
    </div>

    <!-- 健康概览 -->
    <div class="overview-cards">
      <div class="card">
        <div class="card-icon">📊</div>
        <div class="card-content">
          <div class="card-label">{{ t('health.totalAnalyses') }}</div>
          <div class="card-value">{{ summary.total_analyses || 0 }}</div>
        </div>
      </div>
      <div class="card">
        <div class="card-icon">📈</div>
        <div class="card-content">
          <div class="card-label">{{ t('health.overallScore') }}</div>
          <div class="card-value">{{ summary.latest_report?.overall_score?.toFixed(1) || '--' }}</div>
        </div>
      </div>
      <div class="card">
        <div class="card-icon">💡</div>
        <div class="card-content">
          <div class="card-label">{{ t('health.activeRecommendations') }}</div>
          <div class="card-value">{{ summary.active_recommendations || 0 }}</div>
        </div>
      </div>
    </div>

    <!-- 进度图表 -->
    <div class="progress-section">
      <h2>{{ t('health.progressTracking') }}</h2>

      <!-- 报告切换区域 -->
      <div class="report-tabs">
        <el-button
          :type="currentReportType === 'daily' ? 'primary' : ''"
          @click="switchReport('daily')"
          size="small"
        >{{ t('health.dailyReport') }}</el-button>
        <el-button
          :type="currentReportType === 'weekly' ? 'primary' : ''"
          @click="switchReport('weekly')"
          size="small"
        >{{ t('health.weeklyReport') }}</el-button>
        <el-button
          :type="currentReportType === 'monthly' ? 'primary' : ''"
          @click="switchReport('monthly')"
          size="small"
        >{{ t('health.monthlyReport') }}</el-button>
      </div>

      <!-- 当前选中类型的报告卡片（只显示最新一条） -->
      <div v-if="currentReport" class="report-detail">
        <div class="report-info">
          <div class="report-date">{{ formatReportDate(currentReport.report_date, currentReportType) }}</div>
          <div class="report-score">{{ currentReport.overall_score?.toFixed(1) }}</div>
          <div class="report-trend" :class="'trend-' + currentReport.trend">{{ t('health.' + currentReport.trend) }}</div>
        </div>
        <div class="report-summary">{{ currentReport.summary }}</div>
      </div>
      <div v-else class="no-report">{{ t('health.noReport') }}</div>

      <!-- 进度图表 - 根据报告类型显示不同粒度 -->
      <div v-if="chartData.length > 0" class="chart-container">
        <div v-for="(item, index) in chartData" :key="index" class="progress-item">
          <div class="progress-date">{{ item.date }}</div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: item.overall_score + '%' }"></div>
          </div>
          <div class="progress-score">{{ item.overall_score?.toFixed(1) }}</div>
        </div>
      </div>
      <div v-else class="no-data">{{ t('health.noData') }}</div>
    </div>

    <!-- 健康建议 -->
    <div class="recommendations-section">
      <h2>{{ t('health.recommendations') }}</h2>
      <div v-if="aiRecommendation" class="ai-recommendation">
        <div class="ai-header">🤖 {{ t('health.aiRecommendation') }}</div>
        <div class="ai-content">{{ aiRecommendation }}</div>
      </div>
      <div v-if="recommendations.length > 0" class="recommendation-list">
        <div v-for="rec in recommendations" :key="rec.id" class="recommendation-item" :class="'priority-' + rec.priority">
          <div class="rec-category">{{ getCategoryLabel(rec.category) }}</div>
          <div class="rec-content">{{ rec.content }}</div>
        </div>
      </div>
      <div v-else-if="!aiRecommendation" class="no-data">{{ t('health.noData') }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { ElMessage } from 'element-plus';

const { t } = useI18n();

const summary = ref({
  total_analyses: 0,
  latest_report: null,
  active_recommendations: 0
});

const progress = ref([]);
const recommendations = ref([]);
const aiRecommendation = ref('');
const currentReportType = ref('daily');
const currentReport = ref(null);
const reports = ref({ daily: [], weekly: [], monthly: [] });
const chartData = ref([]);
let refreshInterval = null;
let lastAutoGenerate = JSON.parse(localStorage.getItem('lastAutoGenerate') || '{"daily": null, "weekly": null, "monthly": null}');
let lastAIRecommendationTime = localStorage.getItem('lastAIRecommendationTime') || null;

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/health';

const getToken = () => localStorage.getItem('token');

const saveLastAutoGenerate = () => {
  localStorage.setItem('lastAutoGenerate', JSON.stringify(lastAutoGenerate));
};

const loadSummary = async () => {
  try {
    const response = await axios.get(`${baseURL}/summary`, {
      headers: { 'Authorization': 'Bearer ' + getToken() }
    });
    if (response.data.code === 200) {
      summary.value = response.data.data;
    }
  } catch (error) {
    console.error('Failed to load summary:', error);
  }
};

const loadProgress = async () => {
  try {
    const response = await axios.get(`${baseURL}/progress?days=30`, {
      headers: { 'Authorization': 'Bearer ' + getToken() }
    });
    if (response.data.code === 200) {
      progress.value = response.data.data.progress || [];
    }
  } catch (error) {
    console.error('Failed to load progress:', error);
  }
};

const loadRecommendations = async () => {
  try {
    const response = await axios.get(`${baseURL}/recommendations`, {
      headers: { 'Authorization': 'Bearer ' + getToken() }
    });
    if (response.data.code === 200) {
      recommendations.value = response.data.data.recommendations || [];
    }
  } catch (error) {
    console.error('Failed to load recommendations:', error);
  }
};

const refreshAll = async () => {
  await loadSummary();
  await loadProgress();
  await loadRecommendations();
  await loadReports();
};

const loadReports = async () => {
  try {
    const response = await axios.get(`${baseURL}/reports?report_type=all&limit=100`, {
      headers: { 'Authorization': 'Bearer ' + getToken() }
    });
    if (response.data.code === 200) {
      const reportsList = response.data.data.reports || [];
      console.log('Loaded reports:', reportsList);
      reports.value = { daily: [], weekly: [], monthly: [] };
      reportsList.forEach(r => {
        if (r.report_type === 'daily' || r.report_type === 'weekly' || r.report_type === 'monthly') {
          reports.value[r.report_type].push(r);
        }
      });
      console.log('Parsed reports:', reports.value);
      currentReport.value = reports.value[currentReportType.value][0] || null;
      console.log('Current report:', currentReport.value);
      updateChartData();
    }
  } catch (error) {
    console.error('Failed to load reports:', error);
  }
};

const updateChartData = () => {
  const type = currentReportType.value;
  const data = reports.value[type] || [];
  const today = new Date();
  const todayStr = today.toISOString().substring(0, 10);

  if (type === 'daily') {
    const hourlyData = {};
    data.forEach(r => {
      const dateStr = r.report_date.substring(0, 10);
      if (dateStr !== todayStr) return;
      const hour = r.report_date.substring(11, 16);
      if (!hourlyData[hour] || new Date(r.report_date) > new Date(hourlyData[hour].report_date)) {
        hourlyData[hour] = r;
      }
    });
    chartData.value = Object.values(hourlyData).map(r => ({
      date: r.report_date.substring(11, 16),
      overall_score: r.overall_score
    })).sort((a, b) => a.date.localeCompare(b.date)).slice(0, 24);
  } else if (type === 'weekly') {
    const weekStart = new Date(today);
    weekStart.setDate(today.getDate() - today.getDay() + 1);
    const weekEnd = new Date(weekStart);
    weekEnd.setDate(weekStart.getDate() + 6);
    const weekStartStr = weekStart.toISOString().substring(0, 10);
    const weekEndStr = weekEnd.toISOString().substring(0, 10);

    const dailyData = {};
    data.forEach(r => {
      const dateStr = r.report_date.substring(0, 10);
      if (dateStr < weekStartStr || dateStr > weekEndStr) return;
      if (!dailyData[dateStr] || new Date(r.report_date) > new Date(dailyData[dateStr].report_date)) {
        dailyData[dateStr] = r;
      }
    });
    chartData.value = Object.values(dailyData).map(r => ({
      date: r.report_date.substring(5, 10),
      overall_score: r.overall_score
    })).sort((a, b) => a.date.localeCompare(b.date)).slice(0, 7);
  } else if (type === 'monthly') {
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();

    const weeklyData = {};
    data.forEach(r => {
      const date = new Date(r.report_date);
      if (date.getMonth() !== currentMonth || date.getFullYear() !== currentYear) return;

      const weekStart = new Date(date);
      weekStart.setDate(date.getDate() - date.getDay() + 1);
      const weekKey = weekStart.toISOString().substring(0, 10);

      if (!weeklyData[weekKey] || new Date(r.report_date) > new Date(weeklyData[weekKey].report_date)) {
        weeklyData[weekKey] = r;
      }
    });

    chartData.value = Object.entries(weeklyData)
      .map(([weekKey, r]) => {
        const start = new Date(weekKey);
        const end = new Date(start);
        end.setDate(start.getDate() + 6);
        const startStr = start.toISOString().substring(5, 10);
        const endStr = end.toISOString().substring(5, 10);
        return {
          date: `${startStr}~${endStr}`,
          overall_score: r.overall_score
        };
      })
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(0, 4);
  }
};

const switchReport = (type) => {
  currentReportType.value = type;
  currentReport.value = reports.value[type]?.[0] || null;
  updateChartData();
};

const autoGenerateReports = async () => {
  const now = new Date();
  console.log('Auto generating reports, lastAutoGenerate:', lastAutoGenerate);

  let newReportGenerated = false;

  try {
    const shouldGenerateDaily = !lastAutoGenerate.daily ||
      (now - new Date(lastAutoGenerate.daily)) >= 60 * 60 * 1000;
    console.log('Should generate daily:', shouldGenerateDaily);

    if (shouldGenerateDaily) {
      console.log('Generating daily report...');
      await axios.post(
        `${baseURL}/report/generate?report_type=daily`,
        {},
        { headers: { 'Authorization': 'Bearer ' + getToken() } }
      );
      lastAutoGenerate.daily = now.toISOString();
      saveLastAutoGenerate();
      newReportGenerated = true;
    }

    const shouldGenerateWeekly = !lastAutoGenerate.weekly ||
      (now - new Date(lastAutoGenerate.weekly)) >= 24 * 60 * 60 * 1000;
    console.log('Should generate weekly:', shouldGenerateWeekly);

    if (shouldGenerateWeekly) {
      console.log('Generating weekly report...');
      await axios.post(
        `${baseURL}/report/generate?report_type=weekly`,
        {},
        { headers: { 'Authorization': 'Bearer ' + getToken() } }
      );
      lastAutoGenerate.weekly = now.toISOString();
      saveLastAutoGenerate();
      newReportGenerated = true;
    }

    const shouldGenerateMonthly = !lastAutoGenerate.monthly ||
      (now - new Date(lastAutoGenerate.monthly)) >= 24 * 60 * 60 * 1000;
    console.log('Should generate monthly:', shouldGenerateMonthly);

    if (shouldGenerateMonthly) {
      console.log('Generating monthly report...');
      await axios.post(
        `${baseURL}/report/generate?report_type=monthly`,
        {},
        { headers: { 'Authorization': 'Bearer ' + getToken() } }
      );
      lastAutoGenerate.monthly = now.toISOString();
      saveLastAutoGenerate();
      newReportGenerated = true;
    }
  } catch (error) {
    console.error('Auto generate reports failed:', error);
  }

  await loadReports();

  if (newReportGenerated) {
    console.log('New report generated, updating AI recommendation...');
    await loadAIRecommendation();
  }
};

const loadAIRecommendation = async () => {
  try {
    const response = await axios.get(`${baseURL}/recommendations`, {
      headers: { 'Authorization': 'Bearer ' + getToken() }
    });
    if (response.data.code === 200) {
      aiRecommendation.value = response.data.data.ai_recommendation || '';
      lastAIRecommendationTime = new Date().toISOString();
      localStorage.setItem('lastAIRecommendationTime', lastAIRecommendationTime);
    }
  } catch (error) {
    console.error('Failed to load AI recommendation:', error);
  }
};

const formatReportDate = (dateStr, type) => {
  if (!dateStr) return '';
  if (type === 'daily') {
    return dateStr.substring(5, 16);
  } else if (type === 'weekly') {
    return dateStr.substring(5, 10);
  } else if (type === 'monthly') {
    return dateStr.substring(5, 10);
  }
  return dateStr.substring(5, 10);
};

const getCategoryLabel = (category) => {
  const categoryMap = {
    diet: t('health.diet'),
    lifestyle: t('health.lifestyle'),
    exercise: t('health.exercise'),
    sleep: t('health.sleep')
  };
  return categoryMap[category] || category;
};

// 监听舌象分析完成事件（通过 localStorage）
const handleAnalysisComplete = async (event) => {
  if (event.key === 'tongue_analysis_complete') {
    console.log('检测到新的舌象分析完成，刷新健康数据并生成报告...');
    await refreshAll();
    await autoGenerateReports();
  }
};

// 定时刷新（每 30 秒）
const startAutoRefresh = () => {
  refreshInterval = setInterval(() => {
    console.log('定时刷新健康数据...');
    refreshAll();
  }, 30000); // 30 秒
};

const handleTongueAnalysisComplete = async () => {
  console.log('检测到新的舌象分析完成，刷新健康数据并生成报告...');
  await refreshAll();
  await autoGenerateReports();
};

onMounted(async () => {
  await refreshAll();
  await loadAIRecommendation();
  await autoGenerateReports();
  startAutoRefresh();

  window.addEventListener('storage', handleAnalysisComplete);
  window.addEventListener('tongue-analysis-complete', handleTongueAnalysisComplete);
});

onUnmounted(() => {
  // 清理定时器
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }

  // 移除事件监听
  window.removeEventListener('storage', handleAnalysisComplete);
  window.removeEventListener('tongue-analysis-complete', handleTongueAnalysisComplete);
});
</script>

<style scoped>
.health-track {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 40px;
}

.header h1 {
  font-size: 2em;
  color: #333;
  margin-bottom: 10px;
}

.subtitle {
  color: #666;
  font-size: 1.1em;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 15px;
  padding: 25px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  transition: transform 0.3s;
}

.card:hover {
  transform: translateY(-5px);
}

.card-icon {
  font-size: 3em;
}

.card-content {
  flex: 1;
}

.card-label {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9em;
  margin-bottom: 5px;
}

.card-value {
  color: white;
  font-size: 2em;
  font-weight: bold;
}

.generate-section,
.progress-section,
.recommendations-section {
  background: white;
  border-radius: 15px;
  padding: 25px;
  margin-bottom: 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

h2 {
  color: #333;
  margin-bottom: 20px;
  font-size: 1.5em;
}

.report-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.report-tabs .el-button {
  border-radius: 20px;
}

.report-detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.report-date {
  font-size: 1.1em;
  font-weight: bold;
}

.report-score {
  font-size: 2em;
  font-weight: bold;
}

.report-trend {
  padding: 5px 15px;
  border-radius: 20px;
  font-size: 0.9em;
  background: rgba(255, 255, 255, 0.2);
}

.trend-up {
  background: #67c23a;
}

.trend-down {
  background: #f56c6c;
}

.trend-stable {
  background: #909399;
}

.report-summary {
  margin-bottom: 10px;
  line-height: 1.6;
}

.report-recommendations {
  font-size: 0.9em;
  opacity: 0.9;
  line-height: 1.6;
}

.no-report {
  text-align: center;
  color: #999;
  padding: 30px;
  font-size: 1em;
  margin-bottom: 20px;
}

.chart-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.progress-item {
  display: flex;
  align-items: center;
  gap: 15px;
}

.progress-date {
  width: 120px;
  color: #666;
  font-size: 0.9em;
}

.progress-bar {
  flex: 1;
  height: 25px;
  background: #f0f0f0;
  border-radius: 12px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  transition: width 0.5s;
}

.progress-score {
  width: 60px;
  text-align: right;
  font-weight: bold;
  color: #667eea;
}

.ai-recommendation {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 15px;
  padding: 20px;
  margin-bottom: 20px;
  color: white;
}

.ai-header {
  font-size: 1.1em;
  font-weight: bold;
  margin-bottom: 10px;
}

.ai-content {
  line-height: 1.8;
  font-size: 0.95em;
}

.recommendation-list {
  display: grid;
  gap: 15px;
}

.recommendation-item {
  padding: 15px;
  border-radius: 10px;
  border-left: 4px solid;
  background: #f8f9fa;
}

.priority-1 {
  border-left-color: #f56c6c;
  background: #fef0f0;
}

.priority-2 {
  border-left-color: #e6a23c;
  background: #fdf6ec;
}

.priority-3 {
  border-left-color: #67c23a;
  background: #f0f9eb;
}

.rec-category {
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
  text-transform: capitalize;
}

.rec-content {
  color: #666;
  line-height: 1.6;
}

.no-data {
  text-align: center;
  color: #999;
  padding: 40px;
  font-size: 1.1em;
}
</style>
