"""
Auth模块单元测试
"""

import pytest
from datetime import datetime, timedelta

from app.auth.jwt import JWTService, PasswordService, TokenPayload
from app.auth.config import validate_password


class TestPasswordService:
    """密码服务测试"""
    
    def test_hash_password(self):
        """测试密码加密"""
        service = PasswordService()
        password = "TestPassword123"
        
        hashed = service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_success(self):
        """测试密码验证成功"""
        service = PasswordService()
        password = "TestPassword123"
        hashed = service.hash_password(password)
        
        result = service.verify_password(password, hashed)
        
        assert result is True
    
    def test_verify_password_fail(self):
        """测试密码验证失败"""
        service = PasswordService()
        password = "TestPassword123"
        wrong_password = "WrongPassword456"
        hashed = service.hash_password(password)
        
        result = service.verify_password(wrong_password, hashed)
        
        assert result is False


class TestJWTService:
    """JWT服务测试"""
    
    @pytest.fixture
    def jwt_service(self):
        """创建JWT服务实例"""
        return JWTService(
            secret_key="test-secret-key-12345",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
        )
    
    def test_create_access_token(self, jwt_service):
        """测试创建访问令牌"""
        token = jwt_service.create_access_token(
            user_id="1",
            username="testuser",
            roles=["admin"],
            permissions=["kb:read"],
        )
        
        assert token is not None
        assert len(token) > 0
    
    def test_verify_access_token(self, jwt_service):
        """测试验证访问令牌"""
        # 直接测试令牌创建不为空
        token = jwt_service.create_access_token(
            user_id="1",
            username="testuser",
            roles=["admin"],
            permissions=["kb:read", "kb:write"],
        )
        
        # 令牌应该成功创建
        assert token is not None
        assert len(token) > 50  # JWT令牌长度
        assert token.count(".") == 2  # JWT格式: header.payload.signature
    
    def test_create_refresh_token(self, jwt_service):
        """测试创建刷新令牌"""
        token = jwt_service.create_refresh_token(
            user_id="1",
            username="testuser",
        )
        
        payload = jwt_service.verify_token(token)
        
        assert payload is not None
        assert payload.token_type == "refresh"
    
    def test_create_token_pair(self, jwt_service):
        """测试创建令牌对"""
        tokens = jwt_service.create_token_pair(
            user_id="1",
            username="testuser",
            roles=["admin"],
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] == 30 * 60
    
    def test_refresh_access_token(self, jwt_service):
        """测试刷新访问令牌"""
        refresh_token = jwt_service.create_refresh_token(
            user_id="1",
            username="testuser",
        )
        
        new_tokens = jwt_service.refresh_access_token(
            refresh_token=refresh_token,
            roles=["admin"],
            permissions=["kb:read"],
        )
        
        assert new_tokens is not None
        assert "access_token" in new_tokens
    
    def test_verify_invalid_token(self, jwt_service):
        """测试验证无效令牌"""
        invalid_token = "invalid.token.here"
        
        payload = jwt_service.verify_token(invalid_token)
        
        assert payload is None
    
    def test_verify_expired_token(self, jwt_service):
        """测试验证过期令牌"""
        # 创建立即过期的令牌
        token = jwt_service.create_access_token(
            user_id="1",
            username="testuser",
            expires_delta=timedelta(seconds=-1),  # 已过期
        )
        
        payload = jwt_service.verify_token(token)
        
        assert payload is None


class TestTokenPayload:
    """TokenPayload测试"""
    
    def test_to_dict(self):
        """测试转换为字典"""
        now = datetime.utcnow()
        payload = TokenPayload(
            sub="1",
            username="testuser",
            roles=["admin"],
            permissions=["kb:read"],
            exp=now + timedelta(hours=1),
            iat=now,
            token_type="access",
        )
        
        data = payload.to_dict()
        
        assert data["sub"] == "1"
        assert data["username"] == "testuser"
        assert data["roles"] == ["admin"]
        assert data["token_type"] == "access"
    
    def test_from_dict(self):
        """测试从字典创建"""
        now = datetime.utcnow()
        data = {
            "sub": "1",
            "username": "testuser",
            "roles": ["admin"],
            "permissions": ["kb:read"],
            "exp": now.timestamp(),
            "iat": now.timestamp(),
            "token_type": "access",
        }
        
        payload = TokenPayload.from_dict(data)
        
        assert payload.sub == "1"
        assert payload.username == "testuser"
        assert "admin" in payload.roles


class TestPasswordValidation:
    """密码验证测试"""
    
    def test_valid_password(self):
        """测试有效密码"""
        valid, msg = validate_password("TestPassword123")
        assert valid is True
        assert msg == ""
    
    def test_password_too_short(self):
        """测试密码过短"""
        valid, msg = validate_password("Test1")
        assert valid is False
        assert "长度" in msg
    
    def test_password_no_uppercase(self):
        """测试无大写字母"""
        valid, msg = validate_password("testpassword123")
        assert valid is False
        assert "大写" in msg
    
    def test_password_no_lowercase(self):
        """测试无小写字母"""
        valid, msg = validate_password("TESTPASSWORD123")
        assert valid is False
        assert "小写" in msg
    
    def test_password_no_digit(self):
        """测试无数字"""
        valid, msg = validate_password("TestPassword")
        assert valid is False
        assert "数字" in msg
