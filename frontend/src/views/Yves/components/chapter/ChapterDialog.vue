<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Chapter } from '../../tools/ChapterTools'

const props = defineProps<{
  visible: boolean
  chapter?: Chapter | null
  parentChapters: Chapter[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirm', data: {
    title: string
    description: string
    parent_id?: number
  }): void
}>()

const title = ref('')
const description = ref('')
const parentId = ref<number | undefined>(undefined)

// 监听对话框打开，初始化数据
watch(() => props.visible, (visible) => {
  if (visible) {
    if (props.chapter) {
      // 编辑模式
      title.value = props.chapter.title
      description.value = props.chapter.description || ''
      parentId.value = props.chapter.parent_id
    } else {
      // 新建模式
      title.value = ''
      description.value = ''
      parentId.value = undefined
    }
  }
})

function handleConfirm() {
  if (!title.value.trim()) {
    alert('请输入章节标题')
    return
  }

  emit('confirm', {
    title: title.value.trim(),
    description: description.value.trim(),
    parent_id: parentId.value
  })
}
</script>

<template>
  <div v-if="visible" class="dialog-overlay" @click.self="emit('close')">
    <div class="dialog">
      <div class="dialog-header">
        <h3>{{ chapter ? '编辑章节' : '新建章节' }}</h3>
        <button class="btn-close" @click="emit('close')">✕</button>
      </div>

      <div class="dialog-body">
        <div class="form-group">
          <label>章节标题 *</label>
          <input
            v-model="title"
            type="text"
            placeholder="请输入章节标题"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label>章节描述</label>
          <textarea
            v-model="description"
            placeholder="请输入章节描述（可选）"
            class="form-textarea"
            rows="4"
          ></textarea>
        </div>

        <div class="form-group">
          <label>父章节</label>
          <select v-model="parentId" class="form-select">
            <option :value="undefined">无（顶级章节）</option>
            <option v-for="parent in parentChapters" :key="parent.id" :value="parent.id">
              {{ parent.title }}
            </option>
          </select>
        </div>
      </div>

      <div class="dialog-footer">
        <button class="btn secondary" @click="emit('close')">取消</button>
        <button class="btn primary" @click="handleConfirm">确定</button>
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

.form-input,
.form-textarea,
.form-select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
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
