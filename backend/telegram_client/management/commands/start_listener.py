# telegram_client/management/commands/start_listener.py
import logging
from django.core.management.base import BaseCommand
from telegram_client.models import Telegram

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "启动指定账号的消息监听守护进程"

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            required=True,
            help='要启动监听的手机号 (格式: +国家码手机号，如+8613812345678)'
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='会话失效时的最大重试次数 (默认: 3)'
        )

    def handle(self, *args, **options):
        # 检查账号是否存在
        try:
            account = Telegram.objects.get(phone_number=options['phone'])
        except Telegram.DoesNotExist:
            logger.error(f"账号 {options['phone']} 未注册")
            return

        # 检查是否已在运行
        if account.process_result == 1:  # 1表示进程正在运行
            logger.warning(f"账号 {options['phone']} 的监听进程已在运行")
            return

        # 调用你的 listener_daemon 命令
        from django.core.management import call_command
        call_command(
            'listener_daemon',
            phone=options['phone'],
            max_retries=options['max_retries']
        )

        logger.info(f"已成功启动 {options['phone']} 的监听进程")