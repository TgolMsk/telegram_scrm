#backend/telegram/serializers.py

from telegram_client.models import Telegram
from telegram_client.models import TelegramContact
from dvadmin.utils.serializers import CustomModelSerializer


class TelegramModelSerializer(CustomModelSerializer):
    """
    序列化器
    """
#这里是进行了序列化模型及所有的字段
    class Meta:
        model = Telegram
        fields = "__all__"

#这里是创建/更新时的列化器
class TelegramModelCreateUpdateSerializer(CustomModelSerializer):
    """
    创建/更新时的列化器
    """

    class Meta:
        model = Telegram
        fields = '__all__'


class TelegramContactModelSerializer(CustomModelSerializer):
    """
    序列化器
    """
#这里是进行了序列化模型及所有的字段
    class Meta:
        model = TelegramContact
        fields = "__all__"

#这里是创建/更新时的列化器
class TelegramContactModelCreateUpdateSerializer(CustomModelSerializer):
    """
    创建/更新时的列化器
    """

    class Meta:
        model = TelegramContact
        fields = '__all__'