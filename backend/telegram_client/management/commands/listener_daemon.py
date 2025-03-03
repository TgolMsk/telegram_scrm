# telegram_client/management/commands/listener_daemon.py
import asyncio
import logging
import os
import time
from typing import Optional
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from telethon import TelegramClient, events
from telethon.errors import SessionExpiredError, SessionRevokedError
from telethon.sessions import StringSession
from telegram_client.models import Telegram,TelegramContact
from telegram_client.ipc_server import EnhancedIPCServer
from asgiref.sync import sync_to_async
from django.core.cache import cache
from telegram_client.utils.verification import CodeManager
from telethon.tl.types import PeerUser, PeerChat, PeerChannel, MessageMediaPoll, UserStatusRecently, UserStatusOffline, \
    UserStatusLastWeek, UserStatusOnline, UserStatusLastMonth
from telegram_client.models import Message, MessageType
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.types import InputUser

logger = logging.getLogger(__name__)



class Command(BaseCommand):
    help = "启动 Telegram 异步消息监听守护进程（支持会话重连）"

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            required=True,
            help='要监听的 Telegram 账户电话号码'
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='会话失效时的最大重试次数'
        )

    async def _message_handler(self, event: events.NewMessage.Event):
        """异步消息处理（存储到数据库）"""
        try:
            logger.info(event)
            # 获取消息基本信息
            # 消息id
            # 消息内容
            # 消息发出or接收
            # 是否at
            direction = "in"
            sender = await event.get_sender()
            chat = await event.get_chat()
            # 判断发送还是接收
            if event.message.out:
                direction = "send"
            # 判断消息类型 个人 群组 频道。。
            peer = event.message.peer_id
            message_type = MessageType.PRIVATE  # 默认为私聊

            if isinstance(peer, PeerUser):
                message_type = MessageType.PRIVATE
                logger.info(message_type.value)
                logger.info("这是一个个人消息（私聊）")
                logger.info(event)
            elif isinstance(peer, PeerChat):
                message_type = MessageType.GROUP
                logger.info(message_type.value)
                logger.info("这是一个群组消息")
            elif isinstance(peer, PeerChannel):
                message_type = MessageType.CHANNEL
                logger.info(message_type.value)
                logger.info("这是一个频道消息")
            else:
                logger.info("未知类型的消息")
            # 解析媒体信息
            media_info = None
            if event.media:
                if isinstance(event.media, MessageMediaPoll):
                    # 处理投票
                    media_info = {
                        "type": "poll",
                        "poll_id": event.media.poll.id,
                        "question": event.media.poll.question.text,
                        "options": [answer.text.text for answer in event.media.poll.answers],
                        "closed": event.media.poll.closed
                    }
                else:
                    # 处理其他媒体
                    media_type = "unknown"
                    file_id = None
                    size = None

                    if event.photo:
                        media_type = "photo"
                    elif event.video:
                        media_type = "video"
                    elif event.document:
                        media_type = "document"
                        file_id = event.media.document.id
                        size = event.media.document.size

                    media_info = {
                        "type": media_type,
                        "file_id": file_id,
                        "size": size
                    }

            # 构建消息记录
            message_data = {
                "account": self.account,  # 当前监听账号
                "direction": direction,  # 接收的消息
                "content": event.raw_text,  # 原始消息内容
                "media_info": media_info,  # 媒体信息
                "timestamp": event.date,  # 消息时间
                "sender_id": sender.id,  # 发送方ID
                "receiver_id": chat.id,  # 接收方ID（当前账号）
                "telegram_msg_id": event.id,  # Telegram消息ID
                "is_service_msg": event.action is not None,  # 是否为系统消息
                "message_type":message_type.value,  # 保存枚举的值


            }

            # 异步保存到数据库
            await self._save_message(message_data)

            # 日志记录
            # logger.info(
            #     "收到新消息",
            #     extra={
            #         "sender_id": sender.id,
            #         "sender_name": getattr(sender, 'username', '未知用户'),
            #         "chat_id": chat.id,
            #         "message_id": event.id,
            #         "content": event.raw_text[:100]  # 日志只记录前100字符
            #     }
            # )

        except Exception as e:
            logger.error(
                "消息处理异常",
                extra={"error": str(e), "chat_id": event.chat_id}
            )
            logger.info(str(e))

    @sync_to_async
    def _save_message(self, message_data):
        """异步保存消息到数据库"""
        try:
            Message.objects.create(**message_data)
        except Exception as e:
            logger.error(f"消息保存失败: {str(e)}")
            raise

    async def _init_client(self, account: Telegram) -> TelegramClient:
        """异步初始化并连接 Telegram 客户端（带会话验证）"""
        client = TelegramClient(
            session=StringSession(account.session_string),
            api_id=settings.TG_API_ID,
            api_hash=settings.TG_API_HASH,
            connection_retries=3,
            device_model="AsyncListenerDaemon/v3.0"
        )

        try:
            await client.connect()

            # 新增会话有效性检查
            if not await self._validate_session(client):
                await self._relogin(client, account)
                await self._update_session(account, client.session.save())

            me = await client.get_me()
            # 获取头像
            avatar_bytes = await client.download_profile_photo(entity="me",file=bytes,download_big=False)
            logger.info("打印头像信息")
            # logger.info(avatar_bytes)
            save_dir = os.path.join(settings.MEDIA_ROOT, 'telegram_avatars')
            os.makedirs(save_dir, exist_ok=True)
            file_name = f"avatar_{me.id}.jpg"
            filepath = os.path.join(save_dir, file_name)
            avatar_path = None
            if avatar_bytes:
                with open(filepath, 'wb') as f:
                    f.write(avatar_bytes)
                    avatar_path = os.path.join('telegram_avatars', file_name)
                    logger.info(avatar_path)
                    #保存到数据库







            await self._update_telegram_id(account, me.id, avatar_path)
            logger.info(me.id)
            logger.info(
                "客户端连接成功",
                extra={
                    "phone": me.phone,
                    "username": me.username,
                    "user_id": me.id
                }
            )

            # 新增联系人同步逻辑
            await self._sync_contacts(client, account)

            return client
        except Exception as e:
            await client.disconnect()
            logger.critical("客户端初始化失败", exc_info=True)
            raise

    # 新增联系人同步方法
    async def _sync_contacts(self, client: TelegramClient, account: Telegram):
        """同步联系人信息到数据库"""
        from telegram_client.models import TelegramContact

        # 获取所有联系人
        contacts = await client(GetContactsRequest(hash=0))

        # 获取数据库现有记录（批量查询优化）
        existing_contacts = await self._get_existing_contacts(account)

        updates = []
        new_contacts = []

        for contact in contacts.users:
            # 生成状态文本
            status_content = self._get_status_text(contact.status)
            logger.info(contact)
            # 构建当前数据
            current_data = {
                "phone_number": contact.phone,
                "username": contact.username,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "user_status": status_content,
                "premium": contact.premium
            }
            logger.info(current_data)
            # 检查是否已存在记录
            if contact.id in existing_contacts:
                db_contact = existing_contacts[contact.id]

                # 检查字段变化
                if self._is_contact_changed(db_contact, current_data):
                    # 更新变化字段
                    db_contact.phone_number = current_data['phone_number']
                    db_contact.username = current_data['username']
                    db_contact.first_name = current_data['first_name']
                    db_contact.last_name = current_data['last_name']
                    db_contact.user_status = current_data['user_status']
                    db_contact.premium = current_data['premium']
                    updates.append(db_contact)
            else:
                # 创建新记录
                new_contacts.append(
                    TelegramContact(
                        account=account,
                        contact_id=contact.id,
                        **current_data
                    )
                )

        # 批量操作
        await self._bulk_db_operations(new_contacts, updates)

    @sync_to_async
    def _get_existing_contacts(self, account):
        """获取当前账号的现有联系人"""
        return {
            c.contact_id: c
            for c in TelegramContact.objects.filter(account=account)
        }

    def _get_status_text(self, status):
        """获取状态文本（复用你的现有逻辑）"""
        if isinstance(status, UserStatusOnline):
            return "在线"
        elif isinstance(status, UserStatusOffline):
            time_str = status.was_online.strftime("%Y-%m-%d %H:%M:%S")
            return f"离线 (最后在线: {time_str})"
        elif isinstance(status, UserStatusRecently):
            return "最近在线 (24小时内)"
        elif isinstance(status, UserStatusLastWeek):
            return "过去一周内活跃"
        elif isinstance(status, UserStatusLastMonth):
            return "过去一月内活跃"
        else:
            return "未知状态"

    def _is_contact_changed(self, db_contact, current_data):
        """检查联系人信息是否变化"""
        fields_to_check = [
            'phone_number', 'username',
            'first_name', 'last_name',
            'user_status', 'premium'
        ]
        return any(
            getattr(db_contact, field) != current_data[field]
            for field in fields_to_check
        )

    @sync_to_async
    def _bulk_db_operations(self, new_contacts, updates):
        """执行批量数据库操作"""
        from django.db import transaction

        with transaction.atomic():
            if new_contacts:
                TelegramContact.objects.bulk_create(new_contacts, batch_size=100)

            if updates:
                fields = [
                    'phone_number', 'username',
                    'first_name', 'last_name',
                    'user_status', 'premium'
                ]
                TelegramContact.objects.bulk_update(updates, fields, batch_size=100)

        logger.info(
            f"联系人同步完成: 新增 {len(new_contacts)} 条, 更新 {len(updates)} 条"
        )
    async def _validate_session(self, client: TelegramClient) -> bool:
        """深度验证会话有效性"""
        try:
            return await client.is_user_authorized() and bool(await client.get_me())
        except (SessionExpiredError, SessionRevokedError):
            return False

    # 在 _relogin 方法中优化登录流程
    async def _relogin(self, client: TelegramClient, account: Telegram):
        """优化后的重新登录方法"""
        logger.warning("检测到会话失效，开始重新登录...")
        max_retries = 3
        retry_count = 0

        async def code_callback():
            logger.info(f"等待验证码输入 | 手机号: {account.phone_number}")
            start_time = time.time()

            while time.time() - start_time < 300:
                # 获取最新有效验证码（事务内操作）
                valid_code = await CodeManager.get_valid_code(account.phone_number)
                logger.info("获取到验证码：")

                if valid_code and valid_code.code:
                    logger.info(f"获取到验证码: {valid_code.code}")
                    await CodeManager.mark_used(valid_code.id)
                    return valid_code.code

                await asyncio.sleep(1)

            raise asyncio.TimeoutError("验证码等待超时")


        while retry_count < max_retries:
            try:
                if account.login_mode == 1:  # 消息验证码登录
                    logger.info("开始验证码登录流程")

                    # 启动客户端并设置双重超时
                    await client.start(
                            phone=account.phone_number,
                            code_callback=code_callback
                        )
                    logger.info("验证码登录成功")
                    break

                elif account.login_mode == 2:  # 扫码登录
                    # 保持原有扫码登录逻辑，增加时区处理
                    qr_login = await client.qr_login()
                    qr_url = qr_login.url
                    logger.info(f"生成登录二维码: {qr_url}")

                    # 处理时区敏感的时间字段
                    qr_expires = qr_login.expires
                    if not settings.USE_TZ and timezone.is_aware(qr_expires):
                        qr_expires = timezone.make_naive(qr_expires)

                    @sync_to_async
                    def update_qr_info():
                        account.qr_url = qr_url
                        account.qr_expires = qr_expires
                        account.qr_status = True
                        account.save(update_fields=['qr_url', 'qr_expires', 'qr_status'])

                    await update_qr_info()

                    # 设置合理的扫码等待时间
                    await asyncio.wait_for(qr_login.wait(), timeout=180)
                    logger.info("扫码登录成功")
                    break

            except asyncio.TimeoutError as e:
                retry_count += 1
                logger.warning(f"登录超时 (重试 {retry_count}/{max_retries})")

                # 更新二维码状态
                if account.login_mode == 2:
                    @sync_to_async
                    def disable_qr():
                        account.qr_status = False
                        account.save(update_fields=['qr_status'])

                    await disable_qr()

                if retry_count >= max_retries:
                    logger.critical("连续登录失败，终止尝试")
                    raise RuntimeError("超过最大重试次数") from e
                await asyncio.sleep(2 ** retry_count)  # 指数退避

            except Exception as e:
                logger.error("登录流程异常", exc_info=True)
                raise

    async def get_code_via_ipc(self, phone: str) -> str:
        """通过IPC获取验证码（示例实现）"""
        # 此处应实现实际的IPC通信逻辑，例如通过socket接收验证码
        # 示例：模拟用户输入
        logger.info(f"请通过IPC为手机号 {phone} 输入验证码...")
        return await asyncio.get_event_loop().run_in_executor(None, input, "Enter code: ")

    @sync_to_async
    def _update_session(self, account: Telegram, new_session: str):
        """异步更新数据库会话"""
        with transaction.atomic():
            account.session_string = new_session
            account.save(update_fields=['session_string'])
            logger.info("会话信息已更新")

    @sync_to_async
    def _update_telegram_id(self, account: Telegram, telegram_id: int,avatar_path:str=None):
        """异步更新数据库会话"""
        with transaction.atomic():
            logger.info(avatar_path)
            account.telegram_id = telegram_id
            account.avatar = avatar_path
            account.save(update_fields=['avatar'])
            account.save(update_fields=['telegram_id'])
            logger.info("Telegram_id已更新")
    async def _run_listener(self, phone: str, max_retries: int):
        """增强版监听主逻辑"""
        retry_count = 0
        client = None
        ipc_server = None
        try:
            # 增强预检查
            @sync_to_async
            def pre_check():
                if not Telegram.objects.filter(phone_number=phone).exists():
                    raise ValueError(f"账户 {phone} 未注册")
                return Telegram.objects.get(phone_number=phone)

            account = await pre_check()
            logger.debug(f"预检查通过，账户状态: {account.status}")

            while retry_count < max_retries:
                try:
                    # 获取并锁定账户（带状态修复）
                    @sync_to_async
                    def atomic_get_account():
                        with transaction.atomic():
                            acc = Telegram.objects.select_for_update().get(
                                phone_number=phone,
                                status__in=[Telegram.Status.ONLINE, Telegram.Status.CONNECTING,Telegram.Status.OFFLINE]
                            )
                            if acc.status != Telegram.Status.CONNECTING:
                                acc.status = Telegram.Status.CONNECTING
                                acc.save(update_fields=['status'])
                            return acc
                    logger.info("查询数据")
                    account = await atomic_get_account()
                    logger.info(f"成功获取账户: {account.phone_number}")

                    # 初始化客户端
                    client = await self._init_client(account)
                    logger.info('正在注册消息处理器...')

                    # 注册新消息处理器
                    client.add_event_handler(
                        self._message_handler,
                        events.NewMessage()
                    )
                    self.account = account
                    # 启动IPC服务器并更新进程信息
                    ipc_server = EnhancedIPCServer(client, account)
                    await ipc_server.start()

                    @sync_to_async
                    def update_process_info():
                        account.process_id = ipc_server.process_id
                        account.process_url = ipc_server.process_url
                        account.process_result = 1  # 正常
                        account.save(update_fields=['process_id', 'process_url', 'process_result'])

                    await update_process_info()
                    # 更新状态为在线
                    @sync_to_async
                    def set_online():
                        account.status = Telegram.Status.ONLINE
                        account.save(update_fields=['status'])
                    await set_online()
                    retry_count = 0  # 重置重试计数器
                    # 保持连接（带心跳检测）
                    while True:
                        if not await self._validate_session(client):
                            logger.warning("检测到会话失效，触发重新连接")
                            break
                        await asyncio.sleep(60)

                except (SessionExpiredError, SessionRevokedError) as e:
                    logger.warning(f"会话过期/撤销 (重试 {retry_count + 1}/{max_retries})")
                    retry_count += 1
                    await asyncio.sleep(2 ** retry_count)
                except Telegram.DoesNotExist:
                    logger.critical("账户记录异常丢失，终止进程")
                    break
                except Exception as e:
                    logger.critical("监听进程异常终止", exc_info=True)
                    break
                finally:
                    await self._cleanup_resources(client, ipc_server, account)
            if retry_count >= max_retries:
                logger.critical("达到最大重试次数，永久终止监听")

                @sync_to_async
                def set_error_status():
                    account.status = Telegram.Status.ERROR
                    account.save(update_fields=['status'])
                await set_error_status()

        except Exception as e:
            logger.critical("监听进程启动失败", exc_info=True)
            await self._cleanup_resources(client, ipc_server, account)

    async def _cleanup_resources(self, client, ipc_server, account):
        """异步资源清理"""
        cleanup_tasks = []
        try:
            if client and client.is_connected():
                cleanup_tasks.append(client.disconnect())
            if ipc_server:
                cleanup_tasks.append(ipc_server.stop())
            if account:
                @sync_to_async
                def update_resources():
                    account.refresh_from_db()
                    # 更新状态为离线
                    if account.status != Telegram.Status.ERROR:
                        account.status = Telegram.Status.OFFLINE
                    # 清理进程信息
                    account.process_result = 3  # 未启用
                    account.process_id = None
                    account.process_url = ''
                    account.save(update_fields=['status', 'process_result', 'process_id', 'process_url'])

                cleanup_tasks.append(update_resources())

            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        except Exception as e:
            logger.error("资源清理异常", exc_info=True)

    def handle(self, *args, **options):
        """增强版入口点"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                self._run_listener(
                    options['phone'],
                    options['max_retries']
                )
            )
        except KeyboardInterrupt:
            logger.info("用户主动终止进程")
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
