<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirm', payload: { name: string }): void
}>()

const name = ref('')

// 计算属性：是否可以确认
const canConfirm = computed(() => {
  return name.value.trim().length > 0
})

// 确认创建
function handleConfirm() {
  if (!canConfirm.value) {
    return
  }

  emit('confirm', { 
    name: name.value.trim()
  })

  // 重置状态
  handleClose()
}

// 关闭对话框
function handleClose() {
  name.value = ''
  emit('close')
}
</script>

<template>
  <div v-if="visible" class="dialog-mask" @click.self="handleClose">
    <div class="dialog">
      <div class="header">
        <div class="title">新建文件夹</div>
        <button class="close" @click="handleClose">×</button>
      </div>

      <div class="body">
        <label class="field">
          <span>文件夹名称：</span>
          <input 
            v-model="name" 
            class="input" 
            placeholder="请输入文件夹名称"
            @keyup.enter="handleConfirm"
          />
        </label>

        <p class="tip">
          将在当前目录下创建一个新的文件夹。
        </p>
      </div>

      <div class="footer">
        <button class="btn" @click="handleClose">取消</button>
        <button 
          class="btn primary" 
          :disabled="!canConfirm" 
          @click="handleConfirm"
        >
          创建
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
  width: min(420px, 92%);
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  overflow: hidden;
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
}

.field {
  display: flex;
  align-items: center;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
}

.field span {
  min-width: 4.5rem;
}

.input {
  flex: 1;
  border-radius: 6px;
  border: 1px solid #ddd;
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
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

