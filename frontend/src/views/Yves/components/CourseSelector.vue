<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Course {
  id: string
  name: string
  teacherId: number
  teacherName: string
  description?: string
}

const props = defineProps<{
  currentCourse?: Course
}>()

const emit = defineEmits<{
  (e: 'change', course: Course): void
}>()

// 课程列表
const courses = ref<Course[]>([
  {
    id: '1',
    name: 'Web高级编程',
    teacherId: 1,
    teacherName: '于老师',
    description: 'Web开发进阶课程'
  },
  {
    id: '2',
    name: '数据结构与算法',
    teacherId: 1,
    teacherName: '于老师',
    description: '计算机基础课程'
  },
  {
    id: '3',
    name: 'Python程序设计',
    teacherId: 2,
    teacherName: '李老师',
    description: 'Python编程入门'
  },
  {
    id: '4',
    name: '数据库原理',
    teacherId: 1,
    teacherName: '于老师',
    description: '数据库设计与应用'
  }
])

const selectedCourse = ref<Course | null>(props.currentCourse || null)
const showDropdown = ref(false)

// 选择课程
function selectCourse(course: Course) {
  selectedCourse.value = course
  showDropdown.value = false
  
  // 保存到localStorage
  localStorage.setItem('selectedCourse', JSON.stringify(course))
  
  // 触发事件
  emit('change', course)
}

// 从localStorage加载课程
function loadSavedCourse() {
  const saved = localStorage.getItem('selectedCourse')
  if (saved) {
    try {
      const course = JSON.parse(saved)
      selectedCourse.value = course
      emit('change', course)
    } catch (e) {
      console.error('加载课程失败:', e)
    }
  } else if (courses.value.length > 0) {
    // 默认选择第一个课程
    selectCourse(courses.value[0])
  }
}

onMounted(() => {
  if (!props.currentCourse) {
    loadSavedCourse()
  }
})
</script>

<template>
  <div class="course-selector">
    <div class="selector-trigger" @click="showDropdown = !showDropdown">
      <div class="current-course">
        <span class="icon">📚</span>
        <div class="course-info">
          <span class="course-name">{{ selectedCourse?.name || '选择课程' }}</span>
          <span class="course-teacher" v-if="selectedCourse">{{ selectedCourse.teacherName }}</span>
        </div>
      </div>
      <span class="arrow" :class="{ open: showDropdown }">▼</span>
    </div>

    <transition name="dropdown">
      <div v-if="showDropdown" class="dropdown-menu">
        <div class="dropdown-header">
          <span>选择课程</span>
          <button class="close-btn" @click="showDropdown = false">×</button>
        </div>
        
        <div class="course-list">
          <div
            v-for="course in courses"
            :key="course.id"
            class="course-item"
            :class="{ active: selectedCourse?.id === course.id }"
            @click="selectCourse(course)"
          >
            <div class="course-icon">📚</div>
            <div class="course-details">
              <div class="course-name">{{ course.name }}</div>
              <div class="course-meta">
                <span class="teacher">👨‍🏫 {{ course.teacherName }}</span>
                <span class="description" v-if="course.description">{{ course.description }}</span>
              </div>
            </div>
            <span v-if="selectedCourse?.id === course.id" class="check-icon">✓</span>
          </div>
        </div>
      </div>
    </transition>

    <!-- 遮罩层 -->
    <div v-if="showDropdown" class="overlay" @click="showDropdown = false"></div>
  </div>
</template>

<style scoped>
.course-selector {
  position: relative;
}

.selector-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 280px;
}

.selector-trigger:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.current-course {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.icon {
  font-size: 1.5rem;
}

.course-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.course-name {
  font-weight: 600;
  color: #1f2937;
  font-size: 0.95rem;
}

.course-teacher {
  font-size: 0.75rem;
  color: #6b7280;
}

.arrow {
  color: #9ca3af;
  font-size: 0.75rem;
  transition: transform 0.2s;
}

.arrow.open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 0;
  right: 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  z-index: 1001;
  max-height: 400px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  border: none;
  background: none;
  font-size: 1.5rem;
  color: #9ca3af;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #1f2937;
}

.course-list {
  overflow-y: auto;
  max-height: 320px;
}

.course-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid #f3f4f6;
}

.course-item:last-child {
  border-bottom: none;
}

.course-item:hover {
  background: #f9fafb;
}

.course-item.active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
}

.course-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.course-details {
  flex: 1;
  min-width: 0;
}

.course-details .course-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.course-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.teacher {
  font-size: 0.75rem;
  color: #667eea;
  font-weight: 500;
}

.description {
  font-size: 0.75rem;
  color: #9ca3af;
}

.check-icon {
  color: #10b981;
  font-size: 1.25rem;
  font-weight: bold;
  flex-shrink: 0;
}

.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 1000;
}

/* 下拉动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
