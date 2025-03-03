from typing import Union, Optional, Dict
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionExpiredError, AuthKeyError, RPCError
from django.conf import settings
from asgiref.sync import sync_to_async
from telegram_client.models import Telegram
import logging

logger = logging.getLogger(__name__)

async def login_with_session(phone: str) -> Union[TelegramClient, str]:
    """
通过 Session 字符串异步登录 Telegram，并处理数据库查询
:param phone: 手机号码
:return: 成功返回 Client 对象，失败返回错误信息
from telegram_client.telegram_api import query_account_user_id
import asyncio
async def test_send(phone):
    result = await query_account_user_id(phone)
    print(result)
asyncio.run(test_send())

    """
    try:
        # 异步执行 ORM 查询
        get_telegram = sync_to_async(Telegram.objects.get, thread_sensitive=True)
        telegram_obj = await get_telegram(phone_number=phone)

        client = TelegramClient(
            StringSession(telegram_obj.session_string),
            settings.TG_API_ID,
            settings.TG_API_HASH
        )

        # 显式建立连接
        await client.connect()

        if not await client.is_user_authorized():
            await client.disconnect()
            return "Session 无效或未授权，请重新登录"

        return client

    except Telegram.DoesNotExist:
        return f"手机号 {phone} 未注册"
    except (SessionExpiredError, AuthKeyError) as e:
        return f"认证失败: {type(e).__name__} - {str(e)}"
    except RPCError as e:
        await client.disconnect()
        return f"网络错误: {type(e).__name__} - {str(e)}"
    except Exception as e:
        return f"系统错误: {type(e).__name__} - {str(e)}"


async def send_message(phone: str, to, text: str,file="") -> Dict:
    """
    异步发送消息，包含完整错误处理
    :return: 结构化的结果字典
    """
    client = await login_with_session(phone)

    # 处理登录错误
    if isinstance(client, str):
        return {
            "status": False,
            "error": client,
            "action": "请检查 session 有效性或重新登录"
        }

    try:
        # 发送消息
        result = await client.send_message(entity=to,message=text,file=file)
        return {
            "status": True,
            "message_id": result.id,
            "date": result.date.isoformat()
        }
    except RPCError as e:
        return {
            "status": False,
            "error": f"发送失败: {type(e).__name__}",
            "code": e.code,
            "details": str(e)
        }
    finally:
        # 确保断开连接
        if not client.is_connected():
            await client.disconnect()

# 获取好友列表
async def get_account_list(phone):
    client = await login_with_session(phone)
    await client.get_peer_id('me')


# 查询用户id
async def query_account_user_id(phone,qure_phone):

    try:
        client = await login_with_session(phone)
        result = await client.get_peer_id(qure_phone)
        return result
    except (SessionExpiredError, AuthKeyError) as e:
        return e
    except Exception as e:
        logger.info(e)
        return e






# from application.celery import app
# from telegram_client.tasks import send_via_ipc_task
# send_via_ipc_task.delay("+8617774217154", 7827632988, "ipc消息测试")
# <AsyncResult: 96a98f16-b084-45d0-9e28-95ae48795ce0>
# 查询ID
