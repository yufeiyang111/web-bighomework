<template>
  <Layout pageTitle="成绩管理">
    <div class="score-manager">
      <div class="page-header">
      <div class="header-left">
        <h2>成绩管理</h2>
        <p>录入、导入、导出和管理学生成绩</p>
      </div>
      <div class="header-actions">
        <button @click="showManualEntry = true" class="btn-success">
          <i class="fas fa-plus"></i> 手动录入
        </button>
        <button @click="showImportModal = true" class="btn-primary">
          <i class="fas fa-file-import"></i> 导入成绩
        </button>
        <button @click="exportScores" class="btn-secondary">
          <i class="fas fa-file-export"></i> 导出成绩
        </button>
      </div>
    </div>

    <!-- 筛选和统计 -->
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-group">
          <label>班级筛选</label>
          <select v-model="filters.classId" @change="applyFilters">
            <option value="">全部班级</option>
            <option v-for="classItem in classes" :key="classItem.id" :value="classItem.id">
              {{ classItem.name }}
            </option>
          </select>
        </div>
        <div class="filter-group">
          <label>考试筛选</label>
          <select v-model="filters.examId" @change="applyFilters">
            <option value="">全部考试</option>
            <option v-for="exam in exams" :key="exam.id" :value="exam.id">
              {{ exam.title }}
            </option>
          </select>
        </div>
        <div class="filter-group">
          <label>时间范围</label>
          <div class="date-range">
            <input type="date" v-model="filters.startDate" @change="applyFilters">
            <span>至</span>
            <input type="date" v-model="filters.endDate" @change="applyFilters">
          </div>
        </div>
        <button @click="resetFilters" class="btn-outline">重置筛选</button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-chart-line"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.averageScore.toFixed(1) }}</div>
          <div class="stat-label">平均分</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-trophy"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.highestScore }}</div>
          <div class="stat-label">最高分</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-exclamation-circle"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.lowestScore }}</div>
          <div class="stat-label">最低分</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-wave-square"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.stdDeviation.toFixed(1) }}</div>
          <div class="stat-label">标准差</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <i class="fas fa-check-circle"></i>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.passRate }}%</div>
          <div class="stat-label">及格率
          </div>
        </div>
      </div>
    </div>

    <!-- 统计可视化 -->
    <div class="charts-section" v-if="filteredScores.length">
      <div class="chart-card">
        <div class="chart-header">
          <h4>分数段分布</h4>
          <span class="chart-hint">按百分比区间</span>
        </div>
        <div class="histogram">
          <div
              class="histogram-bar"
              v-for="bucket in distributionData"
              :key="bucket.label"
          >
            <div class="histogram-label">{{ bucket.label }}</div>
            <div class="histogram-track">
              <div
                  class="histogram-fill"
                  :style="{ width: bucket.percent + '%' }"
              ></div>
            </div>
            <div class="histogram-count">{{ bucket.count }} 人</div>
          </div>
        </div>
      </div>

      <div class="chart-card">
        <div class="chart-header">
          <h4>成绩趋势</h4>
          <span class="chart-hint">按录入日期平均分</span>
        </div>
        <div class="line-chart-container">
          <LineChart
              v-if="trendChartData.labels.length > 0 && trendChartData.datasets.length > 0"
              :labels="trendChartData.labels"
              :datasets="trendChartData.datasets"
              :options="trendChartOptions"
          />
          <div v-else class="chart-empty">
            <p>暂无趋势数据</p>
            <p style="font-size: 12px; margin-top: 8px; color: #999;">
              提示：需要至少一条包含日期信息的成绩记录才能显示趋势图
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <p>加载中...</p>
    </div>

    <!-- 成绩列表 -->
    <div v-else class="scores-table-container">
      <div class="table-header">
        <h3>成绩列表</h3>
        <div class="table-actions">
          <input
              type="text"
              v-model="searchKeyword"
              placeholder="搜索学生姓名或学号..."
              class="search-input"
              @keyup.enter="searchScores"
          >
          <button @click="refreshScores" class="btn-icon">
            <i class="fas fa-sync-alt"></i>
          </button>
        </div>
      </div>

      <div class="table-responsive">
        <table class="scores-table">
          <thead>
          <tr>
            <th @click="sortBy('studentName')" class="sortable">
              学生姓名
              <i :class="sortIcon('studentName')"></i>
            </th>
            <th @click="sortBy('studentId')" class="sortable">
              学号
              <i :class="sortIcon('studentId')"></i>
            </th>
            <th>班级</th>
            <th>考试名称</th>
            <th @click="sortBy('score')" class="sortable">
              成绩
              <i :class="sortIcon('score')"></i>
            </th>
            <th>总分</th>
            <th>百分比</th>
            <th>录入方式</th>
            <th>录入时间</th>
            <th>操作</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="score in paginatedScores" :key="score.id">
            <td>
              <div class="student-info">
                <img :src="score.avatar || defaultAvatar" class="student-avatar">
                <span>{{ score.studentName || score.student_name }}</span>
              </div>
            </td>
            <td>{{ score.studentId || score.student_id }}</td>
            <td>{{ score.className || score.class_name }}</td>
            <td>{{ score.examTitle || score.exam_title || '外部成绩' }}</td>
            <td :class="getScoreClass(score.percentage || (score.score / (score.total_score || score.totalScore) * 100))">
              <span class="score-value">{{ score.score }}</span>
            </td>
            <td>{{ score.totalScore || score.total_score }}</td>
            <td>
              <div class="percentage-bar">
                <div class="percentage-text">{{ (score.percentage || (score.score / (score.total_score || score.totalScore) * 100)).toFixed(1) }}%</div>
                <div class="percentage-track">
                  <div
                      class="percentage-fill"
                      :style="{ width: (score.percentage || (score.score / (score.total_score || score.totalScore) * 100)) + '%' }"
                      :class="getScoreClass(score.percentage || (score.score / (score.total_score || score.totalScore) * 100))"
                  ></div>
                </div>
              </div>
            </td>
            <td>
                <span :class="'score-type-' + (score.type || 'manual')">
                  {{ getScoreTypeText(score.type || 'manual') }}
                </span>
            </td>
            <td>{{ formatDate(score.recorded_at || score.recordedAt) }}</td>
            <td>
              <div class="action-buttons">
                <button @click="editScore(score)" class="btn-icon small">
                  <i class="fas fa-edit"></i>
                </button>
                <button @click="viewDetails(score)" class="btn-icon small">
                  <i class="fas fa-eye"></i>
                </button>
                <button @click="deleteScore(score.id)" class="btn-icon small danger">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </td>
          </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div class="pagination">
        <div class="pagination-info">
          显示 {{ startIndex + 1 }}-{{ endIndex }} 条，共 {{ filteredScores.length }} 条
        </div>
        <div class="pagination-controls">
          <button @click="prevPage" :disabled="currentPage === 1" class="pagination-btn">
            <i class="fas fa-chevron-left"></i>
          </button>
          <span class="pagination-current">第 {{ currentPage }} 页</span>
          <button @click="nextPage" :disabled="currentPage === totalPages" class="pagination-btn">
            <i class="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 手动录入模态框 -->
    <div v-if="showManualEntry" class="modal-overlay">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>手动录入成绩</h3>
          <button @click="showManualEntry = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="submitManualEntry">
            <div class="form-row">
              <div class="form-group">
                <label>选择班级 *</label>
                <select v-model="manualEntry.classId" required @change="onManualClassChange">
                  <option value="">请选择班级</option>
                  <option v-for="classItem in classes" :key="classItem.id" :value="classItem.id">
                    {{ classItem.name }}
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>选择考试</label>
                <select v-model="manualEntry.examId" :disabled="!manualEntry.classId" @change="onManualExamChange">
                  <option value="">请选择考试（可选）</option>
                  <option v-for="exam in availableExams" :key="exam.id" :value="exam.id">
                    {{ exam.title }}
                  </option>
                </select>
                <small v-if="!manualEntry.classId" style="display: block; color: #666; margin-top: 4px; font-size: 12px;">
                  请先选择班级
                </small>
                <small v-else-if="availableExams.length === 0" style="display: block; color: #999; margin-top: 4px; font-size: 12px;">
                  该班级暂无考试
                </small>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>科目名称 *</label>
                <input v-model="manualEntry.subject" type="text" required placeholder="例如：高等数学">
              </div>
              <div class="form-group">
                <label>总分 *</label>
                <input v-model.number="manualEntry.totalScore" type="number" min="1" required>
              </div>
            </div>

            <div class="form-section">
              <h4>选择学生和录入成绩</h4>
              <div class="student-selection">
                <div class="select-all">
                  <label>
                    <input type="checkbox" v-model="selectAllStudents" @change="toggleAllStudents">
                    全选当前班级学生
                  </label>
                </div>
                <div class="students-grid" v-if="manualEntry.classId">
                  <div v-for="student in availableStudents" :key="student.id" class="student-score-item">
                    <label>
                      <input type="checkbox" v-model="selectedStudents" :value="student.id">
                      {{ student.name }} ({{ student.studentId || student.username }})
                    </label>
                    <input
                        v-model="studentScores[student.id]"
                        type="number"
                        :placeholder="'0-' + manualEntry.totalScore"
                        min="0"
                        :max="manualEntry.totalScore"
                        class="score-input"
                    >
                  </div>
                  <div v-if="availableStudents.length === 0" class="empty-hint">
                    暂无学生，请确认班级下已有学生
                  </div>
                </div>
              </div>
            </div>

            <div class="form-group">
              <label>备注</label>
              <textarea v-model="manualEntry.comments" rows="3" placeholder="添加备注信息..."></textarea>
            </div>

            <div class="form-actions">
              <button type="button" @click="showManualEntry = false" class="btn-secondary">取消</button>
              <button type="submit" class="btn-primary">提交录入</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 导入成绩模态框 -->
    <div v-if="showImportModal" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>导入成绩</h3>
          <button @click="showImportModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="import-options">
            <div class="import-option">
              <h4>Excel导入</h4>
              <p>支持 .xlsx 和 .xls 格式</p>
              <div class="file-drop-zone" @click="triggerFileInput">
                <i class="fas fa-file-excel fa-3x"></i>
                <p>点击或拖拽文件到此处</p>
                <input
                    type="file"
                    ref="fileInput"
                    accept=".xlsx,.xls"
                    @change="handleFileSelect"
                    style="display: none"
                >
              </div>
              <div v-if="selectedFile" class="selected-file">
                <p>已选择: {{ selectedFile.name }}</p>
                <button @click="uploadFile" class="btn-primary">开始导入</button>
              </div>
            </div>

            <div class="import-template">
              <h4>下载模板</h4>
              <p>请使用标准模板填写成绩数据</p>
              <button @click="downloadTemplate" class="btn-outline">
                <i class="fas fa-download"></i> 下载Excel模板
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 成绩详情模态框 -->
    <div v-if="selectedScore" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>成绩详情</h3>
          <button @click="selectedScore = null" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="score-detail">
            <div class="detail-row">
              <span class="detail-label">学生姓名：</span>
              <span class="detail-value">{{ selectedScore.student_name || selectedScore.studentName }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">学号：</span>
              <span class="detail-value">{{ selectedScore.student_id || selectedScore.studentId }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">班级：</span>
              <span class="detail-value">{{ selectedScore.class_name || selectedScore.className }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">科目：</span>
              <span class="detail-value">{{ selectedScore.subject }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">成绩：</span>
              <span class="detail-value score-value-large">{{ selectedScore.score }} / {{ selectedScore.total_score || selectedScore.totalScore }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">百分比：</span>
              <span class="detail-value">{{ (selectedScore.percentage || (selectedScore.score / (selectedScore.total_score || selectedScore.totalScore) * 100)).toFixed(1) }}%</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">录入方式：</span>
              <span :class="'detail-value score-type-' + (selectedScore.type || 'manual')">
                {{ getScoreTypeText(selectedScore.type || 'manual') }}
              </span>
            </div>
            <div class="detail-row">
              <span class="detail-label">录入时间：</span>
              <span class="detail-value">{{ formatDate(selectedScore.recorded_at || selectedScore.recordedAt) }}</span>
            </div>
            <div class="detail-row" v-if="selectedScore.comments">
              <span class="detail-label">备注：</span>
              <span class="detail-value">{{ selectedScore.comments }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { teacherApi } from '@/api/teacher';
import Layout from '@/components/Layout.vue';
import LineChart from '@/components/charts/LineChart.vue';

// 状态管理
const showManualEntry = ref(false);
const showImportModal = ref(false);
const selectedScore = ref<any>(null);
const selectedFile = ref<File | null>(null);
const searchKeyword = ref('');
const currentPage = ref(1);
const pageSize = 10;
const sortField = ref('recorded_at');
const sortDirection = ref('desc');
const isLoading = ref(false);
const defaultAvatar = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAiIHk9IjUwIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOTk5IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+5aS05YOPPC90ZXh0Pjwvc3ZnPg==';

// 筛选条件
const filters = reactive({
  classId: '',
  examId: '',
  startDate: '',
  endDate: ''
});

// 手动录入数据
const manualEntry = reactive({
  classId: '',
  examId: '',
  subject: '',
  totalScore: 100,
  comments: ''
});

// 从API获取的数据
const classes = ref<any[]>([]);
const exams = ref<any[]>([]);
const scores = ref<any[]>([]);
const availableStudents = ref<any[]>([]);

// 计算属性
const availableExams = computed(() => {
  if (!manualEntry.classId) return exams.value;
  const cidNum = Number(manualEntry.classId);
  return exams.value.filter(exam => {
    const examClassId = exam.class_id ?? exam.classId;
    return examClassId === cidNum || String(examClassId) === String(manualEntry.classId);
  });
});

const selectedStudents = ref<string[]>([]);
const studentScores = ref<Record<string, number>>({});
const selectAllStudents = ref(false);
const loadingStudents = ref(false);

const filteredScores = computed(() => {
  let result = [...scores.value];

  // 搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter(score =>
        (score.student_name || score.studentName || '').toLowerCase().includes(keyword) ||
        (score.student_id || score.studentId || '').toLowerCase().includes(keyword)
    );
  }

  // 筛选
  if (filters.classId) {
    result = result.filter(score => String(score.class_id ?? score.classId) === String(filters.classId));
  }
  if (filters.examId) {
    result = result.filter(score => String(score.exam_id ?? score.examId) === String(filters.examId));
  }
  if (filters.startDate) {
    const startDate = new Date(filters.startDate);
    result = result.filter(score => new Date(score.recorded_at || score.recordedAt) >= startDate);
  }
  if (filters.endDate) {
    const endDate = new Date(filters.endDate);
    endDate.setHours(23, 59, 59, 999);
    result = result.filter(score => new Date(score.recorded_at || score.recordedAt) <= endDate);
  }

  // 排序
  result.sort((a, b) => {
    const aVal = a[sortField.value] || a[sortField.value.replace('_', '')];
    const bVal = b[sortField.value] || b[sortField.value.replace('_', '')];
    if (typeof aVal === 'string' && typeof bVal === 'string') {
      return sortDirection.value === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }
    return sortDirection.value === 'asc' ? (aVal < bVal ? -1 : 1) : (bVal < aVal ? -1 : 1);
  });

  return result;
});

const paginatedScores = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredScores.value.slice(start, end);
});

const totalPages = computed(() => Math.ceil(filteredScores.value.length / pageSize));
const startIndex = computed(() => (currentPage.value - 1) * pageSize);
const endIndex = computed(() => Math.min(startIndex.value + pageSize, filteredScores.value.length));

const extractPercentage = (s: any) => {
  const total = s.total_score ?? s.totalScore ?? 100;
  const percent = s.percentage ?? (total ? (s.score / total) * 100 : 0);
  return Number.isFinite(percent) ? percent : 0;
};

const stats = computed(() => {
  const scoreList = filteredScores.value;
  if (scoreList.length === 0) {
    return { averageScore: 0, highestScore: 0, lowestScore: 0, passRate: 0, stdDeviation: 0 };
  }
  const scoresOnly = scoreList.map(s => Number(s.score) || 0);
  const total = scoresOnly.reduce((sum, v) => sum + v, 0);
  const highest = Math.max(...scoresOnly);
  const lowest = Math.min(...scoresOnly);
  const percentages = scoreList.map(extractPercentage);
  const passCount = percentages.filter(p => p >= 60).length;
  const passRate = (passCount / percentages.length) * 100;
  const meanPercent = percentages.reduce((sum, v) => sum + v, 0) / percentages.length;
  const variance = percentages.reduce((sum, v) => sum + Math.pow(v - meanPercent, 2), 0) / percentages.length;
  const stdDeviation = Math.sqrt(variance);
  return {
    averageScore: total / scoresOnly.length,
    highestScore: highest,
    lowestScore: lowest,
    passRate: Number(passRate.toFixed(1)),
    stdDeviation
  };
});

const distributionData = computed(() => {
  const buckets = [
    { label: '0-59', min: 0, max: 59 },
    { label: '60-69', min: 60, max: 69 },
    { label: '70-79', min: 70, max: 79 },
    { label: '80-89', min: 80, max: 89 },
    { label: '90-100', min: 90, max: 100 }
  ];
  const total = filteredScores.value.length || 1;
  return buckets.map(b => {
    const count = filteredScores.value.filter(s => {
      const p = extractPercentage(s);
      return p >= b.min && p <= b.max;
    }).length;
    return { label: b.label, count, percent: Math.round((count / total) * 100) };
  });
});

// 趋势图数据（使用 Chart.js）
const trendChartData = computed(() => {
  console.log('[趋势图] 计算趋势数据，filteredScores 数量:', filteredScores.value.length);
  
  if (!filteredScores.value.length) {
    console.log('[趋势图] 没有成绩数据');
    return { labels: [], datasets: [] };
  }
  
  const grouped: Record<string, number[]> = {};
  let validCount = 0;
  
  filteredScores.value.forEach((s, idx) => {
    // 尝试多种日期字段名
    const dateStr = s.recorded_at || s.recordedAt || s.created_at || s.createdAt;
    if (!dateStr) {
      console.log(`[趋势图] 第 ${idx} 条记录没有日期字段:`, s);
      return;
    }
    
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) {
        console.log(`[趋势图] 第 ${idx} 条记录日期无效:`, dateStr);
        return;
      }
      
      const key = d.toISOString().slice(0, 10); // YYYY-MM-DD
      if (!grouped[key]) grouped[key] = [];
      const percentage = extractPercentage(s);
      if (Number.isFinite(percentage)) {
        grouped[key].push(percentage);
        validCount++;
      } else {
        console.log(`[趋势图] 第 ${idx} 条记录百分比无效:`, percentage, s);
      }
    } catch (e) {
      console.warn(`[趋势图] 解析日期失败 (第 ${idx} 条):`, dateStr, e);
    }
  });
  
  console.log('[趋势图] 有效记录数:', validCount, '分组数:', Object.keys(grouped).length);
  
  // 按日期排序并计算平均值
  const sortedDates = Object.keys(grouped).sort();
  if (sortedDates.length === 0) {
    console.log('[趋势图] 没有有效的日期分组');
    return { labels: [], datasets: [] };
  }
  
  console.log('[趋势图] 日期分组:', sortedDates);
  
  const labels = sortedDates.map(date => {
    // 格式化日期显示为 MM-DD
    const d = new Date(date);
    return `${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`;
  });
  
  const averages = sortedDates.map(date => {
    const arr = grouped[date];
    const avg = arr.reduce((sum, v) => sum + v, 0) / arr.length;
    return avg;
  });
  
  console.log('[趋势图] 最终数据 - labels:', labels, 'averages:', averages);
  
  return {
    labels,
    datasets: [{
      label: '平均分',
      data: averages,
      borderColor: '#4a6fa5',
      backgroundColor: (context: any) => {
        const ctx = context.chart.ctx;
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(74, 111, 165, 0.3)');
        gradient.addColorStop(1, 'rgba(74, 111, 165, 0.05)');
        return gradient;
      },
      tension: 0.4,
      fill: true,
      pointBackgroundColor: '#ffffff',
      pointBorderColor: '#4a6fa5',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointHoverBackgroundColor: '#4a6fa5',
      pointHoverBorderColor: '#ffffff',
      pointHoverBorderWidth: 2
    }]
  };
});

const trendChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index' as const
  },
  plugins: {
    legend: {
      display: false
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      padding: 12,
      titleFont: {
        size: 14,
        weight: 'bold' as const
      },
      bodyFont: {
        size: 13
      },
      callbacks: {
        title: (context: any) => {
          return `日期: ${context[0].label}`;
        },
        label: (context: any) => {
          return `平均分: ${context.parsed.y.toFixed(1)}分`;
        },
        labelColor: () => ({
          borderColor: '#4a6fa5',
          backgroundColor: '#4a6fa5'
        })
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      max: 100,
      grid: {
        color: 'rgba(0, 0, 0, 0.05)',
        drawBorder: false
      },
      ticks: {
        callback: (value: any) => value + '分',
        font: {
          size: 11
        },
        color: '#666'
      },
      title: {
        display: true,
        text: '平均分',
        font: {
          size: 12,
          weight: 'bold' as const
        },
        color: '#333'
      }
    },
    x: {
      grid: {
        display: false
      },
      ticks: {
        font: {
          size: 11
        },
        color: '#666'
      },
      title: {
        display: true,
        text: '日期',
        font: {
          size: 12,
          weight: 'bold' as const
        },
        color: '#333'
      }
    }
  },
  elements: {
    point: {
      radius: 4,
      hoverRadius: 6,
      backgroundColor: '#ffffff',
      borderWidth: 2,
      borderColor: '#4a6fa5'
    },
    line: {
      borderWidth: 3,
      tension: 0.4
    }
  }
};

// 方法
const sortBy = (field: string) => {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortField.value = field;
    sortDirection.value = 'asc';
  }
};

const sortIcon = (field: string) => {
  if (sortField.value !== field) return 'fas fa-sort';
  return sortDirection.value === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
};

const getScoreClass = (percentage: number) => {
  if (percentage >= 90) return 'score-excellent';
  if (percentage >= 80) return 'score-good';
  if (percentage >= 60) return 'score-pass';
  return 'score-fail';
};

const getScoreTypeText = (type: string) => {
  const map: Record<string, string> = {
    exam: '考试录入',
    manual: '手动录入',
    imported: 'Excel导入'
  };
  return map[type] || type;
};

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 手动录入相关方法
const toggleAllStudents = () => {
  if (selectAllStudents.value) {
    selectedStudents.value = availableStudents.value.map(s => s.id);
    availableStudents.value.forEach(student => {
      studentScores.value[student.id] = 0;
    });
  } else {
    selectedStudents.value = [];
    studentScores.value = {};
  }
};

const onManualClassChange = async () => {
  availableStudents.value = [];
  selectedStudents.value = [];
  studentScores.value = {};
  selectAllStudents.value = false;
  manualEntry.examId = '';
  manualEntry.totalScore = 100;

  if (!manualEntry.classId) return;
  try {
    loadingStudents.value = true;
    const detail = await teacherApi.getClassDetail(Number(manualEntry.classId));
    const list = detail?.students || [];
    availableStudents.value = list.map((s: any) => ({
      id: s.id,
      name: s.name || s.username,
      studentId: s.studentId || s.username
    }));
  } catch (error: any) {
    console.error('加载班级学生失败:', error);
    availableStudents.value = [];
  } finally {
    loadingStudents.value = false;
  }
};

const onManualExamChange = () => {
  if (!manualEntry.examId) {
    manualEntry.totalScore = 100;
    return;
  }
  const exam = availableExams.value.find(e => Number(e.id) === Number(manualEntry.examId));
  if (exam && (exam.total_score || exam.totalScore)) {
    manualEntry.totalScore = exam.total_score || exam.totalScore;
  }
};

const submitManualEntry = async () => {
  if (!manualEntry.classId || !manualEntry.subject || !manualEntry.totalScore) {
    alert('请填写必填字段');
    return;
  }
  if (selectedStudents.value.length === 0) {
    alert('请至少选择一个学生');
    return;
  }
  try {
    const scoresData = selectedStudents.value.map(studentId => ({
      student_id: Number(studentId),
      class_id: Number(manualEntry.classId),
      exam_id: manualEntry.examId ? Number(manualEntry.examId) : null,
      subject: manualEntry.subject,
      score: studentScores.value[studentId] || 0,
      total_score: manualEntry.totalScore,
      comments: manualEntry.comments || ''
    }));
    await teacherApi.createScores({ scores: scoresData });
    await loadScores();
    showManualEntry.value = false;
    resetManualEntry();
    alert('成绩录入成功！');
  } catch (error: any) {
    console.error('录入成绩失败:', error);
    alert('录入成绩失败: ' + (error.response?.data?.message || error.message));
  }
};

const resetManualEntry = () => {
  manualEntry.classId = '';
  manualEntry.examId = '';
  manualEntry.subject = '';
  manualEntry.totalScore = 100;
  manualEntry.comments = '';
  selectedStudents.value = [];
  studentScores.value = {};
  selectAllStudents.value = false;
  availableStudents.value = [];
};

// 导入导出相关方法
const triggerFileInput = () => {
  const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
  fileInput?.click();
};

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    selectedFile.value = input.files[0];
  }
};

const uploadFile = async () => {
  if (!selectedFile.value) return;
  try {
    const response = await teacherApi.importScores(selectedFile.value);
    console.log('导入响应:', response);
    
    await loadScores();
    selectedFile.value = null;
    showImportModal.value = false;
    
    // 检查是否有错误信息
    if (response.errors && response.errors.length > 0) {
      const errorCount = response.errors.length;
      const successCount = response.success_count || 0;
      
      // 显示错误详情
      const errorMessages = response.errors.slice(0, 10).join('\n'); // 最多显示10条错误
      const moreErrors = errorCount > 10 ? `\n\n...还有 ${errorCount - 10} 条错误` : '';
      
      const message = `导入完成！\n成功: ${successCount} 条\n错误: ${errorCount} 条\n\n错误详情：\n${errorMessages}${moreErrors}`;
      
      if (successCount > 0) {
        alert(message);
      } else {
        alert(`导入失败！\n错误: ${errorCount} 条\n\n错误详情：\n${errorMessages}${moreErrors}\n\n请检查Excel文件格式和数据是否正确。`);
      }
    } else {
      const successCount = response.success_count || 0;
      alert(`成绩导入成功！共导入 ${successCount} 条记录`);
    }
  } catch (error: any) {
    console.error('导入成绩失败:', error);
    const errorMsg = error.response?.data?.message || error.message || '未知错误';
    alert('导入成绩失败: ' + errorMsg);
  }
};

const downloadTemplate = async () => {
  try {
    console.log('开始下载模板...');
    const response = await teacherApi.downloadScoreTemplate();
    console.log('收到响应:', response);
    
    // 确保 response 是 Blob
    let blob: Blob;
    if (response instanceof Blob) {
      blob = response;
    } else if (response && typeof response === 'object' && 'data' in response) {
      blob = (response as any).data instanceof Blob 
        ? (response as any).data 
        : new Blob([(response as any).data], { 
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
          });
    } else {
      blob = new Blob([response as any], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
    }
    
    if (blob.size === 0) {
      alert('下载失败：文件为空');
      return;
    }
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = '成绩导入模板.xlsx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    console.log('模板下载成功');
  } catch (error: any) {
    console.error('下载模板失败:', error);
    const errorMsg = error.response?.data?.message || error.message || '未知错误';
    alert('下载模板失败: ' + errorMsg);
  }
};

const exportScores = async () => {
  try {
    const params: any = {};
    if (filters.classId) params.class_id = filters.classId;
    if (filters.startDate) params.start_date = filters.startDate;
    if (filters.endDate) params.end_date = filters.endDate;
    
    console.log('开始导出成绩，参数:', params);
    const response = await teacherApi.exportScores(params);
    console.log('导出响应:', response);
    console.log('响应类型:', typeof response);
    console.log('是否为 Blob:', response instanceof Blob);
    
    // 确保 response 是 Blob
    let blob: Blob;
    if (response instanceof Blob) {
      blob = response;
    } else if (response && typeof response === 'object' && 'data' in response) {
      // 如果响应是 axios 响应对象
      blob = (response as any).data instanceof Blob 
        ? (response as any).data 
        : new Blob([(response as any).data], { 
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
          });
    } else {
      // 尝试转换为 Blob
      blob = new Blob([response as any], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
    }
    
    console.log('Blob 大小:', blob.size);
    
    if (blob.size === 0) {
      alert('导出失败：文件为空');
      return;
    }
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `成绩导出_${new Date().toISOString().split('T')[0]}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    alert('成绩导出成功！');
  } catch (error: any) {
    console.error('导出成绩失败:', error);
    console.error('错误详情:', error.response);
    const errorMsg = error.response?.data?.message || error.message || '未知错误';
    alert('导出成绩失败: ' + errorMsg);
  }
};

// 其他操作方法
const editScore = (score: any) => {
  alert(`编辑成绩: ${score.student_name || score.studentName} - ${score.score}分`);
};

const viewDetails = (score: any) => {
  selectedScore.value = score;
};

const deleteScore = async (scoreId: string | number) => {
  if (!confirm('确定要删除这条成绩记录吗？')) return;
  try {
    await teacherApi.deleteScore(Number(scoreId));
    await loadScores();
    alert('成绩记录已删除');
  } catch (error: any) {
    console.error('删除成绩失败:', error);
    alert('删除成绩失败: ' + (error.response?.data?.message || error.message));
  }
};

const applyFilters = () => {
  currentPage.value = 1;
  loadScores();
};

const resetFilters = () => {
  filters.classId = '';
  filters.examId = '';
  filters.startDate = '';
  filters.endDate = '';
  searchKeyword.value = '';
  currentPage.value = 1;
  loadScores();
};

// 防抖函数
const debounce = (func: Function, wait: number) => {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  return function executedFunction(...args: any[]) {
    const later = () => {
      timeout = null;
      func(...args);
    };
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

const searchScores = () => {
  currentPage.value = 1;
  loadScores();
};

// 使用防抖的搜索函数（延迟500ms执行）
const debouncedSearch = debounce(searchScores, 500);

// 监听搜索关键词变化，使用防抖避免频繁请求和页面重新渲染
watch(searchKeyword, () => {
  if (searchKeyword.value.trim() === '') {
    // 如果搜索关键词为空，立即重置
    searchScores();
  } else {
    // 否则使用防抖，避免每次输入都触发搜索
    debouncedSearch();
  }
});

const refreshScores = () => {
  loadScores();
};

const prevPage = () => {
  if (currentPage.value > 1) currentPage.value--;
};

const nextPage = () => {
  if (currentPage.value < totalPages.value) currentPage.value++;
};

// 数据加载
const loadClasses = async () => {
  try {
    const res = await teacherApi.getClasses();
    classes.value = Array.isArray(res) ? res : (res?.data || []);
  } catch (error: any) {
    console.error('加载班级失败:', error);
  }
};

const loadExams = async () => {
  try {
    const res = await teacherApi.getExams();
    exams.value = Array.isArray(res) ? res : (res?.data || []);
  } catch (error: any) {
    console.error('加载考试失败:', error);
  }
};

const loadScores = async () => {
  isLoading.value = true;
  try {
    const params: any = {
      page: currentPage.value,
      per_page: pageSize
    };
    if (filters.classId) params.class_id = filters.classId;
    if (filters.examId) params.exam_id = filters.examId;
    if (filters.startDate) params.start_date = filters.startDate;
    if (filters.endDate) params.end_date = filters.endDate;
    if (searchKeyword.value) params.student_name = searchKeyword.value;

    const res = await teacherApi.getScores(params);
    scores.value = Array.isArray(res) ? res : (res?.data || []);
    console.log('[成绩管理] 加载成绩数据:', scores.value.length, '条');
    if (scores.value.length > 0) {
      console.log('[成绩管理] 第一条成绩数据:', scores.value[0]);
      console.log('[成绩管理] 第一条成绩日期字段:', {
        recorded_at: scores.value[0].recorded_at,
        recordedAt: scores.value[0].recordedAt,
        created_at: scores.value[0].created_at,
        createdAt: scores.value[0].createdAt
      });
    }
  } catch (error: any) {
    console.error('加载成绩失败:', error);
    alert('加载成绩失败: ' + (error.response?.data?.message || error.message));
  } finally {
    isLoading.value = false;
  }
};

// 初始化
onMounted(async () => {
  const end = new Date();
  const start = new Date();
  start.setMonth(start.getMonth() - 1);
  filters.startDate = start.toISOString().split('T')[0];
  filters.endDate = end.toISOString().split('T')[0];
  await Promise.all([loadClasses(), loadExams(), loadScores()]);
});
</script>

<style scoped>
.score-manager {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.header-left h2 {
  margin: 0 0 8px 0;
  color: #1f2328;
  font-size: 24px;
  font-weight: 600;
}

.header-left p {
  margin: 0;
  color: #656d76;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 统一按钮样式 */
.btn-primary,
.btn-secondary,
.btn-success,
.btn-outline {
  padding: 10px 20px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-primary {
  background: #4a6fa5;
  color: white;
}

.btn-primary:hover {
  background: #3a5a8c;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(74, 111, 165, 0.3);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(108, 117, 125, 0.3);
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover {
  background: #218838;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
}

.btn-outline {
  background: white;
  color: #4a6fa5;
  border: 1px solid #4a6fa5;
}

.btn-outline:hover {
  background: #f0f7ff;
  border-color: #3a5a8c;
  transform: translateY(-1px);
}

.btn-icon {
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  transition: all 0.3s ease;
}

.btn-icon:hover {
  background: #f8f9fa;
  border-color: #4a6fa5;
  color: #4a6fa5;
}

.btn-icon.danger {
  color: #dc3545;
  border-color: #dc3545;
}

.btn-icon.danger:hover {
  background: #dc3545;
  color: white;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #f0f0f0;
  color: #333;
}

/* 按钮禁用状态 */
button:disabled,
.btn-primary:disabled,
.btn-secondary:disabled,
.btn-success:disabled,
.btn-outline:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

/* 筛选区域 */
.filter-section {
  background: #ffffff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 0;
}

.filter-row {
  display: flex;
  gap: 24px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-group {
  flex: 1;
  min-width: 200px;
}

.filter-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.filter-group select,
.filter-group input[type="date"] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.date-range {
  display: flex;
  gap: 8px;
  align-items: center;
}

.date-range span {
  color: #666;
  font-size: 14px;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-card:nth-child(1) .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card:nth-child(2) .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card:nth-child(3) .stat-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-card:nth-child(4) .stat-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
  line-height: 1;
}

.stat-label {
  color: #666;
  font-size: 14px;
  margin-top: 4px;
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-header h4 {
  margin: 0;
  font-size: 16px;
}

.chart-hint {
  color: #888;
  font-size: 12px;
}

.histogram {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.histogram-bar {
  display: grid;
  grid-template-columns: 70px 1fr 60px;
  gap: 8px;
  align-items: center;
}

.histogram-label {
  font-size: 13px;
  color: #555;
}

.histogram-track {
  background: #f2f4f7;
  border-radius: 999px;
  height: 10px;
  overflow: hidden;
}

.histogram-fill {
  height: 100%;
  background: linear-gradient(90deg, #4a6fa5, #7fa7e1);
}

.histogram-count {
  font-size: 13px;
  color: #333;
  text-align: right;
}

.line-chart-container {
  height: 400px;
  width: 100%;
  position: relative;
  background: linear-gradient(135deg, #f8f9fb 0%, #ffffff 100%);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.line-chart {
  height: 200px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chart-empty {
  height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #888;
  background: linear-gradient(135deg, #f8f9fb 0%, #ffffff 100%);
  border-radius: 12px;
  font-size: 14px;
  padding: 20px;
}

.trend-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: #555;
}

/* 表格区域 */
.scores-table-container {
  background: #ffffff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  overflow: hidden;
}

.table-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-header h3 {
  margin: 0;
  color: #333;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  width: 250px;
  font-size: 14px;
}

.table-responsive {
  overflow-x: auto;
}

.scores-table {
  width: 100%;
  border-collapse: collapse;
}

.scores-table th {
  background: #f8f9fa;
  padding: 16px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #e0e0e0;
  position: relative;
  cursor: pointer;
  user-select: none;
}

.scores-table th.sortable:hover {
  background: #e9ecef;
}

.scores-table th i {
  margin-left: 8px;
  color: #999;
}

.scores-table td {
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
  vertical-align: middle;
}

.scores-table tbody tr:hover {
  background: #f8f9fa;
}

/* 学生信息单元格 */
.student-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.student-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e0e0e0;
  object-fit: cover;
}

/* 分数样式 */
.score-value {
  font-weight: bold;
}

.score-excellent {
  color: #28a745;
}

.score-good {
  color: #17a2b8;
}

.score-pass {
  color: #ffc107;
}

.score-fail {
  color: #dc3545;
}

/* 百分比进度条 */
.percentage-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.percentage-text {
  width: 50px;
  font-weight: 500;
}

.percentage-track {
  flex: 1;
  height: 6px;
  background: #e0e0e0;
  border-radius: 3px;
  overflow: hidden;
}

.percentage-fill {
  height: 100%;
  transition: width 0.3s;
}

/* 成绩类型标签 */
.score-type-exam {
  background: #e3f2fd;
  color: #1976d2;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.score-type-manual {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.score-type-imported {
  background: #fff3e0;
  color: #f57c00;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-icon.small {
  width: 32px;
  height: 32px;
  padding: 0;
  font-size: 14px;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-top: 1px solid #e0e0e0;
}

.pagination-info {
  color: #666;
  font-size: 14px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.pagination-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pagination-btn:hover:not(:disabled) {
  background: #f8f9fa;
  border-color: #4a6fa5;
  color: #4a6fa5;
  transform: translateY(-1px);
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f8f9fa;
}

.pagination-current {
  color: #333;
  font-weight: 500;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: white;
  border-radius: 8px;
  width: 600px;
  max-width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal.modal-lg {
  width: 800px;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.modal-body {
  padding: 24px;
}

/* 表单样式 */
.form-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.form-group {
  flex: 1;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.form-group textarea {
  resize: vertical;
}

.form-section {
  margin: 24px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 6px;
}

.form-section h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.student-selection {
  max-height: 300px;
  overflow-y: auto;
}

.select-all {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ddd;
}

.students-grid {
  display: grid;
  gap: 12px;
}

.student-score-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

.student-score-item label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  cursor: pointer;
}

.score-input {
  width: 100px;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
}

/* 导入选项 */
.import-options {
  display: grid;
  gap: 30px;
}

.import-option,
.import-template {
  text-align: center;
}

.file-drop-zone {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px 20px;
  margin: 20px 0;
  cursor: pointer;
  transition: all 0.3s;
}

.file-drop-zone:hover {
  border-color: #4a6fa5;
  background: #f8f9fa;
}

.selected-file {
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

/* 成绩详情 */
.score-detail {
  display: grid;
  gap: 16px;
}

.detail-row {
  display: flex;
}

.detail-label {
  width: 120px;
  font-weight: 500;
  color: #666;
}

.detail-value {
  flex: 1;
  color: #333;
}

.score-value-large {
  font-size: 24px;
  font-weight: bold;
  color: #4a6fa5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .filter-row {
    flex-direction: column;
  }

  .form-row {
    flex-direction: column;
  }

  .table-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .table-actions {
    width: 100%;
  }

  .search-input {
    flex: 1;
  }

  .pagination {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
}
.stat-card:nth-child(5) .stat-icon {
  background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);
}
</style>