<script setup lang="ts">
import { ref, computed } from 'vue'
import classifyTools from '../../tools/ClassifyTools'
import { MaterialItem } from '../../tools/MaterialTools'

const props = defineProps<{
  visible: boolean
  nodeId: number | null
  nodeName: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'organized'): void
}>()

// 分类结果
const classificationResult = ref<any>(null)
const loading = ref(false)
const organizing = ref(false)

// 分类统计
const categoryStats = computed(() => {
  if (!classificationResult.value) return []
  
  const stats = []
  for (const [category, data] of Object.entries(classificationResult.value.classification)) {
    stats.push({
      name: category,
      count: (data as any).count,
      files: (data as any).files
    })
  }
  
  return stats.sort((a, b) => b.count - a.count)
})

// 总文件数
const totalFiles = computed(() => {
  return classificationResult.value?.total_files || 0
})

// 分析文件分类
async function analyzeClassification() {
  if (!props.nodeId) return
  
  loading.value = true
  try {
    const response = await classifyTools.classifyNode(props.nodeId)
    classificationResult.value = response
  } catch (error: any) {
    alert(error.message || '分析失败')
  } finally {
    loading.value = false
  }
}

// 自动整理
async function autoOrganize() {
  if (!props.nodeId) return
  
  if (!confirm('确定要自动整理文件吗？\n系统将创建分类文件夹并移动文件。')) {
    return
  }
  
  organizing.value = true
  try {
    const response = await classifyTools.autoOrganize(props.nodeId, true)
    alert(response.message || '整理完成')
    emit('organized')
    emit('close')
  } catch (error: any) {
    alert(error.message || '整理失败')
  } finally {
    organizing.value = false
  }
}

// 获取分类颜色
function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    '文档': '#3b82f6',
    '表格': '#10b981',
    '演示文稿': '#f59e0b',
    '图片': '#ec4899',
    '视频': '#8b5cf6',
    '音频': '#06b6d4',
    '代码': '#6366f1',
    '压缩包': '#84cc16',
    '其他': '#6b7280'
  }
  return colors[category] || '#6b7280'
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

// 监听 visible 变化，自动分析
import { watch } from 'vue'
watch(() => props.visible, (newVisible) => {
  if (newVisible && props.nodeId) {
    analyzeClassification()
  }
})
</script>

<template>
  <div v-if="visible" class="classify-mask" @click.self="emit('close')">
    <div class="classify-panel">
      <div class="header">
        <h2>📊 智能分类分析</h2>
        <button class="close-btn" @click="emit('close')">×</button>
      </div>

      <div class="content">
        <div class="node-info">
          <span class="label">当前目录：</span>
          <span class="value">{{ nodeName }}</span>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>正在分析文件...</p>
        </div>

        <!-- 分类结果 -->
        <div v-else-if="classificationResult" class="result">
          <div class="summary">
            <div class="summary-item">
              <div class="number">{{ totalFiles }}</div>
              <div class="label">总文件数</div>
            </div>
            <div class="summary-item">
              <div class="number">{{ categoryStats.length }}</div>
              <div class="label">分类数量</div>
            </div>
          </div>

          <div class="categories">
            <div
              v-for="stat in categoryStats"
              :key="stat.name"
              class="category-card"
            >
              <div class="category-header">
                <div class="category-name">
                  <span
                    class="color-dot"
                    :style="{ backgroundColor: getCategoryColor(stat.name) }"
                  ></span>
                  <span class="name">{{ stat.name }}</span>
                </div>
                <div class="category-count">{{ stat.count }} 个文件</div>
              </div>

              <div class="file-list">
                <div
                  v-for="file in stat.files"
                  :key="file.node_id"
                  class="file-item"
                >
                  <span class="file-icon">📄</span>
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatSize(file.size) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty">
          <div class="icon">📂</div>
          <p>暂无分类数据</p>
        </div>
      </div>

      <div class="footer">
        <button class="btn btn-secondary" @click="emit('close')">
          取消
        </button>
        <button
          class="btn btn-primary"
          @click="autoOrganize"
          :disabled="!classificationResult || organizing || totalFiles === 0"
        >
          <span v-if="organizing">整理中...</span>
          <span v-else>🗂️ 自动整理</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.classify-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: fadeIn 0.2s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.classify-panel {
  width: min(900px, 90vw);
  max-height: 85vh;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.header h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #1f2937;
}

.close-btn {
  border: none;
  background: none;
  font-size: 2rem;
  color: #9ca3af;
  cursor: pointer;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.node-info {
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.node-info .label {
  color: #6b7280;
  font-size: 0.875rem;
}

.node-info .value {
  color: #1f2937;
  font-weight: 500;
  margin-left: 0.5rem;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
  color: #6b7280;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.result {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.summary-item {
  padding: 1.5rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 12px;
  text-align: center;
  color: white;
}

.summary-item .number {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.summary-item .label {
  font-size: 0.875rem;
  opacity: 0.9;
}

.categories {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.category-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
}

.category-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.category-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #1f2937;
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.category-count {
  font-size: 0.875rem;
  color: #6b7280;
}

.file-list {
  max-height: 200px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  transition: background 0.2s;
}

.file-item:last-child {
  border-bottom: none;
}

.file-item:hover {
  background: #f9fafb;
}

.file-icon {
  font-size: 1.25rem;
}

.file-name {
  flex: 1;
  font-size: 0.875rem;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 0.75rem;
  color: #9ca3af;
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

.footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.btn {
  padding: 0.625rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
</style>
