#文件backend/telegram_client/models.py

from django.db import models
from django.utils import timezone
from enum import Enum

# Create your models here.
from dvadmin.utils.models import CoreModel

class Telegram(CoreModel):
    """
    Telegram云账号实体模型

    状态说明：
    - offline: 未连接状态
    - connecting: 正在建立连接
    - online: 正常在线状态
    - error: 连接异常状态
    """

    class Status(models.TextChoices):
        OFFLINE = 'offline', '离线'
        CONNECTING = 'connecting', '连接中'
        ONLINE = 'online', '在线'
        LOGIN = 'login','待登录'
        ERROR = 'error', '错误'

    phone_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='TG手机号',
        help_text='带国家代码的完整电话号码，例如+79991234567'
    )
    telegram_id = models.BigIntegerField(
        default=0,
        blank=True,
        verbose_name="telegram账号id"
    )
    session_string = models.TextField(
        blank=True,
        verbose_name='会话密钥',
        help_text='Telethon生成的原始session字符串（明文存储）'
    )
    password = models.TextField(
        default='<PASSWORD>',
        verbose_name='2FA密码',
        help_text='账户登录的二次验证简称2FA'
    )
    # 二维码登录地址
    qr_url = models.TextField(
        blank=True,
        verbose_name='二维码url',
        help_text='扫码登录的二维码url，自行转换为二维码'
    )
    # 二维码状态
    qr_status = models.BooleanField(
        default=False,
        verbose_name='二维码状态',
        help_text='二维码是否可用，不可用需要对二维码重新获取'
    )
    # 二维码过期时间
    qr_expires = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='二维码过期时间',
        help_text='扫码登录下二维码的过期时间'
    )
    # 新消息提醒
    new_message = models.BooleanField(
        default=False,
        verbose_name='新消息',
        help_text='显示是否有新消息到达或者去需要处理'
    )
    proxy = models.TextField(
        blank=True,
        verbose_name="代理信息",
        help_text="客户端初始化提供json代理配置信息"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OFFLINE,
        verbose_name='连接状态',
        help_text='当前账号的在线状态'
    )
    last_active = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后活跃',
        help_text='最后一次成功通信的时间戳或者最新心跳'
    )
    device_model = models.CharField(
        max_length=100,
        default='Unknown',
        verbose_name='设备标识',
        help_text='客户端设备信息（例如Telegram Desktop 4.2.3）'
    )
    app_version = models.CharField(
        max_length=100,
        default='Unknown',
        verbose_name="App版本",
        help_text="创建初始连接时发送的 “App version”默认为 telethon.version.__version__"
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='已验证',
        help_text='是否完成手机号验证码验证'
    )
    login_mode = models.IntegerField(
        choices=[(1, '消息'), (2, '扫码'), (3, '短信')], default=1, verbose_name="账号登录模式"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='账号首次注册时间'
    )
    process_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="服务进程ID",
        help_text = "通过创建ipc通讯获取的进程id"
    )
    # 进程状态
    process_result = models.IntegerField(
        choices=[(1, '正常'), (2, '丢失'), (3, '未启用')],
        default=3,
        verbose_name="进程状态"
    )
    # 进程地址
    process_url = models.CharField(
        null=True,
        blank=True,
        max_length=256,
        verbose_name="IPC地址",
        help_text="格式示例: unix:/tmp/tg_123.sock 或 tcp://127.0.0.1:5000"
    )

    # 存储前调用，如果不符合直接报错
    def clean(self):
        pass

    # 保存前调用，比如对内容格式化存储，保存前处理数据
    def pre_save_handler(self):
        pass

    # 删除前调用触发，比如释放僵尸进程啥的
    def pre_delete_handler(self):
        pass
    class Meta:
        db_table  = "telegram"
        verbose_name = 'Telegram账号配置'
        verbose_name_plural = verbose_name
        ordering = ('-create_datetime',)


class VerificationCode(CoreModel):
    """
    验证码存储模型
    """
    phone = models.CharField(
        max_length=20,
        verbose_name='手机号',
        help_text='带国家代码的完整号码，如+8617774217154'
    )
    code = models.CharField(
        max_length=12,
        verbose_name='验证码'
    )
    is_used = models.BooleanField(
        blank=True,
        default=False,
        verbose_name='是否已使用'
    )
    expires_at = models.DateTimeField(
        verbose_name='过期时间'
    )

    class Meta:
        db_table = "verification_code"
        verbose_name = '验证码管理'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['phone', 'expires_at']),
        ]

    def is_valid(self):
        """验证码是否有效"""
        return not self.is_used and timezone.now() < self.expires_at
class MessageType(Enum):
    PRIVATE = 'private'
    GROUP = 'group'
    CHANNEL = 'channel'
class Message(models.Model):
        """
        消息记录实体模型

        方向说明：
        - in: 接收的消息
        - out: 发送的消息
        """
        account = models.ForeignKey(
            Telegram,
            on_delete=models.CASCADE,
            verbose_name='关联账号',
            help_text='发送/接收消息的TG账号'
        )
        direction = models.CharField(
            max_length=10,
            choices=[('in', '接收'), ('out', '发送')],
            verbose_name='消息方向',
            help_text='消息流向（发送或接收）'
        )
        # 消息类型（私聊、群组、频道）
        message_type = models.CharField(
            max_length=10,
            choices=[(tag, tag.value) for tag in MessageType],
            default=MessageType.PRIVATE.value,
        )
        content = models.TextField(
            verbose_name='消息内容',
            help_text='原始消息文本内容',
        )
        media_info = models.JSONField(
            null=True,
            blank=True,
            verbose_name='媒体信息',
            help_text='{"type":"photo|video|document","file_id":"telegram_file_id","size":1024}'
        )
        timestamp = models.DateTimeField(
            verbose_name='消息时间',
            help_text='消息实际发生时间（来自Telegram服务器）'
        )
        sender_id = models.BigIntegerField(
            verbose_name='发送方ID',
            help_text='Telegram用户/群组/频道ID'
        )
        receiver_id = models.BigIntegerField(
            verbose_name='接收方ID',
            help_text='Telegram用户/群组/频道ID'
        )
        telegram_msg_id = models.BigIntegerField(
            verbose_name='消息ID',
            help_text='Telegram平台原始消息ID'
        )
        is_service_msg = models.BooleanField(
            default=False,
            verbose_name='系统消息',
            help_text='是否为Telegram系统消息（如入群通知）'
        )

        def __str__(self):
            return f"Message {self.telegram_msg_id} ({self.get_message_type_display()})"
        class Meta:
            verbose_name = '消息记录'
            verbose_name_plural = '消息记录'
            indexes = [
                models.Index(fields=['timestamp']),
                models.Index(fields=['sender_id', 'receiver_id'])
            ]


class TelegramContact(models.Model):
    """
    Telegram联系人模型（含定时任务配置）

    字段说明：
    - account : 所属TG账号（多对一关系）
    - contact_id : Telegram用户唯一标识
    - schedule_enabled : 是否启用定时任务
    - schedule_config : 定时任务详细配置
    """
    # 关联字段
    account = models.ForeignKey(
        Telegram,
        on_delete=models.CASCADE,
        verbose_name='所属账号',
        related_name='contacts',
        help_text='关联的TG云账号'
    )

    # 基础信息
    contact_id = models.BigIntegerField(
        verbose_name='用户ID',
        help_text='Telegram用户唯一ID（例如：123456789）',
    )
    user_status = models.CharField(
        max_length = 100,
        blank=True,
        verbose_name="好友最近在线时间",
        help_text="最近在线时间"
    )
    phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='手机号',
        help_text='格式：+国际区号号码（例如：+8613812345678）'
    )
    username = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='用户名',
        help_text='@开头的用户名（例如：zhangsan）'
    )
    first_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='名字'
    )
    last_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='姓氏'
    )

    # 关系状态
    remark = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='备注名称',
        help_text='用户自定义的备注名'
    )
    premium = models.BooleanField(
        default=False,
        verbose_name='是否会员',
        help_text='是否开启premium会员服务'
    )
    # 互动数据
    last_interaction = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后互动',
        help_text='最后一次消息交互时间'
    )
    message_count = models.PositiveIntegerField(
        default=0,
        verbose_name='消息总数',
        help_text='历史消息总数（收发合计）'
    )

    # 定时任务配置
    schedule_enabled = models.BooleanField(
        default=False,
        verbose_name='启用定时',
        help_text='是否启用定时消息功能'
    )
    # ai智能对话开关
    ai_chat_switch = models.BooleanField(
        default=False,
        verbose_name='ai回复开关',
        help_text='是否开启ai智能回复'
    )
    # 会话随机延迟开关以及回复范围（接收到消息后多少分钟内回复1-10）
    ai_reply_delay_config = models.JSONField(
        verbose_name="AI回复延迟设置",
        default=dict,  # 默认值为空字典
        help_text="AI回复延迟设置，可以指定固定时间或随机时间范围。"
    )
    # ai会话标识（基于ai平台账号的会话id存储）
    ai_session_id = models.CharField(
        max_length = 100,
        null=True,
        blank=True,
        verbose_name='ai会话标识',
        help_text='当用于ai回复时候对话所带的标识'
    )

    # 已读状态变更

    def get_reply_delay(self):
        """返回实际的回复延迟，支持固定值或随机值"""
        config = self.ai_reply_delay_config

        # 检查配置中的开关
        if config.get("use_random_delay", False):
            # 使用随机延迟
            min_delay = config.get("min_delay", 1)  # 默认最小延迟1分钟
            max_delay = config.get("max_delay", 10)  # 默认最大延迟10分钟
            import random
            return random.randint(min_delay, max_delay)
        else:
            # 使用固定延迟
            fixed_delay = config.get("fixed_delay", 1)  # 默认固定延迟1分钟
            return fixed_delay

    class Meta:
        verbose_name = 'TG联系人'
        verbose_name_plural = 'TG联系人'
        unique_together = ('account', 'contact_id')  # 唯一性约束
        indexes = [
            models.Index(fields=['account']),
            models.Index(fields=['user_status']),
        ]