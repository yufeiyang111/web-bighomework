<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirm', data: {
    file: File
    title: string
    description: string
  }): void
}>()

const title = ref('')
const description = ref('')
const selectedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

// 监听对话框打开，重置数据
watch(() => props.visible, (visible) => {
  if (visible) {
    title.value = ''
    description.value = ''
    selectedFile.value = null
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
  }
})

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    const file = target.files[0]
    
    // 检查文件类型
    if (!file.type.startsWith('video/')) {
      alert('请选择视频文件')
      target.value = ''
      return
    }
    
    selectedFile.value = file
    
    // 如果没有标题，使用文件名
    if (!title.value) {
      title.value = file.name.replace(/\.[^/.]+$/, '')
    }
  }
}

function handleConfirm() {
  if (!selectedFile.value) {
    alert('请选择视频文件')
    return
  }

  if (!title.value.trim()) {
    alert('请输入视频标题')
    return
  }

  emit('confirm', {
    file: selectedFile.value,
    title: title.value.trim(),
    description: description.value.trim()
  })
}

function formatFileSize(bytes: number): string {
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
</script>

<template>
  <div v-if="visible" class="dialog-overlay" @click.self="emit('close')">
    <div class="dialog">
      <div class="dialog-header">
        <h3>上传视频</h3>
        <button class="btn-close" @click="emit('close')">✕</button>
      </div>

      <div class="dialog-body">
        <div class="form-group">
          <label>选择视频文件 *</label>
          <input
            ref="fileInputRef"
            type="file"
            accept="video/*"
            class="form-file"
            @change="handleFileSelect"
          />
          <div v-if="selectedFile" class="file-info">
            <span class="file-name">{{ selectedFile.name }}</span>
            <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
          </div>
        </div>

        <div class="form-group">
          <label>视频标题 *</label>
          <input
            v-model="title"
            type="text"
            placeholder="请输入视频标题"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label>视频描述</label>
          <textarea
            v-model="description"
            placeholder="请输入视频描述（可选）"
            class="form-textarea"
            rows="4"
          ></textarea>
        </div>
      </div>

      <div class="dialog-footer">
        <button class="btn secondary" @click="emit('close')">取消</button>
        <button class="btn primary" @click="handleConfirm">上传</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
}

.dialog-header h3 {
  margin: 0;
  color: #333;
}

.btn-close {
  border: none;
  background: none;
  font-size: 1.5rem;
  color: #999;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.btn-close:hover {
  background: #f5f5f5;
  color: #333;
}

.dialog-body {
  padding: 1.5rem;
  overflow-y: auto;
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
  color: #555;
  font-weight: 500;
}

.form-file {
  width: 100%;
  padding: 0.75rem;
  border: 2px dashed #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.form-file:hover {
  border-color: #667eea;
}

.file-info {
  margin-top: 0.5rem;
  padding: 0.75rem;
  background: #f8f9ff;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-name {
  color: #333;
  font-weight: 500;
}

.file-size {
  color: #999;
  font-size: 0.9rem;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #667eea;
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #eee;
}

.btn {
  padding: 0.6rem 1.5rem;
  border-radius: 6px;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn.secondary {
  background: #f5f5f5;
  color: #666;
}

.btn.secondary:hover {
  background: #e0e0e0;
}

.btn.primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
</style>
