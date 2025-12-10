import requestTools from './RequestTools';

export interface Chapter {
    id: number
    course_name: string
    title: string
    description?: string
    order_num: number
    parent_id?: number
    created_at?: string
    updated_at?: string
    children?: Chapter[]
    videos?: ChapterVideo[]
}

export interface ChapterVideo {
    id: number
    chapter_id: number
    title: string
    description?: string
    file_path: string
    file_size: number
    duration: number
    order_num: number
    created_at?: string
    updated_at?: string
    progress?: number
    completed?: boolean
}

/**
 * 获取课程的章节树
 * @param courseName 课程名称
 * @returns Promise<Chapter[]> 章节树
 */
async function getChapterTree(courseName: string): Promise<Chapter[]> {
    const response = await requestTools.get('/chapter/tree', {
        course_name: courseName
    });
    return response.data || [];
    
    /* 模拟数据（已切换到真实 API）
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve([
                {
                    id: 1,
                    course_name: courseName,
                    title: '第一章：Web 基础',
                    description: '本章介绍 Web 开发的基础知识',
                    order_num: 1,
                    children: [
                        {
                            id: 11,
                            course_name: courseName,
                            title: '1.1 HTML 基础',
                            description: 'HTML 标签和语法',
                            order_num: 1,
                            parent_id: 1,
                            children: [],
                            videos: [
                                {
                                    id: 101,
                                    chapter_id: 11,
                                    title: 'HTML 标签介绍',
                                    description: '介绍常用的 HTML 标签',
                                    file_path: '/videos/html-tags.mp4',
                                    file_size: 15728640,
                                    duration: 600,
                                    order_num: 1,
                                    completed: true
                                },
                                {
                                    id: 102,
                                    chapter_id: 11,
                                    title: 'HTML 表单',
                                    description: '学习 HTML 表单元素',
                                    file_path: '/videos/html-forms.mp4',
                                    file_size: 20971520,
                                    duration: 720,
                                    order_num: 2,
                                    progress: 300,
                                    completed: false
                                }
                            ]
                        },
                        {
                            id: 12,
                            course_name: courseName,
                            title: '1.2 CSS 基础',
                            description: 'CSS 样式和布局',
                            order_num: 2,
                            parent_id: 1,
                            children: [],
                            videos: [
                                {
                                    id: 103,
                                    chapter_id: 12,
                                    title: 'CSS 选择器',
                                    description: '学习各种 CSS 选择器',
                                    file_path: '/videos/css-selectors.mp4',
                                    file_size: 18874368,
                                    duration: 540,
                                    order_num: 1,
                                    completed: false
                                }
                            ]
                        }
                    ],
                    videos: []
                },
                {
                    id: 2,
                    course_name: courseName,
                    title: '第二章：JavaScript 编程',
                    description: '学习 JavaScript 编程语言',
                    order_num: 2,
                    children: [],
                    videos: [
                        {
                            id: 201,
                            chapter_id: 2,
                            title: 'JavaScript 变量和数据类型',
                            description: '介绍 JS 的基本数据类型',
                            file_path: '/videos/js-variables.mp4',
                            file_size: 25165824,
                            duration: 900,
                            order_num: 1,
                            completed: false
                        },
                        {
                            id: 202,
                            chapter_id: 2,
                            title: 'JavaScript 函数',
                            description: '学习函数的定义和使用',
                            file_path: '/videos/js-functions.mp4',
                            file_size: 31457280,
                            duration: 1080,
                            order_num: 2,
                            completed: false
                        }
                    ]
                },
                {
                    id: 3,
                    course_name: courseName,
                    title: '第三章：Vue.js 框架',
                    description: '学习 Vue.js 前端框架',
                    order_num: 3,
                    children: [],
                    videos: [
                        {
                            id: 301,
                            chapter_id: 3,
                            title: 'Vue 基础概念',
                            description: '了解 Vue 的核心概念',
                            file_path: '/videos/vue-basics.mp4',
                            file_size: 28311552,
                            duration: 960,
                            order_num: 1,
                            completed: false
                        }
                    ]
                }
            ]);
        }, 500); // 模拟网络延迟
    });
    */
}

/**
 * 添加章节
 * @param chapterData 章节数据
 * @returns Promise<number> 新章节ID
 */
async function addChapter(chapterData: {
    course_name: string;
    title: string;
    description?: string;
    parent_id?: number;
    order_num?: number;
}): Promise<number> {
    const response = await requestTools.post('/chapter/add', chapterData);
    return response.chapter_id;
}

/**
 * 更新章节
 * @param chapterId 章节ID
 * @param chapterData 章节数据
 * @returns Promise<boolean> 是否成功
 */
async function updateChapter(chapterId: number, chapterData: {
    title?: string;
    description?: string;
    order_num?: number;
}): Promise<boolean> {
    const response = await requestTools.post('/chapter/update', {
        chapter_id: chapterId,
        ...chapterData
    });
    return response.success;
}

/**
 * 删除章节
 * @param chapterId 章节ID
 * @returns Promise<boolean> 是否成功
 */
async function deleteChapter(chapterId: number): Promise<boolean> {
    const response = await requestTools.post('/chapter/delete', {
        chapter_id: chapterId
    });
    return response.success;
}

/**
 * 上传视频
 * @param file 视频文件
 * @param chapterId 章节ID
 * @param title 视频标题
 * @param description 视频描述
 * @returns Promise<number> 新视频ID
 */
async function uploadVideo(
    file: File,
    chapterId: number,
    title: string,
    description?: string
): Promise<number> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('chapter_id', chapterId.toString());
    formData.append('title', title);
    if (description) {
        formData.append('description', description);
    }

    const response = await fetch(`${requestTools.BASE_URL}/chapter/upload-video`, {
        method: 'POST',
        body: formData
    });

    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.error || '上传失败');
    }

    return data.video_id;
}

/**
 * 删除视频
 * @param videoId 视频ID
 * @returns Promise<boolean> 是否成功
 */
async function deleteVideo(videoId: number): Promise<boolean> {
    const response = await requestTools.post('/chapter/delete-video', {
        video_id: videoId
    });
    return response.success;
}

/**
 * 更新学习进度
 * @param videoId 视频ID
 * @param progress 进度（秒）
 * @param completed 是否完成
 * @returns Promise<boolean> 是否成功
 */
async function updateProgress(
    videoId: number,
    progress: number,
    completed: boolean = false
): Promise<boolean> {
    const response = await requestTools.post('/chapter/update-progress', {
        video_id: videoId,
        progress,
        completed
    });
    return response.success;
}

/**
 * 获取视频流URL
 * @param videoId 视频ID
 * @returns string 视频URL
 */
function getVideoUrl(videoId: number): string {
    return `${requestTools.BASE_URL}/chapter/video/${videoId}`;
}

export default {
    getChapterTree,
    addChapter,
    updateChapter,
    deleteChapter,
    uploadVideo,
    deleteVideo,
    updateProgress,
    getVideoUrl
};
