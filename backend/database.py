import pymysql
from pymysql.cursors import DictCursor
from config import Config

class Database:
    """数据库连接类"""
    
    @staticmethod
    def get_connection():
        """获取数据库连接"""
        return pymysql.connect(
            host=Config.DB_CONFIG['host'],
            port=Config.DB_CONFIG['port'],
            user=Config.DB_CONFIG['user'],
            password=Config.DB_CONFIG['password'],
            database=Config.DB_CONFIG['database'],
            charset=Config.DB_CONFIG['charset'],
            cursorclass=DictCursor
        )
    
    @staticmethod
    def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
        """
        执行SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            fetch_one: 是否返回单条结果
            fetch_all: 是否返回所有结果
            commit: 是否提交事务
        
        Returns:
            查询结果或影响的行数
        """
        connection = None
        try:
            connection = Database.get_connection()
            with connection.cursor() as cursor:
                cursor.execute(query, params or ())
                
                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                elif commit:
                    connection.commit()
                    result = cursor.lastrowid if cursor.lastrowid else cursor.rowcount
                else:
                    result = cursor.rowcount
                
                return result
        except Exception as e:
            if connection and commit:
                connection.rollback()
            raise e
        finally:
            if connection:
                connection.close()
