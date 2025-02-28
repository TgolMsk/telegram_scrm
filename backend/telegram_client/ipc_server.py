# telegram_client/ipc_server.py
import asyncio
import json
import os
import struct
from pathlib import Path
import logging
from asgiref.sync import sync_to_async
from django.db import close_old_connections
from django.utils import timezone
from telethon import TelegramClient
from .models import Telegram

logger = logging.getLogger(__name__)


class EnhancedIPCServer:
    def __init__(self, client: TelegramClient, tg_account: Telegram):
        self.client = client
        self.tg_account = tg_account
        self.pid = os.getpid()
        self.sock_path = self._get_socket_path()
        self.server = None
        self._connections = set()

    def _get_socket_path(self) -> str:
        """生成符合模型要求的 IPC 地址"""
        phone_clean = self.tg_account.phone_number.replace('+', '').strip()
        return f"/tmp/tg_{phone_clean}.sock"  # 示例: /tmp/tg_79991234567.sock

    async def _cleanup_socket(self):
        """清理残留的 socket 文件"""
        try:
            sock_file = Path(self.sock_path)
            if sock_file.exists():
                sock_file.unlink(missing_ok=True)
                logger.debug(f"清理旧 socket 文件: {self.sock_path}")
        except Exception as e:
            logger.error(f"Socket 清理失败: {str(e)}")
            raise

    async def _update_account_status(self, status: str):
        """原子化更新账户状态"""
        try:
            @sync_to_async
            def _update():
                Telegram.objects.filter(pk=self.tg_account.pk).update(
                    status=status,
                    last_active=timezone.now()
                )

            await _update()
        except Exception as e:
            logger.error(f"状态更新失败: {str(e)}")
        finally:
            close_old_connections()

    async def start(self):
        """启动 IPC 服务器并更新进程信息"""
        try:
            await self._cleanup_socket()

            # 启动 Unix domain socket 服务器
            self.server = await asyncio.start_unix_server(
                self._handle_connection,
                path=self.sock_path
            )

            # 更新进程信息到 Telegram 模型
            @sync_to_async
            def update_process_info():
                Telegram.objects.filter(pk=self.tg_account.pk).update(
                    process_id=self.pid,
                    process_url=f"unix:{self.sock_path}",
                    process_result=1,  # 1=正常
                    status=Telegram.Status.ONLINE
                )

            await update_process_info()

            logger.info(f"IPC 服务器已启动: {self.sock_path} (PID: {self.pid})")

            # 保持服务器运行
            async with self.server:
                await self.server.serve_forever()

        except Exception as e:
            logger.critical(f"服务器启动失败: {str(e)}", exc_info=True)
            await self._update_account_status(Telegram.Status.ERROR)
            raise

    async def _handle_connection(self, reader, writer):
        """处理客户端连接"""
        self._connections.add(writer)
        try:
            # 读取协议头
            header = await reader.readexactly(4)
            msg_len = struct.unpack('!I', header)[0]

            # 读取完整消息
            data = await reader.readexactly(msg_len)
            request = json.loads(data.decode())

            # 命令路由
            handler = {
                'send_message': self._handle_send_message,
                'get_status': self._handle_get_status,
                'update_session': self._handle_update_session
            }.get(request.get('command'))

            if not handler:
                response = {'status': 'error', 'code': 'invalid_command'}
            else:
                response = await handler(request)

            # 发送响应
            response_data = json.dumps(response).encode()
            writer.write(struct.pack('!I', len(response_data)) + response_data)
            await writer.drain()

        except (asyncio.IncompleteReadError, struct.error) as e:
            logger.warning(f"协议解析错误: {str(e)}")
            response = {'status': 'error', 'code': 'protocol_error'}
        except json.JSONDecodeError:
            logger.warning("无效的 JSON 格式")
            response = {'status': 'error', 'code': 'invalid_json'}
        except Exception as e:
            logger.error("请求处理异常", exc_info=True)
            response = {'status': 'error', 'code': 'server_error'}
        finally:
            writer.close()
            self._connections.discard(writer)

    async def _handle_send_message(self, request):
        """处理消息发送请求"""
        try:
            target = request['target']
            message = request['message']

            if not isinstance(message, str) or len(message) == 0:
                raise ValueError("消息内容无效")

            result = await self.client.send_message(
                entity=target,
                message=message
            )

            await self._update_account_status(Telegram.Status.ONLINE)

            return {
                'status': 'success',
                'message_id': result.id,
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"消息发送失败: {str(e)}")
            await self._update_account_status(Telegram.Status.ERROR)
            return {
                'status': 'error',
                'code': 'send_failed',
                'detail': str(e)
            }

    async def _handle_get_status(self, request):
        """获取账户状态信息"""

        @sync_to_async
        def _get_account():
            return Telegram.objects.get(pk=self.tg_account.pk)

        account = await _get_account()
        return {
            'status': 'success',
            'data': {
                'phone': account.phone_number,
                'status': account.status,
                'process': {
                    'id': account.process_id,
                    'url': account.process_url,
                    'result': account.process_result
                },
                'last_active': account.last_active.isoformat() if account.last_active else None,
                'is_verified': account.is_verified,
                'device_model': account.device_model,
                'app_version': account.app_version
            }
        }

    async def _handle_update_session(self, request):
        """安全更新会话字符串"""
        try:
            new_session = request['new_session']
            if len(new_session) < 10:
                raise ValueError("无效的会话数据")

            @sync_to_async
            def _update():
                Telegram.objects.filter(pk=self.tg_account.pk).update(
                    session_string=new_session
                )

            await _update()
            return {'status': 'success'}
        except Exception as e:
            logger.error("会话更新失败", exc_info=True)
            return {'status': 'error', 'code': 'update_failed'}

    async def stop(self):
        """优雅关闭服务器"""
        logger.info("正在关闭 IPC 服务器...")

        # 关闭所有连接
        for writer in self._connections:
            writer.close()
            await writer.wait_closed()

        # 停止服务器
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # 清理 socket 文件
        await self._cleanup_socket()

        # 更新进程状态
        @sync_to_async
        def _clean_process():
            Telegram.objects.filter(pk=self.tg_account.pk).update(
                process_result=3,  # 2=丢失
                process_id=None,
                process_url='',
                status=Telegram.Status.OFFLINE
            )

        await _clean_process()

        logger.info("IPC 服务器已关闭")