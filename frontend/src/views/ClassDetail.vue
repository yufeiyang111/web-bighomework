<template>
  <Layout pageTitle="班级详情">
    <div class="class-detail">
      <div class="page-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">
          <i class="fas fa-arrow-left"></i> 返回
        </button>
        <div>
          <h2>{{ classInfo.name || '加载中...' }}</h2>
          <p class="class-code">班级代码: {{ classInfo.code }}</p>
        </div>
      </div>
      <button @click="showAddStudentModal = true" class="btn-primary">
        <i class="fas fa-user-plus"></i> 添加学生
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <p>加载中...</p>
    </div>

    <!-- 班级信息 -->
    <div v-else class="class-content">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-users"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ classInfo.student_count || 0 }}</div>
            <div class="stat-label">学生人数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-file-alt"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ classInfo.exam_count || 0 }}</div>
            <div class="stat-label">考试数量</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-chart-line"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ classInfo.score_count || 0 }}</div>
            <div class="stat-label">成绩记录</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-question-circle"></i>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ classInfo.question_count || 0 }}</div>
            <div class="stat-label">提问数量</div>
          </div>
        </div>
      </div>

      <!-- 班级描述 -->
      <div v-if="classInfo.description" class="info-section">
        <h3>班级描述</h3>
        <p>{{ classInfo.description }}</p>
      </div>

      <!-- 学生列表 -->
      <div class="info-section">
        <div class="section-header">
          <h3>学生列表 ({{ students.length }})</h3>
          <div class="search-box">
            <input
                v-model="searchKeyword"
                type="text"
                placeholder="搜索学生姓名或学号..."
                class="search-input"
            >
            <i class="fas fa-search"></i>
          </div>
        </div>

        <div v-if="filteredStudents.length === 0" class="empty-state">
          <i class="fas fa-user-slash"></i>
          <p>{{ searchKeyword ? '没有找到匹配的学生' : '该班级暂无学生' }}</p>
        </div>

        <div v-else class="students-grid">
          <div v-for="student in filteredStudents" :key="student.id" class="student-card">
            <div class="student-avatar">
              <i class="fas fa-user"></i>
            </div>
            <div class="student-info">
              <div class="student-name">{{ student.name || student.real_name || student.system_account || '未知' }}</div>
              <div class="student-meta">
                <span>学号: {{ student.username || student.system_account || student.systemAccount || '-' }}</span>
                <span v-if="student.email">邮箱: {{ student.email }}</span>
              </div>
            </div>
            <button @click="removeStudent(student.id)" class="btn-remove" title="移除学生">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加学生模态框 -->
    <div v-if="showAddStudentModal" class="modal-overlay" @click.self="showAddStudentModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>添加学生到班级</h3>
          <button @click="showAddStudentModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>搜索学生</label>
            <input
                v-model="studentSearch"
                type="text"
                placeholder="输入学生姓名、学号或邮箱..."
                class="search-input"
                @input="searchStudents"
            >
          </div>

          <div class="students-selection">
            <div class="select-all-bar">
              <label>
                <input type="checkbox" v-model="selectAll" @change="toggleSelectAll">
                全选
              </label>
              <span class="selected-count">已选择 {{ selectedStudents.length }} 人</span>
            </div>

            <div class="students-list">
              <div
                  v-for="student in availableStudents"
                  :key="student.id"
                  class="student-item"
                  :class="{ selected: selectedStudents.includes(student.id) }"
              >
                <label>
                  <input
                      type="checkbox"
                      :value="student.id"
                      v-model="selectedStudents"
                  >
                  <div class="student-details">
                    <div class="student-name">{{ student.name || student.real_name || student.system_account || '未知' }}</div>
                    <div class="student-info">
                      <span>学号: {{ student.username || student.system_account || student.systemAccount || '-' }}</span>
                      <span v-if="student.email">邮箱: {{ student.email }}</span>
                    </div>
                  </div>
                </label>
              </div>

              <div v-if="availableStudents.length === 0" class="empty-state">
                <i class="fas fa-search"></i>
                <p>{{ studentSearch ? '没有找到匹配的学生' : '请输入关键词搜索学生' }}</p>
              </div>
            </div>
          </div>

          <div class="form-actions">
            <button @click="showAddStudentModal = false" class="btn-secondary">取消</button>
            <button @click="addStudents" class="btn-primary" :disabled="selectedStudents.length === 0">
              添加选中学生 ({{ selectedStudents.length }})
            </button>
          </div>
        </div>
      </div>
    </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { teacherApi } from '@/api/teacher';
import Layout from '@/components/Layout.vue';

const route = useRoute();
const router = useRouter();

const classId = computed(() => Number(route.params.id));
const isLoading = ref(false);
const showAddStudentModal = ref(false);
const searchKeyword = ref('');
const studentSearch = ref('');
const selectAll = ref(false);
const selectedStudents = ref<number[]>([]);

const classInfo = ref<any>({});
const students = ref<any[]>([]);
const availableStudents = ref<any[]>([]);

const filteredStudents = computed(() => {
  if (!searchKeyword.value) return students.value;
  
  const keyword = searchKeyword.value.toLowerCase();
  return students.value.filter(student =>
      (student.name || student.real_name || '').toLowerCase().includes(keyword) ||
      (student.username || student.system_account || student.systemAccount || '').toLowerCase().includes(keyword) ||
      (student.email || '').toLowerCase().includes(keyword)
  );
});

// 加载班级详情
const loadClassDetail = async () => {
  isLoading.value = true;
  try {
    const response = await teacherApi.getClassDetail(classId.value);
    classInfo.value = response;
    students.value = response.students || [];
  } catch (error: any) {
    console.error('加载班级详情失败:', error);
    alert('加载班级详情失败: ' + (error.response?.data?.message || error.message));
  } finally {
    isLoading.value = false;
  }
};

// 搜索防抖定时器
let searchTimer: NodeJS.Timeout | null = null;

// 搜索学生
const searchStudents = async () => {
  // 清除之前的定时器
  if (searchTimer) {
    clearTimeout(searchTimer);
  }

  // 如果搜索关键词为空，清空结果
  if (!studentSearch.value.trim()) {
    availableStudents.value = [];
    return;
  }

  // 防抖：延迟 300ms 执行搜索
  searchTimer = setTimeout(async () => {
    try {
      console.log('搜索学生:', studentSearch.value);
      const response = await teacherApi.getStudents({
        search: studentSearch.value.trim(),
        exclude_class_id: classId.value
      });
      console.log('搜索结果:', response);
      availableStudents.value = Array.isArray(response) ? response : (response?.data || []);
      console.log('可用学生数量:', availableStudents.value.length);
    } catch (error: any) {
      console.error('搜索学生失败:', error);
      console.error('错误详情:', error.response?.data);
      availableStudents.value = [];
    }
  }, 300);
};

// 全选/取消全选
const toggleSelectAll = () => {
  if (selectAll.value) {
    selectedStudents.value = availableStudents.value.map(s => s.id);
  } else {
    selectedStudents.value = [];
  }
};

// 添加学生
const addStudents = async () => {
  if (selectedStudents.value.length === 0) {
    alert('请至少选择一个学生');
    return;
  }

  try {
    const response = await teacherApi.addStudentsToClass(classId.value, {
      student_ids: selectedStudents.value
    });
    
    alert(`成功添加 ${response.added?.length || 0} 名学生`);
    
    // 重新加载班级详情
    await loadClassDetail();
    
    // 关闭模态框并重置
    showAddStudentModal.value = false;
    studentSearch.value = '';
    selectedStudents.value = [];
    selectAll.value = false;
    availableStudents.value = [];
  } catch (error: any) {
    console.error('添加学生失败:', error);
    alert('添加学生失败: ' + (error.response?.data?.message || error.message));
  }
};

// 移除学生
const removeStudent = async (studentId: number) => {
  if (!confirm('确定要将该学生移出班级吗？')) return;

  try {
    await teacherApi.removeStudentFromClass(classId.value, studentId);
    alert('学生已移出班级');
    await loadClassDetail();
  } catch (error: any) {
    console.error('移除学生失败:', error);
    alert('移除学生失败: ' + (error.response?.data?.message || error.message));
  }
};

const goBack = () => {
  router.push('/teacher/class-manager');
};

onMounted(() => {
  loadClassDetail();
});
</script>

<style scoped>
.class-detail {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-back {
  background: white;
  border: 1px solid #ddd;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
}

.btn-back:hover {
  background: #f8f9fa;
}

.header-left h2 {
  margin: 0 0 4px 0;
  color: #333;
  font-size: 28px;
}

.class-code {
  color: #666;
  font-size: 14px;
}

.loading-state {
  text-align: center;
  padding: 60px;
  color: #666;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 0;
}

.stat-card {
  background: #ffffff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: border-color 0.15s;
}

.stat-card:hover {
  border-color: #0969da;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.stat-card:nth-child(2) .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card:nth-child(3) .stat-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-card:nth-child(4) .stat-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
  line-height: 1;
}

.stat-label {
  color: #666;
  font-size: 14px;
  margin-top: 4px;
}

.info-section {
  background: #ffffff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 0;
}

.info-section h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.search-box {
  position: relative;
  width: 300px;
}

.search-box .search-input {
  width: 100%;
  padding: 10px 40px 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.search-box i {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
}

.students-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.student-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s;
}

.student-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.student-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.student-info {
  flex: 1;
}

.student-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.student-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: #666;
}

.btn-remove {
  background: none;
  border: none;
  color: #dc3545;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.3s;
}

.btn-remove:hover {
  background: #fee;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: white;
  border-radius: 12px;
  width: 600px;
  max-width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal.modal-lg {
  width: 800px;
}

.modal-header {
  padding: 24px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  background: white;
  z-index: 10;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
}

.modal-body {
  padding: 24px;
}

.students-selection {
  margin: 24px 0;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.select-all-bar {
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.select-all-bar label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  margin: 0;
}

.selected-count {
  color: #666;
  font-size: 14px;
}

.students-list {
  max-height: 400px;
  overflow-y: auto;
}

.student-item {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.student-item:hover {
  background: #f8f9fa;
}

.student-item.selected {
  background: #e3f2fd;
}

.student-item label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  margin: 0;
  width: 100%;
}

.student-details {
  flex: 1;
}

.student-details .student-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.student-details .student-info {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #666;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.btn-primary, .btn-secondary {
  padding: 10px 20px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary {
  background: #4a6fa5;
  color: white;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}
</style>
