<template>
  <div class="question-chat">
    <div class="chat-container">
      <!-- 提问列表 -->
      <div class="questions-section">
        <div class="create-question">
          <h3>发布新提问</h3>
          <form @submit.prevent="createQuestion">
            <textarea
                v-model="newQuestion.content"
                placeholder="输入提问内容..."
                rows="3"
                required
            ></textarea>

            <div class="question-options">
              <label>
                <input
                    type="radio"
                    v-model="newQuestion.type"
                    value="individual"
                > 选择学生
              </label>
              <label>
                <input
                    type="radio"
                    v-model="newQuestion.type"
                    value="random"
                > 随机选择
              </label>

              <div v-if="newQuestion.type === 'individual'" class="student-selector">
                <h4>选择学生：</h4>
                <div class="student-list">
                  <label v-for="student in students" :key="student.id">
                    <input
                        type="checkbox"
                        :value="student.id"
                        v-model="newQuestion.selectedStudents"
                    >
                    {{ student.name }}
                  </label>
                </div>
              </div>

              <div v-else class="random-selector">
                <label>
                  随机选择人数：
                  <input
                      type="number"
                      v-model.number="newQuestion.randomCount"
                      min="1"
                      :max="students.length"
                  >
                </label>
              </div>
            </div>

            <button type="submit" class="btn-primary">发布提问</button>
          </form>
        </div>

        <!-- 提问列表 -->
        <div class="questions-list">
          <div
              v-for="question in questions"
              :key="question.id"
              class="question-item"
          >
            <div class="question-header">
              <span class="question-type">
                {{ question.type === 'individual' ? '指定提问' : '随机提问' }}
              </span>
              <span class="question-time">
                {{ formatDate(question.createdAt) }}
              </span>
            </div>
            <p class="question-content">{{ question.content }}</p>

            <!-- 回答列表 -->
            <div class="answers-section">
              <div
                  v-for="answer in getQuestionAnswers(question.id)"
                  :key="answer.id"
                  class="answer-item"
              >
                <div class="answer-header">
                  <span class="student-name">{{ getStudentName(answer.studentId) }}</span>
                  <span class="answer-time">{{ formatDate(answer.createdAt) }}</span>
                </div>
                <p class="answer-content">{{ answer.content }}</p>

                <!-- 回复列表 -->
                <div class="replies">
                  <div
                      v-for="reply in answer.replies"
                      :key="reply.id"
                      class="reply-item"
                  >
                    <span class="reply-user">{{ getUserName(reply.userId) }}</span>：
                    <span class="reply-content">{{ reply.content }}</span>
                  </div>
                  <input
                      v-model="newReplies[answer.id]"
                      @keyup.enter="addReply(answer.id)"
                      placeholder="回复..."
                      class="reply-input"
                  >
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 学生列表 -->
      <div class="students-sidebar">
        <h3>班级学生 ({{ students.length }})</h3>
        <div class="student-list">
          <div
              v-for="student in students"
              :key="student.id"
              class="student-item"
          >
            <img :src="student.avatar || defaultAvatar" class="avatar">
            <div class="student-info">
              <strong>{{ student.name }}</strong>
              <span>{{ student.studentId }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useClassStore } from '@/stores/class';

const route = useRoute();
const classStore = useClassStore();

const classId = route.params.id as string;
const newQuestion = reactive({
  content: '',
  type: 'individual' as 'individual' | 'random',
  selectedStudents: [] as string[],
  randomCount: 1,
});

const newReplies = ref<Record<string, string>>({});
const defaultAvatar = '/default-avatar.png';

const students = computed(() => classStore.currentClassStudents);
const questions = computed(() => classStore.questions);

const getQuestionAnswers = (questionId: string) => {
  return classStore.getAnswersByQuestionId(questionId);
};

const getStudentName = (studentId: string) => {
  const student = students.value.find(s => s.id === studentId);
  return student?.name || '未知学生';
};

const createQuestion = async () => {
  await classStore.createQuestion({
    ...newQuestion,
    classId,
    teacherId: 'current-teacher-id',
  });
  newQuestion.content = '';
  newQuestion.selectedStudents = [];
  newQuestion.randomCount = 1;
};

const addReply = async (answerId: string) => {
  const content = newReplies.value[answerId];
  if (content.trim()) {
    await classStore.addReply({
      answerId,
      userId: 'current-teacher-id',
      content,
    });
    newReplies.value[answerId] = '';
  }
};

const formatDate = (date: Date) => {
  return new Date(date).toLocaleString();
};

onMounted(() => {
  classStore.fetchClassData(classId);
});
</script>