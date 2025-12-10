<template>
  <Layout pageTitle="班级管理">
    <div class="class-manager">
      <div class="page-header">
      <div class="header-left">
        <h2>班级管理</h2>
        <p>创建和管理您的班级</p>
      </div>
      <button @click="showCreateModal = true" class="btn-primary">
        <i class="fas fa-plus"></i> 创建班级
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <p>加载中...</p>
    </div>

    <!-- 班级列表 -->
    <div v-else class="class-list">
      <div class="class-card" v-for="classItem in classes" :key="classItem.id">
        <div class="class-header">
          <h3>{{ classItem.name }}</h3>
          <span class="class-code">班级代码: {{ classItem.code }}</span>
        </div>
        <p class="class-desc">{{ classItem.description }}</p>
        <div class="class-stats">
          <span><i class="fas fa-users"></i> {{ classItem.student_count || 0 }} 名学生</span>
          <span><i class="fas fa-calendar"></i> 创建于 {{ formatDate(classItem.created_at) }}</span>
        </div>
        <div class="class-actions">
          <button @click="enterClass(classItem.id)" class="btn-outline">
            进入班级
          </button>
          <button @click="editClass(classItem)" class="btn-icon">
            <i class="fas fa-edit"></i>
          </button>
          <button @click="deleteClass(classItem.id)" class="btn-icon danger">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 创建班级模态框 -->
    <div v-if="showCreateModal" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>创建新班级</h3>
          <button @click="showCreateModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="createClass">
            <div class="form-group">
              <label>班级名称 *</label>
              <input 
                v-model="newClass.name" 
                type="text" 
                placeholder="例如：2023级软件工程1班" 
                required
                autocomplete="off"
                :disabled="false"
              >
            </div>
            <div class="form-group">
              <label>班级描述</label>
              <textarea 
                v-model="newClass.description" 
                placeholder="描述班级的基本信息..." 
                rows="3"
                :disabled="false"
              ></textarea>
            </div>
            <div class="form-actions">
              <button type="button" @click="showCreateModal = false" class="btn-secondary">取消</button>
              <button type="submit" class="btn-primary">创建班级</button>
            </div>
          </form>
        </div>
      </div>
    </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { teacherApi } from '@/api/teacher';
import Layout from '@/components/Layout.vue';

const router = useRouter();

const showCreateModal = ref(false);
const isLoading = ref(false);
const newClass = reactive({
  name: '',
  description: ''
});

// 从API获取的班级数据
const classes = ref<any[]>([]);

const formatDate = (dateStr: string) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('zh-CN');
};

// 加载班级列表
const loadClasses = async () => {
  isLoading.value = true;
  try {
    const response = await teacherApi.getClasses();
    classes.value = Array.isArray(response) ? response : (response?.data || []);
  } catch (error: any) {
    console.error('加载班级失败:', error);
    alert('加载班级失败: ' + (error.response?.data?.message || error.message));
  } finally {
    isLoading.value = false;
  }
};

const createClass = async () => {
  if (!newClass.name.trim()) return;

  try {
    const response = await teacherApi.createClass({
      name: newClass.name,
      description: newClass.description || ''
    });
    
    // 重新加载班级列表
    await loadClasses();
    showCreateModal.value = false;

    // 重置表单
    newClass.name = '';
    newClass.description = '';

    alert(`班级 "${newClass.name}" 创建成功！`);
  } catch (error: any) {
    console.error('创建班级失败:', error);
    alert('创建班级失败: ' + (error.response?.data?.message || error.message));
  }
};

const enterClass = (classId: string | number) => {
  router.push(`/teacher/classes/${classId}`);
};

const editClass = (classItem: any) => {
  alert(`编辑班级: ${classItem.name}`);
};

const deleteClass = async (classId: string | number) => {
  if (!confirm('确定要删除这个班级吗？')) return;

  try {
    await teacherApi.deleteClass(Number(classId));
    // 重新加载班级列表
    await loadClasses();
    alert('班级已删除');
  } catch (error: any) {
    console.error('删除班级失败:', error);
    alert('删除班级失败: ' + (error.response?.data?.message || error.message));
  }
};

// 组件挂载时加载数据
onMounted(() => {
  loadClasses();
});
</script>

<style scoped>
.class-manager {
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

.header-left h2 {
  margin: 0 0 8px 0;
  color: #1f2328;
  font-size: 24px;
  font-weight: 600;
}

.header-left p {
  margin: 0;
  color: #656d76;
  font-size: 14px;
}

.btn-primary {
  background: #4a6fa5;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}

.btn-primary:hover {
  background: #3a5a8c;
}

.class-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
}

.class-card {
  background: #ffffff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 16px;
  transition: border-color 0.15s;
}

.class-card:hover {
  border-color: #0969da;
}

.class-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.class-header h3 {
  margin: 0;
  color: #333;
  font-size: 18px;
}

.class-code {
  background: #f0f7ff;
  color: #4a6fa5;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.class-desc {
  color: #666;
  margin: 12px 0;
  line-height: 1.6;
}

.class-stats {
  display: flex;
  gap: 20px;
  margin: 16px 0;
  color: #888;
  font-size: 14px;
}

.class-stats i {
  margin-right: 6px;
}

.class-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.btn-outline {
  background: white;
  color: #4a6fa5;
  border: 1px solid #4a6fa5;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  flex: 1;
}

.btn-icon {
  width: 36px;
  height: 36px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon.danger {
  color: #dc3545;
  border-color: #dc3545;
}

.btn-icon.danger:hover {
  background: #dc3545;
  color: white;
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
  pointer-events: auto;
}

.modal {
  background: white;
  border-radius: 8px;
  width: 500px;
  max-width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  pointer-events: auto;
  position: relative;
  z-index: 1001;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
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

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  pointer-events: auto !important;
  background: #ffffff !important;
  cursor: text;
  -webkit-user-select: text;
  user-select: text;
}

.form-group input:disabled,
.form-group textarea:disabled {
  background: #f6f8fa !important;
  cursor: not-allowed;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #0969da;
  box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.1);
}

.form-group textarea {
  resize: vertical;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 32px;
}

/* 统一按钮样式 */
.btn-primary,
.btn-secondary,
.btn-outline {
  padding: 10px 20px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-primary {
  background: #4a6fa5;
  color: white;
}

.btn-primary:hover {
  background: #3a5a8c;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(74, 111, 165, 0.3);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(108, 117, 125, 0.3);
}

.btn-outline {
  background: white;
  color: #4a6fa5;
  border: 1px solid #4a6fa5;
  padding: 8px 16px;
  flex: 1;
}

.btn-outline:hover {
  background: #f0f7ff;
  border-color: #3a5a8c;
  transform: translateY(-1px);
}

.btn-icon {
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  transition: all 0.3s ease;
}

.btn-icon:hover {
  background: #f8f9fa;
  border-color: #4a6fa5;
  color: #4a6fa5;
}

.btn-icon.danger {
  color: #dc3545;
  border-color: #dc3545;
}

.btn-icon.danger:hover {
  background: #dc3545;
  color: white;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #f0f0f0;
  color: #333;
}

/* 按钮禁用状态 */
button:disabled,
.btn-primary:disabled,
.btn-secondary:disabled,
.btn-outline:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

.loading-state {
  text-align: center;
  padding: 40px;
  color: #666;
}
</style>