import request from '@/utils/request'

// 获取我的群组列表
export const getMyGroups = () => {
  return request({
    url: '/group-chat/groups',
    method: 'get'
  })
}

// 创建群组
export const createGroup = (data) => {
  return request({
    url: '/group-chat/groups',
    method: 'post',
    data
  })
}

// 获取群组详情
export const getGroupInfo = (groupId) => {
  return request({
    url: `/group-chat/groups/${groupId}`,
    method: 'get'
  })
}

// 获取群消息
export const getGroupMessages = (groupId, page = 1) => {
  return request({
    url: `/group-chat/groups/${groupId}/messages`,
    method: 'get',
    params: { page }
  })
}

// 添加群成员
export const addGroupMembers = (groupId, memberIds) => {
  return request({
    url: `/group-chat/groups/${groupId}/members`,
    method: 'post',
    data: { member_ids: memberIds }
  })
}

// 移除群成员
export const removeGroupMember = (groupId, memberId) => {
  return request({
    url: `/group-chat/groups/${groupId}/members/${memberId}`,
    method: 'delete'
  })
}

// 退出群组
export const leaveGroup = (groupId) => {
  return request({
    url: `/group-chat/groups/${groupId}/leave`,
    method: 'post'
  })
}

// 解散群组（仅群主）
export const dissolveGroup = (groupId) => {
  return request({
    url: `/group-chat/groups/${groupId}/dissolve`,
    method: 'delete'
  })
}

// 获取我的课程
export const getMyCourses = () => {
  return request({
    url: '/group-chat/courses/my',
    method: 'get'
  })
}

// 获取课程学生
export const getCourseStudents = (courseId) => {
  return request({
    url: `/group-chat/courses/${courseId}/students`,
    method: 'get'
  })
}

// 获取我的班级
export const getMyClasses = () => {
  return request({
    url: '/group-chat/classes/my',
    method: 'get'
  })
}

// 获取班级学生
export const getClassStudents = (classId) => {
  return request({
    url: `/group-chat/classes/${classId}/students`,
    method: 'get'
  })
}

// 搜索用户
export const searchUsersForGroup = (keyword) => {
  return request({
    url: '/group-chat/users/search',
    method: 'get',
    params: { keyword }
  })
}

// 发送群公告
export const sendGroupNotice = (groupId, content) => {
  return request({
    url: `/group-chat/groups/${groupId}/send-notice`,
    method: 'post',
    data: { content }
  })
}

// 发送签到通知到群
export const notifyGroupCheckin = (groupId, checkinId, content) => {
  return request({
    url: `/group-chat/groups/${groupId}/checkin-notify`,
    method: 'post',
    data: { checkin_id: checkinId, content }
  })
}
