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

// 文件列表
const files = ref<any[]>([])
const loading = ref(false)
const classifying = ref(false)
const classifyStep = ref<'loading' | 'classifying' | 'result'>('loading')

// 标签管理
const tags = ref<any[]>([])
const showTagDialog = ref(false)
const newTagName = ref('')
const newTagColor = ref('#667eea')
const newTagDescription = ref('')

// 分类状态
const fileClassifications = ref<Map<number, number[]>>(new Map())
const selectedFiles = ref<Set<number>>(new Set())
const selectAll = ref(false)

// 自动分类建议
const autoSuggestions = ref<Map<number, string>>(new Map())

// 分类统计
const classificationStats = ref<Record<string, number>>({})

// 颜色选项
const colorOptions = [
  '#3b82f6', '#10b981', '#f59e0b', '#ec4899',
  '#8b5cf6', '#06b6d4', '#6366f1', '#84cc16', '#6b7280'
]

// 加载标签
async function loadTags() {
  try {
    const response = await classifyTools.getTags()
    tags.value = response.tags || []
  } catch (error: any) {
    console.error('加载标签失败:', error)
  }
}

// 递归获取所有文件（包括子目录）
async function getAllFilesRecursive(nodeId: number): Promise<any[]> {
  const allFiles: any[] = []
  
  const data = await materialTools.getNextDepthTree(nodeId)
  
  for (const item of data) {
    if (item.type === 'file') {
      allFiles.push({
        ...item,
        node_id: item.node_id || item.id
      })
    } else if (item.type === 'folder') {
      // 递归获取子文件夹中的文件
      const subFiles = await getAllFilesRecursive(item.node_id || item.id)
      allFiles.push(...subFiles)
    }
  }
  
  return allFiles
}

// 加载文件列表并自动分类
async function loadFiles() {
  if (!nodeId.value) return
  
  classifyStep.value = 'loading'
  loading.value = true
  
  try {
    // 获取根目录下的所有文件（递归）
    files.value = await getAllFilesRecursive(nodeId.value)
    
    if (files.value.length === 0) {
      classifyStep.value = 'result'
      loading.value = false
      return
    }
    
    // 开始自动分类
    classifyStep.value = 'classifying'
    classifying.value = true
    
    // 生成自动分类建议
    generateAutoSuggestions()
    
    // 自动应用分类建议
    await autoClassifyAllFiles()
    
    // 加载每个文件的分类
    await loadFileClassifications()
    
    // 显示结果
    classifyStep.value = 'result'
    
  } catch (error: any) {
    alert('加载文件失败: ' + error.message)
    classifyStep.value = 'result'
  } finally {
    loading.value = false
    classifying.value = false
  }
}

// 加载文件分类
async function loadFileClassifications() {
  for (const file of files.value) {
    try {
      const response = await classifyTools.getFileClassifications(file.node_id)
      const tagIds = response.classifications.map((c: any) => c.tag_id)
      fileClassifications.value.set(file.node_id, tagIds)
    } catch (error) {
      fileClassifications.value.set(file.node_id, [])
    }
  }
}

// 生成自动分类建议
function generateAutoSuggestions() {
  const stats: Record<string, number> = {}
  
  files.value.forEach(file => {
    const category = smartClassify(file.name)
    autoSuggestions.value.set(file.node_id, category)
    
    // 统计分类数量
    stats[category] = (stats[category] || 0) + 1
  })
  
  classificationStats.value = stats
}

// 自动分类所有文件
async function autoClassifyAllFiles() {
  // 确保所有分类标签都存在
  const categories = new Set(autoSuggestions.value.values())
  
  for (const category of categories) {
    // 检查标签是否存在
    let tag = tags.value.find(t => t.name === category)
    
    if (!tag) {
      // 自动创建标签
      try {
        const result = await classifyTools.createTag({
          name: category,
          color: getCategoryColor(category),
          description: `自动生成的${category}分类标签`
        })
        
        // 重新加载标签
        await loadTags()
        tag = tags.value.find(t => t.name === category)
      } catch (error) {
        console.error(`创建标签失败: ${category}`, error)
      }
    }
  }
  
  // 应用分类到所有文件
  files.value.forEach(file => {
    const suggestion = autoSuggestions.value.get(file.node_id)
    if (suggestion) {
      const tag = tags.value.find(t => t.name === suggestion)
      if (tag) {
        fileClassifications.value.set(file.node_id, [tag.id])
      }
    }
  })
}

// 获取分类对应的颜色
function getCategoryColor(category: string): string {
  const colorMap: Record<string, string> = {
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
  return colorMap[category] || '#667eea'
}

// 简单的分类算法
function smartClassify(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  
  const categories: Record<string, string[]> = {
    '文档': ['doc', 'docx', 'pdf', 'txt', 'md', 'rtf'],
    '表格': ['xls', 'xlsx', 'csv'],
    '演示文稿': ['ppt', 'pptx'],
    '图片': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'],
    '视频': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv'],
    '音频': ['mp3', 'wav', 'flac', 'aac', 'm4a'],
    '代码': ['py', 'js', 'ts', 'java', 'c', 'cpp', 'go'],
    '压缩包': ['zip', 'rar', '7z', 'tar', 'gz']
  }
  
  for (const [category, extensions] of Object.entries(categories)) {
    if (extensions.includes(ext)) {
      return category
    }
  }
  
  return '其他'
}

// 创建新标签
async function createTag() {
  if (!newTagName.value.trim()) {
    alert('请输入标签名称')
    return
  }
  
  try {
    await classifyTools.createTag({
      name: newTagName.value.trim(),
      color: newTagColor.value,
      description: newTagDescription.value
    })
    
    await loadTags()
    
    // 重置表单
    newTagName.value = ''
    newTagColor.value = '#667eea'
    newTagDescription.value = ''
    showTagDialog.value = false
  } catch (error: any) {
    alert('创建标签失败: ' + error.message)
  }
}

// 切换文件的标签
function toggleFileTag(fileNodeId: number, tagId: number) {
  const current = fileClassifications.value.get(fileNodeId) || []
  const index = current.indexOf(tagId)
  
  if (index > -1) {
    current.splice(index, 1)
  } else {
    current.push(tagId)
  }
  
  fileClassifications.value.set(fileNodeId, [...current])
}

// 获取文件的标签
function getFileTags(fileNodeId: number): number[] {
  return fileClassifications.value.get(fileNodeId) || []
}

// 获取标签对象
function getTag(tagId: number) {
  return tags.value.find(t => t.id === tagId)
}

// 应用自动分类建议
function applyAutoSuggestion(fileNodeId: number) {
  const suggestion = autoSuggestions.value.get(fileNodeId)
  if (!suggestion) return
  
  const tag = tags.value.find(t => t.name === suggestion)
  if (tag) {
    const current = fileClassifications.value.get(fileNodeId) || []
    if (!current.includes(tag.id)) {
      current.push(tag.id)
      fileClassifications.value.set(fileNodeId, [...current])
    }
  }
}

// 批量应用建议
function applyAllSuggestions() {
  files.value.forEach(file => {
    if (selectedFiles.value.has(file.node_id)) {
      applyAutoSuggestion(file.node_id)
    }
  })
}

// 切换全选
function toggleSelectAll() {
  if (selectAll.value) {
    files.value.forEach(file => selectedFiles.value.add(file.node_id))
  } else {
    selectedFiles.value.clear()
  }
}

// 保存分类结果
async function saveClassifications() {
  const classifications: any[] = []
  
  fileClassifications.value.forEach((tagIds, nodeId) => {
    tagIds.forEach(tagId => {
      classifications.push({
        node_id: nodeId,
        tag_id: tagId,
        is_manual: true,
        confidence: 100
      })
    })
  })
  
  if (classifications.length === 0) {
    alert('没有分类数据需要保存')
    return
  }
  
  try {
    await classifyTools.saveClassifications({
      classifications,
      classified_by: account.name
    })
    
    alert('分类保存成功！')
    router.back()
  } catch (error: any) {
    alert('保存失败: ' + error.message)
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

// 获取统计图标
function getStatIcon(category: string): string {
  const iconMap: Record<string, string> = {
    '文档': '📄',
    '表格': '📊',
    '演示文稿': '📽️',
    '图片': '🖼️',
    '视频': '🎬',
    '音频': '🎵',
    '代码': '💻',
    '压缩包': '📦',
    '其他': '📁'
  }
  return iconMap[category] || '📄'
}

onMounted(() => {
  loadTags()
  loadFiles()
})
</script>

<template>
  <div class="smart-classify-page">
    <div class="header">
      <div class="title-section">
        <button class="back-btn" @click="goBack">← 返回</button>
        <h1>📊 智能分类</h1>
        <p class="subtitle">当前目录：{{ nodeName }}</p>
      </div>
      
      <div class="actions">
        <button class="btn btn-secondary" @click="showTagDialog = true">
          + 新建标签
        </button>
        <button class="btn btn-primary" @click="saveClassifications">
          💾 保存分类
        </button>
      </div>
    </div>

    <!-- 标签列表 -->
    <div class="tags-section">
      <h3>可用标签</h3>
      <div class="tags-list">
        <div
          v-for="tag in tags"
          :key="tag.id"
          class="tag-item"
          :style="{ borderColor: tag.color }"
        >
          <span class="tag-dot" :style="{ backgroundColor: tag.color }"></span>
          <span class="tag-name">{{ tag.name }}</span>
          <span class="tag-desc">{{ tag.description }}</span>
        </div>
      </div>
    </div>

    <!-- 分类进度 -->
    <div v-if="classifyStep === 'loading'" class="loading">
      <div class="spinner"></div>
      <p>正在加载文件...</p>
    </div>

    <div v-else-if="classifyStep === 'classifying'" class="loading">
      <div class="spinner"></div>
      <p>正在智能分类中...</p>
      <p class="sub-text">已找到 {{ files.length }} 个文件</p>
    </div>

    <!-- 分类统计 -->
    <div v-else-if="classifyStep === 'result' && files.length > 0" class="stats-section">
      <h3>📊 分类统计</h3>
      <div class="stats-grid">
        <div
          v-for="(count, category) in classificationStats"
          :key="category"
          class="stat-card"
        >
          <div class="stat-icon" :style="{ backgroundColor: getCategoryColor(category) }">
            {{ getStatIcon(category) }}
          </div>
          <div class="stat-info">
            <div class="stat-name">{{ category }}</div>
            <div class="stat-count">{{ count }} 个文件</div>
          </div>
        </div>
      </div>
      <div class="total-info">
        <span>共分类 <strong>{{ files.length }}</strong> 个文件</span>
      </div>
    </div>

    <!-- 批量操作 -->
    <div v-if="classifyStep === 'result' && files.length > 0" class="batch-actions">
      <label class="checkbox-label">
        <input type="checkbox" v-model="selectAll" @change="toggleSelectAll" />
        <span>全选</span>
      </label>
      <button
        class="btn btn-small"
        :disabled="selectedFiles.size === 0"
        @click="applyAllSuggestions"
      >
        重新应用建议到选中项 ({{ selectedFiles.size }})
      </button>
    </div>

    <!-- 文件列表 -->

    <div v-else-if="classifyStep === 'result'" class="files-section">
      <div v-for="file in files" :key="file.node_id" class="file-card">
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
              <span class="file-size">{{ formatSize(file.size) }}</span>
            </div>
          </div>

          <div class="suggestion">
            <span class="label">建议：</span>
            <span class="value">{{ autoSuggestions.get(file.node_id) }}</span>
            <button
              class="btn-apply"
              @click="applyAutoSuggestion(file.node_id)"
            >
              应用
            </button>
          </div>
        </div>

        <div class="file-tags">
          <span class="label">分类标签：</span>
          <div class="tags">
            <button
              v-for="tag in tags"
              :key="tag.id"
              class="tag-btn"
              :class="{ active: getFileTags(file.node_id).includes(tag.id) }"
              :style="{
                borderColor: tag.color,
                backgroundColor: getFileTags(file.node_id).includes(tag.id) ? tag.color : 'transparent',
                color: getFileTags(file.node_id).includes(tag.id) ? 'white' : tag.color
              }"
              @click="toggleFileTag(file.node_id, tag.id)"
            >
              {{ tag.name }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="files.length === 0" class="empty">
        <div class="icon">📂</div>
        <p>当前目录没有文件</p>
      </div>
    </div>

    <!-- 新建标签对话框 -->
    <div v-if="showTagDialog" class="dialog-mask" @click.self="showTagDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <h3>新建标签</h3>
          <button class="close-btn" @click="showTagDialog = false">×</button>
        </div>

        <div class="dialog-body">
          <div class="form-group">
            <label>标签名称 *</label>
            <input
              v-model="newTagName"
              type="text"
              placeholder="例如：重要文档"
              maxlength="50"
            />
          </div>

          <div class="form-group">
            <label>标签颜色</label>
            <div class="color-picker">
              <div
                v-for="color in colorOptions"
                :key="color"
                class="color-option"
                :class="{ active: newTagColor === color }"
                :style="{ backgroundColor: color }"
                @click="newTagColor = color"
              ></div>
            </div>
          </div>

          <div class="form-group">
            <label>描述</label>
            <textarea
              v-model="newTagDescription"
              placeholder="标签描述（可选）"
              rows="3"
            ></textarea>
          </div>
        </div>

        <div class="dialog-footer">
          <button class="btn btn-secondary" @click="showTagDialog = false">
            取消
          </button>
          <button class="btn btn-primary" @click="createTag">
            创建
          </button>
        </div>
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
  margin: 0;
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

.btn-secondary {
  background: white;
  border: 1px solid #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background: #f9fafb;
}

.btn-small {
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 标签区域 */
.tags-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 12px;
}

.tags-section h3 {
  margin: 0 0 1rem 0;
  color: #374151;
  font-size: 1.1rem;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.tag-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: white;
  border: 2px solid;
  border-radius: 8px;
}

.tag-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.tag-name {
  font-weight: 600;
  color: #1f2937;
}

.tag-desc {
  font-size: 0.75rem;
  color: #9ca3af;
}

/* 批量操作 */
.batch-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
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

/* 文件列表 */
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
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
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

.file-size {
  font-size: 0.75rem;
  color: #9ca3af;
}

.suggestion {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #f0fdf4;
  border-radius: 6px;
}

.suggestion .label {
  font-size: 0.875rem;
  color: #6b7280;
}

.suggestion .value {
  font-weight: 600;
  color: #10b981;
}

.btn-apply {
  padding: 0.25rem 0.75rem;
  border: 1px solid #10b981;
  background: white;
  color: #10b981;
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-apply:hover {
  background: #10b981;
  color: white;
}

.file-tags {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-tags .label {
  font-size: 0.875rem;
  color: #6b7280;
  white-space: nowrap;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag-btn {
  padding: 0.5rem 1rem;
  border: 2px solid;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tag-btn:hover {
  transform: translateY(-1px);
}

/* 加载和空状态 */
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

/* 对话框 */
.dialog-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog {
  width: min(500px, 90vw);
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.dialog-header h3 {
  margin: 0;
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

.dialog-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #374151;
  font-size: 0.875rem;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.color-picker {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.color-option {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 3px solid transparent;
}

.color-option:hover {
  transform: scale(1.1);
}

.color-option.active {
  border-color: #1f2937;
  transform: scale(1.15);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
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
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
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
}

.stat-info {
  flex: 1;
}

.stat-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.stat-count {
  font-size: 0.875rem;
  color: #6b7280;
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
</style>
