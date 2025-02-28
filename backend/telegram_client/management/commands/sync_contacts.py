# sync_contacts.py
import asyncio
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.types import UserStatusOnline, UserStatusOffline

from telegram_client.models import Telegram
from telethon import TelegramClient
from telethon.sessions import StringSession

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "手动触发指定 Telegram 账户的联系人同步"

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=int,
            required=True,
            help='要同步的 Telegram 账户数据库 ID'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制全量同步（忽略最近更新时间）'
        )

    def handle(self, *args, **options):
        # 将异步执行逻辑包装到同步上下文中
        asyncio.run(self.async_handle(options))

    async def async_handle(self, options):
        account_id = options['account_id']
        force_update = options['force']

        try:
            # 获取账户对象
            account = await self.get_account(account_id)

            # 初始化客户端
            async with TelegramClient(
                    session=StringSession(account.session_string),
                    api_id=settings.TG_API_ID,
                    api_hash=settings.TG_API_HASH
            ) as client:
                await client.connect()

                # 执行同步逻辑
                result = await self.sync_contacts(client, account, force_update)

                # 输出结果
                self.stdout.write(self.style.SUCCESS(
                    f"同步成功！新增 {result['created']} 条，更新 {result['updated']} 条"
                ))

        except Exception as e:
            logger.error(f"同步失败: {str(e)}")
            self.stdout.write(self.style.ERROR(f"错误: {str(e)}"))

    @staticmethod
    async def get_account(account_id: int) -> Telegram:
        """异步获取账户实例"""
        try:
            return await Telegram.objects.aget(id=account_id)
        except Telegram.DoesNotExist:
            raise ValueError(f"ID 为 {account_id} 的账户不存在")

    async def sync_contacts(self, client: TelegramClient, account: Telegram, force: bool) -> dict:
        """执行联系人同步的核心逻辑"""
        from telegram_client.models import TelegramContact

        # 获取所有联系人
        contacts = await client(GetContactsRequest(hash=0))

        # 获取现有记录
        existing_contacts = {
            c.contact_id: c
            async for c in TelegramContact.objects.filter(account=account)
        }

        created = 0
        updated = 0

        # 遍历处理每个联系人
        for contact in contacts.users:
            status_text = self.parse_user_status(contact.status)

            contact_data = {
                'phone_number': contact.phone,
                'username': contact.username,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'user_status': status_text,
                'premium': contact.premium
            }

            if contact.id in existing_contacts:
                # 更新逻辑
                db_contact = existing_contacts[contact.id]
                if force or self.is_contact_changed(db_contact, contact_data):
                    await self.update_contact(db_contact, contact_data)
                    updated += 1
            else:
                # 新建逻辑
                await TelegramContact.objects.acreate(
                    account=account,
                    contact_id=contact.id,
                    **contact_data
                )
                created += 1

        return {'created': created, 'updated': updated}

    def parse_user_status(self, status):
        """解析用户在线状态（复用现有逻辑）"""
        if isinstance(status, UserStatusOnline):
            return "在线"
        elif isinstance(status, UserStatusOffline):
            return f"离线 (最后在线: {status.was_online.strftime('%Y-%m-%d %H:%M:%S')}"
        # ...其他状态处理...
        else:
            return "未知状态"

    def is_contact_changed(self, db_contact, new_data) -> bool:
        """检查联系人是否变化"""
        return any(
            getattr(db_contact, field) != new_data[field]
            for field in ['phone_number', 'username', 'first_name', 'last_name', 'user_status', 'premium']
        )

    @staticmethod
    async def update_contact(db_contact, new_data):
        """异步更新联系人"""
        for field, value in new_data.items():
            setattr(db_contact, field, value)
        await db_contact.asave(update_fields=new_data.keys())