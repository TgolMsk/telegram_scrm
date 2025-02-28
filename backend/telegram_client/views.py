# Create your views here.
from rest_framework import status
from websockets.legacy.server import HTTPResponse
from django.core.management import call_command

from telegram_client.models import Telegram,TelegramContact
from telegram_client.models import VerificationCode
from telegram_client.serializers import TelegramModelSerializer, TelegramModelCreateUpdateSerializer,TelegramContactModelSerializer,TelegramContactModelCreateUpdateSerializer
from dvadmin.utils.viewset import CustomModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from telegram_client.tasks import start_listener,stop_listener,input_code
from telegram_client.utils.verification import CodeManager

class TelegramModelViewSet(CustomModelViewSet):
    """
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """

    @action(detail=True, methods=['post'])
    def start_process(self, request, pk=None):
        instance = self.get_object()
        task_id = None  # 初始化任务ID

        if instance.process_result == 1:
            # 停止任务
            async_result = stop_listener.delay(phone=instance.phone_number)
            instance.process_result = 3
            instance.status = "offline"
        elif instance.process_result in [2, 3]:
            # 启动任务
            async_result = start_listener.delay(phone=instance.phone_number)
            instance.process_result = 1
            instance.status = "online"

        # 保存实例变更
        instance.save()

        # 返回任务ID（可序列化的字符串）
        return Response({
            "success": True,
            "task_id": async_result.id if async_result else None,
            "status": instance.status
        }, status=status.HTTP_200_OK)

    # 输入验证码
    @action(detail=True, methods=['post'])
    def in_code(self, request, pk=None):
        instance = self.get_object()  # 获取当前Telegram账号实例
        code = request.data.get('code')
        input_code.delay(phone_number=instance.phone_number, code=code)
        return Response({
            "success": True,
        }, status=status.HTTP_200_OK)


    queryset = Telegram.objects.all()
    serializer_class = TelegramModelSerializer
    create_serializer_class = TelegramModelCreateUpdateSerializer
    update_serializer_class = TelegramModelCreateUpdateSerializer



class TelegramContactModelViewSet(CustomModelViewSet):
    """
    list:查询
    create:新增
    update:修改
    retrieve:单例
    destroy:删除
    """
    queryset = TelegramContact.objects.all()
    serializer_class = TelegramContactModelSerializer
    create_serializer_class = TelegramContactModelCreateUpdateSerializer
    update_serializer_class = TelegramContactModelCreateUpdateSerializer

