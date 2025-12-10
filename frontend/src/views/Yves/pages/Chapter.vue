<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import baseInfoTools from '../tools/BaseInfoTools'
import chapterTools from '../tools/ChapterTools'
import type { Chapter, ChapterVideo } from '../tools/ChapterTools'
import ChapterTree from '../components/chapter/ChapterTree.vue'
import VideoPlayer from '../components/chapter/VideoPlayer.vue'
import ChapterDialog from '../components/chapter/ChapterDialog.vue'
import VideoUploadDialog from '../components/chapter/VideoUploadDialog.vue'
import Layout from "@/components/Layout.vue";

const account = baseInfoTools.getAccountInfo(1)
const isTeacher = computed(() => account.Identity === 'teacher')
const classInfo = computed(() => baseInfoTools.getClassInfo())
const classTeacherInfo = computed(() => baseInfoTools.getClassTeacherInfo())

// 课程名称
const courseName = computed(() => 
  `${classTeacherInfo.value.id}-${classInfo.value.classId}`
)

// 数据状态
const chapters = ref<Chapter[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// UI 状态
const expandedIds = ref<Set<number>>(new Set())
const selectedVideo = ref<ChapterVideo | null>(null)
const selectedChapter = ref<Chapter | null>(null)

// 对话框状态
const chapterDialogVisible = ref(false)
const videoUploadDialogVisible = ref(false)
const editingChapter = ref<Chapter | null>(null)
const uploadTargetChapter = ref<Chapter | null>(null)

// 加载章节树
async function loadChapters() {
  loading.value = true
  error.value = null
  try {
    chapters.value = await chapterTools.getChapterTree(courseName.value)
    
    // 默认展开所有章节
    chapters.value.forEach(chapter => {
      expandedIds.value.add(chapter.id)
      if (chapter.children) {
        chapter.children.forEach(child => expandedIds.value.add(child.id))
      }
    })
  } catch (err: any) {
    error.value = err.message || '加载失败'
    console.error('加载章节失败:', err)
  } finally {
    loading.value = false
  }
}

// 切换展开/折叠
function toggleExpand(chapterId: number) {
  if (expandedIds.value.has(chapterId)) {
    expandedIds.value.delete(chapterId)
  } else {
    expandedIds.value.add(chapterId)
  }
}

// 选择章节
function handleSelectChapter(chapter: Chapter) {
  selectedChapter.value = chapter
  selectedVideo.value = null
}

// 选择视频
function handleSelectVideo(video: ChapterVideo, chapter?: Chapter) {
  selectedVideo.value = video
}

// 新建章节
function handleAddChapter() {
  editingChapter.value = null
  chapterDialogVisible.value = true
}

// 编辑章节
function handleEditChapter(chapter: Chapter) {
  editingChapter.value = chapter
  chapterDialogVisible.value = true
}

// 删除章节
async function handleDeleteChapter(chapter: Chapter) {
  if (!confirm(`确定要删除章节 "${chapter.title}" 吗？${chapter.children?.length ? '（包括所有子章节）' : ''}`)) {
    return
  }

  loading.value = true
  try {
    await chapterTools.deleteChapter(chapter.id)
    await loadChapters()
  } catch (err: any) {
    alert('删除失败: ' + (err.message || '未知错误'))
    console.error('删除章节失败:', err)
  } finally {
    loading.value = false
  }
}

// 确认章节编辑
async function handleConfirmChapter(data: { title: string; description: string; parent_id?: number }) {
  loading.value = true
  try {
    if (editingChapter.value) {
      // 更新章节
      await chapterTools.updateChapter(editingChapter.value.id, data)
    } else {
      // 新建章节
      await chapterTools.addChapter({
        course_name: courseName.value,
        ...data
      })
    }
    
    chapterDialogVisible.value = false
    await loadChapters()
  } catch (err: any) {
    alert('操作失败: ' + (err.message || '未知错误'))
    console.error('章节操作失败:', err)
  } finally {
    loading.value = false
  }
}

// 上传视频
function handleUploadVideo(chapter: Chapter) {
  uploadTargetChapter.value = chapter
  videoUploadDialogVisible.value = true
}

// 确认上传视频
async function handleConfirmUpload(data: { file: File; title: string; description: string }) {
  if (!uploadTargetChapter.value) return

  loading.value = true
  try {
    await chapterTools.uploadVideo(
      data.file,
      uploadTargetChapter.value.id,
      data.title,
      data.description
    )
    
    videoUploadDialogVisible.value = false
    await loadChapters()
  } catch (err: any) {
    alert('上传失败: ' + (err.message || '未知错误'))
    console.error('上传视频失败:', err)
  } finally {
    loading.value = false
  }
}

// 删除视频
async function handleDeleteVideo(video: ChapterVideo) {
  if (!confirm(`确定要删除视频 "${video.title}" 吗？`)) {
    return
  }

  loading.value = true
  try {
    await chapterTools.deleteVideo(video.id)
    await loadChapters()
    
    if (selectedVideo.value?.id === video.id) {
      selectedVideo.value = null
    }
  } catch (err: any) {
    alert('删除失败: ' + (err.message || '未知错误'))
    console.error('删除视频失败:', err)
  } finally {
    loading.value = false
  }
}

// 更新学习进度
async function handleProgressUpdate(progress: number, completed: boolean) {
  if (!selectedVideo.value) return

  try {
    await chapterTools.updateProgress(selectedVideo.value.id, progress, completed)
  } catch (err: any) {
    console.error('更新进度失败:', err)
  }
}

// 获取所有顶级章节（用于父章节选择）
const topLevelChapters = computed(() => {
  return chapters.value.filter(c => !c.parent_id)
})

onMounted(() => {
  loadChapters()
})
</script>

<template>
  <Layout pageTitle="资料中心">
  <div class="chapter-page">
    <div class="page-header">
      <div>
        <h1>章节学习</h1>
        <p class="sub-title">
          当前身份：
          <span class="tag" :class="isTeacher ? 'teacher' : 'student'">
            {{ isTeacher ? '老师，可管理章节和视频' : '学生，可观看视频学习' }}
          </span>
        </p>
      </div>
      <button v-if="isTeacher" class="btn primary" @click="handleAddChapter">
        <i class="fas fa-plus"></i> 新建章节
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- 错误提示 -->
    <div v-else-if="error" class="error-message">
      <p><i class="fas fa-exclamation-circle"></i> {{ error }}</p>
      <button class="btn-retry" @click="loadChapters">重试</button>
    </div>

    <!-- 主内容区 -->
    <div v-else class="content-layout">
      <!-- 左侧：章节树 -->
      <div class="sidebar">
        <div class="sidebar-header">
          <h3>章节目录</h3>
          <span v-if="isTeacher && selectedChapter" class="selected-hint">
            已选择: {{ selectedChapter.title }}
          </span>
        </div>
        <ChapterTree
          :chapters="chapters"
          :is-teacher="isTeacher"
          :expanded-ids="expandedIds"
          @select-chapter="handleSelectChapter"
          @select-video="handleSelectVideo"
          @edit-chapter="handleEditChapter"
          @delete-chapter="handleDeleteChapter"
          @delete-video="handleDeleteVideo"
          @toggle-expand="toggleExpand"
        />
        <div v-if="isTeacher" class="upload-section">
          <button
            v-if="selectedChapter"
            class="btn-upload primary"
            @click="handleUploadVideo(selectedChapter)"
          >
            <i class="fas fa-upload"></i> 上传视频到 "{{ selectedChapter.title }}"
          </button>
          <div v-else class="upload-hint">
            <i class="fas fa-info-circle"></i> 点击章节标题以选择，然后上传视频
          </div>
        </div>
      </div>

      <!-- 右侧：视频播放器 -->
      <div class="main-content">
        <VideoPlayer
          :video="selectedVideo"
          :is-student="!isTeacher"
          @close="selectedVideo = null"
          @progress-update="handleProgressUpdate"
        />
      </div>
    </div>

    <!-- 章节编辑对话框 -->
    <ChapterDialog
      :visible="chapterDialogVisible"
      :chapter="editingChapter"
      :parent-chapters="topLevelChapters"
      @close="chapterDialogVisible = false"
      @confirm="handleConfirmChapter"
    />

    <!-- 视频上传对话框 -->
    <VideoUploadDialog
      :visible="videoUploadDialogVisible"
      @close="videoUploadDialogVisible = false"
      @confirm="handleConfirmUpload"
    />
  </div>
  </Layout>
</template>

<style scoped>
.chapter-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #d0d7de;
}

.page-header h1 {
  color: #1f2328;
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.sub-title {
  color: #656d76;
  margin: 0;
  font-size: 0.875rem;
}

.tag {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  margin-left: 0.5rem;
}

.tag.teacher {
  background: #ddf4ff;
  color: #0969da;
  border: 1px solid #b6e3ff;
}

.tag.student {
  background: #dafbe1;
  color: #1a7f37;
  border: 1px solid #ace1af;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: none;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn.primary {
  background-color: #2da44e;
  color: white;
  border: 1px solid #2da44e;
}

.btn.primary:hover {
  background-color: #2c974b;
  border-color: #2c974b;
}

/* 加载和错误状态 */
.loading,
.error-message {
  text-align: center;
  padding: 3rem 1rem;
  color: #656d76;
}

.spinner {
  width: 32px;
  height: 32px;
  margin: 0 auto 1rem;
  border: 3px solid #f6f8fa;
  border-top: 3px solid #0969da;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message p {
  margin-bottom: 1rem;
  color: #cf222e;
  font-size: 0.875rem;
}

.btn-retry {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid #d0d7de;
  background: #ffffff;
  color: #1f2328;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 0.875rem;
  font-weight: 500;
}

.btn-retry:hover {
  background: #f6f8fa;
  border-color: #0969da;
  color: #0969da;
}

/* 内容布局 */
.content-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 1.5rem;
  min-height: 500px;
}

.sidebar {
  border-right: 1px solid #d0d7de;
  padding-right: 1.5rem;
  overflow-y: auto;
  max-height: calc(100vh - 250px);
}

.sidebar-header {
  margin-bottom: 1rem;
}

.sidebar-header h3 {
  margin: 0 0 0.5rem 0;
  color: #1f2328;
  font-size: 1rem;
  font-weight: 600;
}

.selected-hint {
  display: block;
  font-size: 0.75rem;
  color: #0969da;
  background: #ddf4ff;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  margin-top: 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border: 1px solid #b6e3ff;
}

.upload-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #d0d7de;
}

.btn-upload {
  width: 100%;
  padding: 0.625rem 1rem;
  border: 1px solid #2da44e;
  background: #2da44e;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.15s;
}

.btn-upload:hover {
  background: #2c974b;
  border-color: #2c974b;
}

.btn-upload:active {
  transform: scale(0.98);
}

.upload-hint {
  padding: 1rem;
  text-align: center;
  color: #656d76;
  font-size: 0.875rem;
  background: #f6f8fa;
  border-radius: 6px;
  border: 1px dashed #d0d7de;
}

.main-content {
  overflow-y: auto;
  max-height: calc(100vh - 250px);
}

@media (max-width: 768px) {
  .content-layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: none;
    border-bottom: 1px solid #eee;
    padding-right: 0;
    padding-bottom: 2rem;
    max-height: 300px;
  }
}
</style>

