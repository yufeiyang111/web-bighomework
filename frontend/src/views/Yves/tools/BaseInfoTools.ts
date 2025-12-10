interface Course {
    id: string
    name: string
    teacherId: number
    teacherName: string
    description?: string
}

// 当前选中的课程（从localStorage加载）
let currentCourse: Course | null = null

/** 根据flg获取账号信息 0为老师，1为学生 */
function getAccountInfo(flg:number) {
    if (flg == 1) {
        return {
            id: 1, // 对应主键
            name: '余老师',
            Identity: 'teacher',
        }
    } else {
        return {
            id: 2,
            name: '余老师',
            Identity: 'student',
        }
    }
}

/** 获取当前班级信息 */
function getClassInfo() {
    // 从localStorage加载当前课程
    loadCurrentCourse()
    
    if (currentCourse) {
        return {
            classId: currentCourse.id,
            className: currentCourse.name,
        }
    }
    
    // 默认课程
    return {
        classId: '1',
        className: 'Web高级编程',
    }
}

/** 获取当前进入的课程的老师 */
function getClassTeacherInfo() {
    // 从localStorage加载当前课程
    loadCurrentCourse()
    
    if (currentCourse) {
        return {
            id: currentCourse.teacherId,
            name: currentCourse.teacherName,
            Identity: 'teacher',
        }
    }
    
    // 默认老师
    return {
        id: 1,
        name: '余老师',
        Identity: 'teacher',
    }
}

/** 从localStorage加载当前课程 */
function loadCurrentCourse() {
    if (currentCourse) return
    
    const saved = localStorage.getItem('selectedCourse')
    if (saved) {
        try {
            currentCourse = JSON.parse(saved)
        } catch (e) {
            console.error('加载课程失败:', e)
        }
    }
}

/** 设置当前课程 */
function setCurrentCourse(course: Course) {
    currentCourse = course
    localStorage.setItem('selectedCourse', JSON.stringify(course))
}

/** 获取当前课程 */
function getCurrentCourse(): Course | null {
    loadCurrentCourse()
    return currentCourse
}

/** 清除当前课程 */
function clearCurrentCourse() {
    currentCourse = null
    localStorage.removeItem('selectedCourse')
}

export default { 
    getAccountInfo, 
    getClassInfo, 
    getClassTeacherInfo,
    setCurrentCourse,
    getCurrentCourse,
    clearCurrentCourse,
}; 