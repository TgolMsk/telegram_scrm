<template>
  <div class="container">
    <!-- 左侧信息面板 -->
    <div class="left-panel">

      <!-- 头像区域 -->
      <div class="avatar-container">
        <el-avatar :size="72" class="avatar">
          <el-icon :size="36"><User /></el-icon>
        </el-avatar>
        <div v-if="hasNewMessage" class="message-alert"></div>
      </div>

      <!-- 用户信息 -->
      <div class="user-info">
        <div class="online-status">


          <el-icon :color="isOnline ? '#67C23A' : '#909399'"><SuccessFilled /></el-icon>
          <span>{{ telegram_status  }}</span>


        </div>
        <div class="phone-section">
          <el-icon class="phone-icon"><Iphone /></el-icon>
          <span>{{ phone_number }}</span>
        </div>
        <div class="connection-status">
          连接状态: {{ process_result }}
        </div>
      </div>

      <!-- 连接按钮 -->

      <el-button type="primary" :icon="Refresh" circle  @click="handleConnection" />
      <el-button type="primary" round @click="showChat = true"> 展开会话</el-button>
      <!-- 弹窗容器 -->
      <el-dialog
          v-model="showComponent"
          :modal="false"
          :show-close="false"
          width="80%"
          custom-class="custom-dialog"
      >
        <!-- 这里放入你要显示的组件 -->
        <YourComponent @close="showComponent = false" />
      </el-dialog>

    </div>

    <!-- 右侧日志面板 -->
    <div class="right-panel">
      <div class="log-header">
        <el-icon><Document /></el-icon>
        <span>运行日志</span>
      </div>
      <div class="log-content">
        <div
            v-for="(log, index) in logs"
            :key="index"
            class="log-item"
        >
          [{{ log.time }}] {{ log.content }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { User, Iphone, Document, SuccessFilled } from '@element-plus/icons-vue'
import {
  Refresh,
  Check,
  Delete,
  Edit,
  Message,
  Search,
  Star,
} from '@element-plus/icons-vue'
// eslint-disable-next-line vue/valid-define-props

// 状态管理
const isConnecting = ref(false)
const hasNewMessage = ref(true)
const connectionStatus = ref<'connecting' | 'connected' | 'error'>('connected')
const logs = ref([
  { time: '10:23:45', content: '成功建立安全连接' },
  { time: '10:24:01', content: '收到新消息通知' },
  { time: '10:24:15', content: '心跳包发送成功' },
  { time: '10:24:30', content: '加密通道已激活' },
  { time: '10:25:00', content: '同步5条新消息' }
])

// 计算属性  在线状态 手机号。连接状态  新消息提醒
// 手机号
const phone_number = computed(() => {
  return props.phone_number
})
// 在线状态
const telegram_status = computed(() => {
  return props.telegram_status
})
// 连接状态
const process_result = computed(() => {
  return props.process_result
})
// 新消息提醒
const new_message = computed(() => {
  return props.new_message
});


const connectionText = computed(() => {
  return {
    connecting: '建立连接中...',
    connected: '已加密',
    error: '连接失败'
  }[connectionStatus.value]
})
const buttonText = computed(() => {
  return isConnecting.value ? '连接中...' : '重新连接'
})

// 连接操作
const handleConnection = () => {
  if (isConnecting.value) return
  isConnecting.value = true
  connectionStatus.value = 'connecting'

  setTimeout(() => {
    isConnecting.value = false
    connectionStatus.value = Math.random() > 0.2 ? 'connected' : 'error'
    if(connectionStatus.value === 'connected') {
      logs.value.push({
        time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
        content: '重新连接成功'
      })
    }
  }, 2000)
}

// 组件参数
const props = defineProps({
  phone_number: {
    type: String,
    default: '13800138000'
  },
  telegram_status: {
    type: String,
    default: '13800138000'
  },
  process_result: {
    type: String,
    default: '13800138000'
  },
  new_message: {
    type: String,
    default: '13800138000'
  },
})
</script>

<style scoped>
/* 基础容器 */
.container {
  width: 510px;
  height: 310px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  overflow: hidden;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', sans-serif;
}

/* 左侧信息面板 */
.left-panel {
  width: 180px;
  padding: 20px;
  background: #ffffff;
  border-right: 1px solid #e0dddd;
  position: relative;
}

.status-indicator {
  position: absolute;
  top: 12px;
  left: 12px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;

  &.connected { background: #67C23A; }
  &.connecting { background: #e6a23c; }
  &.error { background: #f56c6c; }
}

.avatar-container {
  position: relative;
  width: 84px;
  height: 84px;
  margin: 25px auto;
}

.avatar {
  position: absolute;
  left: 6px;
  top: 6px;
  background: #26a6e5;
  box-shadow: 0 2px 8px rgba(38, 166, 229, 0.2);
  transition: all 0.3s;
}

.message-alert {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 14px;
  height: 14px;
  background: #ff4d4f;
  border: 2px solid #fff;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(255, 77, 79, 0.2);
  animation: pulse 1.5s infinite;
}

.user-info {
  margin: 15px 0;
  text-align: center;
}

.online-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #606266;
  font-size: 13px;
  margin-bottom: 12px;
}

.phone-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #909399;
  font-size: 12px;
  margin-bottom: 15px;
}

.connection-status {
  color: #409eff;
  font-size: 12px;
  margin: 8px 0;
}

.connect-btn {
  width: 30px;
  height: 34px;
  border-radius: 17px;
  font-size: 13px;
  margin-top: 10px;
  transition: all 0.3s;
}

/* 右侧日志面板 */
.right-panel {
  flex: 1;
  padding: 18px;
  display: flex;
  flex-direction: column;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #303133;
  font-size: 14px;
  margin-bottom: 12px;
  position: relative;
}

.new-message-dot {
  position: absolute;
  top: 2px;
  right: -6px;
  width: 8px;
  height: 8px;
  background: #f56c6c;
  border-radius: 50%;
}

.log-content {
  flex: 1;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 8px;
  background: #fcfcfc;
}

.log-item {
  font-size: 12px;
  color: #606266;
  line-height: 1.6;
  padding: 4px 0;
  white-space: nowrap;
}

/* 动画 */
@keyframes pulse {
  0% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.15); opacity: 1; }
  100% { transform: scale(1); opacity: 0.8; }
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}
::-webkit-scrollbar-track {
  background: #f1f1f1;
}
</style>