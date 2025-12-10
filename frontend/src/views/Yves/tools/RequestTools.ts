// 后端 API 基础地址
const BASE_URL = 'http://192.168.95.26:5000/api';

// 请求配置接口
interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: any;
  params?: Record<string, any>;
}

// 响应接口
interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
  [key: string]: any;
}

/**
 * 构建 URL 查询参数
 */
function buildQueryString(params: Record<string, any>): string {
  const query = Object.entries(params)
    .filter(([_, value]) => value !== undefined && value !== null)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&');
  return query ? `?${query}` : '';
}

/**
 * 通用请求方法
 * @param endpoint API 端点（如 '/material/get-course-root-node-id'）
 * @param config 请求配置
 * @returns Promise<ApiResponse>
 */
async function request<T = any>(
  endpoint: string,
  config: RequestConfig = {}
): Promise<ApiResponse<T>> {
  const {
    method = 'GET',
    headers = {},
    body,
    params
  } = config;

  // 构建完整 URL
  let url = `${BASE_URL}${endpoint}`;
  if (params && method === 'GET') {
    url += buildQueryString(params);
  }

  // 构建请求选项
  const options: RequestInit = {
    method,
    headers: {
      ...headers
    }
  };

  // 添加请求体和 Content-Type（仅对有 body 的请求）
  if (body && method !== 'GET') {
    options.headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, options);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `请求失败: ${response.status}`);
    }

    return data;
  } catch (error) {
    console.error('请求错误:', error);
    throw error;
  }
}

/**
 * GET 请求
 */
async function get<T = any>(
  endpoint: string,
  params?: Record<string, any>
): Promise<ApiResponse<T>> {
  return request<T>(endpoint, { method: 'GET', params });
}

/**
 * POST 请求
 */
async function post<T = any>(
  endpoint: string,
  body?: any
): Promise<ApiResponse<T>> {
  return request<T>(endpoint, { method: 'POST', body });
}

/**
 * PUT 请求
 */
async function put<T = any>(
  endpoint: string,
  body?: any
): Promise<ApiResponse<T>> {
  return request<T>(endpoint, { method: 'PUT', body });
}

/**
 * DELETE 请求
 */
async function del<T = any>(
  endpoint: string,
  body?: any
): Promise<ApiResponse<T>> {
  return request<T>(endpoint, { method: 'DELETE', body });
}

export default {
  request,
  get,
  post,
  put,
  delete: del,
  BASE_URL
};
