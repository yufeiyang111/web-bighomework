<script setup lang="ts">
// 资料管理页面：学生具有下载/预览功能，老师在此基础上多了创建文件/文件夹功能
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import baseInfoTools from '../tools/BaseInfoTools'
import MaterialToolbar from '../components/material/MaterialToolbar.vue'
import MaterialList from '../components/material/MaterialList.vue'
import type { MaterialItem } from '../tools/MaterialTools'
import MaterialPreview from '../components/material/MaterialPreview.vue'
import MaterialUploadDialog from '../components/material/MaterialUploadDialog.vue'
import MaterialCreateFolderDialog from '../components/material/MaterialCreateFolderDialog.vue'
import CourseSelector from '../components/CourseSelector.vue'
import materialTools from '../tools/MaterialTools'
import Layout from "@/components/Layout.vue";

const router = useRouter()
const account = baseInfoTools.getAccountInfo(1) // 这里可以根据登录状态动态传参
const isTeacher = computed(() => account.Identity === 'teacher')

// 当前路径（用简化的 folder 结构模拟）
const currentPath = ref<MaterialItem[]>([])
const currentNodeId = ref<number | null>(null)

// 课程名称（从班级信息获取）
const classInfo = computed(() => baseInfoTools.getClassInfo())
const classTeacherInfo = computed(() => baseInfoTools.getClassTeacherInfo())

// 课程名称（用于查询根目录）
const courseName = computed(() => {
  const teacherId = classTeacherInfo.value.id
  const classId = classInfo.value.classId
  return `${teacherId}-${classId}`
})

// 课程根目录名称（包含 -root 后缀）
const rootFolderName = computed(() => {
  return `${courseName.value}-root`
})

// 课程根目录路径
const rootPath = computed(() => {
  return `/${rootFolderName.value}`
})

// 构建完整路径
function buildFullPath(fileName: string): string {
  const pathParts = [rootPath.value]
  
  // 添加当前路径中的所有文件夹
  currentPath.value.forEach(folder => {
    pathParts.push(folder.name)
  })
  
  // 添加文件名或文件夹名
  pathParts.push(fileName)
  
  return pathParts.join('/')
}

// 材料列表
const materials = ref<MaterialItem[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// 批量选择
const selectedItems = ref<Set<number>>(new Set())
const isSelectMode = ref(false)
const selectModeType = ref<'download' | 'delete'>('download') // 选择模式类型

// 预览状态
const previewVisible = ref(false)
const previewItem = ref<MaterialItem | null>(null)

// 对话框状态
const uploadDialogVisible = ref(false)
const createFolderDialogVisible = ref(false)

// 格式化文件大小
function formatFileSize(bytes: number | string | undefined): string {
  if (!bytes) return '-'
  const size = typeof bytes === 'string' ? parseInt(bytes) : bytes
  if (isNaN(size) || size === 0) return '-'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(size) / Math.log(k))
  return Math.round(size / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 加载材料列表
async function loadMaterials(nodeId: number) {
  loading.value = true
  error.value = null
  try {
    const data = await materialTools.getNextDepthTree(nodeId)
    
    // 处理数据：添加创建者和格式化
    materials.value = data.map(item => ({
      ...item,
      id: item.id || item.node_id || 0,  // 确保 id 存在
      node_id: item.node_id || item.id,  // 确保 node_id 存在
      creator: classTeacherInfo.value.name,  // 设置为当前课程老师
      updatedAt: item.updated_at || item.created_at || '-',  // 使用 updated_at
      size: item.type === 'folder' ? '-' : formatFileSize(item.size)  // 格式化文件大小
    }))
  } catch (err: any) {
    error.value = err.message || '加载失败'
    console.error('加载材料列表失败:', err)
  } finally {
    loading.value = false
  }
}

// 初始化：获取课程根节点并加载材料
async function initializeMaterials() {
  loading.value = true
  error.value = null
  try {
    console.log('初始化资料管理')
    console.log('  课程名称:', courseName.value)
    console.log('  根目录名称:', rootFolderName.value)
    console.log('  根目录路径:', rootPath.value)
    
    // 1. 获取课程根节点ID（使用不带 -root 的课程名称）
    const rootNodeId = await materialTools.getCourseRootNodeId(courseName.value)
    currentNodeId.value = rootNodeId
    
    console.log('  根节点ID:', rootNodeId)
    
    // 2. 加载根节点下的材料
    await loadMaterials(rootNodeId)
  } catch (err: any) {
    error.value = err.message || '初始化失败'
    console.error('初始化材料失败:', err)
    
    // 如果课程不存在，提示创建
    if (err.message?.includes('不存在')) {
      console.log('课程根目录不存在，尝试创建...')
      try {
        // 自动创建课程根目录
        await materialTools.addCourseRoot(courseName.value)
        console.log('课程根目录创建成功，重新初始化...')
        // 重新初始化
        await initializeMaterials()
      } catch (createErr: any) {
        console.error('创建课程根目录失败:', createErr)
        error.value = '课程根目录不存在且创建失败: ' + createErr.message
      }
    }
  } finally {
    loading.value = false
  }
}

async function handleOpen(item: MaterialItem) {
  if (item.type === 'folder') {
    // 进入文件夹：加载子节点
    currentPath.value.push(item)
    const nodeId = item.node_id || item.id
    currentNodeId.value = nodeId
    if (nodeId) {
      await loadMaterials(nodeId)
    }
  } else {
    previewItem.value = item
    previewVisible.value = true
  }
}

async function handleDownload(item: MaterialItem) {
  try {
    const nodeId = item.node_id || item.id
    await materialTools.downloadFile(nodeId, item.name)
  } catch (err: any) {
    alert('下载失败: ' + (err.message || '未知错误'))
    console.error('下载失败:', err)
  }
}

// 切换选择模式
function toggleSelectMode(type: 'download' | 'delete' = 'download') {
  isSelectMode.value = !isSelectMode.value
  selectModeType.value = type
  if (!isSelectMode.value) {
    selectedItems.value.clear()
  }
}

// 切换选中状态
function toggleSelect(item: MaterialItem) {
  const id = item.node_id || item.id
  if (selectedItems.value.has(id)) {
    selectedItems.value.delete(id)
  } else {
    selectedItems.value.add(id)
  }
}

// 全选/取消全选
function toggleSelectAll() {
  if (selectedItems.value.size === materials.value.length) {
    selectedItems.value.clear()
  } else {
    materials.value.forEach(item => {
      const id = item.node_id || item.id
      selectedItems.value.add(id)
    })
  }
}

// 单个删除
async function handleDelete(item: MaterialItem) {
  if (!confirm(`确定要删除 "${item.name}" 吗？${item.type === 'folder' ? '（包括其中的所有文件）' : ''}`)) {
    return
  }
  
  loading.value = true
  try {
    const nodeId = item.node_id || item.id
    await materialTools.deleteNode(nodeId)
    
    // 刷新当前目录
    if (currentNodeId.value) {
      await loadMaterials(currentNodeId.value)
    }
  } catch (err: any) {
    alert('删除失败: ' + (err.message || '未知错误'))
    console.error('删除失败:', err)
  } finally {
    loading.value = false
  }
}

// 批量下载
async function handleBatchDownload() {
  if (selectedItems.value.size === 0) {
    alert('请先选择要下载的文件')
    return
  }
  
  try {
    const nodeIds = Array.from(selectedItems.value)
    await materialTools.downloadBatch(nodeIds)
    
    // 下载成功后退出选择模式
    isSelectMode.value = false
    selectedItems.value.clear()
  } catch (err: any) {
    alert('批量下载失败: ' + (err.message || '未知错误'))
    console.error('批量下载失败:', err)
  }
}

// 批量删除
async function handleBatchDelete() {
  if (selectedItems.value.size === 0) {
    alert('请先选择要删除的项目')
    return
  }
  
  if (!confirm(`确定要删除选中的 ${selectedItems.value.size} 项吗？此操作不可恢复！`)) {
    return
  }
  
  loading.value = true
  try {
    const nodeIds = Array.from(selectedItems.value)
    const result = await materialTools.deleteBatch(nodeIds)
    
    alert(`删除完成：成功 ${result.deleted_count} 项，失败 ${result.failed_count} 项`)
    
    // 刷新当前目录
    if (currentNodeId.value) {
      await loadMaterials(currentNodeId.value)
    }
    
    // 退出选择模式
    isSelectMode.value = false
    selectedItems.value.clear()
  } catch (err: any) {
    alert('批量删除失败: ' + (err.message || '未知错误'))
    console.error('批量删除失败:', err)
  } finally {
    loading.value = false
  }
}

async function handleBack(targetId?: number) {
  if (!targetId) {
    // 返回根目录
    currentPath.value = []
    await initializeMaterials()
    return
  }
  const idx = currentPath.value.findIndex((p: MaterialItem) => p.id === targetId)
  if (idx !== -1) {
    currentPath.value = currentPath.value.slice(0, idx + 1)
    const targetItem = currentPath.value[idx]
    if (targetItem) {
      const nodeId = targetItem.node_id || targetItem.id
      currentNodeId.value = nodeId
      if (nodeId) {
        await loadMaterials(nodeId)
      }
    }
  }
}

function handleCreateFolder() {
  createFolderDialogVisible.value = true
}

function handleUploadFile() {
  uploadDialogVisible.value = true
}

function handleSmartClassify() {
  // 跳转到智能分类页面
  const currentFolderName = currentPath.value.length > 0 
    ? currentPath.value[currentPath.value.length - 1]?.name || '根目录'
    : '根目录'
  
  router.push({
    path: '/smart-classify',
    query: {
      nodeId: currentNodeId.value?.toString(),
      nodeName: currentFolderName
    }
  })
}

// 处理新建文件夹确认
async function handleConfirmCreateFolder(payload: { name: string }) {
  if (!currentNodeId.value) {
    alert('当前目录无效')
    return
  }

  loading.value = true
  try {
    // 使用新的路径构建逻辑
    const fullPath = buildFullPath(payload.name)

    console.log('创建文件夹:', {
      name: payload.name,
      path: fullPath,
      parent_node_id: currentNodeId.value
    })

    // 调用后端 API 创建文件夹
    const newNodeId = await materialTools.addNode({
      name: payload.name,
      path: fullPath,
      type: 'folder',
      parent_node_id: currentNodeId.value
    })

    console.log('文件夹创建成功，节点ID:', newNodeId)
    
    // 刷新当前目录
    await loadMaterials(currentNodeId.value)
    
    createFolderDialogVisible.value = false
  } catch (err: any) {
    alert('创建文件夹失败: ' + (err.message || '未知错误'))
    console.error('创建文件夹失败:', err)
  } finally {
    loading.value = false
  }
}

// 处理文件上传确认
async function handleConfirmUpload(payload: { files: File[] }) {
  if (!currentNodeId.value) {
    alert('当前目录无效')
    return
  }

  loading.value = true
  try {
    // 处理多个文件上传
    for (const file of payload.files) {
      // 使用新的路径构建逻辑
      const fullPath = buildFullPath(file.name)

      console.log('上传文件:', {
        name: file.name,
        path: fullPath,
        parent_node_id: currentNodeId.value
      })

      // 调用后端 API 上传文件
      const newNodeId = await materialTools.uploadFile(
        file,
        currentNodeId.value!,
        fullPath
      )

      console.log('文件上传成功，节点ID:', newNodeId)
    }
    
    // 刷新当前目录
    await loadMaterials(currentNodeId.value)
    
    uploadDialogVisible.value = false
  } catch (err: any) {
    alert('上传文件失败: ' + (err.message || '未知错误'))
    console.error('上传文件失败:', err)
  } finally {
    loading.value = false
  }
}

// 课程切换处理
function handleCourseChange(course: any) {
  console.log('切换课程:', course)
  
  // 更新baseInfoTools中的课程信息
  baseInfoTools.setCurrentCourse(course)
  
  // 重新初始化资料
  initializeMaterials()
}

// 组件挂载时初始化
onMounted(() => {
  initializeMaterials()
})
</script>

<template>
  <Layout pageTitle="资料中心">
  <div class="material-page">
    <div class="page-header">
      <div class="header-left">
        <h1>资料管理</h1>
        <p class="sub-title">
          当前身份：
          <span class="tag" :class="isTeacher ? 'teacher' : 'student'">
            {{ isTeacher ? '老师，可上传与新建资料' : '学生，仅可下载与预览资料' }}
          </span>
        </p>
      </div>
      
      <div class="header-right">
        <CourseSelector @change="handleCourseChange" />
      </div>
    </div>

    <MaterialToolbar
      :is-teacher="isTeacher"
      :current-path="currentPath"
      :root-name="rootFolderName"
      :is-select-mode="isSelectMode"
      :selected-count="selectedItems.size"
      :select-mode-type="selectModeType"
      @create-folder="handleCreateFolder"
      @upload-file="handleUploadFile"
      @smart-classify="handleSmartClassify"
      @back="handleBack"
      @toggle-select-mode="toggleSelectMode"
      @batch-download="handleBatchDownload"
      @batch-delete="handleBatchDelete"
      @select-all="toggleSelectAll"
    />

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- 错误提示 -->
    <div v-else-if="error" class="error-message">
      <p><i class="fas fa-exclamation-circle"></i> {{ error }}</p>
      <button class="btn-retry" @click="initializeMaterials">重试</button>
    </div>

    <!-- 材料列表 -->
    <MaterialList
      v-else
      :list="materials"
      :is-select-mode="isSelectMode"
      :selected-items="selectedItems"
      :is-teacher="isTeacher"
      @open="handleOpen"
      @download="handleDownload"
      @delete="handleDelete"
      @toggle-select="toggleSelect"
    />

    <MaterialPreview
      :visible="previewVisible"
      :item="previewItem"
      @close="previewVisible = false"
    />

    <MaterialCreateFolderDialog
      :visible="createFolderDialogVisible && isTeacher"
      @close="createFolderDialogVisible = false"
      @confirm="handleConfirmCreateFolder"
    />

    <MaterialUploadDialog
      :visible="uploadDialogVisible && isTeacher"
      @close="uploadDialogVisible = false"
      @confirm="handleConfirmUpload"
    />
  </div>
    </Layout>
</template>

<style scoped>
.material-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  gap: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #d0d7de;
}

.header-left {
  flex: 1;
}

.header-right {
  flex-shrink: 0;
}

.material-page h1 {
  color: #1f2328;
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.sub-title {
  color: #656d76;
  margin: 0;
  font-size: 0.875rem;
}

.tag {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  margin-left: 0.5rem;
}

.tag.teacher {
  background: #ddf4ff;
  color: #0969da;
  border: 1px solid #b6e3ff;
}

.tag.student {
  background: #dafbe1;
  color: #1a7f37;
  border: 1px solid #ace1af;
}

/* 加载状态 */
.loading {
  text-align: center;
  padding: 3rem 1rem;
  color: #656d76;
}

.spinner {
  width: 32px;
  height: 32px;
  margin: 0 auto 1rem;
  border: 3px solid #f6f8fa;
  border-top: 3px solid #0969da;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误提示 */
.error-message {
  text-align: center;
  padding: 3rem 1rem;
  color: #cf222e;
}

.error-message p {
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.btn-retry {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid #d0d7de;
  background: #ffffff;
  color: #1f2328;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-retry:hover {
  background: #f6f8fa;
  border-color: #0969da;
  color: #0969da;
}
</style>

