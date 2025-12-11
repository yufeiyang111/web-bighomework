import request from '@/utils/request'

// 创建签到
export const createCheckin = (data) => {
  return request({
    url: '/checkin/create',
    method: 'post',
    data
  })
}

// 获取签到详情
export const getCheckinDetail = (checkinId) => {
  return request({
    url: `/checkin/${checkinId}`,
    method: 'get'
  })
}

// 获取签到二维码数据
export const getCheckinQrcode = (checkinId) => {
  return request({
    url: `/checkin/${checkinId}/qrcode`,
    method: 'get'
  })
}

// 学生签到
export const doCheckin = (data) => {
  return request({
    url: '/checkin/do',
    method: 'post',
    data
  })
}

// 获取签到记录（已签到/未签到）
export const getCheckinRecords = (checkinId) => {
  return request({
    url: `/checkin/${checkinId}/records`,
    method: 'get'
  })
}

// 获取进行中的签到
export const getActiveCheckins = () => {
  return request({
    url: '/checkin/active',
    method: 'get'
  })
}

// 获取我创建的签到
export const getMyCreatedCheckins = () => {
  return request({
    url: '/checkin/my-created',
    method: 'get'
  })
}

// 获取我的签到历史
export const getMyCheckinHistory = () => {
  return request({
    url: '/checkin/history',
    method: 'get'
  })
}

// 结束签到
export const endCheckin = (checkinId) => {
  return request({
    url: `/checkin/${checkinId}/end`,
    method: 'post'
  })
}

// 人脸签到
export const faceCheckin = (data) => {
  return request({
    url: '/checkin/face',
    method: 'post',
    data
  })
}

// 手势签到
export const gestureCheckin = (data) => {
  return request({
    url: '/checkin/gesture',
    method: 'post',
    data
  })
}

// 位置签到
export const locationCheckin = (data) => {
  return request({
    url: '/checkin/location',
    method: 'post',
    data
  })
}

// 智能点到（上传班级合照）
export const smartCheckin = (data) => {
  return request({
    url: '/checkin/smart-checkin',
    method: 'post',
    data
  })
}
