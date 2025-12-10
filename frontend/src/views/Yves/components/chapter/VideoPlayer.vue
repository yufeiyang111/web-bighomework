<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue'
import type { ChapterVideo } from '../../tools/ChapterTools'
import chapterTools from '../../tools/ChapterTools'

const props = defineProps<{
  video: ChapterVideo | null
  isStudent: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'progress-update', progress: number, completed: boolean): void
}>()

const videoRef = ref<HTMLVideoElement | null>(null)
const playerContainer = ref<HTMLDivElement | null>(null)
const currentTime = ref(0)
const duration = ref(0)
const isPlaying = ref(false)
const volume = ref(1)
const isMuted = ref(false)
const playbackRate = ref(1)
const isFullscreen = ref(false)
const showControls = ref(true)
const controlsTimeout = ref<number | null>(null)
const progressUpdateInterval = ref<number | null>(null)

// 可用的播放速度
const playbackRates = [0.5, 0.75, 1, 1.25, 1.5, 2]

// 进度百分比
const progressPercent = computed(() => {
  return duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0
})

// 音量图标
const volumeIcon = computed(() => {
  if (isMuted.value || volume.value === 0) return '🔇'
  if (volume.value < 0.5) return '🔉'
  return '🔊'
})

// 格式化时间
function formatTime(seconds: number): string {
  if (!isFinite(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 播放/暂停
function togglePlay() {
  if (!videoRef.value) return
  
  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play().catch(err => {
      console.error('播放失败:', err)
    })
  }
}

// 跳转到指定时间
function seekTo(event: MouseEvent) {
  if (!videoRef.value) return
  
  const progressBar = event.currentTarget as HTMLElement
  const rect = progressBar.getBoundingClientRect()
  const percent = (event.clientX - rect.left) / rect.width
  videoRef.value.currentTime = percent * duration.value
}

// 快进/快退
function skip(seconds: number) {
  if (!videoRef.value) return
  videoRef.value.currentTime = Math.max(0, Math.min(duration.value, videoRef.value.currentTime + seconds))
}

// 切换静音
function toggleMute() {
  if (!videoRef.value) return
  isMuted.value = !isMuted.value
  videoRef.value.muted = isMuted.value
}

// 更新音量
function updateVolume(value: number) {
  if (!videoRef.value) return
  volume.value = value
  videoRef.value.volume = value
  if (value > 0 && isMuted.value) {
    isMuted.value = false
    videoRef.value.muted = false
  }
}

// 切换播放速度
function changePlaybackRate() {
  if (!videoRef.value) return
  const currentIndex = playbackRates.indexOf(playbackRate.value)
  const nextIndex = (currentIndex + 1) % playbackRates.length
  playbackRate.value = playbackRates[nextIndex]
  videoRef.value.playbackRate = playbackRate.value
}

// 切换全屏
function toggleFullscreen() {
  if (!playerContainer.value) return
  
  if (!isFullscreen.value) {
    if (playerContainer.value.requestFullscreen) {
      playerContainer.value.requestFullscreen()
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    }
  }
}

// 显示控制栏
function showControlsBar() {
  showControls.value = true
  
  if (controlsTimeout.value) {
    clearTimeout(controlsTimeout.value)
  }
  
  // 3秒后自动隐藏控制栏（播放时）
  if (isPlaying.value) {
    controlsTimeout.value = window.setTimeout(() => {
      showControls.value = false
    }, 3000)
  }
}

// 键盘快捷键
function handleKeydown(event: KeyboardEvent) {
  if (!videoRef.value) return
  
  switch (event.key) {
    case ' ':
    case 'k':
      event.preventDefault()
      togglePlay()
      break
    case 'ArrowLeft':
      event.preventDefault()
      skip(-5)
      break
    case 'ArrowRight':
      event.preventDefault()
      skip(5)
      break
    case 'ArrowUp':
      event.preventDefault()
      updateVolume(Math.min(1, volume.value + 0.1))
      break
    case 'ArrowDown':
      event.preventDefault()
      updateVolume(Math.max(0, volume.value - 0.1))
      break
    case 'm':
      event.preventDefault()
      toggleMute()
      break
    case 'f':
      event.preventDefault()
      toggleFullscreen()
      break
    case 'j':
      event.preventDefault()
      skip(-10)
      break
    case 'l':
      event.preventDefault()
      skip(10)
      break
  }
}

// 更新进度
function updateProgress() {
  if (!videoRef.value || !props.isStudent) return
  
  const progress = Math.floor(videoRef.value.currentTime)
  const completed = progress >= duration.value * 0.9 // 观看90%算完成
  
  emit('progress-update', progress, completed)
}

// 视频时间更新
function onTimeUpdate() {
  if (videoRef.value) {
    currentTime.value = videoRef.value.currentTime
  }
}

// 视频元数据加载完成
function onLoadedMetadata() {
  if (videoRef.value) {
    duration.value = videoRef.value.duration
    
    // 恢复上次观看进度
    if (props.video?.progress && props.video.progress > 0) {
      videoRef.value.currentTime = props.video.progress
    }
  }
}

// 视频播放
function onPlay() {
  isPlaying.value = true
  showControlsBar()
}

// 视频暂停
function onPause() {
  isPlaying.value = false
  showControls.value = true
  if (controlsTimeout.value) {
    clearTimeout(controlsTimeout.value)
  }
}

// 音量变化
function onVolumeChange() {
  if (videoRef.value) {
    volume.value = videoRef.value.volume
    isMuted.value = videoRef.value.muted
  }
}

// 视频加载错误
function onError(event: Event) {
  const video = event.target as HTMLVideoElement
  if (video.error) {
    console.error('视频加载错误 - 代码:', video.error.code, '信息:', video.error.message)
  }
}

// 视频可以播放
function onCanPlay() {
  // 视频准备就绪
}

// 监听全屏变化
function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

// 监听视频变化
watch(() => props.video, (newVideo, oldVideo) => {
  if (newVideo && newVideo.id !== oldVideo?.id) {
    // 重置状态
    isPlaying.value = false
    currentTime.value = 0
    duration.value = 0
    
    // 重新加载视频
    if (videoRef.value) {
      videoRef.value.load()
    }
  }
})

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('keydown', handleKeydown)
  
  // 学生观看时，每10秒更新一次进度
  if (props.isStudent) {
    progressUpdateInterval.value = window.setInterval(updateProgress, 10000)
  }
})

onBeforeUnmount(() => {
  if (progressUpdateInterval.value) {
    clearInterval(progressUpdateInterval.value)
  }
  
  if (controlsTimeout.value) {
    clearTimeout(controlsTimeout.value)
  }
  
  // 保存最后的进度
  if (props.isStudent && videoRef.value) {
    updateProgress()
  }
  
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div v-if="video" class="video-player">
    <div class="player-header">
      <h3>{{ video.title }}</h3>
      <button class="btn-close" @click="emit('close')">✕</button>
    </div>

    <div 
      ref="playerContainer" 
      class="player-container"
      :class="{ 'fullscreen': isFullscreen, 'hide-cursor': !showControls && isPlaying }"
      @mousemove="showControlsBar"
      @mouseleave="showControls = false"
    >
      <video
        ref="videoRef"
        class="video-element"
        :src="video ? chapterTools.getVideoUrl(video.id) : ''"
        @click="togglePlay"
        @timeupdate="onTimeUpdate"
        @loadedmetadata="onLoadedMetadata"
        @play="onPlay"
        @pause="onPause"
        @volumechange="onVolumeChange"
        @error="onError"
        @canplay="onCanPlay"
      >
        您的浏览器不支持视频播放
      </video>

      <!-- 中央播放按钮 -->
      <transition name="fade">
        <div v-if="!isPlaying" class="center-play-btn" @click="togglePlay">
          <div class="play-icon">▶</div>
        </div>
      </transition>

      <!-- 控制栏 -->
      <div class="player-controls" :class="{ 'show': showControls }">
        <!-- 进度条 -->
        <div class="progress-bar" @click="seekTo">
          <div class="progress-filled" :style="{ width: progressPercent + '%' }"></div>
          <div class="progress-handle" :style="{ left: progressPercent + '%' }"></div>
        </div>

        <!-- 控制按钮 -->
        <div class="controls-row">
          <div class="controls-left">
            <button class="btn-control" @click="togglePlay" :title="isPlaying ? '暂停 (空格)' : '播放 (空格)'">
              {{ isPlaying ? '⏸' : '▶️' }}
            </button>

            <button class="btn-control" @click="skip(-10)" title="后退10秒 (J)">
              ⏪
            </button>

            <button class="btn-control" @click="skip(10)" title="前进10秒 (L)">
              ⏩
            </button>

            <div class="volume-control">
              <button class="btn-control" @click="toggleMute" :title="isMuted ? '取消静音 (M)' : '静音 (M)'">
                {{ volumeIcon }}
              </button>
              <input
                :value="volume"
                type="range"
                min="0"
                max="1"
                step="0.01"
                class="volume-slider"
                @input="(e) => updateVolume(parseFloat((e.target as HTMLInputElement).value))"
                title="音量 (↑↓)"
              />
            </div>

            <span class="time-display">
              {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
            </span>
          </div>

          <div class="controls-right">
            <button class="btn-control btn-rate" @click="changePlaybackRate" title="播放速度">
              {{ playbackRate }}x
            </button>

            <button class="btn-control" @click="toggleFullscreen" :title="isFullscreen ? '退出全屏 (F)' : '全屏 (F)'">
              {{ isFullscreen ? '⛶' : '⛶' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="video.description" class="video-description">
      <h4>视频简介</h4>
      <p>{{ video.description }}</p>
    </div>

    <!-- 快捷键提示 -->
    <div class="keyboard-hints">
      <details>
        <summary>⌨️ 键盘快捷键</summary>
        <div class="hints-content">
          <div class="hint-item"><kbd>空格</kbd> / <kbd>K</kbd> 播放/暂停</div>
          <div class="hint-item"><kbd>←</kbd> / <kbd>→</kbd> 快退/快进 5秒</div>
          <div class="hint-item"><kbd>J</kbd> / <kbd>L</kbd> 快退/快进 10秒</div>
          <div class="hint-item"><kbd>↑</kbd> / <kbd>↓</kbd> 增加/减少音量</div>
          <div class="hint-item"><kbd>M</kbd> 静音/取消静音</div>
          <div class="hint-item"><kbd>F</kbd> 全屏/退出全屏</div>
        </div>
      </details>
    </div>
  </div>

  <div v-else class="no-video">
    <div class="no-video-icon">🎬</div>
    <p>请选择要观看的视频</p>
  </div>
</template>

<style scoped>
.video-player {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.player-header h3 {
  margin: 0;
  font-size: 1.2rem;
  flex: 1;
}

.btn-close {
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 1.5rem;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

.player-container {
  position: relative;
  background: #000;
}

.player-container.fullscreen {
  position: fixed;
  inset: 0;
  z-index: 9999;
}

.player-container.hide-cursor {
  cursor: none;
}

.video-element {
  width: 100%;
  max-height: 500px;
  display: block;
}

.fullscreen .video-element {
  max-height: 100vh;
  height: 100vh;
  object-fit: contain;
}

/* 中央播放按钮 */
.center-play-btn {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  cursor: pointer;
  z-index: 10;
}

.play-icon {
  width: 80px;
  height: 80px;
  background: rgba(102, 126, 234, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: white;
  transition: all 0.3s;
}

.play-icon:hover {
  background: rgba(102, 126, 234, 1);
  transform: scale(1.1);
}

/* 控制栏 */
.player-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
  padding: 1rem;
  opacity: 0;
  transition: opacity 0.3s;
}

.player-controls.show {
  opacity: 1;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
  cursor: pointer;
  position: relative;
  margin-bottom: 0.75rem;
}

.progress-bar:hover {
  height: 8px;
}

.progress-filled {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 3px;
  transition: width 0.1s;
}

.progress-handle {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 14px;
  height: 14px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  opacity: 0;
  transition: opacity 0.2s;
}

.progress-bar:hover .progress-handle {
  opacity: 1;
}

.controls-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.controls-left,
.controls-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-control {
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 1rem;
  width: 36px;
  height: 36px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-control:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

.btn-rate {
  min-width: 48px;
  font-size: 0.85rem;
  font-weight: 600;
}

.volume-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.volume-slider {
  width: 80px;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
  cursor: pointer;
}

.volume-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.time-display {
  font-size: 0.9rem;
  color: white;
  min-width: 100px;
  font-variant-numeric: tabular-nums;
}

.video-description {
  padding: 1.5rem;
  border-top: 1px solid #eee;
}

.video-description h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.video-description p {
  margin: 0;
  color: #666;
  line-height: 1.6;
}

/* 快捷键提示 */
.keyboard-hints {
  padding: 1rem 1.5rem;
  border-top: 1px solid #eee;
  background: #f8f9ff;
}

.keyboard-hints summary {
  cursor: pointer;
  color: #667eea;
  font-size: 0.9rem;
  user-select: none;
}

.keyboard-hints summary:hover {
  color: #5568d3;
}

.hints-content {
  margin-top: 0.75rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.5rem;
}

.hint-item {
  font-size: 0.85rem;
  color: #666;
}

.hint-item kbd {
  display: inline-block;
  padding: 0.15rem 0.4rem;
  background: white;
  border: 1px solid #ddd;
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.8rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.no-video {
  padding: 4rem 2rem;
  text-align: center;
  color: #999;
}

.no-video-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .volume-control {
    display: none;
  }
  
  .time-display {
    font-size: 0.8rem;
    min-width: 80px;
  }
  
  .hints-content {
    grid-template-columns: 1fr;
  }
}
</style>
