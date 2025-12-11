# -*- coding: utf-8 -*-
"""Group Chat Service"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import Database
from pymysql.cursors import DictCursor

group_chat_bp = Blueprint('group_chat', __name__)

def get_db_connection():
    return Database.get_connection()

def get_cursor(conn):
    return conn.cursor(DictCursor)

def get_current_user_id():
    """获取当前用户ID（转换为整数）"""
    return int(get_jwt_identity())


@group_chat_bp.route('/groups', methods=['GET'])
@jwt_required()
def get_my_groups():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT g.*, gm.role as my_role,
                   u.real_name as owner_name,
                   c.name as course_name,
                   cl.name as class_name,
                   (SELECT COUNT(*) FROM group_members WHERE group_id = g.id) as member_count
            FROM chat_groups g
            JOIN group_members gm ON g.id = gm.group_id AND gm.user_id = %s
            LEFT JOIN users u ON g.owner_id = u.user_id
            LEFT JOIN courses c ON g.course_id = c.id
            LEFT JOIN classes cl ON g.class_id = cl.id
            WHERE g.is_active = 1
            ORDER BY g.updated_at DESC
        """, (user_id,))
        
        groups = cursor.fetchall()
        return jsonify({'success': True, 'groups': groups})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@group_chat_bp.route('/groups', methods=['POST'])
@jwt_required()
def create_group():
    user_id = get_current_user_id()
    data = request.json
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT r.role_name as role FROM users u 
            JOIN roles r ON u.role_id = r.role_id 
            WHERE u.user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user or user['role'] not in ('teacher', 'admin'):
            return jsonify({'success': False, 'message': 'Only teachers can create groups'}), 403
        
        cursor.execute("""
            INSERT INTO chat_groups (name, description, owner_id, course_id, class_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['name'], data.get('description'), user_id, 
              data.get('course_id'), data.get('class_id')))
        
        group_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO group_members (group_id, user_id, role)
            VALUES (%s, %s, 'owner')
        """, (group_id, user_id))
        
        member_ids = data.get('member_ids', [])
        for member_id in member_ids:
            if member_id != user_id:
                cursor.execute("""
                    INSERT INTO group_members (group_id, user_id, role)
                    VALUES (%s, %s, 'member')
                """, (group_id, member_id))
        
        cursor.execute("""
            INSERT INTO group_messages (group_id, sender_id, message_type, content)
            VALUES (%s, %s, 'system', %s)
        """, (group_id, user_id, 'Group created'))
        
        conn.commit()
        return jsonify({'success': True, 'group_id': group_id, 'message': 'Group created'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@group_chat_bp.route('/groups/<int:group_id>', methods=['GET'])
@jwt_required()
def get_group_info(group_id):
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT role FROM group_members WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        member = cursor.fetchone()
        if not member:
            return jsonify({'success': False, 'message': 'Not a member'}), 403
        
        cursor.execute("""
            SELECT g.*, u.real_name as owner_name,
                   c.name as course_name, c.code as course_code,
                   cl.name as class_name
            FROM chat_groups g
            LEFT JOIN users u ON g.owner_id = u.user_id
            LEFT JOIN courses c ON g.course_id = c.id
            LEFT JOIN classes cl ON g.class_id = cl.id
            WHERE g.id = %s
        """, (group_id,))
        group = cursor.fetchone()
        
        cursor.execute("""
            SELECT gm.*, u.real_name, u.photo_url, u.system_account
            FROM group_members gm
            JOIN users u ON gm.user_id = u.user_id
            WHERE gm.group_id = %s
            ORDER BY FIELD(gm.role, 'owner', 'admin', 'member'), gm.joined_at
        """, (group_id,))
        members = cursor.fetchall()
        
        group['members'] = members
        group['my_role'] = member['role']
        
        return jsonify({'success': True, 'group': group})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@group_chat_bp.route('/groups/<int:group_id>/messages', methods=['GET'])
@jwt_required()
def get_group_messages(group_id):
    user_id = get_current_user_id()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT role FROM group_members WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Not a member'}), 403
        
        offset = (page - 1) * per_page
        cursor.execute("""
            SELECT gm.*, u.real_name as sender_name, u.photo_url as sender_avatar
            FROM group_messages gm
            JOIN users u ON gm.sender_id = u.user_id
            WHERE gm.group_id = %s AND gm.is_deleted = 0
            ORDER BY gm.created_at DESC
            LIMIT %s OFFSET %s
        """, (group_id, per_page, offset))
        
        messages = cursor.fetchall()
        messages.reverse()
        
        return jsonify({'success': True, 'messages': messages})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@group_chat_bp.route('/groups/<int:group_id>/members', methods=['POST'])
@jwt_required()
def add_members(group_id):
    user_id = get_current_user_id()
    data = request.json
    member_ids = data.get('member_ids', [])
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT role FROM group_members WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        member = cursor.fetchone()
        if not member or member['role'] not in ('owner', 'admin'):
            return jsonify({'success': False, 'message': 'No permission'}), 403
        
        added = []
        for mid in member_ids:
            try:
                cursor.execute("""
                    INSERT INTO group_members (group_id, user_id, role)
                    VALUES (%s, %s, 'member')
                """, (group_id, mid))
                cursor.execute("SELECT real_name FROM users WHERE user_id = %s", (mid,))
                new_member = cursor.fetchone()
                if new_member:
                    added.append(new_member['real_name'])
            except:
                pass
        
        if added:
            cursor.execute("""
                INSERT INTO group_messages (group_id, sender_id, message_type, content)
                VALUES (%s, %s, 'system', %s)
            """, (group_id, user_id, f'{", ".join(added)} joined'))
        
        conn.commit()
        return jsonify({'success': True, 'message': f'Added {len(added)} members'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@group_chat_bp.route('/groups/<int:group_id>/members/<int:member_id>', methods=['DELETE'])
@jwt_required()
def remove_member(group_id, member_id):
    user_id = get_current_user_id()
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT role FROM group_members WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        operator = cursor.fetchone()
        if not operator or operator['role'] not in ('owner', 'admin'):
            return jsonify({'success': False, 'message': 'No permission'}), 403
        
        cursor.execute("""
            SELECT gm.role, u.real_name FROM group_members gm
            JOIN users u ON gm.user_id = u.user_id
            WHERE gm.group_id = %s AND gm.user_id = %s
        """, (group_id, member_id))
        target = cursor.fetchone()
        
        if not target:
            return jsonify({'success': False, 'message': 'User not in group'}), 404
        
        if target['role'] == 'owner':
            return jsonify({'success': False, 'message': 'Cannot remove owner'}), 403
        
        cursor.execute("""
            DELETE FROM group_members WHERE group_id = %s AND user_id = %s
        """, (group_id, member_id))
        
        cursor.execute("""
            INSERT INTO group_messages (group_id, sender_id, message_type, content)
            VALUES (%s, %s, 'system', %s)
        """, (group_id, user_id, f'{target["real_name"]} was removed'))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Member removed'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@group_chat_bp.route('/groups/<int:group_id>/leave', methods=['POST'])
@jwt_required()
def leave_group(group_id):
    user_id = get_current_user_id()
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT gm.role, u.real_name FROM group_members gm
            JOIN users u ON gm.user_id = u.user_id
            WHERE gm.group_id = %s AND gm.user_id = %s
        """, (group_id, user_id))
        member = cursor.fetchone()
        
        if not member:
            return jsonify({'success': False, 'message': 'Not in group'}), 404
        
        if member['role'] == 'owner':
            return jsonify({'success': False, 'message': 'Owner cannot leave'}), 403
        
        cursor.execute("""
            DELETE FROM group_members WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        
        cursor.execute("""
            INSERT INTO group_messages (group_id, sender_id, message_type, content)
            VALUES (%s, %s, 'system', %s)
        """, (group_id, user_id, f'{member["real_name"]} left'))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Left group'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@group_chat_bp.route('/courses/my', methods=['GET'])
@jwt_required()
def get_my_courses():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT r.role_name as role FROM users u 
            JOIN roles r ON u.role_id = r.role_id 
            WHERE u.user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        
        if user and user['role'] == 'teacher':
            cursor.execute("""
                SELECT c.* FROM courses c
                WHERE c.teacher_id = %s AND c.is_active = 1
                UNION
                SELECT c.* FROM courses c
                JOIN course_teachers ct ON c.id = ct.course_id
                WHERE ct.teacher_id = %s AND c.is_active = 1
            """, (user_id, user_id))
        else:
            cursor.execute("SELECT c.* FROM courses c WHERE c.is_active = 1")
        
        courses = cursor.fetchall()
        return jsonify({'success': True, 'courses': courses})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@group_chat_bp.route('/courses/<int:course_id>/students', methods=['GET'])
@jwt_required()
def get_course_students(course_id):
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT DISTINCT u.user_id, u.real_name, u.photo_url, u.system_account, u.email
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE r.role_name = 'student'
            ORDER BY u.real_name
            LIMIT 50
        """)
        
        students = cursor.fetchall()
        return jsonify({'success': True, 'students': students})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@group_chat_bp.route('/classes/my', methods=['GET'])
@jwt_required()
def get_my_classes():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT r.role_name as role FROM users u 
            JOIN roles r ON u.role_id = r.role_id 
            WHERE u.user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        
        if user and user['role'] == 'teacher':
            cursor.execute("SELECT * FROM classes WHERE teacher_id = %s AND is_active = 1", (user_id,))
        else:
            cursor.execute("SELECT * FROM classes WHERE is_active = 1")
        
        classes = cursor.fetchall()
        return jsonify({'success': True, 'classes': classes})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@group_chat_bp.route('/users/search', methods=['GET'])
@jwt_required()
def search_users_for_group():
    keyword = request.args.get('keyword', '')
    if len(keyword) < 2:
        return jsonify({'success': True, 'users': []})
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT user_id, real_name, photo_url, system_account, email
            FROM users
            WHERE (real_name LIKE %s OR system_account LIKE %s OR email LIKE %s)
            AND is_active = 1
            LIMIT 20
        """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
        
        users = cursor.fetchall()
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@group_chat_bp.route('/groups/<int:group_id>/send-notice', methods=['POST'])
@jwt_required()
def send_group_notice(group_id):
    user_id = get_current_user_id()
    data = request.json
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT role FROM group_members WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        member = cursor.fetchone()
        if not member or member['role'] not in ('owner', 'admin'):
            return jsonify({'success': False, 'message': 'No permission'}), 403
        
        cursor.execute("""
            INSERT INTO group_messages (group_id, sender_id, message_type, content)
            VALUES (%s, %s, 'notice', %s)
        """, (group_id, user_id, data['content']))
        
        message_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute("""
            SELECT gm.*, u.real_name as sender_name, u.photo_url as sender_avatar
            FROM group_messages gm
            JOIN users u ON gm.sender_id = u.user_id
            WHERE gm.id = %s
        """, (message_id,))
        message = cursor.fetchone()
        
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@group_chat_bp.route('/groups/<int:group_id>/checkin-notify', methods=['POST'])
@jwt_required()
def notify_checkin(group_id):
    user_id = get_current_user_id()
    data = request.json
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT role FROM group_members WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        member = cursor.fetchone()
        if not member or member['role'] not in ('owner', 'admin'):
            return jsonify({'success': False, 'message': 'No permission'}), 403
        
        cursor.execute("""
            INSERT INTO group_messages (group_id, sender_id, message_type, content, reference_id, reference_type)
            VALUES (%s, %s, 'checkin', %s, %s, 'checkin')
        """, (group_id, user_id, data.get('content', 'Checkin started'), data.get('checkin_id')))
        
        message_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute("""
            SELECT gm.*, u.real_name as sender_name
            FROM group_messages gm
            JOIN users u ON gm.sender_id = u.user_id
            WHERE gm.id = %s
        """, (message_id,))
        message = cursor.fetchone()
        
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()



@group_chat_bp.route('/groups/<int:group_id>/dissolve', methods=['DELETE'])
@jwt_required()
def dissolve_group(group_id):
    """解散群聊（仅群主可操作）"""
    user_id = get_current_user_id()
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        # 检查是否是群主
        cursor.execute("""
            SELECT role FROM group_members WHERE group_id = %s AND user_id = %s
        """, (group_id, user_id))
        member = cursor.fetchone()
        
        if not member or member['role'] != 'owner':
            return jsonify({'success': False, 'message': '只有群主可以解散群聊'}), 403
        
        # 禁用外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # 删除已读记录（如果表存在）
        try:
            cursor.execute("DELETE FROM group_message_reads WHERE group_id = %s", (group_id,))
        except:
            pass
        
        # 删除群消息
        cursor.execute("DELETE FROM group_messages WHERE group_id = %s", (group_id,))
        
        # 删除群成员
        cursor.execute("DELETE FROM group_members WHERE group_id = %s", (group_id,))
        
        # 删除群组
        cursor.execute("DELETE FROM chat_groups WHERE id = %s", (group_id,))
        
        # 恢复外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        conn.commit()
        return jsonify({'success': True, 'message': '群聊已解散'})
    except Exception as e:
        conn.rollback()
        print(f"解散群聊错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
