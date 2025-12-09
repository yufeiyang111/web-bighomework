<template>
  <div class="roster-container">
    <el-card class="header-card">
      <h2>学生花名册管理</h2>
      <p class="subtitle">上传学生基本信息和人脸照片，用于学生注册验证</p>
    </el-card>

    <!-- 添加学生表单 -->
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <span>添加学生</span>
          <el-button type="primary" @click="showAddDialog = true" :icon="Plus">
            新增学生
          </el-button>
        </div>
      </template>

      <!-- 学生列表 -->
      <el-table :data="students" border stripe v-loading="loading">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="student_name" label="姓名" width="120" />
        <el-table-column prop="student_id_number" label="学号" width="150" />
        <el-table-column prop="gender" label="性别" width="80" />
        <el-table-column prop="class_name" label="班级" width="120" />
        <el-table-column prop="grade" label="年级" width="100" />
        <el-table-column prop="contact_phone" label="联系电话" width="130" />
        <el-table-column prop="is_registered" label="注册状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_registered ? 'success' : 'info'">
              {{ row.is_registered ? '已注册' : '未注册' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="添加时间" width="180" />
        <el-table-column label="操作" fixed="right" width="100">
          <template #default="{ row }">
            <el-button 
              type="danger" 
              size="small" 
              @click="handleDelete(row)"
              :disabled="row.is_registered"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadStudents"
        @current-change="loadStudents"
        class="pagination"
      />
    </el-card>

    <!-- 添加学生对话框 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加学生信息"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="studentForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="学生姓名" prop="studentName">
          <el-input v-model="studentForm.studentName" placeholder="请输入学生姓名" />
        </el-form-item>
        
        <el-form-item label="学号" prop="studentIdNumber">
          <el-input v-model="studentForm.studentIdNumber" placeholder="请输入学号" />
        </el-form-item>
        
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="studentForm.gender">
            <el-radio label="男">男</el-radio>
            <el-radio label="女">女</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="班级">
          <el-input v-model="studentForm.className" placeholder="请输入班级" />
        </el-form-item>
        
        <el-form-item label="年级">
          <el-input v-model="studentForm.grade" placeholder="请输入年级" />
        </el-form-item>
        
        <el-form-item label="联系电话">
          <el-input v-model="studentForm.contactPhone" placeholder="请输入联系电话" />
        </el-form-item>
        
        <el-form-item label="人脸照片">
          <el-upload
            class="upload-demo"
            :auto-upload="false"
            :limit="1"
            accept="image/*"
            :on-change="handleImageChange"
            :on-remove="handleImageRemove"
            list-type="picture-card"
            :file-list="fileList"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">
            请上传学生清晰的正面照片，用于后续身份验证
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="submitStudent" :loading="submitting">
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '../utils/request'

const students = ref([])
const loading = ref(false)
const submitting = ref(false)
const showAddDialog = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const formRef = ref(null)
const fileList = ref([])

const studentForm = reactive({
  studentName: '',
  studentIdNumber: '',
  gender: '',
  className: '',
  grade: '',
  contactPhone: ''
})

const faceImage = ref(null)

const rules = {
  studentName: [
    { required: true, message: '请输入学生姓名', trigger: 'blur' }
  ],
  studentIdNumber: [
    { required: true, message: '请输入学号', trigger: 'blur' }
  ],
  gender: [
    { required: true, message: '请选择性别', trigger: 'change' }
  ]
}

const handleImageChange = (file) => {
  console.log('图片上传触发:', {
    file: file,
    raw: file.raw,
    name: file.name,
    size: file.size
  })
  faceImage.value = file.raw
  fileList.value = [file]
  ElMessage.success('图片已选择: ' + file.name)
}

const handleImageRemove = () => {
  faceImage.value = null
  fileList.value = []
}

const loadStudents = async () => {
  loading.value = true
  try {
    const res = await request({
      url: '/roster/my-students',
      method: 'get',
      params: {
        page: currentPage.value,
        pageSize: pageSize.value
      }
    })
    
    if (res.success) {
      students.value = res.students
      total.value = res.total
    }
  } catch (error) {
    ElMessage.error('加载学生列表失败')
  } finally {
    loading.value = false
  }
}

const submitStudent = async () => {
  if (!formRef.value) return
  
  // 先检查图片是否上传
  if (!faceImage.value) {
    ElMessage.error('请上传人脸照片')
    console.error('表单验证失败: 未上传人脸照片', {
      faceImage: faceImage.value,
      fileList: fileList.value
    })
    return
  }
  
  await formRef.value.validate(async (valid) => {
    if (!valid) {
      console.error('表单验证失败', studentForm)
      return
    }

    submitting.value = true
    const formData = new FormData()
    
    // 添加表单数据
    Object.keys(studentForm).forEach(key => {
      if (studentForm[key]) {
        formData.append(key, studentForm[key])
        console.log(`添加表单字段: ${key} = ${studentForm[key]}`)
      }
    })
    
    // 添加图片
    formData.append('faceImage', faceImage.value)
    console.log('添加图片文件:', {
      name: faceImage.value.name,
      size: faceImage.value.size,
      type: faceImage.value.type
    })

    try {
      console.log('发送请求到 /roster/add-student')
      const res = await request({
        url: '/roster/add-student',
        method: 'post',
        data: formData,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      console.log('服务器响应:', res)
      
      if (res.success) {
        ElMessage.success('添加成功')
        showAddDialog.value = false
        loadStudents()
        resetForm()
      } else {
        ElMessage.error(res.message || '添加失败')
      }
    } catch (error) {
      console.error('添加学生失败:', error)
      console.error('错误详情:', {
        response: error.response,
        message: error.message,
        stack: error.stack
      })
      ElMessage.error(error.response?.data?.message || '添加失败，请查看控制台')
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除学生 ${row.student_name}(${row.student_id_number}) 吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await request({
      url: `/roster/delete-student/${row.roster_id}`,
      method: 'delete'
    })
    
    if (res.success) {
      ElMessage.success('删除成功')
      loadStudents()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.assign(studentForm, {
    studentName: '',
    studentIdNumber: '',
    gender: '',
    className: '',
    grade: '',
    contactPhone: ''
  })
  faceImage.value = null
  fileList.value = []
}

onMounted(() => {
  loadStudents()
})
</script>

<style scoped>
.roster-container {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-card h2 {
  margin: 0 0 10px 0;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.form-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.upload-tip {
  margin-top: 10px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

:deep(.el-upload-list--picture-card .el-upload-list__item) {
  width: 148px;
  height: 148px;
}

:deep(.el-upload--picture-card) {
  width: 148px;
  height: 148px;
}
</style>
