<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirm', payload: { files: File[] }): void
}>()

const selectedFiles = ref<File[]>([])
const isDragging = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

// 计算属性：是否有文件
const canConfirm = computed(() => {
  return selectedFiles.value.length > 0
})

// 处理文件选择
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files) {
    selectedFiles.value = Array.from(target.files)
  }
}

// 点击选择文件
function handleClickSelect() {
  fileInputRef.value?.click()
}

// 拖拽处理
function handleDragOver(event: DragEvent) {
  event.preventDefault()
  event.stopPropagation()
  isDragging.value = true
}

function handleDragLeave(event: DragEvent) {
  event.preventDefault()
  event.stopPropagation()
  isDragging.value = false
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  event.stopPropagation()
  isDragging.value = false

  if (event.dataTransfer?.files) {
    selectedFiles.value = Array.from(event.dataTransfer.files)
  }
}

// 移除文件
function handleRemoveFile(index: number) {
  selectedFiles.value.splice(index, 1)
}

// 格式化文件大小
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 确认上传
function handleConfirm() {
  if (!canConfirm.value) {
    return
  }

  emit('confirm', { 
    files: selectedFiles.value
  })

  // 重置状态
  handleClose()
}

// 关闭对话框
function handleClose() {
  selectedFiles.value = []
  isDragging.value = false
  emit('close')
}
</script>

<template>
  <div v-if="visible" class="dialog-mask" @click.self="handleClose">
    <div class="dialog">
      <div class="header">
        <div class="title">上传文件</div>
        <button class="close" @click="handleClose">×</button>
      </div>

      <div class="body">
        <!-- 文件上传区域 -->
        <div 
          class="upload-area"
          :class="{ 'dragging': isDragging, 'has-files': selectedFiles.length > 0 }"
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @drop="handleDrop"
          @click="handleClickSelect"
        >
          <input
            ref="fileInputRef"
            type="file"
            multiple
            class="file-input"
            @change="handleFileSelect"
          />
          
          <div class="upload-content">
            <div class="upload-icon">📁</div>
            <p class="upload-text">
              <span v-if="!isDragging && selectedFiles.length === 0">
                拖拽文件到此处或 <span class="link">点击选择文件</span>
              </span>
              <span v-else-if="isDragging">
                释放文件以上传
              </span>
              <span v-else>
                已选择 {{ selectedFiles.length }} 个文件
              </span>
            </p>
            <p class="upload-hint">支持多文件上传</p>
          </div>
        </div>

        <!-- 已选择的文件列表 -->
        <div v-if="selectedFiles.length > 0" class="file-list">
          <div 
            v-for="(file, index) in selectedFiles" 
            :key="index"
            class="file-item"
          >
            <div class="file-info">
              <span class="file-icon">📄</span>
              <div class="file-details">
                <div class="file-name">{{ file.name }}</div>
                <div class="file-size">{{ formatFileSize(file.size) }}</div>
              </div>
            </div>
            <button 
              class="remove-btn"
              @click.stop="handleRemoveFile(index)"
              title="移除"
            >
              ×
            </button>
          </div>
        </div>

        <p class="tip">
          <span v-if="selectedFiles.length > 0">
            将上传 {{ selectedFiles.length }} 个文件到当前目录。
          </span>
          <span v-else>
            请选择要上传的文件。
          </span>
        </p>
      </div>

      <div class="footer">
        <button class="btn" @click="handleClose">取消</button>
        <button 
          class="btn primary" 
          :disabled="!canConfirm" 
          @click="handleConfirm"
        >
          上传
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dialog-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.dialog {
  width: min(520px, 92%);
  max-height: 90vh;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.25rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
}

.title {
  font-weight: 600;
}

.close {
  border: none;
  background: none;
  color: #fff;
  font-size: 1.3rem;
  cursor: pointer;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close:hover {
  background: rgba(255, 255, 255, 0.2);
}

.body {
  padding: 1.25rem;
  overflow-y: auto;
  flex: 1;
}

/* 上传区域 */
.upload-area {
  position: relative;
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 2rem 1rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
  margin-bottom: 1rem;
}

.upload-area:hover {
  border-color: #667eea;
  background: #f0f4ff;
}

.upload-area.dragging {
  border-color: #667eea;
  background: #e8edff;
  transform: scale(1.02);
}

.upload-area.has-files {
  border-color: #4caf50;
  background: #f1f8f4;
}

.file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  overflow: hidden;
}

.upload-content {
  pointer-events: none;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 0.5rem;
}

.upload-text {
  font-size: 0.95rem;
  color: #333;
  margin-bottom: 0.25rem;
}

.link {
  color: #667eea;
  text-decoration: underline;
  pointer-events: auto;
  cursor: pointer;
}

.upload-hint {
  font-size: 0.8rem;
  color: #999;
  margin: 0;
}

/* 文件列表 */
.file-list {
  margin-bottom: 1rem;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 0.5rem;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem;
  background: #f9f9f9;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  transition: background-color 0.2s;
}

.file-item:last-child {
  margin-bottom: 0;
}

.file-item:hover {
  background: #f0f0f0;
}

.file-info {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.file-icon {
  font-size: 1.2rem;
  margin-right: 0.5rem;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 0.9rem;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 0.15rem;
}

.file-size {
  font-size: 0.75rem;
  color: #999;
}

.remove-btn {
  border: none;
  background: #ff5252;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
  margin-left: 0.5rem;
}

.remove-btn:hover {
  background: #ff1744;
  transform: scale(1.1);
}

.tip {
  font-size: 0.8rem;
  color: #777;
  line-height: 1.4;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #f5f5f5;
  border-radius: 4px;
}

.footer {
  padding: 0.75rem 1.25rem 1rem;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  border-top: 1px solid #eee;
  background: #fafafa;
}

.btn {
  padding: 0.5rem 1.2rem;
  border-radius: 6px;
  border: 1px solid #dee2f7;
  background: #f8f9ff;
  color: #4c51bf;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.btn.primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-color: transparent;
  color: #fff;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn:not(:disabled):hover {
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  transform: translateY(-1px);
}

.btn:not(:disabled):active {
  transform: translateY(0);
}
</style>
