# telegram_client/management/commands/stop_listener.py
import os
import signal
import logging
from django.core.management.base import BaseCommand
from telegram_client.models import Telegram

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "停止指定账号的消息监听守护进程"

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            required=True,
            help='要停止监听的手机号'
        )

    def handle(self, *args, **options):
        try:
            account = Telegram.objects.get(phone_number=options['phone'])
        except Telegram.DoesNotExist:
            logger.error(f"账号 {options['phone']} 不存在")
            return

        if not account.process_id:
            logger.warning(f"账号 {options['phone']} 没有运行中的监听进程")
            return

        # 发送终止信号
        try:
            os.kill(account.process_id, signal.SIGTERM)
            logger.info(f"已发送终止信号给进程 {account.process_id}")
        except ProcessLookupError:
            logger.warning(f"进程 {account.process_id} 不存在")
        except PermissionError:
            logger.error(f"无权限终止进程 {account.process_id}")

        # 清理数据库状态
        account.process_id = None
        account.process_url = ''
        account.process_result = 3  # 3表示已停止
        account.status = Telegram.Status.OFFLINE
        account.save(update_fields=[
            'process_id',
            'process_url',
            'process_result',
            'status'
        ])

        logger.info(f"已停止 {options['phone']} 的监听进程")