<script setup lang="ts">
import { computed } from 'vue'
import { MaterialItem } from '../../tools/MaterialTools'

const props = defineProps<{
  list: MaterialItem[]
  isSelectMode?: boolean
  selectedItems?: Set<number>
  isTeacher?: boolean
}>()

const emit = defineEmits<{
  (e: 'open', item: MaterialItem): void
  (e: 'download', item: MaterialItem): void
  (e: 'delete', item: MaterialItem): void
  (e: 'toggle-select', item: MaterialItem): void
}>()

const hasData = computed(() => props.list && props.list.length > 0)

// 检查是否选中
function isSelected(item: MaterialItem): boolean {
  const id = item.node_id || item.id
  return props.selectedItems?.has(id) || false
}

// 获取文件图标
function getFileIcon(item: MaterialItem): string {
  if (item.type === 'folder') {
    return '📁'
  }
  
  // 从文件名获取扩展名
  const fileName = item.name || ''
  const ext = fileName.split('.').pop()?.toLowerCase() || ''
  
  // 图标映射
  const iconMap: Record<string, string> = {
    // 文档
    'pdf': '📄',
    'doc': '📝',
    'docx': '📝',
    'txt': '📃',
    'rtf': '📃',
    
    // 表格
    'xls': '📊',
    'xlsx': '📊',
    'csv': '📊',
    
    // 演示文稿
    'ppt': '📽️',
    'pptx': '📽️',
    
    // 图片
    'jpg': '🖼️',
    'jpeg': '🖼️',
    'png': '🖼️',
    'gif': '🖼️',
    'bmp': '🖼️',
    'svg': '🖼️',
    'webp': '🖼️',
    
    // 视频
    'mp4': '🎬',
    'avi': '🎬',
    'mov': '🎬',
    'wmv': '🎬',
    'flv': '🎬',
    'mkv': '🎬',
    
    // 音频
    'mp3': '🎵',
    'wav': '🎵',
    'flac': '🎵',
    'aac': '🎵',
    'ogg': '🎵',
    
    // 压缩包
    'zip': '📦',
    'rar': '📦',
    '7z': '📦',
    'tar': '📦',
    'gz': '📦',
    
    // 代码
    'js': '💻',
    'ts': '💻',
    'py': '💻',
    'java': '💻',
    'cpp': '💻',
    'c': '💻',
    'html': '💻',
    'css': '💻',
    'json': '💻',
    'xml': '💻',
    
    // 其他
    'md': '📋',
    'exe': '⚙️',
    'apk': '📱',
  }
  
  return iconMap[ext] || '📄'
}

// 获取文件类型描述
function getFileTypeLabel(item: MaterialItem): string {
  if (item.type === 'folder') {
    return '文件夹'
  }
  
  const fileName = item.name || ''
  const ext = fileName.split('.').pop()?.toUpperCase() || ''
  
  // 类型映射
  const typeMap: Record<string, string> = {
    'PDF': 'PDF文档',
    'DOC': 'Word文档',
    'DOCX': 'Word文档',
    'XLS': 'Excel表格',
    'XLSX': 'Excel表格',
    'PPT': 'PowerPoint',
    'PPTX': 'PowerPoint',
    'TXT': '文本文件',
    'ZIP': '压缩包',
    'RAR': '压缩包',
    'MP4': '视频文件',
    'MP3': '音频文件',
    'JPG': '图片',
    'JPEG': '图片',
    'PNG': '图片',
  }
  
  return typeMap[ext] || (ext ? `${ext}文件` : '文件')
}
</script>

<template>
  <div class="material-list">
    <table v-if="hasData" class="material-table">
      <thead>
        <tr>
          <th v-if="isSelectMode" style="width: 50px">
            <input type="checkbox" disabled />
          </th>
          <th>名称</th>
          <th>类型</th>
          <th>创建者</th>
          <th>大小</th>
          <th>最近更新</th>
          <th style="width: 140px; text-align: right">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in list" :key="item.id" :class="{ 'selected': isSelected(item) }">
          <td v-if="isSelectMode">
            <input 
              type="checkbox" 
              :checked="isSelected(item)"
              @change="emit('toggle-select', item)"
            />
          </td>
          <td>
            <div class="file-name">
              <span class="file-icon">{{ getFileIcon(item) }}</span>
              <span
                class="link"
                @click="isSelectMode ? emit('toggle-select', item) : emit('open', item)"
              >
                {{ item.name }}
              </span>
            </div>
          </td>
          <td>
            <span class="file-type">{{ getFileTypeLabel(item) }}</span>
          </td>
          <td>{{ item.creator }}</td>
          <td>{{ item.size || '-' }}</td>
          <td>{{ item.updatedAt }}</td>
          <td class="actions">
            <button class="link-button" @click="emit('open', item)">预览</button>
            <button
              v-if="item.type === 'file'"
              class="link-button"
              @click="emit('download', item)"
            >
              下载
            </button>
            <button
              v-if="isTeacher"
              class="link-button delete"
              @click="emit('delete', item)"
            >
              删除
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-else class="empty">
      暂无资料
    </div>
  </div>
</template>

<style scoped>
.material-list {
  margin-top: 1rem;
}

.material-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.material-table th {
  text-align: left;
}

.material-table th,
.material-table td {
  padding: 0.6rem 0.8rem;
  border-bottom: 1px solid #eee;
}

.material-table thead {
  background: #f7f7fb;
}

.actions {
  text-align: right;
  white-space: nowrap;
}

.link {
  color: #667eea;
  cursor: pointer;
}

.link:hover {
  text-decoration: underline;
}

.link-button {
  border: none;
  background: none;
  color: #667eea;
  cursor: pointer;
  padding: 0;
  margin-left: 0.75rem;
}

.link-button:hover {
  text-decoration: underline;
}

.link-button.delete {
  color: #e53e3e;
}

.link-button.delete:hover {
  color: #c53030;
}

.empty {
  padding: 2rem;
  text-align: center;
  color: #999;
}

/* 文件名样式 */
.file-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.file-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.file-type {
  color: #666;
  font-size: 0.9rem;
}

/* 选中行样式 */
.material-table tbody tr.selected {
  background-color: #e8edff;
}

.material-table tbody tr:hover {
  background-color: #f5f7fa;
}

.material-table tbody tr.selected:hover {
  background-color: #dce4ff;
}
</style>


