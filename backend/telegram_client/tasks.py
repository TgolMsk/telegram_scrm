import asyncio

from asgiref.sync import sync_to_async
from celery import shared_task
from django.core.cache import cache
import logging
from celery.utils.log import get_task_logger
from telegram_client.utils.verification import CodeManager
from django.core.management import call_command
logger = logging.getLogger(__name__)

# 增强启动任务start_listener.delay(data.phone_number)
# @shared_task
# def start_listener(phone: str):
#     """增强版监听器启动任务"""
#     try:
#         # 初始化验证码状态 清理缓存的验证码数据
#         cache.delete(f'code_verified_{phone}')
#         # cache.set(f'sms_code_{phone}', '123456', timeout=300)  # 5分钟过期
#         # cache.get("sms_code_8888")
#         # cache.delete("sms_code_8888")
#
#
#         call_command('listener_daemon', '--phone', phone)
#     except Exception as e:
#         logger.critical("监听器启动失败", exc_info=True)
#         raise


@shared_task(bind=True)
def start_listener(self,phone: str, max_retries: int = 3):
    """增强版监听器启动任务"""
    try:
        # 清理可能存在的残留状态
        cache.delete_many([
            f'code_verified_{phone}',
            f'listener_status_{phone}'
        ])

        # 调用管理命令（带重试参数）
        call_command(
            'listener_daemon',
            '--phone', phone,
            '--max-retries', str(max_retries)
        )

        logger.info(f"成功启动 {phone} 的监听守护进程")
        return {"status": "success", "phone": phone}

    except Exception as e:
        logger.critical(
            f"监听器启动失败 | 手机号: {phone}",
            exc_info=True,
            extra={"phone": phone}
        )
        # 更新缓存状态
        cache.set(f'listener_status_{phone}', 'error', timeout=600)
        raise self.retry(exc=e, countdown=60)


@shared_task()
def stop_listener(phone: str):
    """增强版监听器停止任务"""
    try:
        # 调用停止命令
        call_command('stop_listener', '--phone', phone)

        # 清理关联缓存
        cache.delete_many([
            f'code_verified_{phone}',
            f'qr_session_{phone}'
        ])

        logger.info(f"已终止 {phone} 的监听进程")
        return {"status": "stopped", "phone": phone}

    except Exception as e:
        logger.error(
            f"监听器停止失败 | 手机号: {phone}",
            exc_info=True,
            extra={"phone": phone}
        )
        # 设置保护状态防止重复操作
        cache.set(f'stop_failed_{phone}', '1', timeout=300)
        raise

@shared_task
def input_code(phone_number, code):
    """包装异步操作为同步任务"""
    try:
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 执行异步方法
        result = loop.run_until_complete(
            CodeManager.create_code(phone_number, code)
        )
        loop.close()

        # 返回可序列化的简单类型
        return {
            "success": True,
            "data": str(result)  # 确保结果可以序列化
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }