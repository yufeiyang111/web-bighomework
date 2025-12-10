import requestTools from './RequestTools';

export interface ClassificationResult {
    success: boolean
    node_id: number
    total_files: number
    classification: Record<string, {
        count: number
        files: Array<{
            node_id: number
            name: string
            size: number | string
        }>
    }>
    files: Array<{
        node_id: number
        name: string
        category: string
    }>
}

export interface OrganizeResult {
    success: boolean
    message: string
    organized_count: number
    categories: string[]
    category_folders: Record<string, number>
}

export interface Category {
    name: string
    extensions: string[]
    keywords: string[]
}

/**
 * 对单个文件进行分类
 * @param filename 文件名
 * @returns Promise<{success: boolean, filename: string, category: string}>
 */
async function classifyFile(filename: string): Promise<{success: boolean, filename: string, category: string}> {
    const response = await requestTools.post('/classify/classify-file', {
        filename
    });
    return response;
}

/**
 * 对指定节点下的所有文件进行分类分析
 * @param nodeId 节点ID
 * @returns Promise<ClassificationResult>
 */
async function classifyNode(nodeId: number): Promise<ClassificationResult> {
    const response = await requestTools.post('/classify/classify-node', {
        node_id: nodeId
    });
    return response;
}

/**
 * 自动整理：在指定节点下创建分类文件夹并移动文件
 * @param nodeId 节点ID
 * @param createFolders 是否创建分类文件夹
 * @returns Promise<OrganizeResult>
 */
async function autoOrganize(nodeId: number, createFolders: boolean = true): Promise<OrganizeResult> {
    const response = await requestTools.post('/classify/auto-organize', {
        node_id: nodeId,
        create_folders: createFolders
    });
    return response;
}

/**
 * 为文件建议分类（批量）
 * @param filenames 文件名列表
 * @returns Promise<Array<{filename: string, category: string}>>
 */
async function suggestCategories(filenames: string[]): Promise<Array<{filename: string, category: string}>> {
    const response = await requestTools.post('/classify/suggest-categories', {
        filenames
    });
    return response.suggestions || [];
}

/**
 * 获取所有可用的分类类别
 * @returns Promise<Category[]>
 */
async function getCategories(): Promise<Category[]> {
    const response = await requestTools.get('/classify/get-categories');
    return response.categories || [];
}

/**
 * 获取所有标签
 * @returns Promise<{success: boolean, tags: any[]}>
 */
async function getTags(): Promise<{success: boolean, tags: any[]}> {
    const response = await requestTools.get('/classify/tags');
    return response;
}

/**
 * 创建新标签
 * @param tag 标签信息
 * @returns Promise<{success: boolean, tag_id: number}>
 */
async function createTag(tag: {name: string, color: string, description: string}): Promise<{success: boolean, tag_id: number}> {
    const response = await requestTools.post('/classify/tags', tag);
    return response;
}

/**
 * 更新标签
 * @param tagId 标签ID
 * @param tag 标签信息
 * @returns Promise<{success: boolean}>
 */
async function updateTag(tagId: number, tag: any): Promise<{success: boolean}> {
    const response = await requestTools.put(`/classify/tags/${tagId}`, tag);
    return response;
}

/**
 * 删除标签
 * @param tagId 标签ID
 * @returns Promise<{success: boolean}>
 */
async function deleteTag(tagId: number): Promise<{success: boolean}> {
    const response = await requestTools.delete(`/classify/tags/${tagId}`);
    return response;
}

/**
 * 保存文件分类
 * @param data 分类数据
 * @returns Promise<{success: boolean, count: number}>
 */
async function saveClassifications(data: {classifications: any[], classified_by: string}): Promise<{success: boolean, count: number}> {
    const response = await requestTools.post('/classify/classify-files', data);
    return response;
}

/**
 * 保存AI分类结果
 * @param data AI分类数据
 * @returns Promise<{success: boolean, count: number}>
 */
async function saveAIClassifications(data: {classifications: any[], classified_by: string}): Promise<{success: boolean, count: number}> {
    const response = await requestTools.post('/classify/save-ai-classifications', data);
    return response;
}

/**
 * 获取文件的AI分类结果
 * @param nodeId 文件节点ID
 * @returns Promise<{success: boolean, classification: any}>
 */
async function getAIClassification(nodeId: number): Promise<{success: boolean, classification: any}> {
    const response = await requestTools.get(`/classify/get-ai-classification/${nodeId}`);
    return response;
}

/**
 * 获取文件的分类标签
 * @param nodeId 文件节点ID
 * @returns Promise<{success: boolean, classifications: any[]}>
 */
async function getFileClassifications(nodeId: number): Promise<{success: boolean, classifications: any[]}> {
    const response = await requestTools.get(`/classify/file-classifications/${nodeId}`);
    return response;
}

/**
 * 获取节点下所有文件的分类情况
 * @param nodeId 节点ID
 * @returns Promise<{success: boolean, files: any[]}>
 */
async function getNodeClassifications(nodeId: number): Promise<{success: boolean, files: any[]}> {
    const response = await requestTools.get(`/classify/node-classifications/${nodeId}`);
    return response;
}

/**
 * 移除文件的分类标签
 * @param nodeId 文件节点ID
 * @param tagId 标签ID（可选，不传则移除所有标签）
 * @returns Promise<{success: boolean}>
 */
async function removeClassification(nodeId: number, tagId?: number): Promise<{success: boolean}> {
    const response = await requestTools.post('/classify/remove-classification', {
        node_id: nodeId,
        tag_id: tagId
    });
    return response;
}

export default {
    classifyFile,
    classifyNode,
    autoOrganize,
    suggestCategories,
    getCategories,
    getTags,
    createTag,
    updateTag,
    deleteTag,
    saveClassifications,
    getFileClassifications,
    getNodeClassifications,
    removeClassification,
    saveAIClassifications,
    getAIClassification
};
