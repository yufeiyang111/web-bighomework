<template>
  <Layout pageTitle="成绩导入导出">
    <div class="grade-importer">
    <div class="import-section">
      <div class="section-header">
        <h3>导入成绩</h3>
        <button @click.stop="downloadTemplate" class="btn-outline" type="button">
          <i class="fas fa-download"></i> 下载模板
        </button>
      </div>
      
      <div class="template-notice">
        <i class="fas fa-info-circle"></i>
        <span>请使用标准模板填写成绩数据，模板包含示例数据和填写说明</span>
      </div>
      
      <FileUploader
          accept=".xlsx,.xls"
          @file-selected="handleFileSelected"
      >
        <template #default="{ isDragging }">
          <div :class="['drop-zone', { dragging: isDragging }]">
            <i class="fas fa-file-excel fa-3x"></i>
            <p>点击或拖拽Excel文件到这里</p>
            <p class="hint">支持 .xlsx 和 .xls 格式</p>
          </div>
        </template>
      </FileUploader>

      <div v-if="selectedFile" class="file-preview">
        <p>已选择文件：{{ selectedFile.name }}</p>
        <button @click="confirmImport" class="btn-primary">上传并导入</button>
      </div>
    </div>

    <div class="export-section">
      <h3>导出成绩</h3>
      <div class="export-options">
        <div class="form-group">
          <label>选择班级</label>
          <select v-model="exportParams.classId">
            <option value="">全部班级</option>
            <option v-for="classItem in classes" :key="classItem.id" :value="classItem.id">
              {{ classItem.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>时间范围</label>
          <div class="date-range">
            <input type="date" v-model="exportParams.startDate">
            <span>至</span>
            <input type="date" v-model="exportParams.endDate">
          </div>
        </div>

        <div class="form-group">
          <label>包含字段</label>
          <div class="field-selector">
            <label v-for="field in exportFields" :key="field.key">
              <input type="checkbox" v-model="field.selected"> {{ field.label }}
            </label>
          </div>
        </div>
      </div>

      <button @click="exportToExcel" class="btn-primary">
        <i class="fas fa-download"></i> 导出Excel
      </button>
    </div>

    <!-- 导入预览 -->
    <Modal v-model="showPreview" title="导入预览" size="xlarge">
      <div v-if="previewData" class="preview-table">
        <table>
          <thead>
          <tr>
            <th v-for="header in previewHeaders" :key="header">
              {{ header }}
            </th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="(row, index) in previewData" :key="index">
            <td v-for="header in previewHeaders" :key="header">
              {{ row[header] }}
            </td>
          </tr>
          </tbody>
        </table>
        <div class="preview-actions">
          <button @click="confirmImport" class="btn-primary">确认导入</button>
          <button @click="showPreview = false" class="btn-secondary">取消</button>
        </div>
      </div>
    </Modal>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import * as XLSX from 'xlsx';
import { teacherApi } from '@/api/teacher';
import FileUploader from '@/components/common/FileUploader.vue';
import Modal from '@/components/common/Modal.vue';
import Layout from '@/components/Layout.vue';

const selectedFile = ref<File | null>(null);
const showPreview = ref(false);
const previewData = ref<any[]>([]);
const previewHeaders = ref<string[]>([]);

const exportParams = reactive({
  classId: '',
  startDate: '',
  endDate: '',
});

const exportFields = ref([
  { key: 'studentName', label: '学生姓名', selected: true },
  { key: 'studentId', label: '学号', selected: true },
  { key: 'className', label: '班级', selected: true },
  { key: 'score', label: '成绩', selected: true },
  { key: 'totalScore', label: '总分', selected: true },
  { key: 'percentage', label: '百分比', selected: true },
  { key: 'examTitle', label: '考试名称', selected: false },
  { key: 'recordedAt', label: '记录时间', selected: true },
  { key: 'comments', label: '备注', selected: false },
]);

const classes = ref<any[]>([]);

const handleFileSelected = (file: File) => {
  selectedFile.value = file;
  readExcelFile(file);
};

const readExcelFile = (file: File) => {
  const reader = new FileReader();
  reader.onload = (e) => {
    const data = new Uint8Array(e.target?.result as ArrayBuffer);
    const workbook = XLSX.read(data, { type: 'array' });
    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
    const jsonData = XLSX.utils.sheet_to_json(firstSheet);

    // 提取表头和数据
    previewHeaders.value = Object.keys(jsonData[0] || {});
    previewData.value = jsonData;
    showPreview.value = true;
  };
  reader.readAsArrayBuffer(file);
};

const confirmImport = async () => {
  if (previewData.value.length === 0 || !selectedFile.value) {
    alert('没有可导入的数据');
    return;
  }
  
  try {
    const response = await teacherApi.importScores(selectedFile.value);
    console.log('导入响应:', response);
    
    // 检查是否有错误信息
    if (response.errors && response.errors.length > 0) {
      // 部分成功或全部失败
      const errorCount = response.errors.length;
      const successCount = response.success_count || 0;
      
      // 显示错误详情
      const errorMessages = response.errors.slice(0, 10).join('\n'); // 最多显示10条错误
      const moreErrors = errorCount > 10 ? `\n\n...还有 ${errorCount - 10} 条错误` : '';
      
      const message = `导入完成！\n成功: ${successCount} 条\n错误: ${errorCount} 条\n\n错误详情：\n${errorMessages}${moreErrors}`;
      
      if (successCount > 0) {
        alert(message);
      } else {
        alert(`导入失败！\n错误: ${errorCount} 条\n\n错误详情：\n${errorMessages}${moreErrors}`);
      }
    } else {
      // 完全成功
      const successCount = response.success_count || 0;
      alert(`成绩导入成功！共导入 ${successCount} 条记录`);
    }
    
    showPreview.value = false;
    selectedFile.value = null;
    previewData.value = [];
    previewHeaders.value = [];
  } catch (error: any) {
    console.error('导入失败:', error);
    const errorMsg = error.response?.data?.message || error.message || '未知错误';
    alert('导入失败: ' + errorMsg);
  }
};

const exportToExcel = async () => {
  try {
    const params: any = {};
    if (exportParams.classId) params.class_id = exportParams.classId;
    if (exportParams.startDate) params.start_date = exportParams.startDate;
    if (exportParams.endDate) params.end_date = exportParams.endDate;
    
    const blob = await teacherApi.exportScores(params) as unknown as Blob;
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `成绩导出_${new Date().toISOString().split('T')[0]}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    alert('成绩导出成功！');
  } catch (error: any) {
    console.error('导出失败:', error);
    alert('导出失败: ' + (error.response?.data?.message || error.message));
  }
};

const downloadTemplate = async () => {
  console.log('downloadTemplate 函数被调用');
  try {
    console.log('开始下载模板...');
    const response = await teacherApi.downloadScoreTemplate();
    console.log('收到响应:', response);
    console.log('响应类型:', typeof response);
    console.log('是否为 Blob:', response instanceof Blob);
    
    // 确保 response 是 Blob
    let blob: Blob;
    if (response instanceof Blob) {
      blob = response;
    } else if (response && typeof response === 'object' && 'data' in response) {
      // 如果响应是 axios 响应对象
      blob = (response as any).data instanceof Blob 
        ? (response as any).data 
        : new Blob([(response as any).data], { 
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
          });
    } else {
      blob = new Blob([response as any], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
    }
    
    console.log('Blob 大小:', blob.size);
    
    if (blob.size === 0) {
      alert('下载失败：文件为空');
      return;
    }
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = '成绩导入模板.xlsx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    console.log('模板下载成功');
  } catch (error: any) {
    console.error('下载模板失败:', error);
    console.error('错误详情:', error.response);
    const errorMsg = error.response?.data?.message || error.message || '未知错误';
    alert('下载模板失败: ' + errorMsg);
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

onMounted(async () => {
  // 设置默认时间范围
  const now = new Date();
  const lastMonth = new Date();
  lastMonth.setMonth(lastMonth.getMonth() - 1);

  exportParams.startDate = lastMonth.toISOString().split('T')[0];
  exportParams.endDate = now.toISOString().split('T')[0];
  
  // 加载班级列表
  await loadClasses();
});
</script>

<style scoped>
.grade-importer {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.import-section,
.export-section {
  background: #ffffff;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  padding: 24px;
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #24292e;
}

.template-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f6f8fa;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  margin-bottom: 16px;
  color: #586069;
  font-size: 14px;
}

.template-notice i {
  color: #0366d6;
  font-size: 16px;
}

.drop-zone {
  border: 2px dashed #d1d5da;
  border-radius: 6px;
  padding: 48px;
  text-align: center;
  background: #fafbfc;
  transition: all 0.2s;
  cursor: pointer;
}

.drop-zone:hover {
  border-color: #0366d6;
  background: #f1f8ff;
}

.drop-zone.dragging {
  border-color: #0366d6;
  background: #e3f2fd;
}

.drop-zone i {
  color: #28a745;
  margin-bottom: 16px;
}

.drop-zone p {
  margin: 8px 0;
  color: #586069;
}

.drop-zone .hint {
  font-size: 12px;
  color: #959da5;
}

.file-preview {
  margin-top: 16px;
  padding: 12px;
  background: #f6f8fa;
  border-radius: 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.export-options {
  margin-bottom: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #24292e;
}

.form-group select,
.form-group input[type="date"] {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5da;
  border-radius: 6px;
  font-size: 14px;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 12px;
}

.field-selector {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
}

.field-selector label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: normal;
  cursor: pointer;
}

.btn-primary,
.btn-outline,
.btn-secondary {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-primary {
  background: #28a745;
  color: #ffffff;
  border-color: #28a745;
}

.btn-primary:hover {
  background: #22863a;
  border-color: #22863a;
}

.btn-outline {
  background: #ffffff;
  color: #0366d6;
  border-color: #d1d5da;
}

.btn-outline:hover {
  background: #f6f8fa;
  border-color: #0366d6;
}

.btn-secondary {
  background: #6c757d;
  color: #ffffff;
  border-color: #6c757d;
}

.btn-secondary:hover {
  background: #5a6268;
  border-color: #5a6268;
}

.preview-table {
  max-height: 500px;
  overflow: auto;
}

.preview-table table {
  width: 100%;
  border-collapse: collapse;
}

.preview-table th,
.preview-table td {
  padding: 8px 12px;
  border: 1px solid #e1e4e8;
  text-align: left;
}

.preview-table th {
  background: #f6f8fa;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.preview-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>