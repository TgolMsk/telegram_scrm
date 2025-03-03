#backend/telegram_client/urls.py

from rest_framework.routers import SimpleRouter

from .views import TelegramModelViewSet,TelegramContactModelViewSet

router = SimpleRouter()
# 这里进行注册路径，并把视图关联上，这里的api地址以视图名称为后缀，这样方便记忆api/CrudDemoModelViewSet
router.register("api/TelegramModelViewSet", TelegramModelViewSet)
router.register("api/TelegramContactModelViewSet", TelegramContactModelViewSet)
# 自定义api
router.register("api/TelegramModelViewSet", TelegramModelViewSet,basename="start_process")
router.register("api/TelegramModelViewSet", TelegramModelViewSet,basename="in_code")



urlpatterns = [
]
urlpatterns += router.urls