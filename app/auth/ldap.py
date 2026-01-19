"""
LDAP认证服务
支持LDAP和Active Directory
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from app.config import settings


class LDAPService:
    """LDAP认证服务"""
    
    def __init__(
        self,
        server_url: str = None,
        base_dn: str = None,
        user_search_base: str = None,
        user_filter: str = None,
        bind_dn: str = None,
        bind_password: str = None,
    ):
        self.server_url = server_url or settings.ldap_server
        self.base_dn = base_dn or settings.ldap_base_dn
        self.user_search_base = user_search_base or settings.ldap_user_search_base
        self.user_filter = user_filter or settings.ldap_user_filter or "(uid={username})"
        self.bind_dn = bind_dn or settings.ldap_bind_dn
        self.bind_password = bind_password or settings.ldap_bind_password
        self._connection = None
    
    def _get_connection(self):
        """获取LDAP连接"""
        try:
            from ldap3 import Server, Connection, ALL
            
            server = Server(self.server_url, get_info=ALL)
            
            if self.bind_dn and self.bind_password:
                conn = Connection(
                    server,
                    user=self.bind_dn,
                    password=self.bind_password,
                    auto_bind=True,
                )
            else:
                conn = Connection(server, auto_bind=True)
            
            return conn
            
        except ImportError:
            raise RuntimeError("ldap3未安装，请执行: pip install ldap3")
    
    async def authenticate(
        self,
        username: str,
        password: str,
    ) -> Optional[Dict[str, Any]]:
        """LDAP认证"""
        try:
            from ldap3 import Server, Connection, ALL
            
            # 1. 使用管理账号搜索用户
            conn = self._get_connection()
            
            # 构建搜索过滤器
            search_filter = self.user_filter.replace("{username}", username)
            search_base = self.user_search_base or self.base_dn
            
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                attributes=["cn", "sn", "givenName", "mail", "uid", "memberOf"],
            )
            
            if not conn.entries:
                logger.warning(f"LDAP用户不存在: {username}")
                return None
            
            user_entry = conn.entries[0]
            user_dn = user_entry.entry_dn
            
            # 2. 使用用户DN和密码验证
            server = Server(self.server_url, get_info=ALL)
            user_conn = Connection(server, user=user_dn, password=password)
            
            if not user_conn.bind():
                logger.warning(f"LDAP密码验证失败: {username}")
                return None
            
            user_conn.unbind()
            
            # 3. 提取用户信息
            user_info = {
                "username": username,
                "dn": user_dn,
                "display_name": str(user_entry.cn) if hasattr(user_entry, "cn") else username,
                "email": str(user_entry.mail) if hasattr(user_entry, "mail") else None,
                "groups": [],
            }
            
            # 提取组信息
            if hasattr(user_entry, "memberOf"):
                for group_dn in user_entry.memberOf:
                    # 提取CN
                    cn_part = str(group_dn).split(",")[0]
                    if cn_part.startswith("CN=") or cn_part.startswith("cn="):
                        user_info["groups"].append(cn_part[3:])
            
            logger.info(f"LDAP认证成功: {username}")
            return user_info
            
        except Exception as e:
            logger.error(f"LDAP认证失败: {e}")
            return None
    
    async def get_user_groups(self, user_dn: str) -> List[str]:
        """获取用户所属组"""
        try:
            conn = self._get_connection()
            
            conn.search(
                search_base=user_dn,
                search_filter="(objectClass=*)",
                attributes=["memberOf"],
            )
            
            if not conn.entries:
                return []
            
            groups = []
            entry = conn.entries[0]
            if hasattr(entry, "memberOf"):
                for group_dn in entry.memberOf:
                    cn_part = str(group_dn).split(",")[0]
                    if cn_part.startswith("CN=") or cn_part.startswith("cn="):
                        groups.append(cn_part[3:])
            
            return groups
            
        except Exception as e:
            logger.error(f"获取LDAP组失败: {e}")
            return []
    
    async def search_users(
        self,
        keyword: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """搜索LDAP用户"""
        try:
            conn = self._get_connection()
            
            search_base = self.user_search_base or self.base_dn
            search_filter = f"(|(uid=*{keyword}*)(cn=*{keyword}*)(mail=*{keyword}*))"
            
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                attributes=["cn", "uid", "mail"],
                size_limit=limit,
            )
            
            users = []
            for entry in conn.entries:
                users.append({
                    "username": str(entry.uid) if hasattr(entry, "uid") else "",
                    "display_name": str(entry.cn) if hasattr(entry, "cn") else "",
                    "email": str(entry.mail) if hasattr(entry, "mail") else "",
                })
            
            return users
            
        except Exception as e:
            logger.error(f"搜索LDAP用户失败: {e}")
            return []


class SSOService:
    """SSO单点登录服务"""
    
    def __init__(
        self,
        sso_url: str = None,
        client_id: str = None,
        client_secret: str = None,
    ):
        self.sso_url = sso_url or settings.sso_url
        self.client_id = client_id or settings.sso_client_id
        self.client_secret = client_secret or settings.sso_client_secret
    
    async def get_login_url(self, redirect_uri: str) -> str:
        """获取SSO登录URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid profile email",
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.sso_url}/authorize?{query_string}"
    
    async def exchange_token(
        self,
        code: str,
        redirect_uri: str,
    ) -> Optional[Dict[str, Any]]:
        """交换授权码获取令牌"""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.sso_url}/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"SSO Token交换失败: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"SSO Token交换失败: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """获取SSO用户信息"""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.sso_url}/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"获取SSO用户信息失败: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取SSO用户信息失败: {e}")
            return None


# 创建全局服务实例
ldap_service = LDAPService()
sso_service = SSOService()
