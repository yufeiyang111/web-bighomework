import axios from 'axios';
import config from '@/config';
import type {
    Class, Exam, Course, Question,
    CreateClassRequest, CreateExamRequest
} from '@/types';

const api = axios.create({
    baseURL: `${config.apiBaseUrl}/api`,
    timeout: 10000,
});

// 请求拦截器：添加认证token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// 响应拦截器：处理错误
api.interceptors.response.use(
    (response) => {
        // 对于207状态码（部分成功），也认为是成功的响应
        if (response.status === 207) {
            return response;
        }
        // 不在这里处理数据提取，让每个API方法自己处理
        return response;
    },
    (error) => {
        console.error('API请求错误:', error.response?.status, error.response?.data);
        if (error.response?.status === 401) {
            // token过期，清除并跳转到登录页
            localStorage.removeItem('token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export const teacherApi = {
    // 班级管理
    getClasses: () => api.get('/teacher/classes').then(res => res.data?.data || res.data || []),
    getClassDetail: (classId: number) => api.get(`/teacher/classes/${classId}`).then(res => res.data?.data || res.data),
    createClass: (data: CreateClassRequest) => api.post('/teacher/classes', data).then(res => res.data?.data || res.data),
    updateClass: (classId: number, data: Partial<Class>) => api.put(`/teacher/classes/${classId}`, data).then(res => res.data?.data || res.data),
    deleteClass: (classId: number) => api.delete(`/teacher/classes/${classId}`),
    addStudentsToClass: (classId: number, data: { student_ids: number[] }) => 
        api.post(`/teacher/classes/${classId}`, data).then(res => res.data?.data || res.data),
    removeStudentFromClass: (classId: number, studentId: number) => 
        api.delete(`/teacher/classes/${classId}/students/${studentId}`),
    
    // 学生管理
    getStudents: (params?: { search?: string; exclude_class_id?: number }) => 
        api.get('/teacher/students', { params }).then(res => res.data?.data || res.data || []),

    // 课程管理
    getCourses: () => api.get('/teacher/courses').then(res => {
        console.log('getCourses 原始响应:', res.data);
        const data = res.data?.data || res.data || [];
        console.log('getCourses 提取的数据:', data);
        return data;
    }),
    getCourseDetail: (courseId: number) => api.get(`/teacher/courses/${courseId}`).then(res => {
        console.log('getCourseDetail 原始响应:', res.data);
        return res.data?.data || res.data;
    }),
    createCourse: (data: any) => api.post('/teacher/courses', data).then(res => {
        console.log('createCourse 原始响应:', res.data);
        return res.data?.data || res.data;
    }),
    updateCourse: (courseId: number, data: any) => api.put(`/teacher/courses/${courseId}`, data).then(res => res.data?.data || res.data),
    updateCourseClasses: (courseId: number, class_ids: number[]) =>
        api.post(`/teacher/courses/${courseId}/classes`, { class_ids }).then(res => res.data?.data || res.data),
    deleteCourse: (courseId: number) => api.delete(`/teacher/courses/${courseId}`),

    // 考试管理
    getExams: (params?: { class_id?: number; status?: string; page?: number; per_page?: number }) => 
        api.get('/teacher/exams', { params }).then(res => {
            console.log('getExams 原始响应:', res.data);
            const data = res.data?.data || res.data || [];
            console.log('getExams 提取的数据:', data);
            return data;
        }),
    getExamDetail: (examId: number) => api.get(`/teacher/exams/${examId}`).then(res => res.data?.data || res.data),
    createExam: (data: CreateExamRequest) => api.post('/teacher/exams', data).then(res => res.data?.data || res.data),
    updateExam: (examId: number, data: any) => api.put(`/teacher/exams/${examId}`, data).then(res => res.data?.data || res.data),
    deleteExam: (examId: number) => api.delete(`/teacher/exams/${examId}`),
    publishExam: (examId: number, data: { class_ids: number[]; publish_type: 'immediate' | 'scheduled'; scheduled_publish_time?: string; student_ids?: number[] }) =>
        api.post(`/teacher/exams/${examId}/publish`, data).then(res => res.data?.data || res.data),

    // 提问管理
    getQuestions: (params?: { class_id?: number; page?: number; per_page?: number }) =>
        api.get('/teacher/questions', { params }).then(res => res.data?.data || res.data || []),
    getQuestionDetail: (questionId: number) => api.get(`/teacher/questions/${questionId}`).then(res => res.data?.data || res.data),
    createQuestion: (data: Omit<Question, 'id' | 'createdAt'>) =>
        api.post('/teacher/questions', data).then(res => res.data?.data || res.data),
    updateQuestion: (questionId: number, data: any) => api.put(`/teacher/questions/${questionId}`, data).then(res => res.data?.data || res.data),
    deleteQuestion: (questionId: number) => api.delete(`/teacher/questions/${questionId}`),

    // 成绩管理
    getScores: (params?: { class_id?: number; exam_id?: number; student_name?: string; start_date?: string; end_date?: string; page?: number; per_page?: number }) =>
        api.get('/teacher/scores', { params }).then(res => res.data?.data || res.data || []),
    getScoreDetail: (scoreId: number) => api.get(`/teacher/scores/${scoreId}`).then(res => res.data?.data || res.data),
    createScores: (data: { scores: any[] }) => api.post('/teacher/scores', data).then(res => res.data?.data || res.data),
    updateScore: (scoreId: number, data: any) => api.put(`/teacher/scores/${scoreId}`, data).then(res => res.data?.data || res.data),
    deleteScore: (scoreId: number) => api.delete(`/teacher/scores/${scoreId}`),
    importScores: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return api.post('/teacher/scores/import', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        }).then(res => res.data);
    },
    downloadScoreTemplate: () => {
        return api.get('/teacher/scores/export', { 
            params: { template: 'true' }, 
            responseType: 'blob' 
        }).then(res => {
            // 确保返回的是 Blob
            if (res.data instanceof Blob) {
                return res.data;
            }
            // 如果不是 Blob，尝试转换
            return new Blob([res.data], { 
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
            });
        });
    },
    exportScores: async (params?: { class_id?: number; start_date?: string; end_date?: string }) => {
        try {
            console.log('调用 exportScores API，参数:', params);
            const response = await api.get('/teacher/scores/export', { 
                params, 
                responseType: 'blob' 
            });
            console.log('exportScores API 响应:', response);
            console.log('响应数据:', response.data);
            console.log('响应数据类型:', typeof response.data);
            
            // 确保返回的是 Blob
            if (response.data instanceof Blob) {
                console.log('返回 Blob 对象');
                return response.data;
            }
            // 如果不是 Blob，尝试转换
            console.log('转换响应为 Blob');
            return new Blob([response.data], { 
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
            });
        } catch (error) {
            console.error('exportScores API 错误:', error);
            throw error;
        }
    },
    getScoreAnalysis: (params?: { class_id?: number; exam_id?: number; start_date?: string; end_date?: string }) =>
        api.get('/teacher/scores/analysis', { params }).then(res => res.data?.data || res.data),

    // 题库管理
    getQuestionBanks: () => api.get('/teacher/question-banks').then(res => res.data?.data || res.data || []),
    getQuestionBankDetail: (bankId: number) => api.get(`/teacher/question-banks/${bankId}`).then(res => res.data?.data || res.data),
    createQuestionBank: (data: { name: string; description?: string; is_public?: boolean }) =>
        api.post('/teacher/question-banks', data).then(res => res.data?.data || res.data),
    updateQuestionBank: (bankId: number, data: any) => api.put(`/teacher/question-banks/${bankId}`, data).then(res => res.data?.data || res.data),
    deleteQuestionBank: (bankId: number) => api.delete(`/teacher/question-banks/${bankId}`),

    // 选择题管理
    createMCQQuestion: (data: {
        question_bank_id: number;
        content: string;
        option_a: string;
        option_b: string;
        option_c: string;
        option_d: string;
        correct_option: 'A' | 'B' | 'C' | 'D';
        explanation?: string;
        score?: number;
        difficulty?: string;
    }) => api.post('/teacher/mcq-questions', data).then(res => res.data?.data || res.data),
    updateMCQQuestion: (questionId: number, data: any) => api.put(`/teacher/mcq-questions/${questionId}`, data).then(res => res.data?.data || res.data),
    deleteMCQQuestion: (questionId: number) => api.delete(`/teacher/mcq-questions/${questionId}`),
};