<template>
  <div class="admin-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>管理中心</h1>
          <el-button @click="router.push('/dashboard')">返回首页</el-button>
        </div>
      </el-header>
      
      <el-main>
        <el-card>
          <template #header>
            <div class="card-header">
              <h2>教师审核</h2>
              <el-button type="primary" size="small" @click="loadPendingTeachers">
                刷新列表
              </el-button>
            </div>
          </template>
          
          <el-table :data="pendingTeachers" v-loading="loading" border>
            <el-table-column prop="system_account" label="系统账号" width="120" />
            <el-table-column prop="email" label="邮箱" width="200" />
            <el-table-column prop="real_name" label="真实姓名" width="120" />
            <el-table-column prop="application_time" label="申请时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.application_time) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button
                  type="success"
                  size="small"
                  @click="handleApprove(row.approval_id, true)"
                >
                  通过
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click="handleApprove(row.approval_id, false)"
                >
                  拒绝
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-empty v-if="!loading && pendingTeachers.length === 0" description="暂无待审核教师" />
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getPendingTeachers, approveTeacher } from '@/api/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const pendingTeachers = ref([])

const loadPendingTeachers = async () => {
  loading.value = true
  
  try {
    const response = await getPendingTeachers()
    
    if (response.success) {
      pendingTeachers.value = response.teachers || []
    }
  } catch (error) {
    console.error('获取待审核教师列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleApprove = async (approvalId, approved) => {
  const action = approved ? '通过' : '拒绝'
  
  ElMessageBox.prompt(
    `请输入${action}原因（选填）`,
    `${action}审核`,
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /.*/,
      inputPlaceholder: '请输入原因'
    }
  ).then(async ({ value }) => {
    try {
      const response = await approveTeacher(approvalId, approved, value || '')
      
      if (response.success) {
        ElMessage.success(response.message || '审核完成')
        // 刷新列表
        loadPendingTeachers()
      }
    } catch (error) {
      console.error('审核失败:', error)
    }
  }).catch(() => {})
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadPendingTeachers()
})
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
}

.el-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 40px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
}

.el-main {
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
}
</style>
