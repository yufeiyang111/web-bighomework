<script setup lang="ts">
import { computed } from 'vue'
import type { Chapter } from '../../tools/ChapterTools'

const props = defineProps<{
  chapters: Chapter[]
  isTeacher: boolean
  expandedIds?: Set<number>
}>()

const emit = defineEmits<{
  (e: 'select-chapter', chapter: Chapter): void
  (e: 'select-video', video: any, chapter: Chapter): void
  (e: 'edit-chapter', chapter: Chapter): void
  (e: 'delete-chapter', chapter: Chapter): void
  (e: 'delete-video', video: any, chapter: Chapter): void
  (e: 'toggle-expand', chapterId: number): void
}>()

function isExpanded(chapterId: number): boolean {
  return props.expandedIds?.has(chapterId) || false
}

function getVideoIcon(completed?: boolean): string {
  return completed ? '✅' : '▶️'
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function handleChapterClick(chapter: Chapter) {
  // 切换展开状态
  emit('toggle-expand', chapter.id)
  // 同时选中章节（用于显示上传按钮）
  emit('select-chapter', chapter)
}
</script>

<template>
  <div class="chapter-tree">
    <div v-for="chapter in chapters" :key="chapter.id" class="chapter-item">
      <!-- 章节折叠面板 -->
      <div class="chapter-panel" :class="{ 'expanded': isExpanded(chapter.id) }">
        <!-- 章节头部 -->
        <div class="chapter-header" @click="handleChapterClick(chapter)">
          <div class="header-left">
            <span class="expand-arrow">{{ isExpanded(chapter.id) ? '▼' : '▶' }}</span>
            <span class="chapter-icon">📚</span>
            <span class="chapter-title">{{ chapter.title }}</span>
            <span v-if="chapter.description" class="chapter-desc">{{ chapter.description }}</span>
          </div>
          <div v-if="isTeacher" class="chapter-actions" @click.stop>
            <button class="btn-icon" @click="emit('edit-chapter', chapter)" title="编辑章节">
              <span>✏️</span>
            </button>
            <button class="btn-icon delete" @click="emit('delete-chapter', chapter)" title="删除章节">
              <span>🗑️</span>
            </button>
          </div>
        </div>

        <!-- 展开内容 -->
        <transition name="slide">
          <div v-if="isExpanded(chapter.id)" class="chapter-content">
            <!-- 视频列表 -->
            <div v-if="chapter.videos && chapter.videos.length > 0" class="video-list">
              <div
                v-for="video in chapter.videos"
                :key="video.id"
                class="video-item"
                @click="emit('select-video', video, chapter)"
              >
                <div class="video-info">
                  <span class="video-icon">{{ getVideoIcon(video.completed) }}</span>
                  <div class="video-details">
                    <span class="video-title">{{ video.title }}</span>
                    <span v-if="video.description" class="video-desc">{{ video.description }}</span>
                  </div>
                </div>
                <div class="video-meta">
                  <span v-if="video.duration" class="video-duration">
                    ⏱ {{ formatDuration(video.duration) }}
                  </span>
                  <button
                    v-if="isTeacher"
                    class="btn-icon delete"
                    @click.stop="emit('delete-video', video, chapter)"
                    title="删除视频"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>

            <!-- 空状态 -->
            <div v-else class="empty-videos">
              <span>📹 暂无视频</span>
            </div>

            <!-- 子章节 -->
            <div v-if="chapter.children && chapter.children.length > 0" class="sub-chapters">
              <ChapterTree
                :chapters="chapter.children"
                :is-teacher="isTeacher"
                :expanded-ids="expandedIds"
                @select-chapter="(c) => emit('select-chapter', c)"
                @select-video="(v, c) => emit('select-video', v, c)"
                @edit-chapter="(c) => emit('edit-chapter', c)"
                @delete-chapter="(c) => emit('delete-chapter', c)"
                @delete-video="(v, c) => emit('delete-video', v, c)"
                @toggle-expand="(id) => emit('toggle-expand', id)"
              />
            </div>
          </div>
        </transition>
      </div>
    </div>

    <div v-if="chapters.length === 0" class="empty">
      <span>📚 暂无章节</span>
      <p v-if="isTeacher">点击上方"新建章节"按钮开始创建</p>
    </div>
  </div>
</template>

<style scoped>
.chapter-tree {
  padding: 0;
}

.chapter-item {
  margin-bottom: 0.75rem;
}

/* 折叠面板样式 */
.chapter-panel {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  overflow: hidden;
  transition: all 0.3s ease;
}

.chapter-panel.expanded {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

/* 章节头部 */
.chapter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.chapter-panel.expanded .chapter-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.chapter-header:hover {
  background: linear-gradient(135deg, #e8edff 0%, #f8f9ff 100%);
}

.chapter-panel.expanded .chapter-header:hover {
  background: linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
  min-width: 0;
}

.expand-arrow {
  font-size: 0.8rem;
  transition: transform 0.3s;
  flex-shrink: 0;
}

.chapter-icon {
  font-size: 1.3rem;
  flex-shrink: 0;
}

.chapter-title {
  font-weight: 600;
  font-size: 1.05rem;
  color: #333;
  flex-shrink: 0;
}

.chapter-panel.expanded .chapter-title {
  color: white;
}

.chapter-desc {
  font-size: 0.85rem;
  color: #666;
  margin-left: 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chapter-panel.expanded .chapter-desc {
  color: rgba(255, 255, 255, 0.9);
}

/* 章节操作按钮 */
.chapter-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.btn-icon {
  border: none;
  background: rgba(0, 0, 0, 0.05);
  cursor: pointer;
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  transition: all 0.2s;
  font-size: 1rem;
}

.btn-icon:hover {
  background: rgba(0, 0, 0, 0.1);
  transform: scale(1.05);
}

.chapter-panel.expanded .btn-icon {
  background: rgba(255, 255, 255, 0.2);
}

.chapter-panel.expanded .btn-icon:hover {
  background: rgba(255, 255, 255, 0.3);
}

.btn-icon.delete:hover {
  background: rgba(229, 62, 62, 0.2);
}

/* 展开内容 */
.chapter-content {
  padding: 1rem;
  background: #fafbff;
  border-top: 1px solid #e8edff;
}

/* 过渡动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  max-height: 2000px;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}

/* 视频列表 */
.video-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.video-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.video-item:hover {
  border-color: #667eea;
  background: #f8f9ff;
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.video-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
  min-width: 0;
}

.video-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.video-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
  min-width: 0;
}

.video-title {
  color: #333;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-desc {
  font-size: 0.85rem;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.video-duration {
  font-size: 0.85rem;
  color: #999;
  white-space: nowrap;
}

/* 空状态 */
.empty-videos {
  padding: 2rem;
  text-align: center;
  color: #999;
  font-size: 0.95rem;
}

/* 子章节 */
.sub-chapters {
  margin-top: 1rem;
  padding-left: 1.5rem;
  border-left: 2px solid #e8edff;
}

/* 空状态 */
.empty {
  padding: 3rem 2rem;
  text-align: center;
  color: #999;
}

.empty span {
  font-size: 1.2rem;
  display: block;
  margin-bottom: 0.5rem;
}

.empty p {
  margin: 0.5rem 0 0 0;
  font-size: 0.9rem;
  color: #bbb;
}

/* 响应式 */
@media (max-width: 768px) {
  .chapter-header {
    padding: 0.75rem 1rem;
  }

  .header-left {
    gap: 0.5rem;
  }

  .chapter-desc {
    display: none;
  }

  .video-desc {
    display: none;
  }

  .sub-chapters {
    padding-left: 0.75rem;
  }
}
</style>
