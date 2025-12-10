<script setup lang="ts">
import { computed } from 'vue'
import type { MaterialItem } from '../../tools/MaterialTools'

const props = defineProps<{
  isTeacher: boolean
  currentPath: MaterialItem[]
  rootName?: string  // 根目录显示名称
  isSelectMode?: boolean
  selectedCount?: number
  selectModeType?: 'download' | 'delete'
}>()

const emit = defineEmits<{
  (e: 'create-folder'): void
  (e: 'upload-file'): void
  (e: 'smart-classify'): void
  (e: 'back', targetId?: number): void
  (e: 'toggle-select-mode', type: 'download' | 'delete'): void
  (e: 'batch-download'): void
  (e: 'batch-delete'): void
  (e: 'select-all'): void
}>()

const canBack = computed(() => props.currentPath.length > 0)
</script>

<template>
  <div class="toolbar">
    <div class="left">
      <span class="label">当前路径：</span>
      <span
        class="path-part link"
        v-if="currentPath.length === 0"
      >
        {{ rootName || '根目录' }}
      </span>
      <template v-else>
        <span
          class="path-part link"
          @click="emit('back', undefined)"
        >
          {{ rootName || '根目录' }}
        </span>
        <span v-for="p in currentPath" :key="p.id">
          <span class="divider">/</span>
          <span
            class="path-part link"
            @click="emit('back', p.id)"
          >
            {{ p.name }}
          </span>
        </span>
      </template>
    </div>

    <div class="right">
      <!-- 选择模式下的按钮 -->
      <template v-if="isSelectMode">
        <span class="selected-info">已选择 {{ selectedCount }} 项</span>
        <button class="btn" @click="emit('select-all')">全选</button>
        
        <!-- 下载模式 -->
        <template v-if="selectModeType === 'download'">
          <button 
            class="btn primary" 
            :disabled="selectedCount === 0"
            @click="emit('batch-download')"
          >
            下载选中
          </button>
        </template>
        
        <!-- 删除模式 -->
        <template v-else>
          <button 
            class="btn danger" 
            :disabled="selectedCount === 0"
            @click="emit('batch-delete')"
          >
            删除选中
          </button>
        </template>
        
        <button class="btn secondary" @click="emit('toggle-select-mode', selectModeType || 'download')">取消</button>
      </template>
      
      <!-- 普通模式下的按钮 -->
      <template v-else>
        <button
          class="btn secondary"
          :disabled="!canBack"
          @click="emit('back', undefined)"
        >
          返回上级
        </button>
        
        <button class="btn" @click="emit('toggle-select-mode', 'download')">批量下载</button>

        <template v-if="isTeacher">
          <button class="btn" @click="emit('toggle-select-mode', 'delete')">批量删除</button>
          <button class="btn smart" @click="emit('smart-classify')">📊 智能分类</button>
          <button class="btn" @click="emit('create-folder')">新建文件夹</button>
          <button class="btn primary" @click="emit('upload-file')">上传资料</button>
        </template>
      </template>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.left {
  font-size: 0.9rem;
  color: #555;
}

.label {
  font-weight: 600;
  margin-right: 0.25rem;
}

.path-part {
  max-width: 160px;
  display: inline-block;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

.divider {
  margin: 0 0.25rem;
  color: #bbb;
}

.right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn {
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  border: 1px solid #dee2f7;
  background: #f8f9ff;
  color: #4c51bf;
  font-size: 0.85rem;
  cursor: pointer;
}

.btn.primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-color: transparent;
  color: #fff;
}

.btn.secondary {
  background: #fff;
}

.btn.danger {
  background: linear-gradient(135deg, #f56565, #e53e3e);
  border-color: transparent;
  color: #fff;
}

.btn.smart {
  background: linear-gradient(135deg, #10b981, #059669);
  border-color: transparent;
  color: #fff;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn:not(:disabled):hover {
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
}

.link {
  color: #667eea;
  cursor: pointer;
}

.link:hover {
  text-decoration: underline;
}

.selected-info {
  font-size: 0.9rem;
  color: #667eea;
  font-weight: 600;
}
</style>


