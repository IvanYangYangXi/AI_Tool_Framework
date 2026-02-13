"""
权限控制系统 - 提供插件执行的安全控制和访问管理
"""

import hashlib
import hmac
import jwt
import logging
import time
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """权限级别枚举"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class ResourceType(Enum):
    """资源类型枚举"""
    PLUGIN = "plugin"
    CONFIG = "config"
    FILE = "file"
    NETWORK = "network"


@dataclass
class Role:
    """角色定义"""
    name: str
    permissions: Dict[ResourceType, PermissionLevel] = field(default_factory=dict)
    description: str = ""


@dataclass
class User:
    """用户信息"""
    username: str
    roles: List[str] = field(default_factory=list)
    active: bool = True
    created_at: float = field(default_factory=time.time)


class PermissionSystem:
    """
    权限控制系统
    
    负责：
    - 基于角色的访问控制(RBAC)
    - 代码签名验证
    - 执行环境隔离
    - 审计日志记录
    """
    
    def __init__(self, secret_key: str = None, config_path: str = "./configs/security.json"):
        """
        初始化权限系统
        
        Args:
            secret_key: JWT密钥
            config_path: 安全配置文件路径
        """
        self.secret_key = secret_key or self._generate_secret_key()
        self.config_path = config_path
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self._setup_logging()
        self._load_configuration()
        self._setup_default_roles()
    
    def _setup_logging(self):
        """设置日志"""
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    def _generate_secret_key(self) -> str:
        """生成随机密钥"""
        return hashlib.sha256(str(time.time()).encode()).hexdigest()
    
    def _load_configuration(self):
        """加载安全配置"""
        print(f"DEBUG: 尝试加载配置文件: {self.config_path}")
        try:
            config_file = Path(self.config_path)
            print(f"DEBUG: 配置文件存在: {config_file.exists()}")
            
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"DEBUG: 加载的配置: {config}")
                
                # 加载角色配置
                for role_data in config.get('roles', []):
                    role = Role(
                        name=role_data['name'],
                        description=role_data.get('description', ''),
                        permissions={}
                    )
                    
                    # 解析权限
                    for perm_str in role_data.get('permissions', []):
                        if ':' in perm_str:
                            resource_str, level_str = perm_str.split(':', 1)
                            try:
                                resource_type = ResourceType(resource_str.lower())
                                permission_level = PermissionLevel(level_str.lower())
                                role.permissions[resource_type] = permission_level
                            except ValueError:
                                logger.warning(f"无效的权限定义: {perm_str}")
                    
                    self.roles[role.name] = role
                    print(f"DEBUG: 加载角色: {role.name}")
                
                # 加载用户配置
                for user_data in config.get('users', []):
                    user = User(
                        username=user_data['username'],
                        roles=user_data.get('roles', []),
                        active=user_data.get('active', True)
                    )
                    self.users[user.username] = user
                    print(f"DEBUG: 加载用户: {user.username}")
                    
                logger.info("安全配置加载成功")
                
            else:
                print("DEBUG: 配置文件不存在，使用默认配置")
                self._setup_default_configuration()
                
        except Exception as e:
            print(f"DEBUG: 加载配置异常: {e}")
            logger.error(f"加载安全配置失败: {e}")
            self._setup_default_configuration()
    
    def _setup_default_configuration(self):
        """设置默认配置"""
        # 默认角色
        admin_role = Role("admin", description="管理员角色")
        admin_role.permissions[ResourceType.PLUGIN] = PermissionLevel.ADMIN
        admin_role.permissions[ResourceType.CONFIG] = PermissionLevel.ADMIN
        admin_role.permissions[ResourceType.FILE] = PermissionLevel.ADMIN
        admin_role.permissions[ResourceType.NETWORK] = PermissionLevel.ADMIN
        
        user_role = Role("user", description="普通用户角色")
        user_role.permissions[ResourceType.PLUGIN] = PermissionLevel.EXECUTE
        user_role.permissions[ResourceType.CONFIG] = PermissionLevel.READ
        user_role.permissions[ResourceType.FILE] = PermissionLevel.READ
        
        guest_role = Role("guest", description="访客角色")
        guest_role.permissions[ResourceType.PLUGIN] = PermissionLevel.NONE
        guest_role.permissions[ResourceType.CONFIG] = PermissionLevel.READ
        
        self.roles.update({
            "admin": admin_role,
            "user": user_role,
            "guest": guest_role
        })
        
        # 默认用户
        self.users["admin"] = User("admin", roles=["admin"])
        self.users["default"] = User("default", roles=["user"])
        
        logger.info("默认安全配置已设置")
    
    def _setup_default_roles(self):
        """确保默认角色存在"""
        default_roles = {
            "admin": {
                ResourceType.PLUGIN: PermissionLevel.ADMIN,
                ResourceType.CONFIG: PermissionLevel.ADMIN,
                ResourceType.FILE: PermissionLevel.ADMIN,
                ResourceType.NETWORK: PermissionLevel.ADMIN
            },
            "developer": {
                ResourceType.PLUGIN: PermissionLevel.WRITE,
                ResourceType.CONFIG: PermissionLevel.WRITE,
                ResourceType.FILE: PermissionLevel.WRITE,
                ResourceType.NETWORK: PermissionLevel.READ
            },
            "user": {
                ResourceType.PLUGIN: PermissionLevel.EXECUTE,
                ResourceType.CONFIG: PermissionLevel.READ,
                ResourceType.FILE: PermissionLevel.READ,
                ResourceType.NETWORK: PermissionLevel.NONE
            }
        }
        
        for role_name, permissions in default_roles.items():
            if role_name not in self.roles:
                role = Role(role_name, description=f"默认{role_name}角色")
                role.permissions.update(permissions)
                self.roles[role_name] = role
    
    def authenticate_user(self, username: str, password: str = None) -> Optional[str]:
        """
        用户认证并生成JWT令牌
        
        Args:
            username: 用户名
            password: 密码（可选，简化实现）
            
        Returns:
            JWT令牌或None
        """
        print(f"DEBUG: 尝试认证用户: {username}")
        print(f"DEBUG: 当前用户列表: {list(self.users.keys())}")
        
        user = self.users.get(username)
        print(f"DEBUG: 用户对象: {user}")
        
        if not user or not user.active:
            logger.warning(f"用户认证失败: {username}")
            return None
        
        try:
            payload = {
                'username': username,
                'roles': user.roles,
                'exp': time.time() + 3600,  # 1小时过期
                'iat': time.time()
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')
            self._log_audit("AUTHENTICATION", username, f"用户 {username} 认证成功")
            return token
            
        except Exception as e:
            logger.error(f"生成JWT令牌失败: {e}")
            return None
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            令牌载荷或None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"JWT令牌无效: {e}")
            return None
    
    def check_permission(self, username: str, resource_type: ResourceType, 
                        required_level: PermissionLevel) -> bool:
        """
        检查用户权限
        
        Args:
            username: 用户名
            resource_type: 资源类型
            required_level: 所需权限级别
            
        Returns:
            是否有足够权限
        """
        user = self.users.get(username)
        if not user or not user.active:
            self._log_audit("PERMISSION_DENIED", username, 
                          f"用户 {username} 不存在或已禁用")
            return False
        
        # 获取用户的最高权限级别
        max_level = PermissionLevel.NONE
        for role_name in user.roles:
            role = self.roles.get(role_name)
            if role and resource_type in role.permissions:
                role_level = role.permissions[resource_type]
                if self._compare_permission_levels(role_level, max_level) > 0:
                    max_level = role_level
        
        has_permission = self._compare_permission_levels(max_level, required_level) >= 0
        
        if not has_permission:
            self._log_audit("PERMISSION_DENIED", username,
                          f"用户 {username} 对 {resource_type.value} 缺少 {required_level.value} 权限")
        
        return has_permission
    
    def _compare_permission_levels(self, level1: PermissionLevel, 
                                 level2: PermissionLevel) -> int:
        """
        比较权限级别
        
        Args:
            level1: 权限级别1
            level2: 权限级别2
            
        Returns:
            比较结果 (-1, 0, 1)
        """
        level_order = {
            PermissionLevel.NONE: 0,
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.EXECUTE: 3,
            PermissionLevel.ADMIN: 4
        }
        
        return level_order[level1] - level_order[level2]
    
    def verify_code_signature(self, code_content: str, signature: str, 
                            public_key: str = None) -> bool:
        """
        验证代码签名
        
        Args:
            code_content: 代码内容
            signature: 签名
            public_key: 公钥（简化实现）
            
        Returns:
            签名是否有效
        """
        try:
            # 简化的HMAC签名验证（实际项目中应使用RSA或其他非对称加密）
            expected_signature = hmac.new(
                self.secret_key.encode(),
                code_content.encode(),
                hashlib.sha256
            ).hexdigest()
            
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if not is_valid:
                logger.warning("代码签名验证失败")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"签名验证异常: {e}")
            return False
    
    def _log_audit(self, event_type: str, username: str, message: str):
        """
        记录审计日志
        
        Args:
            event_type: 事件类型
            username: 用户名
            message: 日志消息
        """
        audit_entry = {
            'timestamp': time.time(),
            'event_type': event_type,
            'username': username,
            'message': message
        }
        
        self.audit_log.append(audit_entry)
        
        # 保持日志大小限制
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-500:]
        
        logger.info(f"[AUDIT] {event_type} - {username}: {message}")
    
    def get_user_permissions(self, username: str) -> Dict[ResourceType, PermissionLevel]:
        """
        获取用户的完整权限映射
        
        Args:
            username: 用户名
            
        Returns:
            资源类型到权限级别的映射
        """
        user = self.users.get(username)
        if not user:
            return {}
        
        permissions = {}
        
        # 合并所有角色的权限，取最高等级
        for role_name in user.roles:
            role = self.roles.get(role_name)
            if role:
                for resource_type, level in role.permissions.items():
                    if (resource_type not in permissions or 
                        self._compare_permission_levels(level, permissions[resource_type]) > 0):
                        permissions[resource_type] = level
        
        return permissions
    
    def add_user(self, username: str, roles: List[str] = None, 
                active: bool = True) -> bool:
        """
        添加用户
        
        Args:
            username: 用户名
            roles: 角色列表
            active: 是否激活
            
        Returns:
            是否添加成功
        """
        if username in self.users:
            logger.warning(f"用户已存在: {username}")
            return False
        
        user = User(username, roles or [], active)
        self.users[username] = user
        
        self._log_audit("USER_CREATED", username, f"创建用户 {username}")
        return True
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取审计日志
        
        Args:
            limit: 返回条数限制
            
        Returns:
            审计日志列表
        """
        return self.audit_log[-limit:] if limit else self.audit_log.copy()


# 使用示例
if __name__ == "__main__":
    # 创建权限系统
    ps = PermissionSystem()
    
    # 用户认证
    token = ps.authenticate_user("admin")
    if token:
        print(f"认证成功，令牌: {token[:20]}...")
        
        # 验证令牌
        payload = ps.verify_token(token)
        if payload:
            print(f"令牌验证成功: {payload}")
            
            # 检查权限
            has_permission = ps.check_permission(
                "admin", 
                ResourceType.PLUGIN, 
                PermissionLevel.ADMIN
            )
            print(f"管理员权限检查: {has_permission}")