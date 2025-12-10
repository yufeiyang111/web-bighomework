import baseInfoTools from './BaseInfoTools';
import requestTools from './RequestTools';

export interface MaterialItem {
    id: number
    name: string
    type: 'file' | 'folder'
    fileType?: string
    creator?: string
    updatedAt?: string
    size?: string | number
    path?: string
    node_id?: number
    parent_node_id?: number
    created_at?: string
    updated_at?: string
}

/**
 * 通过课程名称获取根节点ID
 * @param courseName 课程名称
 * @returns Promise<number> 节点ID
 */
async function getCourseRootNodeId(courseName: string): Promise<number> {
    const response = await requestTools.get('/material/get-course-root-node-id', {
        name: courseName
    });
    return response.node_id;
}

/**
 * 获取指定节点的子节点列表
 * @param nodeId 父节点ID
 * @returns Promise<MaterialItem[]> 子节点列表
 */
async function getNextDepthTree(nodeId: number): Promise<MaterialItem[]> {
    const response = await requestTools.get('/material/get-next-depth-tree', {
        node_id: nodeId
    });
    return response.data || [];
}

/**
 * 添加节点
 * @param nodeData 节点数据
 * @returns Promise<number> 新节点ID
 */
async function addNode(nodeData: {
    name: string;
    path: string;
    type: 'file' | 'folder';
    size?: number;
    parent_node_id: number;
}): Promise<number> {
    const response = await requestTools.post('/material/add-node', nodeData);
    return response.node_id;
}

/**
 * 删除节点
 * @param nodeId 节点ID
 * @returns Promise<boolean> 是否成功
 */
async function deleteNode(nodeId: number): Promise<boolean> {
    const response = await requestTools.post('/material/delete-node', {
        node_id: nodeId
    });
    return response.success;
}

/**
 * 批量删除节点
 * @param nodeIds 节点ID数组
 * @returns Promise<{deleted_count: number, failed_count: number}> 删除结果
 */
async function deleteBatch(nodeIds: number[]): Promise<{deleted_count: number, failed_count: number}> {
    const response = await requestTools.post('/material/delete-batch', {
        node_ids: nodeIds
    });
    return {
        deleted_count: response.deleted_count || 0,
        failed_count: response.failed_count || 0
    };
}

/**
 * 添加课程根目录
 * @param name 课程名称
 * @param path 路径（默认 '/'）
 * @returns Promise<number> 新节点ID
 */
async function addCourseRoot(name: string, path: string = '/'): Promise<number> {
    const response = await requestTools.post('/material/add-course-root', {
        name,
        path
    });
    return response.node_id;
}

/**
 * 删除课程根目录
 * @param name 课程名称
 * @returns Promise<boolean> 是否成功
 */
async function deleteCourseRoot(name: string): Promise<boolean> {
    const response = await requestTools.post('/material/delete-course-root', {
        name
    });
    return response.success;
}

/**
 * 上传文件
 * @param file 文件对象
 * @param parentNodeId 父节点ID
 * @param path 文件路径
 * @returns Promise<number> 新节点ID
 */
async function uploadFile(file: File, parentNodeId: number, path: string): Promise<number> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('parent_node_id', parentNodeId.toString());
    formData.append('path', path);

    const response = await fetch(`${requestTools.BASE_URL}/material/upload-file`, {
        method: 'POST',
        body: formData
    });

    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.error || '上传失败');
    }

    return data.node_id;
}

/**
 * 下载单个文件
 * @param nodeId 节点ID
 * @param fileName 文件名
 */
async function downloadFile(nodeId: number, fileName: string): Promise<void> {
    const url = `${requestTools.BASE_URL}/material/download-file/${nodeId}`;
    
    // 创建隐藏的 a 标签触发下载
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * 批量下载文件
 * @param nodeIds 节点ID数组
 */
async function downloadBatch(nodeIds: number[]): Promise<void> {
    // 直接使用 fetch 处理二进制响应（ZIP 文件）
    const url = `${requestTools.BASE_URL}/material/download-batch`;
    
    const res = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ node_ids: nodeIds })
    });
    
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({ error: '批量下载失败' }));
        throw new Error(errorData.error || '批量下载失败');
    }
    
    // 获取文件 blob
    const blob = await res.blob();
    
    // 创建下载链接
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = '批量下载.zip';
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // 释放 URL 对象
    window.URL.revokeObjectURL(downloadUrl);
}

export default {
    getCourseRootNodeId,
    getNextDepthTree,
    addNode,
    deleteNode,
    deleteBatch,
    addCourseRoot,
    deleteCourseRoot,
    uploadFile,
    downloadFile,
    downloadBatch
};