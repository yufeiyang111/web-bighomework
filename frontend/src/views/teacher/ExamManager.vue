<template>
  <Layout pageTitle="考试管理">
    <div class="exam-manager">
      <div class="page-header">
      <div class="header-left">
      <h2>考试管理</h2>
        <p>创建和管理考试，选择题库自动出题</p>
      </div>
      <div class="header-actions">
        <button class="btn-secondary" @click="showQuestionBankManager = true">
          <i class="fas fa-book"></i> 题库管理
        </button>
      <button class="btn-primary" @click="showCreateExam = true">
        <i class="fas fa-plus"></i> 创建考试
      </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <p>加载中...</p>
    </div>

    <!-- 考试列表 -->
    <div v-else class="exam-list">
      <div class="exam-card" v-for="exam in exams" :key="exam.id">
        <div class="exam-status" :class="exam.status">
          {{ getStatusText(exam.status) }}
        </div>
        <h3>{{ exam.title }}</h3>
        <p class="exam-desc">{{ exam.description || '暂无描述' }}</p>
        <div class="exam-info">
          <span><i class="fas fa-calendar"></i> {{ formatDateTime(exam.start_time) }}</span>
          <span><i class="fas fa-clock"></i> {{ exam.duration }}分钟</span>
          <span><i class="fas fa-users"></i> {{ exam.participant_count || 0 }}/{{ exam.total_students || 0 }}人</span>
          <span><i class="fas fa-question-circle"></i> {{ exam.total_questions || 0 }}题</span>
        </div>
        <div class="exam-actions">
          <button v-if="exam.status === 'draft'" class="btn-primary" @click="openPublishModal(exam)">
            <i class="fas fa-paper-plane"></i> 发布
          </button>
          <button class="btn-outline" @click="viewExamDetail(exam)">查看详情</button>
          <button class="btn-outline" @click="deleteExam(exam.id)">删除</button>
        </div>
      </div>
    </div>

    <!-- 创建考试模态框 -->
    <div v-if="showCreateExam" class="modal-overlay" @click.self="showCreateExam = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>创建新考试</h3>
          <button @click="showCreateExam = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="createExam">
            <div class="form-group">
              <label>考试名称 *</label>
              <input v-model="newExam.title" type="text" required placeholder="例如：期中考试" />
            </div>

            <div class="form-group">
              <label>考试描述</label>
              <textarea v-model="newExam.description" rows="3" placeholder="考试说明..."></textarea>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>选择题库 *</label>
                <select v-model="newExam.question_bank_id" required @change="onQuestionBankChange">
                  <option value="">请选择题库</option>
                  <option v-for="bank in questionBanks" :key="bank.id" :value="bank.id">
                    {{ bank.name }} ({{ bank.question_count }}题)
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>题目数量 *</label>
                <input 
                  v-model.number="newExam.total_questions" 
                  type="number" 
                  required 
                  :max="selectedBankQuestionCount"
                  :min="1"
                  placeholder="从题库中选择的题目数"
                />
                <small v-if="selectedBankQuestionCount > 0">
                  题库中共有 {{ selectedBankQuestionCount }} 道题目
                </small>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>开始时间 *</label>
                <input v-model="newExam.start_time" type="datetime-local" required />
              </div>
              <div class="form-group">
                <label>结束时间 *</label>
                <input v-model="newExam.end_time" type="datetime-local" required />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>考试时长（分钟） *</label>
                <input v-model.number="newExam.duration" type="number" required min="1" />
              </div>
              <div class="form-group">
                <label>总分 *</label>
                <input v-model.number="newExam.total_score" type="number" required min="1" step="0.1" />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>及格分数</label>
                <input v-model.number="newExam.passing_score" type="number" min="0" step="0.1" />
              </div>
              <div class="form-group">
                <label>
                  <input type="checkbox" v-model="newExam.auto_grade" />
                  自动批改并录入成绩
                </label>
              </div>
            </div>

          <div class="form-actions">
              <button type="button" @click="showCreateExam = false" class="btn-secondary">取消</button>
              <button type="submit" class="btn-primary">创建考试</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 题库管理模态框 -->
    <div v-if="showQuestionBankManager" class="modal-overlay" @click.self="showQuestionBankManager = false">
      <div class="modal modal-xl">
        <div class="modal-header">
          <h3>题库管理</h3>
          <button @click="showQuestionBankManager = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="question-bank-tabs">
            <button 
              class="tab-btn" 
              :class="{ active: currentTab === 'banks' }"
              @click="currentTab = 'banks'"
            >
              题库列表
            </button>
            <button 
              class="tab-btn" 
              :class="{ active: currentTab === 'questions' }"
              @click="currentTab = 'questions'"
            >
              题目管理
            </button>
          </div>

          <!-- 题库列表 -->
          <div v-if="currentTab === 'banks'" class="tab-content">
            <div class="toolbar">
              <button class="btn-primary" @click="showCreateBank = true">
                <i class="fas fa-plus"></i> 创建题库
              </button>
            </div>

            <div class="bank-list">
              <div class="bank-card" v-for="bank in questionBanks" :key="bank.id">
                <h4>{{ bank.name }}</h4>
                <p>{{ bank.description || '暂无描述' }}</p>
                <div class="bank-info">
                  <span>{{ bank.question_count }} 道题目</span>
                  <span>{{ bank.is_public ? '公开' : '私有' }}</span>
                </div>
                <div class="bank-actions">
                  <button class="btn-outline" @click="viewBankQuestions(bank.id)">查看题目</button>
                  <button class="btn-outline" @click="deleteQuestionBank(bank.id)">删除</button>
                </div>
              </div>
            </div>
          </div>

          <!-- 题目管理 -->
          <div v-if="currentTab === 'questions'" class="tab-content">
            <div class="toolbar">
              <div class="form-group-inline">
                <label>选择题库：</label>
                <select v-model="selectedBankForQuestions" @change="loadBankQuestions">
                  <option value="">请选择题库</option>
                  <option v-for="bank in questionBanks" :key="bank.id" :value="bank.id">
                    {{ bank.name }}
                  </option>
                </select>
              </div>
              <button 
                class="btn-primary" 
                @click="showCreateQuestion = true"
                :disabled="!selectedBankForQuestions"
              >
                <i class="fas fa-plus"></i> 添加题目
              </button>
            </div>

            <div class="question-list">
              <div class="question-card" v-for="question in currentBankQuestions" :key="question.id">
                <div class="question-content">
                  <p><strong>{{ question.content }}</strong></p>
                  <div class="options">
                    <div>A. {{ question.options.A }}</div>
                    <div>B. {{ question.options.B }}</div>
                    <div>C. {{ question.options.C }}</div>
                    <div>D. {{ question.options.D }}</div>
                  </div>
                  <div class="question-meta">
                    <span>正确答案：<strong>{{ question.correct_option }}</strong></span>
                    <span>分值：{{ question.score }}分</span>
                    <span>难度：{{ question.difficulty }}</span>
                  </div>
                  <div v-if="question.explanation" class="explanation">
                    解析：{{ question.explanation }}
                  </div>
                </div>
                <div class="question-actions">
                  <button class="btn-outline" @click="editQuestion(question)">编辑</button>
                  <button class="btn-outline danger" @click="deleteQuestion(question.id)">删除</button>
                </div>
              </div>
          </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建题库模态框 -->
    <div v-if="showCreateBank" class="modal-overlay" @click.self="showCreateBank = false">
      <div class="modal">
        <div class="modal-header">
          <h3>创建题库</h3>
          <button @click="showCreateBank = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="createQuestionBank">
            <div class="form-group">
              <label>题库名称 *</label>
              <input v-model="newBank.name" type="text" required />
            </div>
            <div class="form-group">
              <label>题库描述</label>
              <textarea v-model="newBank.description" rows="3"></textarea>
            </div>
            <div class="form-group">
              <label>
                <input type="checkbox" v-model="newBank.is_public" />
                公开题库
              </label>
            </div>
            <div class="form-actions">
              <button type="button" @click="showCreateBank = false" class="btn-secondary">取消</button>
              <button type="submit" class="btn-primary">创建</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 发布考试模态框 -->
    <div v-if="showPublishModal" class="modal-overlay" @click.self="showPublishModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>发布考试：{{ currentExam?.title }}</h3>
          <button @click="showPublishModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="publishExam">
            <div class="form-group">
              <label>发布方式 *</label>
              <div class="radio-group">
                <label>
                  <input type="radio" v-model="publishData.publish_type" value="immediate" @change="publishData.scheduled_publish_time = ''">
                  立即发布
                </label>
                <label>
                  <input type="radio" v-model="publishData.publish_type" value="scheduled">
                  定时发布
                </label>
              </div>
            </div>

            <div v-if="publishData.publish_type === 'scheduled'" class="form-group">
              <label>发布时间 *</label>
              <input v-model="publishData.scheduled_publish_time" type="datetime-local" required>
              <small>考试将在指定时间自动发布给班级学生</small>
            </div>

            <div class="form-group">
              <label>选择班级 *</label>
              <select v-model="publishData.class_ids" multiple required @change="onPublishClassChange">
                <option v-for="cls in classes" :key="cls.id" :value="cls.id">
                  {{ cls.name }}
                </option>
              </select>
              <small class="text-info">可多选；若不选学生则将通知所选班级的全部学生</small>
            </div>

            <div class="form-group">
              <label>发布范围</label>
              <div class="radio-group">
                <label>
                  <input type="radio" v-model="publishData.target_type" value="all" @change="publishData.student_ids = []">
                  整个班级
                </label>
                <label>
                  <input type="radio" v-model="publishData.target_type" value="selected">
                  选择学生
                </label>
              </div>
            </div>

            <div v-if="publishData.target_type === 'selected'" class="form-group">
              <label>选择学生</label>
              <div class="students-selection">
                <div class="select-all-bar">
                  <label>
                    <input type="checkbox" v-model="selectAllStudents" @change="toggleSelectStudents">
                    全选
                  </label>
                  <span>已选择 {{ publishData.student_ids.length }} 人</span>
                </div>
                <div class="students-list" style="max-height: 300px; overflow-y: auto;">
                  <div v-for="student in classStudents" :key="student.id" class="student-item">
                    <label>
                      <input type="checkbox" :value="student.id" v-model="publishData.student_ids">
                      <span>{{ student.name }} ({{ student.username }})</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <div class="form-actions">
              <button type="button" @click="showPublishModal = false" class="btn-secondary">取消</button>
              <button type="submit" class="btn-primary">
                {{ publishData.publish_type === 'immediate' ? '立即发布' : '设置定时发布' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- 创建/编辑题目模态框 -->
    <div v-if="showCreateQuestion || editingQuestion" class="modal-overlay" @click.self="closeQuestionModal">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>{{ editingQuestion ? '编辑题目' : '添加题目' }}</h3>
          <button @click="closeQuestionModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="saveQuestion">
            <div class="form-group">
              <label>题目内容 *</label>
              <textarea v-model="newQuestion.content" rows="3" required></textarea>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>选项A *</label>
                <input v-model="newQuestion.option_a" type="text" required />
              </div>
              <div class="form-group">
                <label>选项B *</label>
                <input v-model="newQuestion.option_b" type="text" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>选项C *</label>
                <input v-model="newQuestion.option_c" type="text" required />
              </div>
              <div class="form-group">
                <label>选项D *</label>
                <input v-model="newQuestion.option_d" type="text" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>正确答案 *</label>
                <select v-model="newQuestion.correct_option" required>
                  <option value="">请选择</option>
                  <option value="A">A</option>
                  <option value="B">B</option>
                  <option value="C">C</option>
                  <option value="D">D</option>
                </select>
              </div>
              <div class="form-group">
                <label>分值</label>
                <input v-model.number="newQuestion.score" type="number" min="0" step="0.1" />
              </div>
            </div>
            <div class="form-group">
              <label>难度</label>
              <select v-model="newQuestion.difficulty">
                <option value="easy">简单</option>
                <option value="medium">中等</option>
                <option value="hard">困难</option>
              </select>
            </div>
            <div class="form-group">
              <label>解析</label>
              <textarea v-model="newQuestion.explanation" rows="2"></textarea>
            </div>
            <div class="form-actions">
              <button type="button" @click="closeQuestionModal" class="btn-secondary">取消</button>
              <button type="submit" class="btn-primary">保存</button>
            </div>
          </form>
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

const showCreateExam = ref(false);
const showQuestionBankManager = ref(false);
const showCreateBank = ref(false);
const showCreateQuestion = ref(false);
const showPublishModal = ref(false);
const isLoading = ref(false);
const currentTab = ref('banks');
const selectedBankForQuestions = ref<number | ''>('');
const editingQuestion = ref<any>(null);
const currentExam = ref<any>(null);
const classStudents = ref<any[]>([]);
const selectAllStudents = ref(false);

const exams = ref<any[]>([]);
const classes = ref<any[]>([]);
const questionBanks = ref<any[]>([]);
const currentBankQuestions = ref<any[]>([]);

const publishData = reactive({
  class_ids: [] as (string | number)[],
  publish_type: 'immediate' as 'immediate' | 'scheduled',
  scheduled_publish_time: '',
  target_type: 'all' as 'all' | 'selected',
  student_ids: [] as number[]
});

const newExam = reactive({
  title: '',
  description: '',
  question_bank_id: '',
  total_questions: 10,
  start_time: '',
  end_time: '',
  duration: 60,
  total_score: 100,
  passing_score: 60,
  auto_grade: true
});

const newBank = reactive({
  name: '',
  description: '',
  is_public: false
});

const newQuestion = reactive({
  question_bank_id: 0,
  content: '',
  option_a: '',
  option_b: '',
  option_c: '',
  option_d: '',
  correct_option: 'A' as 'A' | 'B' | 'C' | 'D',
  explanation: '',
  score: 1.0,
  difficulty: 'medium'
});

const selectedBankQuestionCount = computed(() => {
  if (!newExam.question_bank_id) return 0;
  const bank = questionBanks.value.find(b => b.id === Number(newExam.question_bank_id));
  return bank?.question_count || 0;
});

// 加载数据
const loadExams = async () => {
  isLoading.value = true;
  try {
    const response = await teacherApi.getExams();
    console.log('加载考试响应:', response);
    // 后端返回格式: { message: '获取成功', data: [...], pagination: {...} }
    // API方法已经提取了data字段，所以response应该是数组
    if (Array.isArray(response)) {
      exams.value = response;
    } else if (response && Array.isArray(response.data)) {
      exams.value = response.data;
    } else {
      console.warn('考试数据格式异常:', response);
      exams.value = [];
    }
  } catch (error: any) {
    console.error('加载考试失败:', error);
    console.error('错误详情:', error.response);
    alert('加载考试失败: ' + (error.response?.data?.message || error.message || '未知错误'));
    exams.value = [];
  } finally {
    isLoading.value = false;
  }
};

const loadClasses = async () => {
  try {
    const response = await teacherApi.getClasses();
    classes.value = Array.isArray(response) ? response : (response?.data || []);
  } catch (error: any) {
    console.error('加载班级失败:', error);
  }
};

const loadQuestionBanks = async () => {
  try {
    const response = await teacherApi.getQuestionBanks();
    questionBanks.value = Array.isArray(response) ? response : (response?.data || []);
  } catch (error: any) {
    console.error('加载题库失败:', error);
  }
};

const loadBankQuestions = async () => {
  if (!selectedBankForQuestions.value) {
    currentBankQuestions.value = [];
    return;
  }
  try {
    const response = await teacherApi.getQuestionBankDetail(Number(selectedBankForQuestions.value));
    currentBankQuestions.value = response.questions || [];
  } catch (error: any) {
    console.error('加载题目失败:', error);
  }
};

// 创建考试
const createExam = async () => {
  try {
    const examData: any = {
      ...newExam,
      question_bank_id: Number(newExam.question_bank_id),
      start_time: new Date(newExam.start_time).toISOString(),
      end_time: new Date(newExam.end_time).toISOString()
    };
    // class_id 不再需要，发布时再选择
    
    await teacherApi.createExam(examData);
    alert('考试创建成功！');
    showCreateExam.value = false;
    resetNewExam();
    loadExams();
  } catch (error: any) {
    console.error('创建考试失败:', error);
    alert('创建考试失败: ' + (error.response?.data?.message || error.message));
  }
};

const resetNewExam = () => {
  Object.assign(newExam, {
    title: '',
    description: '',
    question_bank_id: '',
    total_questions: 10,
    start_time: '',
    end_time: '',
    duration: 60,
    total_score: 100,
    passing_score: 60,
    auto_grade: true
  });
};

const onQuestionBankChange = () => {
  if (newExam.question_bank_id) {
    const bank = questionBanks.value.find(b => b.id === Number(newExam.question_bank_id));
    if (bank && newExam.total_questions > bank.question_count) {
      newExam.total_questions = bank.question_count;
    }
  }
};

// 题库管理
const createQuestionBank = async () => {
  try {
    await teacherApi.createQuestionBank(newBank);
    alert('题库创建成功！');
    showCreateBank.value = false;
    Object.assign(newBank, { name: '', description: '', is_public: false });
    loadQuestionBanks();
  } catch (error: any) {
    console.error('创建题库失败:', error);
    alert('创建题库失败: ' + (error.response?.data?.message || error.message));
  }
};

const deleteQuestionBank = async (bankId: number) => {
  if (!confirm('确定要删除这个题库吗？')) return;
  try {
    await teacherApi.deleteQuestionBank(bankId);
    alert('题库删除成功！');
    loadQuestionBanks();
  } catch (error: any) {
    console.error('删除题库失败:', error);
    alert('删除题库失败: ' + (error.response?.data?.message || error.message));
  }
};

const viewBankQuestions = (bankId: number) => {
  selectedBankForQuestions.value = bankId;
  currentTab.value = 'questions';
  loadBankQuestions();
};

// 题目管理
const saveQuestion = async () => {
  try {
    if (!newQuestion.correct_option) {
      newQuestion.correct_option = 'A';
    }
    if (editingQuestion.value) {
      await teacherApi.updateMCQQuestion(editingQuestion.value.id, newQuestion);
      alert('题目更新成功！');
    } else {
      newQuestion.question_bank_id = Number(selectedBankForQuestions.value);
      await teacherApi.createMCQQuestion(newQuestion);
      alert('题目添加成功！');
    }
    closeQuestionModal();
    loadBankQuestions();
    loadQuestionBanks();
  } catch (error: any) {
    console.error('保存题目失败:', error);
    alert('保存题目失败: ' + (error.response?.data?.message || error.message));
  }
};

const editQuestion = (question: any) => {
  editingQuestion.value = question;
  Object.assign(newQuestion, {
    question_bank_id: question.question_bank_id,
    content: question.content,
    option_a: question.options.A,
    option_b: question.options.B,
    option_c: question.options.C,
    option_d: question.options.D,
    correct_option: question.correct_option,
    explanation: question.explanation || '',
    score: question.score,
    difficulty: question.difficulty
  });
  showCreateQuestion.value = true;
};

const deleteQuestion = async (questionId: number) => {
  if (!confirm('确定要删除这道题目吗？')) return;
  try {
    await teacherApi.deleteMCQQuestion(questionId);
    alert('题目删除成功！');
    loadBankQuestions();
    loadQuestionBanks();
  } catch (error: any) {
    console.error('删除题目失败:', error);
    alert('删除题目失败: ' + (error.response?.data?.message || error.message));
  }
};

const closeQuestionModal = () => {
  showCreateQuestion.value = false;
  editingQuestion.value = null;
  Object.assign(newQuestion, {
    question_bank_id: 0,
    content: '',
    option_a: '',
    option_b: '',
    option_c: '',
    option_d: '',
    correct_option: '' as 'A' | 'B' | 'C' | 'D' | '',
    explanation: '',
    score: 1.0,
    difficulty: 'medium'
  });
};

const deleteExam = async (examId: number) => {
  if (!confirm('确定要删除这个考试吗？')) return;
  try {
    await teacherApi.deleteExam(examId);
    alert('考试删除成功！');
    loadExams();
  } catch (error: any) {
    console.error('删除考试失败:', error);
    alert('删除考试失败: ' + (error.response?.data?.message || error.message));
  }
};

const viewExamDetail = (exam: any) => {
  const totalStudents = exam.total_students || 0;
  const participants = exam.participant_count || 0;
  alert(`考试详情：${exam.title}\n状态：${getStatusText(exam.status)}\n应参与人数：${totalStudents}人\n实际参与人数：${participants}人`);
};

// 显示发布模态框
const openPublishModal = async (exam: any) => {
  currentExam.value = exam;
  publishData.class_ids = exam.class_ids && exam.class_ids.length ? [...exam.class_ids] : (exam.class_id ? [exam.class_id] : []);
  publishData.publish_type = 'immediate';
  publishData.scheduled_publish_time = '';
  publishData.target_type = 'all';
  publishData.student_ids = [];
  selectAllStudents.value = false;
  classStudents.value = [];
  
  // 如果考试已有班级关联，预加载这些班级的学生
  if (publishData.class_ids.length) {
    await onPublishClassChange();
  }
  
  showPublishModal.value = true;
};

// 发布时选择班级变化
const onPublishClassChange = async () => {
  if (!publishData.class_ids || publishData.class_ids.length === 0) {
    classStudents.value = [];
    return;
  }
  
  try {
    // 逐个班级加载学生并去重
    const seen = new Set<number>();
    const students: any[] = [];
    for (const cid of publishData.class_ids) {
      const detail = await teacherApi.getClassDetail(Number(cid));
      (detail.students || []).forEach((stu: any) => {
        if (!seen.has(stu.id)) {
          seen.add(stu.id);
          students.push(stu);
        }
      });
    }
    classStudents.value = students;
    if (publishData.target_type === 'all') {
      publishData.student_ids = [];
    } else {
      // 去掉不在当前班级集合的已选学生
      publishData.student_ids = publishData.student_ids.filter(id => seen.has(id));
    }
  } catch (error: any) {
    console.error('加载班级学生失败:', error);
    classStudents.value = [];
  }
};

// 全选/取消全选学生
const toggleSelectStudents = () => {
  if (selectAllStudents.value) {
    publishData.student_ids = classStudents.value.map(s => s.id);
  } else {
    publishData.student_ids = [];
  }
};

// 发布考试
const publishExam = async () => {
  if (!currentExam.value) return;
  
  if (!publishData.class_ids || publishData.class_ids.length === 0) {
    alert('请选择班级');
    return;
  }
  
  if (publishData.publish_type === 'scheduled' && !publishData.scheduled_publish_time) {
    alert('请选择发布时间');
    return;
  }
  
  if (publishData.target_type === 'selected' && publishData.student_ids.length === 0) {
    alert('请至少选择一个学生');
    return;
  }
  
  try {
    const publishPayload: any = {
      class_ids: publishData.class_ids.map(id => Number(id)),
      publish_type: publishData.publish_type
    };
    
    if (publishData.publish_type === 'scheduled') {
      publishPayload.scheduled_publish_time = new Date(publishData.scheduled_publish_time).toISOString();
    }
    
    if (publishData.target_type === 'selected') {
      publishPayload.student_ids = publishData.student_ids;
    }
    
    const response = await teacherApi.publishExam(currentExam.value.id, publishPayload);
    
    alert(response.message || '发布成功！');
    showPublishModal.value = false;
    await loadExams();
  } catch (error: any) {
    console.error('发布考试失败:', error);
    alert('发布考试失败: ' + (error.response?.data?.message || error.message));
  }
};

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    published: '已发布',
    ongoing: '进行中',
    ended: '已结束'
  };
  return map[status] || status;
};

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN');
};

onMounted(() => {
  loadExams();
  loadClasses();
  loadQuestionBanks();
});
</script>

<style scoped>
.exam-manager {
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

.header-actions {
  display: flex;
  gap: 12px;
}

.exam-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
}

.exam-card {
  background: #ffffff;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 16px;
  position: relative;
  transition: border-color 0.15s;
}

.exam-card:hover {
  border-color: #0969da;
}

.exam-status {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.exam-status.draft { background: #f8f9fa; color: #6c757d; }
.exam-status.published { background: #d4edda; color: #155724; }
.exam-status.ongoing { background: #fff3cd; color: #856404; }
.exam-status.ended { background: #e2e3e5; color: #383d41; }

.exam-card h3 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 18px;
  padding-right: 80px;
}

.exam-desc {
  color: #666;
  margin: 12px 0;
  line-height: 1.6;
  font-size: 14px;
}

.exam-info {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin: 16px 0;
  color: #888;
  font-size: 14px;
}

.exam-info i {
  margin-right: 6px;
}

.exam-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.loading-state {
  text-align: center;
  padding: 40px;
  color: #666;
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
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.form-group small {
  display: block;
  margin-top: 4px;
  color: #666;
  font-size: 12px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

/* 统一按钮样式 */
.btn-primary,
.btn-secondary,
.btn-success,
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

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover {
  background: #218838;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
}

.btn-outline {
  background: white;
  color: #4a6fa5;
  border: 1px solid #4a6fa5;
}

.btn-outline:hover {
  background: #f0f7ff;
  border-color: #3a5a8c;
  transform: translateY(-1px);
}

.btn-outline.danger {
  color: #dc3545;
  border-color: #dc3545;
}

.btn-outline.danger:hover {
  background: #fff5f5;
  border-color: #c82333;
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
.btn-success:disabled,
.btn-outline:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

/* 题库管理样式 */
.question-bank-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  border-bottom: 2px solid #e0e0e0;
}

.tab-btn {
  padding: 12px 24px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  color: #666;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  margin-bottom: -2px;
}

.tab-btn:hover {
  color: #4a6fa5;
  background: #f8f9fa;
}

.tab-btn.active {
  color: #4a6fa5;
  border-bottom-color: #4a6fa5;
  font-weight: 600;
  background: #f0f7ff;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.form-group-inline {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-group-inline select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.bank-list, .question-list {
  display: grid;
  gap: 16px;
}

.bank-card, .question-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
}

.bank-card h4 {
  margin: 0 0 8px 0;
  color: #333;
}

.bank-info {
  display: flex;
  gap: 16px;
  margin: 12px 0;
  color: #666;
  font-size: 14px;
}

.bank-actions, .question-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.question-content {
  margin-bottom: 16px;
}

.question-content p {
  margin: 0 0 12px 0;
  color: #333;
}

.options {
  margin: 12px 0;
  padding-left: 20px;
}

.options div {
  margin: 8px 0;
  color: #666;
}

.question-meta {
  display: flex;
  gap: 16px;
  margin: 12px 0;
  color: #888;
  font-size: 14px;
}

.explanation {
  margin-top: 12px;
  padding: 12px;
  background: #e3f2fd;
  border-radius: 6px;
  color: #1976d2;
  font-size: 14px;
}

/* 发布考试样式 */
.radio-group {
  display: flex;
  gap: 24px;
  margin-top: 8px;
}

.radio-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  margin: 0;
  font-weight: normal;
}

.radio-group input[type="radio"] {
  width: auto;
  margin: 0;
}

.students-selection {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  margin-top: 12px;
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
  font-weight: normal;
}

.students-list {
  max-height: 300px;
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

.student-item label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  margin: 0;
  width: 100%;
  font-weight: normal;
}

.student-item input[type="checkbox"] {
  width: auto;
  margin: 0;
}

.disabled-input {
  background-color: #f5f5f5;
  color: #666;
  cursor: not-allowed;
}

.text-warning {
  color: #ff9800;
  font-size: 12px;
  margin-top: 4px;
  display: block;
}

.text-info {
  color: #2196f3;
  font-size: 13px;
  margin-top: 4px;
  display: block;
  padding: 8px 12px;
  background: #e3f2fd;
  border-radius: 4px;
}
</style>
