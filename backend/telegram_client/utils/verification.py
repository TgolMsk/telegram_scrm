from django.utils import timezone
from telegram_client.models import VerificationCode
from asgiref.sync import sync_to_async
from django.db import transaction

class CodeManager:
    @staticmethod
    @sync_to_async
    def create_code(phone: str, code: str, expires_minutes=5):
        """异步创建验证码"""
        expires_at = timezone.now() + timezone.timedelta(minutes=expires_minutes)
        return VerificationCode.objects.create(
            phone=phone,
            code=code,
            expires_at=expires_at
        )

    @staticmethod
    @sync_to_async
    def get_valid_code(phone: str):
        """事务中获取有效验证码"""
        with transaction.atomic():
            # 使用 select_for_update 锁定记录
            return VerificationCode.objects.select_for_update().filter(
                phone=phone,
                is_used=False,
                expires_at__gt=timezone.now()
            ).order_by('expires_at').first()

    @staticmethod
    @sync_to_async
    def mark_used(code_id: int):
        """事务中标记为已使用"""
        with transaction.atomic():
            VerificationCode.objects.filter(id=code_id).update(is_used=True)

    @staticmethod
    @sync_to_async
    def clean_expired_codes():
        """清理过期验证码"""
        VerificationCode.objects.filter(
            expires_at__lte=timezone.now()
        ).delete()
