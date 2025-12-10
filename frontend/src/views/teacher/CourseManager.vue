<template>
  <Layout pageTitle="课程管理">
    <div class="course-manager">
      <div class="page-header">
      <div class="header-left">
        <h2>课程管理</h2>
        <p>创建、管理和维护课程信息</p>
      </div>
      <button @click="showCreateModal = true" class="btn-primary">
        <i class="fas fa-plus"></i> 创建课程
      </button>
    </div>

    <!-- 绑定班级模态框 -->
    <div v-if="showBindModal" class="modal-overlay" @click.self="showBindModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>绑定班级</h3>
          <button @click="showBindModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-section">
            <h4>选择班级</h4>
            <div class="class-binding">
              <div class="select-all">
                <label>
                  <input type="checkbox" v-model="selectAllClasses" @change="toggleAllClasses">
                  全选所有班级
                </label>
              </div>
              <div class="classes-grid">
                <div v-for="classItem in availableClasses" :key="classItem.id" class="class-item">
                  <label>
                    <input type="checkbox" :value="classItem.id" v-model="newCourse.classes">
                    {{ classItem.name }} ({{ classItem.code }})
                  </label>
                  <span class="student-count">{{ classItem.studentCount }} 名学生</span>
                </div>
              </div>
            </div>
          </div>
          <div class="form-actions">
            <button type="button" @click="showBindModal = false" class="btn-secondary">取消</button>
            <button type="button" @click="saveBindClasses" class="btn-primary">保存绑定</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 课程统计 -->
    <div class="course-stats">
      <div class="stat-item">
        <div class="stat-number">{{ totalCourses }}</div>
        <div class="stat-label">总课程数</div>
      </div>
      <div class="stat-item">
        <div class="stat-number">{{ totalStudents }}</div>
        <div class="stat-label">覆盖学生</div>
      </div>
      <div class="stat-item">
        <div class="stat-number">{{ totalClasses }}</div>
        <div class="stat-label">绑定班级</div>
      </div>
      <div class="stat-item">
        <div class="stat-number">{{ totalMaterials }}</div>
        <div class="stat-label">课程资料</div>
      </div>
    </div>

    <!-- 课程列表 -->
    <div class="course-list">
      <div class="course-card" v-for="course in courses" :key="course.id">
        <div class="course-header">
          <div class="course-title-section">
            <h3>{{ course.name }}</h3>
            <div class="course-meta">
              <span class="course-code">{{ course.code }}</span>
              <span class="course-credit">{{ course.credit }} 学分</span>
              <span class="course-semester">{{ course.semester }}</span>
            </div>
          </div>
          <div class="course-status" :class="getStatusClass(course.status)">
            {{ getStatusText(course.status) }}
          </div>
        </div>

        <p class="course-description">{{ course.description }}</p>

        <div class="course-info">
          <div class="info-item">
            <i class="fas fa-user-tie"></i>
            <span>{{ teacherNamesFor(course) }}</span>
          </div>
          <div class="info-item">
            <i class="fas fa-users"></i>
            <span>{{ course.classCount || course.class_count || 0 }} 个班级</span>
          </div>
          <div class="info-item">
            <i class="fas fa-book"></i>
            <span>{{ course.materialCount || course.material_count || 0 }} 个资料</span>
          </div>
          <div class="info-item">
            <i class="fas fa-calendar"></i>
            <span>创建于 {{ formatDate(course.createdAt || course.created_at) }}</span>
          </div>
        </div>

        <div class="course-tags" v-if="course.tags && Array.isArray(course.tags) && course.tags.length > 0">
          <span v-for="tag in course.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>

        <div class="course-actions">
          <button @click="viewCourseDetail(course)" class="btn-outline">
            <i class="fas fa-eye"></i> 查看详情
          </button>
          <button @click="bindClasses(course)" class="btn-outline">
            <i class="fas fa-link"></i> 绑定班级
          </button>
          <button @click="uploadMaterial(course)" class="btn-outline">
            <i class="fas fa-upload"></i> 上传资料
          </button>
          <button @click="editCourse(course)" class="btn-icon">
            <i class="fas fa-edit"></i>
          </button>
          <button @click="deleteCourse(course.id)" class="btn-icon danger">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 创建课程模态框 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>创建新课程</h3>
          <button @click="showCreateModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="createCourse">
            <div class="form-section">
              <h4>基本信息</h4>
              <div class="form-row">
                <div class="form-group">
                  <label>课程名称 *</label>
                  <input v-model="newCourse.name" type="text" required placeholder="例如：数据结构与算法">
                </div>
                <div class="form-group">
                  <label>课程代码</label>
                  <input v-model="newCourse.code" type="text" placeholder="留空自动生成">
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label>学分 *</label>
                  <select v-model="newCourse.credit" required>
                    <option value="1">1 学分</option>
                    <option value="2">2 学分</option>
                    <option value="3">3 学分</option>
                    <option value="4">4 学分</option>
                    <option value="5">5 学分</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>学期 *</label>
                  <select v-model="newCourse.semester" required>
                    <option value="2023-2024-1">2023-2024 第一学期</option>
                    <option value="2023-2024-2">2023-2024 第二学期</option>
                    <option value="2024-2025-1">2024-2025 第一学期</option>
                  </select>
                </div>
              </div>

              <div class="form-group">
                <label>课程描述</label>
                <textarea v-model="newCourse.description" rows="4" placeholder="详细描述课程内容、教学目标等..."></textarea>
              </div>
            </div>

            <div class="form-section">
              <h4>班级绑定</h4>
              <div class="class-binding">
                <div class="select-all">
                  <label>
                    <input type="checkbox" v-model="selectAllClasses" @change="toggleAllClasses">
                    全选所有班级
                  </label>
                </div>
                <div class="classes-grid">
                  <div v-for="classItem in availableClasses" :key="classItem.id" class="class-item">
                    <label>
                      <input type="checkbox" :value="classItem.id" v-model="newCourse.classes">
                      {{ classItem.name }} ({{ classItem.code }})
                    </label>
                    <span class="student-count">{{ classItem.studentCount }} 名学生</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="form-section">
              <h4>课程标签</h4>
              <div class="tags-input">
                <div class="tags-list">
                  <span v-for="tag in newCourse.tags" :key="tag" class="tag">
                    {{ tag }}
                    <i class="fas fa-times" @click="removeTag(tag)"></i>
                  </span>
                </div>
                <div class="tag-input-group">
                  <input
                      v-model="tagInput"
                      type="text"
                      placeholder="添加标签..."
                      @keydown.enter="addTag"
                      class="tag-input"
                  >
                  <button type="button" @click="addTag" class="btn-icon">
                    <i class="fas fa-plus"></i>
                  </button>
                </div>
                <div class="tag-suggestions">
                  <span>常用标签：</span>
                  <span
                      v-for="suggestion in tagSuggestions"
                      :key="suggestion"
                      class="tag-suggestion"
                      @click="addSuggestion(suggestion)"
                  >
                    {{ suggestion }}
                  </span>
                </div>
              </div>
            </div>

            <div class="form-actions">
              <button type="button" @click="showCreateModal = false" class="btn-secondary">取消</button>
              <button type="submit" class="btn-primary">创建课程</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 课程详情模态框 -->
    <div v-if="showCourseDetail && selectedCourse" class="modal-overlay">
      <div class="modal modal-xl">
        <div class="modal-header">
          <h3>课程详情</h3>
          <button @click="closeCourseDetail" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="course-detail">
            <div class="detail-header">
              <h2>{{ selectedCourse.name }}</h2>
              <div class="detail-meta">
                <span class="course-code">{{ selectedCourse.code }}</span>
                <span class="course-credit">{{ selectedCourse.credit }} 学分</span>
                <span class="course-semester">{{ selectedCourse.semester }}</span>
                <span :class="'status-' + selectedCourse.status">
                  {{ getStatusText(selectedCourse.status) }}
                </span>
              </div>
            </div>

            <div class="detail-description">
              <h4>课程描述</h4>
              <p>{{ selectedCourse.description }}</p>
            </div>

            <div class="detail-sections">
              <div class="detail-section">
                <h4>绑定的班级</h4>
                <div class="classes-list">
                  <div v-for="cls in (selectedCourse.classes || [])" :key="typeof cls === 'object' ? cls.id : cls" class="class-card-small">
                    <div class="class-info">
                      <div class="class-name">{{ getClassName(cls) }}</div>
                      <div class="class-code">{{ getClassCode(cls) }}</div>
                    </div>
                    <div class="class-stats">
                      <span>{{ getClassStudentCount(cls) }} 名学生</span>
                    </div>
                    <button @click="unbindClass(selectedCourse.id, cls)" class="btn-icon small danger">
                      <i class="fas fa-unlink"></i>
                    </button>
                  </div>
                </div>
              </div>

              <div class="detail-section">
                <h4>课程资料</h4>
                <div class="materials-list">
                  <div v-for="material in (selectedCourse.materials || [])" :key="material.id" class="material-item">
                    <div class="material-icon">
                      <i :class="getMaterialIcon(material.type)"></i>
                    </div>
                    <div class="material-info">
                      <div class="material-name">{{ material.name }}</div>
                      <div class="material-meta">
                        <span>{{ formatFileSize(material.size) }}</span>
                        <span>·</span>
                        <span>{{ formatDate(material.uploadedAt) }}</span>
                        <span>·</span>
                        <span>{{ material.uploadedBy }}</span>
                      </div>
                    </div>
                    <div class="material-actions">
                      <button @click="downloadMaterial(material)" class="btn-icon small">
                        <i class="fas fa-download"></i>
                      </button>
                      <button @click="deleteMaterial(material.id)" class="btn-icon small danger">
                        <i class="fas fa-trash"></i>
                      </button>
                    </div>
                  </div>
                </div>
                <button @click="uploadMaterial(selectedCourse)" class="btn-outline">
                  <i class="fas fa-plus"></i> 上传新资料
                </button>
              </div>

              <div class="detail-section">
                <h4>课程作业</h4>
                <div class="assignments-list">
                  <div v-for="assignment in (selectedCourse.assignments || [])" :key="assignment.id" class="assignment-item">
                    <div class="assignment-info">
                      <div class="assignment-title">{{ assignment.title }}</div>
                      <div class="assignment-meta">
                        <span>截止时间: {{ formatDate(assignment.dueDate) }}</span>
                        <span>·</span>
                        <span>总分: {{ assignment.totalScore }} 分</span>
                      </div>
                    </div>
                    <div class="assignment-actions">
                      <button @click="viewAssignment(assignment)" class="btn-icon small">
                        <i class="fas fa-eye"></i>
                      </button>
                      <button @click="editAssignment(assignment)" class="btn-icon small">
                        <i class="fas fa-edit"></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传资料模态框 -->
    <div v-if="showUploadModal" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>上传课程资料</h3>
          <button @click="showUploadModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="upload-section">
            <div class="upload-zone" @click="triggerUpload" @dragover.prevent @drop="handleDrop">
              <i class="fas fa-cloud-upload-alt fa-3x"></i>
              <p>点击或拖拽文件到此处上传</p>
              <p class="upload-hint">支持 PDF、PPT、Word、Excel、视频等格式</p>
              <input
                  type="file"
                  ref="uploadInput"
                  multiple
                  @change="handleFileUpload"
                  style="display: none"
              >
            </div>

            <div v-if="uploadingFiles.length > 0" class="upload-list">
              <h4>上传队列</h4>
              <div v-for="file in uploadingFiles" :key="file.id" class="upload-item">
                <div class="file-info">
                  <i :class="getFileIcon(file.name)"></i>
                  <div>
                    <div class="file-name">{{ file.name }}</div>
                    <div class="file-size">{{ formatFileSize(file.size) }}</div>
                  </div>
                </div>
                <div class="upload-progress">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: file.progress + '%' }"></div>
                  </div>
                  <span class="progress-text">{{ file.progress }}%</span>
                </div>
              </div>
            </div>

            <div class="upload-actions">
              <button @click="startUpload" :disabled="uploadingFiles.length === 0" class="btn-primary">
                开始上传
              </button>
              <button @click="clearUploads" class="btn-secondary">清空列表</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { teacherApi } from '@/api/teacher';
import Layout from '@/components/Layout.vue';

// 状态管理
const showCreateModal = ref(false);
const showBindModal = ref(false);
const showUploadModal = ref(false);
const showCourseDetail = ref(false);
const selectedCourse = ref<any>(null);
const tagInput = ref('');
const selectAllClasses = ref(false);

// 表单数据
const newCourse = reactive({
  name: '',
  code: '',
  description: '',
  credit: '3',
  semester: '2023-2024-1',
  classes: [] as string[],
  tags: [] as string[]
});

// 上传相关
const uploadingFiles = ref<any[]>([]);

// 从API获取的数据
const courses = ref<any[]>([]);
const availableClasses = ref<any[]>([]);

const tagSuggestions = ['计算机', '算法', '编程', '前端', '后端', '数据库', '数学', '英语', '专业必修', '公共选修'];

// 计算属性
const totalCourses = computed(() => courses.value.length);
const totalStudents = computed(() => {
  return courses.value.reduce((sum, course) => sum + (course.studentCount || course.student_count || 0), 0);
});
const totalClasses = computed(() => {
  // 直接累加每门课的绑定班级数量（优先后端提供的 class_count）
  return courses.value.reduce((sum, course) => {
    const count = course.class_count ?? course.classCount ?? (Array.isArray(course.classes) ? course.classes.length : 0);
    return sum + (Number.isFinite(count) ? count : 0);
  }, 0);
});
const totalMaterials = computed(() => {
  return courses.value.reduce((sum, course) => sum + (course.materialCount || course.material_count || 0), 0);
});

// 方法
const getStatusClass = (status: string) => {
  const map: Record<string, string> = {
    active: 'status-active',
    planning: 'status-planning',
    archived: 'status-archived'
  };
  return map[status] || '';
};

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    active: '进行中',
    planning: '规划中',
    archived: '已归档'
  };
  return map[status] || status;
};

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN');
};

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const getMaterialIcon = (type: string) => {
  const map: Record<string, string> = {
    pdf: 'fas fa-file-pdf',
    doc: 'fas fa-file-word',
    xls: 'fas fa-file-excel',
    ppt: 'fas fa-file-powerpoint',
    video: 'fas fa-video',
    image: 'fas fa-image',
    link: 'fas fa-link',
    zip: 'fas fa-file-archive'
  };
  return map[type] || 'fas fa-file';
};

const getFileIcon = (filename: string) => {
  const extension = filename.split('.').pop()?.toLowerCase();
  const map: Record<string, string> = {
    pdf: 'fas fa-file-pdf',
    doc: 'fas fa-file-word',
    docx: 'fas fa-file-word',
    xls: 'fas fa-file-excel',
    xlsx: 'fas fa-file-excel',
    ppt: 'fas fa-file-powerpoint',
    pptx: 'fas fa-file-powerpoint',
    jpg: 'fas fa-image',
    jpeg: 'fas fa-image',
    png: 'fas fa-image',
    gif: 'fas fa-image',
    mp4: 'fas fa-video',
    avi: 'fas fa-video',
    mov: 'fas fa-video',
    zip: 'fas fa-file-archive',
    rar: 'fas fa-file-archive',
    txt: 'fas fa-file-alt'
  };
  return map[extension || ''] || 'fas fa-file';
};

const resetNewCourse = () => {
  newCourse.name = '';
  newCourse.code = '';
  newCourse.description = '';
  newCourse.credit = '3';
  newCourse.semester = '2023-2024-1';
  newCourse.classes = [];
  newCourse.tags = [];
  selectAllClasses.value = false;
};

const toggleAllClasses = () => {
  if (selectAllClasses.value) {
    newCourse.classes = availableClasses.value.map(c => c.id);
  } else {
    newCourse.classes = [];
  }
};

const addTag = () => {
  if (tagInput.value.trim() && !newCourse.tags.includes(tagInput.value.trim())) {
    newCourse.tags.push(tagInput.value.trim());
    tagInput.value = '';
  }
};

const addSuggestion = (suggestion: string) => {
  if (!newCourse.tags.includes(suggestion)) {
    newCourse.tags.push(suggestion);
  }
};

const removeTag = (tag: string) => {
  newCourse.tags = newCourse.tags.filter(t => t !== tag);
};

const viewCourseDetail = async (course: any) => {
  try {
    if (!availableClasses.value.length) {
      await loadClasses();
    }
    // 从API加载完整的课程详情
    const response = await teacherApi.getCourseDetail(course.id);
    // 兼容 classes 可能是对象数组或 ID 数组，补齐名称/人数等信息
    const classes = (response.classes || []).map((c: any) => {
      const classId = typeof c === 'object' ? c.id : c;
      const base = typeof c === 'object' ? c : { id: classId };
      const matched = availableClasses.value.find(cls => cls.id === String(classId));
      return {
        ...base,
        id: String(classId),
        name: base.name || matched?.name || '未知班级',
        code: base.code || matched?.code || '',
        student_count: base.student_count ?? base.studentCount ?? matched?.studentCount ?? 0
      };
    });
    selectedCourse.value = {
      ...response,
      classes
    };
    showCourseDetail.value = true;
  } catch (error: any) {
    console.error('加载课程详情失败:', error);
    // 如果加载失败，使用传入的课程数据
    const classes = (course.classes || []).map((c: any) => {
      const classId = typeof c === 'object' ? c.id : c;
      const base = typeof c === 'object' ? c : { id: classId };
      const matched = availableClasses.value.find(cls => cls.id === String(classId));
      return {
        ...base,
        id: String(classId),
        name: base.name || matched?.name || '未知班级',
        code: base.code || matched?.code || '',
        student_count: base.student_count ?? base.studentCount ?? matched?.studentCount ?? 0
      };
    });
    selectedCourse.value = {
      ...course,
      classes
    };
    showCourseDetail.value = true;
  }
};

const closeCourseDetail = () => {
  showCourseDetail.value = false;
  selectedCourse.value = null;
};

const editCourse = (course: any) => {
  // 填充表单
  newCourse.name = course.name;
  newCourse.code = course.code;
  newCourse.description = course.description;
  newCourse.credit = course.credit.toString();
  newCourse.semester = course.semester;
  newCourse.classes = [...(course.classes || [])];
  newCourse.tags = [...(course.tags || [])];
  selectAllClasses.value = (course.classes || []).length === availableClasses.value.length;
  showCreateModal.value = true;
};

const unbindClass = async (courseId: string, classId: any) => {
  // 兼容对象/数字/字符串 ID
  const targetId = typeof classId === 'object' ? classId.id : classId;
  const course = courses.value.find(c => String(c.id) === String(courseId)) || selectedCourse.value;
  if (!course) return;
  const ids = (course.classes || []).map((c: any) => (typeof c === 'object' ? c.id : c));
  const updated = ids.filter((id: any) => String(id) !== String(targetId));
  try {
    await teacherApi.updateCourseClasses(Number(courseId), updated.map((id: any) => Number(id)));
    alert('班级解绑成功');
    await Promise.all([loadCourses(), loadClasses()]);
    // 如果当前详情打开，刷新详情数据
    if (selectedCourse.value && String(selectedCourse.value.id) === String(courseId)) {
      await viewCourseDetail(selectedCourse.value);
    }
  } catch (error: any) {
    console.error('班级解绑失败:', error);
    alert('班级解绑失败: ' + (error.response?.data?.message || error.message));
  }
};

const getClassName = (classId: any) => {
  if (classId && typeof classId === 'object') {
    return classId.name || '未知班级';
  }
  const classItem = availableClasses.value.find(c => c.id === String(classId));
  return classItem?.name || '未知班级';
};

const getClassCode = (classId: any) => {
  if (classId && typeof classId === 'object') {
    return classId.code || '';
  }
  const classItem = availableClasses.value.find(c => c.id === String(classId));
  return classItem?.code || '';
};

const getClassStudentCount = (classId: any) => {
  if (classId && typeof classId === 'object') {
    return classId.student_count ?? classId.studentCount ?? 0;
  }
  const classItem = availableClasses.value.find(c => c.id === String(classId));
  return classItem?.studentCount || 0;
};

const teacherNamesFor = (course: any) => {
  const names = course.teacherNames || course.teacher_names || [];
  return (Array.isArray(names) && names.length) ? names.join('，') : (course.teacherName || '未知教师');
};

// 资料管理
const uploadMaterial = (course: any) => {
  selectedCourse.value = course;
  showUploadModal.value = true;
};

const triggerUpload = () => {
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  input?.click();
};

const handleDrop = (event: DragEvent) => {
  event.preventDefault();
  const files = event.dataTransfer?.files;
  if (files) {
    addFilesToUpload(Array.from(files));
  }
};

const handleFileUpload = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files) {
    addFilesToUpload(Array.from(input.files));
  }
};

const addFilesToUpload = (files: File[]) => {
  files.forEach(file => {
    if (!uploadingFiles.value.some(f => f.name === file.name)) {
      uploadingFiles.value.push({
        id: Date.now() + Math.random(),
        file: file,
        name: file.name,
        size: file.size,
        progress: 0,
        status: 'pending'
      });
    }
  });
};

const startUpload = async () => {
  if (!selectedCourse.value || uploadingFiles.value.length === 0) return;

  for (const uploadFile of uploadingFiles.value) {
    // 模拟上传进度
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 100));
      uploadFile.progress = i;
    }

    // 添加到课程资料
    const material = {
      id: Date.now().toString(),
      name: uploadFile.name,
      type: getFileType(uploadFile.name),
      size: uploadFile.size,
      uploadedAt: new Date().toISOString(),
      uploadedBy: '当前教师'
    };

    selectedCourse.value.materials.push(material);
    selectedCourse.value.materialCount++;
  }

  alert('资料上传成功！');
  uploadingFiles.value = [];
  showUploadModal.value = false;
};

const getFileType = (filename: string) => {
  const extension = filename.split('.').pop()?.toLowerCase();
  const typeMap: Record<string, string> = {
    pdf: 'pdf',
    doc: 'doc',
    docx: 'doc',
    xls: 'xls',
    xlsx: 'xls',
    ppt: 'ppt',
    pptx: 'ppt',
    jpg: 'image',
    jpeg: 'image',
    png: 'image',
    gif: 'image',
    mp4: 'video',
    avi: 'video',
    mov: 'video'
  };
  return typeMap[extension || ''] || 'file';
};

const clearUploads = () => {
  uploadingFiles.value = [];
};

const downloadMaterial = (material: any) => {
  alert(`下载资料: ${material.name}\n（在实际项目中，这里会触发文件下载）`);
};

const deleteMaterial = (materialId: string) => {
  if (!selectedCourse.value || !confirm('确定要删除这个资料吗？')) return;

  selectedCourse.value.materials = selectedCourse.value.materials.filter((m: any) => m.id !== materialId);
  selectedCourse.value.materialCount = selectedCourse.value.materials.length;
  alert('资料已删除');
};

// 作业管理
const viewAssignment = (assignment: any) => {
  alert(`查看作业: ${assignment.title}\n截止时间: ${formatDate(assignment.dueDate)}`);
};

const editAssignment = (assignment: any) => {
  alert(`编辑作业: ${assignment.title}`);
};

// 加载课程列表
const loadCourses = async () => {
  try {
    const response = await teacherApi.getCourses();
    console.log('加载课程响应:', response);
    const coursesList = Array.isArray(response) ? response : (response?.data || []);
    console.log('课程列表:', coursesList);
    courses.value = coursesList.map((course: any) => {
      const classIds = (course.classes || []).map((id: any) => String(id));
      const classCount = course.class_count ?? course.classCount ?? (classIds?.length ?? 0);
      const studentCount = course.student_count ?? course.studentCount ?? 0;
      const teacherNames = course.teacher_names || course.teacherNames || [];
      return {
        ...course,
        classCount,
        studentCount,
        materialCount: course.material_count ?? course.materialCount ?? 0,
        classes: classIds,
        teacherNames,
        teacherName: teacherNames.join('，') || course.teacherName || '未知教师',
        createdAt: course.created_at ?? course.createdAt
      };
    });
  } catch (error: any) {
    console.error('加载课程失败:', error);
    alert('加载课程失败: ' + (error.response?.data?.message || error.message));
  }
};

// 加载班级列表
const loadClasses = async () => {
  try {
    const response = await teacherApi.getClasses();
    const classesList = Array.isArray(response) ? response : (response?.data || []);
    // 转换数据格式以匹配前端使用
    availableClasses.value = classesList.map((cls: any) => ({
      id: String(cls.id),
      name: cls.name,
      code: cls.code,
      studentCount: cls.student_count || 0
    }));
  } catch (error: any) {
    console.error('加载班级失败:', error);
  }
};

// 课程操作
const createCourse = async () => {
  if (!newCourse.name) {
    alert('请填写课程名称');
    return;
  }

  try {
    const response = await teacherApi.createCourse({
      name: newCourse.name,
      code: newCourse.code || undefined, // 留空则后端自动生成
      description: newCourse.description || '',
      credit: parseFloat(newCourse.credit) || 3.0,
      semester: newCourse.semester || '',
      classes: (newCourse.classes && Array.isArray(newCourse.classes) && newCourse.classes.length > 0)
        ? newCourse.classes.map((id: string | number) => Number(id))
        : []
    });
    
    console.log('课程创建成功，响应:', response);
    
    // 先关闭模态框和重置表单
    showCreateModal.value = false;
    resetNewCourse();
    
    // 然后重新加载课程列表
    await loadCourses();
    
    alert('课程创建成功！');
  } catch (error: any) {
    console.error('创建课程失败:', error);
    alert('创建课程失败: ' + (error.response?.data?.message || error.message));
  }
};

const deleteCourse = async (courseId: string, confirm = true) => {
  if (confirm && !window.confirm('确定要删除这个课程吗？')) {
    return;
  }

  try {
    await teacherApi.deleteCourse(Number(courseId));
    await loadCourses();
    if (confirm) {
      alert('课程已删除');
    }
  } catch (error: any) {
    console.error('删除课程失败:', error);
    alert('删除课程失败: ' + (error.response?.data?.message || error.message));
  }
};

const bindClasses = async (course: any) => {
  // 打开绑定模态框，用现有班级选中
  newCourse.classes = (course.classes || []).map((id: any) => String(id));
  selectedCourse.value = course;
  showCreateModal.value = false;
  showBindModal.value = true;
};

const saveBindClasses = async () => {
  if (!selectedCourse.value) return;
  try {
    await teacherApi.updateCourseClasses(
        Number(selectedCourse.value.id),
        newCourse.classes.map((id: string) => Number(id))
    );
    alert('班级绑定已更新');
    showBindModal.value = false;
    await Promise.all([loadCourses(), loadClasses()]);
  } catch (error: any) {
    console.error('更新班级绑定失败:', error);
    alert('更新班级绑定失败: ' + (error.response?.data?.message || error.message));
  }
};

onMounted(() => {
  loadCourses();
  loadClasses();
});
</script>

<style scoped>
.course-manager {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 页面头部 */
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

/* 课程统计 */
.course-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 0;
}

.stat-item {
  background: #ffffff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 16px;
  text-align: center;
  transition: border-color 0.15s;
}

.stat-item:hover {
  border-color: #0969da;
}

.stat-number {
  font-size: 36px;
  font-weight: bold;
  color: #4a6fa5;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

/* 课程列表 */
.course-list {
  display: grid;
  gap: 24px;
}

.course-card {
  background: #ffffff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 16px;
  transition: border-color 0.15s;
}

.course-card:hover {
  border-color: #0969da;
}

.course-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.course-title-section h3 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 20px;
  font-weight: 600;
}

.course-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.course-code,
.course-credit,
.course-semester {
  background: #f0f7ff;
  color: #4a6fa5;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.course-credit {
  background: #e8f5e9;
  color: #2e7d32;
}

.course-semester {
  background: #fff3e0;
  color: #f57c00;
}

.course-status {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-active {
  background: #d4edda;
  color: #155724;
}

.status-planning {
  background: #fff3cd;
  color: #856404;
}

.status-archived {
  background: #e2e3e5;
  color: #383d41;
}

.course-description {
  color: #666;
  line-height: 1.6;
  margin-bottom: 20px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.course-info {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #888;
  font-size: 14px;
}

.info-item i {
  color: #4a6fa5;
}

.course-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.tag {
  background: #f8f9fa;
  color: #666;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  border: 1px solid #e0e0e0;
}

.course-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
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

.btn-icon.small {
  width: 32px;
  height: 32px;
  font-size: 14px;
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

.modal.modal-xl {
  width: 1000px;
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

/* 表单样式 */
.form-section {
  margin-bottom: 32px;
}

.form-section h4 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.form-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.form-group {
  flex: 1;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #4a6fa5;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

/* 班级绑定 */
.class-binding {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
}

.select-all {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e0e0e0;
}

.classes-grid {
  max-height: 300px;
  overflow-y: auto;
  display: grid;
  gap: 12px;
}

.class-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.class-item label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  cursor: pointer;
}

.student-count {
  color: #666;
  font-size: 12px;
}

/* 标签输入 */
.tags-input {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
}

.tags-list {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.tags-list .tag {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #e3f2fd;
  color: #1976d2;
  border: none;
  cursor: default;
}

.tags-list .tag i {
  cursor: pointer;
  font-size: 10px;
  opacity: 0.6;
}

.tags-list .tag i:hover {
  opacity: 1;
}

.tag-input-group {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.tag-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.tag-suggestions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.tag-suggestions span:first-child {
  color: #666;
  font-size: 14px;
}

.tag-suggestion {
  color: #4a6fa5;
  cursor: pointer;
  font-size: 14px;
  padding: 4px 8px;
  border-radius: 4px;
}

.tag-suggestion:hover {
  background: #f0f7ff;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
}

/* 课程详情 */
.course-detail {
  display: grid;
  gap: 32px;
}

.detail-header {
  border-bottom: 2px solid #f0f0f0;
  padding-bottom: 24px;
}

.detail-header h2 {
  margin: 0 0 16px 0;
  color: #333;
}

.detail-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.detail-description h4 {
  margin: 0 0 12px 0;
  color: #333;
}

.detail-description p {
  color: #666;
  line-height: 1.6;
  margin: 0;
}

.detail-sections {
  display: grid;
  gap: 32px;
}

.detail-section h4 {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

/* 班级列表 */
.classes-list {
  display: grid;
  gap: 12px;
  margin-bottom: 16px;
}

.class-card-small {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.class-info {
  flex: 1;
}

.class-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.class-code {
  color: #666;
  font-size: 12px;
}

.class-stats {
  margin-right: 16px;
  color: #888;
  font-size: 14px;
}

/* 资料列表 */
.materials-list {
  display: grid;
  gap: 12px;
  margin-bottom: 16px;
}

.material-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.material-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #f0f7ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4a6fa5;
  font-size: 18px;
}

.material-info {
  flex: 1;
}

.material-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.material-meta {
  color: #888;
  font-size: 12px;
  display: flex;
  gap: 8px;
}

.material-actions {
  display: flex;
  gap: 8px;
}

/* 作业列表 */
.assignments-list {
  display: grid;
  gap: 12px;
}

.assignment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.assignment-info {
  flex: 1;
}

.assignment-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.assignment-meta {
  color: #888;
  font-size: 12px;
  display: flex;
  gap: 8px;
}

/* 上传区域 */
.upload-section {
  padding: 20px;
}

.upload-zone {
  border: 2px dashed #ddd;
  border-radius: 12px;
  padding: 60px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 24px;
}

.upload-zone:hover {
  border-color: #4a6fa5;
  background: #f8f9fa;
}

.upload-zone i {
  color: #4a6fa5;
  margin-bottom: 16px;
}

.upload-zone p {
  margin: 8px 0;
  color: #666;
}

.upload-hint {
  font-size: 12px;
  color: #999;
}

.upload-list {
  margin-bottom: 24px;
}

.upload-list h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.upload-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 12px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-info i {
  font-size: 24px;
  color: #4a6fa5;
}

.file-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.file-size {
  color: #888;
  font-size: 12px;
}

.upload-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 2;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #e0e0e0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #4a6fa5;
  transition: width 0.3s;
}

.progress-text {
  width: 40px;
  text-align: right;
  color: #666;
  font-size: 12px;
}

.upload-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .course-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .course-header {
    flex-direction: column;
    gap: 16px;
  }

  .course-info {
    flex-direction: column;
    gap: 12px;
  }

  .course-actions {
    justify-content: flex-start;
  }

  .form-row {
    flex-direction: column;
  }

  .modal.modal-xl,
  .modal.modal-lg {
    width: 90%;
  }
}
</style>