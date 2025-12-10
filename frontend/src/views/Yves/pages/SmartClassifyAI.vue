<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import materialTools from '../tools/MaterialTools'
import classifyTools from '../tools/ClassifyTools'
import baseInfoTools from '../tools/BaseInfoTools'

const route = useRoute()
const router = useRouter()

// 从路由获取参数
const nodeId = ref<number>(parseInt(route.query.nodeId as string) || 0)
const nodeName = ref<string>(route.query.nodeName as string || '根目录')

// 用户信息
const account = baseInfoTools.getAccountInfo(1)

// AI分类结果
interface ClassificationResult {
  node_id: number
  name: string
  category: string
  description: string
  confidence: number
  keywords: string[]
}

const classificationResults = ref<ClassificationResult[]>([])
const loading = ref(false)
const classifying = ref(false)
const classifyStep = ref<'loading' | 'classifying' | 'result'>('loading')

// 分类统计
const classificationStats = ref<Record<string, { count: number, avgConfidence: number }>>({})

// 视图模式
const viewMode = ref<'list' | 'grouped'>('grouped')

// 选择状态
const selectedFiles = ref<Set<number>>(new Set())
const selectAll = ref(false)

// 按分类分组的文件
const groupedFiles = computed(() => {
  const groups: Record<string, ClassificationResult[]> = {}
  
  classificationResults.value.forEach(file => {
    const category = file.category || '其他资料'
    if (!groups[category]) {
      groups[category] = []
    }
    groups[category].push(file)
  })
  
  return groups
})

// 加载文件并进行AI分类
async function loadAndClassifyFiles() {
  if (!nodeId.value) return
  
  classifyStep.value = 'loading'
  loading.value = true
  
  try {
    // 调用后端AI分类接口
    classifyStep.value = 'classifying'
    classifying.value = true
    
    const response = await classifyTools.classifyNode(nodeId.value)
    
    // 处理分类结果
    classificationResults.value = response.files || []
    
    // 统计分类结果
    const stats: Record<string, { count: number, totalConfidence: number }> = {}
    
    classificationResults.value.forEach(file => {
      const category = file.category
      if (!stats[category]) {
        stats[category] = { count: 0, totalConfidence: 0 }
      }
      stats[category].count++
      stats[category].totalConfidence += file.confidence
    })
    
    // 计算平均置信度
    Object.keys(stats).forEach(category => {
      classificationStats.value[category] = {
        count: stats[category].count,
        avgConfidence: Math.round(stats[category].totalConfidence / stats[category].count)
      }
    })
    
    // 显示结果
    classifyStep.value = 'result'
    
  } catch (error: any) {
    alert('AI分类失败: ' + error.message)
    classifyStep.value = 'result'
  } finally {
    loading.value = false
    classifying.value = false
  }
}

// 保存分类结果
async function saveClassifications() {
  if (classificationResults.value.length === 0) {
    alert('没有分类数据需要保存')
    return
  }
  
  try {
    await classifyTools.saveAIClassifications({
      classifications: classificationResults.value,
      classified_by: account.name
    })
    
    alert(`分类保存成功！共保存 ${classificationResults.value.length} 个文件的分类结果`)
    router.back()
  } catch (error: any) {
    alert('保存失败: ' + error.message)
  }
}

// 切换全选
function toggleSelectAll() {
  if (selectAll.value) {
    classificationResults.value.forEach(file => selectedFiles.value.add(file.node_id))
  } else {
    selectedFiles.value.clear()
  }
}

// 返回
function goBack() {
  router.back()
}

// 格式化文件大小
function formatSize(size: number | string): string {
  if (typeof size === 'string') return size
  if (!size) return '-'
  
  const units = ['B', 'KB', 'MB', 'GB']
  let index = 0
  let fileSize = size
  
  while (fileSize >= 1024 && index < units.length - 1) {
    fileSize /= 1024
    index++
  }
  
  return `${fileSize.toFixed(2)} ${units[index]}`
}

// 获取分类图标
function getCategoryIcon(category: string): string {
  const iconMap: Record<string, string> = {
    '课程资料': '📚',
    '作业习题': '📝',
    '考试试卷': '📋',
    '实验报告': '🔬',
    '项目文档': '📁',
    '参考资料': '📖',
    '多媒体资料': '🎬',
    '代码程序': '💻',
    '数据文件': '📊',
    '其他资料': '📄'
  }
  return iconMap[category] || '📄'
}

// 获取分类颜色
function getCategoryColor(category: string): string {
  const colorMap: Record<string, string> = {
    '课程资料': '#3b82f6',
    '作业习题': '#10b981',
    '考试试卷': '#f59e0b',
    '实验报告': '#8b5cf6',
    '项目文档': '#ec4899',
    '参考资料': '#06b6d4',
    '多媒体资料': '#6366f1',
    '代码程序': '#84cc16',
    '数据文件': '#10b981',
    '其他资料': '#6b7280'
  }
  return colorMap[category] || '#667eea'
}

// 获取置信度颜色
function getConfidenceColor(confidence: number): string {
  if (confidence >= 80) return '#10b981'  // 绿色
  if (confidence >= 60) return '#f59e0b'  // 橙色
  return '#ef4444'  // 红色
}

onMounted(() => {
  loadAndClassifyFiles()
})
</script>

<template>
  <div class="smart-classify-page">
    <div class="header">
      <div class="title-section">
        <button class="back-btn" @click="goBack">← 返回</button>
        <h1>🤖 AI智能分类</h1>
        <p class="subtitle">当前目录：{{ nodeName }}</p>
        <p class="ai-info">使用豆包AI进行智能内容分析</p>
      </div>
      
      <div class="actions">
        <button class="btn btn-primary" @click="saveClassifications">
          💾 保存分类结果
        </button>
      </div>
    </div>

    <!-- 分类进度 -->
    <div v-if="classifyStep === 'loading'" class="loading">
      <div class="spinner"></div>
      <p>正在加载文件...</p>
    </div>

    <div v-else-if="classifyStep === 'classifying'" class="loading">
      <div class="spinner"></div>
      <p>🤖 AI正在智能分析中...</p>
      <p class="sub-text">正在分析文件内容和上下文</p>
    </div>

    <!-- 分类统计 -->
    <div v-else-if="classifyStep === 'result' && classificationResults.length > 0" class="stats-section">
      <h3>📊 分类统计</h3>
      <div class="stats-grid">
        <div
          v-for="(stat, category) in classificationStats"
          :key="category"
          class="stat-card"
        >
          <div class="stat-icon" :style="{ backgroundColor: getCategoryColor(category) }">
            {{ getCategoryIcon(category) }}
          </div>
          <div class="stat-info">
            <div class="stat-name">{{ category }}</div>
            <div class="stat-count">{{ stat.count }} 个文件</div>
            <div class="stat-confidence">
              平均置信度: 
              <span :style="{ color: getConfidenceColor(stat.avgConfidence) }">
                {{ stat.avgConfidence }}%
              </span>
            </div>
          </div>
        </div>
      </div>
      <div class="total-info">
        <span>共分类 <strong>{{ classificationResults.length }}</strong> 个文件</span>
      </div>
    </div>

    <!-- 视图切换 -->
    <div v-if="classifyStep === 'result' && classificationResults.length > 0" class="controls-bar">
      <div class="view-toggle">
        <button
          class="toggle-btn"
          :class="{ active: viewMode === 'grouped' }"
          @click="viewMode = 'grouped'"
        >
          📁 分组视图
        </button>
        <button
          class="toggle-btn"
          :class="{ active: viewMode === 'list' }"
          @click="viewMode = 'list'"
        >
          📄 列表视图
        </button>
      </div>
      
      <div class="batch-actions">
        <label class="checkbox-label">
          <input type="checkbox" v-model="selectAll" @change="toggleSelectAll" />
          <span>全选</span>
        </label>
        <span class="selected-info">已选择 {{ selectedFiles.size }} 项</span>
      </div>
    </div>

    <!-- 分组视图 -->
    <div v-if="classifyStep === 'result' && viewMode === 'grouped'" class="grouped-section">
      <div v-for="(categoryFiles, category) in groupedFiles" :key="category" class="category-group">
        <div class="category-header">
          <div class="category-title">
            <span class="category-icon" :style="{ backgroundColor: getCategoryColor(category) }">
              {{ getCategoryIcon(category) }}
            </span>
            <h3>{{ category }}</h3>
            <span class="category-count">{{ categoryFiles.length }} 个文件</span>
          </div>
        </div>
        
        <div class="category-files">
          <div v-for="file in categoryFiles" :key="file.node_id" class="file-card-compact">
            <label class="checkbox-label">
              <input
                type="checkbox"
                :checked="selectedFiles.has(file.node_id)"
                @change="() => {
                  if (selectedFiles.has(file.node_id)) {
                    selectedFiles.delete(file.node_id)
                  } else {
                    selectedFiles.add(file.node_id)
                  }
                }"
              />
            </label>
            
            <div class="file-info-compact">
              <span class="file-icon-small">📄</span>
              <div class="file-details-compact">
                <span class="file-name-compact" :title="file.name">{{ file.name }}</span>
                <span class="file-desc">{{ file.description }}</span>
              </div>
            </div>
            
            <div class="file-meta">
              <span class="confidence-badge" :style="{ backgroundColor: getConfidenceColor(file.confidence) }">
                {{ file.confidence }}%
              </span>
              <div class="keywords" v-if="file.keywords && file.keywords.length > 0">
                <span v-for="keyword in file.keywords.slice(0, 3)" :key="keyword" class="keyword-tag">
                  {{ keyword }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 列表视图 -->
    <div v-else-if="classifyStep === 'result' && viewMode === 'list'" class="files-section">
      <div v-for="file in classificationResults" :key="file.node_id" class="file-card">
        <div class="file-header">
          <label class="checkbox-label">
            <input
              type="checkbox"
              :checked="selectedFiles.has(file.node_id)"
              @change="() => {
                if (selectedFiles.has(file.node_id)) {
                  selectedFiles.delete(file.node_id)
                } else {
                  selectedFiles.add(file.node_id)
                }
              }"
            />
          </label>
          
          <div class="file-info">
            <span class="file-icon">📄</span>
            <div class="file-details">
              <span class="file-name">{{ file.name }}</span>
              <span class="file-category">
                {{ getCategoryIcon(file.category) }} {{ file.category }}
              </span>
            </div>
          </div>

          <div class="file-classification">
            <div class="classification-info">
              <span class="label">分类描述：</span>
              <span class="value">{{ file.description }}</span>
            </div>
            <div class="classification-meta">
              <span class="confidence" :style="{ color: getConfidenceColor(file.confidence) }">
                置信度: {{ file.confidence }}%
              </span>
              <div class="keywords" v-if="file.keywords && file.keywords.length > 0">
                <span class="label">关键词：</span>
                <span v-for="keyword in file.keywords" :key="keyword" class="keyword-tag">
                  {{ keyword }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="classificationResults.length === 0" class="empty">
        <div class="icon">📂</div>
        <p>当前目录没有文件</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.smart-classify-page {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid #e5e7eb;
}

.title-section h1 {
  margin: 0.5rem 0;
  color: #1f2937;
  font-size: 2rem;
}

.subtitle {
  color: #6b7280;
  margin: 0.25rem 0;
}

.ai-info {
  color: #10b981;
  font-size: 0.875rem;
  margin: 0.25rem 0;
  font-weight: 500;
}

.back-btn {
  border: none;
  background: none;
  color: #667eea;
  font-size: 1rem;
  cursor: pointer;
  padding: 0.5rem 0;
  transition: all 0.2s;
}

.back-btn:hover {
  color: #5568d3;
}

.actions {
  display: flex;
  gap: 1rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* 加载状态 */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
  color: #6b7280;
}

.loading .sub-text {
  font-size: 0.875rem;
  color: #9ca3af;
  margin: 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 分类统计 */
.stats-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.stats-section h3 {
  margin: 0 0 1.5rem 0;
  color: #1f2937;
  font-size: 1.1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  transition: all 0.2s;
}

.stat-card:hover {
  background: #f3f4f6;
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 1.5rem;
  color: white;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.stat-count {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.stat-confidence {
  font-size: 0.75rem;
  color: #9ca3af;
}

.total-info {
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
  text-align: center;
  color: #6b7280;
}

.total-info strong {
  color: #667eea;
  font-size: 1.2rem;
}

/* 控制栏 */
.controls-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  gap: 1rem;
  flex-wrap: wrap;
}

.view-toggle {
  display: flex;
  gap: 0.5rem;
}

.toggle-btn {
  padding: 0.5rem 1rem;
  border: 1px solid #e5e7eb;
  background: white;
  color: #6b7280;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-btn:hover {
  background: #f9fafb;
}

.toggle-btn.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-color: transparent;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.selected-info {
  font-size: 0.875rem;
  color: #667eea;
  font-weight: 600;
}

/* 分组视图 */
.grouped-section {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.category-group {
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.category-header {
  padding: 1.5rem;
  background: linear-gradient(135deg, #f9fafb, #ffffff);
  border-bottom: 2px solid #e5e7eb;
}

.category-title {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.category-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 1.5rem;
  color: white;
  flex-shrink: 0;
}

.category-title h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.25rem;
  flex: 1;
}

.category-count {
  padding: 0.5rem 1rem;
  background: #667eea;
  color: white;
  border-radius: 999px;
  font-size: 0.875rem;
  font-weight: 600;
}

.category-files {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 1px;
  background: #e5e7eb;
}

.file-card-compact {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: white;
  transition: all 0.2s;
}

.file-card-compact:hover {
  background: #f9fafb;
}

.file-info-compact {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.file-icon-small {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.file-details-compact {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
  flex: 1;
}

.file-name-compact {
  font-weight: 500;
  color: #1f2937;
  font-size: 0.875rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-desc {
  font-size: 0.75rem;
  color: #6b7280;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.confidence-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
}

.keywords {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.keyword-tag {
  padding: 0.25rem 0.5rem;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 4px;
  font-size: 0.7rem;
}

/* 列表视图 */
.files-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.file-card {
  padding: 1.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  transition: all 0.2s;
}

.file-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.file-header {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.file-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.file-icon {
  font-size: 1.5rem;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.file-name {
  font-weight: 500;
  color: #1f2937;
}

.file-category {
  font-size: 0.875rem;
  color: #667eea;
  font-weight: 500;
}

.file-classification {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.classification-info {
  display: flex;
  gap: 0.5rem;
}

.classification-info .label {
  font-size: 0.875rem;
  color: #6b7280;
}

.classification-info .value {
  font-size: 0.875rem;
  color: #1f2937;
}

.classification-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.confidence {
  font-size: 0.875rem;
  font-weight: 600;
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
  color: #9ca3af;
}

.empty .icon {
  font-size: 4rem;
  opacity: 0.5;
}
</style>
