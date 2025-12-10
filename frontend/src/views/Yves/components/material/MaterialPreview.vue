<script setup lang="ts">
import { computed, ref, nextTick } from 'vue'
import { MaterialItem } from '../../tools/MaterialTools'
import requestTools from '../../tools/RequestTools'
import { renderAsync } from 'docx-preview'

const props = defineProps<{
  visible: boolean
  item: MaterialItem | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

// 获取文件扩展名
const fileExtension = computed(() => {
  if (!props.item?.name) return ''
  const parts = props.item.name.split('.')
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : ''
})

// 判断文件类型
const fileType = computed(() => {
  const ext = fileExtension.value
  
  // 图片
  if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext)) {
    return 'image'
  }
  
  // 视频
  if (['mp4', 'webm', 'ogg', 'mov', 'avi', 'mkv'].includes(ext)) {
    return 'video'
  }
  
  // 音频
  if (['mp3', 'wav', 'ogg', 'aac', 'm4a', 'flac'].includes(ext)) {
    return 'audio'
  }
  
  // PDF
  if (ext === 'pdf') {
    return 'pdf'
  }
  
  // 文本
  if (['txt', 'md', 'json', 'xml', 'csv', 'log'].includes(ext)) {
    return 'text'
  }
  
  // 代码
  if (['js', 'ts', 'jsx', 'tsx', 'vue', 'html', 'css', 'scss', 'less', 'py', 'java', 'c', 'cpp', 'go', 'rs', 'php', 'rb', 'swift', 'kt'].includes(ext)) {
    return 'code'
  }
  
  // Word 文档
  if (['docx'].includes(ext)) {
    return 'docx'
  }
  
  // 其他 Office 文档
  if (['doc', 'xls', 'xlsx', 'ppt', 'pptx'].includes(ext)) {
    return 'office'
  }
  
  return 'unknown'
})

// 获取文件URL
const fileUrl = computed(() => {
  if (!props.item) return ''
  const nodeId = props.item.node_id || props.item.id
  return `${requestTools.BASE_URL}/material/download-file/${nodeId}`
})

// 文本内容
const textContent = ref('')
const loadingText = ref(false)

// Word 文档相关
const docxContainer = ref<HTMLElement | null>(null)
const loadingDocx = ref(false)
const docxError = ref('')

// 加载文本内容
async function loadTextContent() {
  if (!props.item || fileType.value !== 'text' && fileType.value !== 'code') return
  
  loadingText.value = true
  try {
    console.log('正在加载文本文件:', fileUrl.value)
    const response = await fetch(fileUrl.value)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('文本加载失败:', response.status, errorText)
      throw new Error(`加载失败 (${response.status})`)
    }
    
    textContent.value = await response.text()
    console.log('文本加载成功')
  } catch (err) {
    console.error('加载文本失败:', err)
    textContent.value = '加载失败: ' + (err instanceof Error ? err.message : String(err))
  } finally {
    loadingText.value = false
  }
}

// 加载 Word 文档
async function loadDocxContent() {
  if (!props.item || fileType.value !== 'docx') return
  
  loadingDocx.value = true
  docxError.value = ''
  
  try {
    // 多次等待确保 DOM 完全渲染
    await nextTick()
    await nextTick()
    
    // 最多等待 10 次，直到容器出现
    let retries = 10
    while (!docxContainer.value && retries > 0) {
      await new Promise(resolve => setTimeout(resolve, 50))
      retries--
    }
    
    if (!docxContainer.value) {
      throw new Error('容器未找到，请重试')
    }
    
    // 清空容器
    docxContainer.value.innerHTML = ''
    
    // 获取文件
    console.log('正在加载文件:', fileUrl.value)
    const response = await fetch(fileUrl.value)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('文件加载失败:', response.status, errorText)
      throw new Error(`文件加载失败 (${response.status}): ${errorText}`)
    }
    
    const blob = await response.blob()
    console.log('文件加载成功，大小:', blob.size)
    
    // 渲染文档
    await renderAsync(blob, docxContainer.value, undefined, {
      className: 'docx-wrapper',
      inWrapper: true,
      ignoreWidth: false,
      ignoreHeight: false,
      ignoreFonts: false,
      breakPages: true,
      ignoreLastRenderedPageBreak: true,
      experimental: false,
      trimXmlDeclaration: true,
      useBase64URL: false,
      renderHeaders: true,
      renderFooters: true,
      renderFootnotes: true,
      renderEndnotes: true
    })
  } catch (err: any) {
    console.error('加载 Word 文档失败:', err)
    docxError.value = err.message || '加载失败'
  } finally {
    loadingDocx.value = false
  }
}

// 监听文件变化，加载内容
import { watch } from 'vue'
watch(() => [props.visible, props.item], async ([newVisible, newItem]) => {
  if (newVisible && newItem) {
    if (fileType.value === 'text' || fileType.value === 'code') {
      loadTextContent()
    } else if (fileType.value === 'docx') {
      // 等待 DOM 完全渲染
      await nextTick()
      await nextTick()
      loadDocxContent()
    }
  }
})

// 获取文件图标
function getFileIcon(type: string): string {
  const icons: Record<string, string> = {
    image: '🖼️',
    video: '🎬',
    audio: '🎵',
    pdf: '📄',
    text: '📝',
    code: '💻',
    docx: '📝',
    office: '📊',
    unknown: '📎'
  }
  return icons[type] || icons.unknown
}
</script>

<template>
  <div v-if="visible && item" class="preview-mask" @click.self="emit('close')">
    <div class="preview-panel">
      <div class="header">
        <div class="title">
          <span class="icon">{{ getFileIcon(fileType) }}</span>
          <span class="name">{{ item.name }}</span>
        </div>
        <button class="close" @click="emit('close')">×</button>
      </div>

      <div class="content">
        <!-- 图片预览 -->
        <div v-if="fileType === 'image'" class="preview-image">
          <img :src="fileUrl" :alt="item.name" />
        </div>

        <!-- 视频预览 -->
        <div v-else-if="fileType === 'video'" class="preview-video">
          <video :src="fileUrl" controls controlsList="nodownload">
            您的浏览器不支持视频播放
          </video>
        </div>

        <!-- 音频预览 -->
        <div v-else-if="fileType === 'audio'" class="preview-audio">
          <div class="audio-icon">🎵</div>
          <audio :src="fileUrl" controls controlsList="nodownload">
            您的浏览器不支持音频播放
          </audio>
        </div>

        <!-- PDF预览 -->
        <div v-else-if="fileType === 'pdf'" class="preview-pdf">
          <iframe :src="fileUrl" frameborder="0"></iframe>
        </div>

        <!-- 文本/代码预览 -->
        <div v-else-if="fileType === 'text' || fileType === 'code'" class="preview-text">
          <div v-if="loadingText" class="loading">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>
          <pre v-else><code>{{ textContent }}</code></pre>
        </div>

        <!-- Word 文档预览 -->
        <div v-else-if="fileType === 'docx'" class="preview-docx">
          <div v-if="loadingDocx" class="loading">
            <div class="spinner"></div>
            <p>加载 Word 文档中...</p>
          </div>
          <div v-if="docxError" class="error">
            <div class="icon">⚠️</div>
            <h3>加载失败</h3>
            <p>{{ docxError }}</p>
            <a :href="fileUrl" download class="btn-download">
              📥 下载文件
            </a>
          </div>
          <div ref="docxContainer" class="docx-content" :style="{ display: loadingDocx || docxError ? 'none' : 'block' }"></div>
        </div>

        <!-- Office文档提示 -->
        <div v-else-if="fileType === 'office'" class="preview-unsupported">
          <div class="icon">📊</div>
          <h3>Office 文档</h3>
          <p>浏览器无法直接预览 Office 文档</p>
          <p class="hint">请下载后使用相应软件打开</p>
          <a :href="fileUrl" download class="btn-download">
            📥 下载文件
          </a>
        </div>

        <!-- 不支持的文件类型 -->
        <div v-else class="preview-unsupported">
          <div class="icon">📎</div>
          <h3>无法预览</h3>
          <p>该文件类型暂不支持在线预览</p>
          <p class="hint">文件扩展名: .{{ fileExtension }}</p>
          <a :href="fileUrl" download class="btn-download">
            📥 下载文件
          </a>
        </div>
      </div>

      <div class="footer">
        <div class="file-info">
          <span v-if="item.size">大小: {{ item.size }}</span>
          <span v-if="item.updatedAt">更新时间: {{ item.updatedAt }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.preview-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
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

.preview-panel {
  width: min(1200px, 95vw);
  height: min(800px, 90vh);
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  overflow: hidden;
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
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  flex-shrink: 0;
}

.title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 1.1rem;
}

.icon {
  font-size: 1.5rem;
}

.name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.close {
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 2rem;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

.content {
  flex: 1;
  overflow: auto;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 图片预览 */
.preview-image {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: #000;
}

.preview-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

/* 视频预览 */
.preview-video {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
}

.preview-video video {
  max-width: 100%;
  max-height: 100%;
  outline: none;
}

/* 音频预览 */
.preview-audio {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  padding: 3rem;
}

.audio-icon {
  font-size: 6rem;
  opacity: 0.3;
}

.preview-audio audio {
  width: 100%;
  max-width: 500px;
}

/* PDF预览 */
.preview-pdf {
  width: 100%;
  height: 100%;
}

.preview-pdf iframe {
  width: 100%;
  height: 100%;
  border: none;
}

/* 文本/代码预览 */
.preview-text {
  width: 100%;
  height: 100%;
  overflow: auto;
  background: #1e1e1e;
  color: #d4d4d4;
}

.preview-text pre {
  margin: 0;
  padding: 2rem;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.9rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.preview-text code {
  font-family: inherit;
}

/* Word 文档预览 */
.preview-docx {
  width: 100%;
  height: 100%;
  overflow: auto;
  background: #f5f5f5;
  padding: 2rem;
}

.docx-content {
  max-width: 900px;
  margin: 0 auto;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-height: 100%;
}

/* docx-preview 样式覆盖 */
.preview-docx :deep(.docx-wrapper) {
  background: white;
  padding: 2rem;
  font-family: 'Calibri', 'Arial', sans-serif;
}

.preview-docx :deep(.docx-wrapper > section.docx) {
  margin-bottom: 0;
}

.preview-docx .error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
  text-align: center;
}

.preview-docx .error .icon {
  font-size: 4rem;
  opacity: 0.5;
}

.preview-docx .error h3 {
  margin: 0;
  color: #d32f2f;
  font-size: 1.3rem;
}

.preview-docx .error p {
  margin: 0;
  color: #666;
}

/* 加载状态 */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
  color: #999;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 不支持的文件类型 */
.preview-unsupported {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
  text-align: center;
}

.preview-unsupported .icon {
  font-size: 5rem;
  opacity: 0.3;
}

.preview-unsupported h3 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

.preview-unsupported p {
  margin: 0;
  color: #666;
  font-size: 1rem;
}

.preview-unsupported .hint {
  font-size: 0.9rem;
  color: #999;
}

.btn-download {
  margin-top: 1rem;
  padding: 0.75rem 2rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.btn-download:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* 底部信息 */
.footer {
  padding: 1rem 1.5rem;
  background: white;
  border-top: 1px solid #eee;
  flex-shrink: 0;
}

.file-info {
  display: flex;
  gap: 2rem;
  font-size: 0.9rem;
  color: #666;
}

.file-info span {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

@media (max-width: 768px) {
  .preview-panel {
    width: 100vw;
    height: 100vh;
    border-radius: 0;
  }

  .file-info {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
