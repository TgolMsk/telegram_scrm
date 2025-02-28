<template>
  <div class="chat-container">
    <!-- 左侧好友列表 -->
    <el-aside width="300px" class="friends-list">
      <div class="search-box">
        <el-input
            v-model="searchKeyword"
            placeholder="搜索好友"
            prefix-icon="el-icon-search"
        />
      </div>

      <el-menu class="friend-items">
        <el-menu-item
            v-for="friend in filteredFriends"
            :key="friend.id"
            @click="selectFriend(friend)"
        >
          <div class="friend-item">
            <el-avatar :src="friend.avatar" />
            <div class="friend-info">
              <h4>{{ friend.name }}</h4>
              <p class="last-msg">{{ friend.lastMessage }}</p>
            </div>
          </div>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 右侧聊天区域 -->
    <el-main class="chat-main">
      <!-- 聊天头部 -->
      <div class="chat-header">
        <div class="friend-info">
          <el-avatar :src="currentFriend?.avatar" />
          <h3>{{ currentFriend?.name }}</h3>
        </div>
        <el-button
            icon="el-icon-close"
            circle
            @click="$emit('close')"
        />
      </div>

      <!-- 消息区域 -->
      <el-scrollbar class="message-area">
        <div
            v-for="msg in currentFriend?.messages"
            :key="msg.id"
            class="message-bubble"
            :class="{ 'my-message': msg.isMe }"
        >
          <div class="message-content">
            <p>{{ msg.content }}</p>
            <span class="time">{{ msg.time }}</span>
          </div>
        </div>
      </el-scrollbar>

      <!-- 消息输入 -->
      <div class="message-input">
        <el-input
            v-model="newMessage"
            placeholder="输入消息..."
            @keyup.enter="sendMessage"
        >
          <template #append>
            <el-button icon="el-icon-position" @click="sendMessage" />
          </template>
        </el-input>
      </div>
    </el-main>

    <!-- 好友资料抽屉 -->
    <el-drawer
        title="好友资料"
        v-model:visible="showProfile"
        direction="rtl"
        size="25%"
    >
      <div class="profile-content">
        <el-avatar :src="currentFriend?.avatar" :size="100" />
        <h3>{{ currentFriend?.name }}</h3>
        <p class="signature">{{ currentFriend?.signature }}</p>

        <el-button
            type="primary"
            @click="showEditDialog = true"
        >
          编辑资料
        </el-button>
      </div>
    </el-drawer>

    <!-- 资料编辑对话框 -->
    <el-dialog title="编辑资料" v-model:visible="showEditDialog">
      <el-form :model="currentFriend">
        <el-form-item label="姓名">
          <el-input v-model="currentFriend.name" />
        </el-form-item>
        <el-form-item label="签名">
          <el-input v-model="currentFriend.signature" type="textarea" />
        </el-form-item>
        <el-form-item label="头像URL">
          <el-input v-model="currentFriend.avatar" />
        </el-form-item>
      </el-form>
      <template v-slot:footer>
<span >
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </span>
</template>
    </el-dialog>
  </div>
</template>

<script>
export default {
  data() {
    return {
      searchKeyword: '',
      currentFriend: null,
      newMessage: '',
      showProfile: false,
      showEditDialog: false,
      friends: [
        {
          id: 1,
          name: '张三',
          avatar: 'https://example.com/avatar1.jpg',
          signature: '前端开发者',
          lastMessage: '你好！',
          messages: [
            { id: 1, content: '你好！', time: '09:00', isMe: false },
            { id: 2, content: '你好呀！', time: '09:01', isMe: true }
          ]
        },
        // 更多好友数据...
      ]
    }
  },

  computed: {
    filteredFriends() {
      return this.friends.filter(friend =>
          friend.name.toLowerCase().includes(this.searchKeyword.toLowerCase())
      )
    }
  },

  methods: {
    selectFriend(friend) {
      this.currentFriend = friend
      this.showProfile = true
    },

    sendMessage() {
      if (!this.newMessage.trim()) return

      this.currentFriend.messages.push({
        id: Date.now(),
        content: this.newMessage,
        time: new Date().toLocaleTimeString(),
        isMe: true
      })
      this.newMessage = ''
    },

    saveProfile() {
      this.showEditDialog = false
      // 这里可以添加保存到服务器的逻辑
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
}

.friends-list {
  border-right: 1px solid #ebeef5;
}

.friend-item {
  display: flex;
  align-items: center;
  padding: 10px;
}

.friend-info {
  margin-left: 15px;
}

.last-msg {
  color: #909399;
  font-size: 12px;
}

.chat-main {
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #ebeef5;
}

.message-area {
  flex: 1;
  padding: 20px;
  height: 60vh;
}

.message-bubble {
  max-width: 70%;
  margin: 10px 0;
  padding: 10px;
  border-radius: 8px;
  background: #f0f2f5;
}

.my-message {
  margin-left: auto;
  background: #409eff;
  color: white;
}

.message-content p {
  margin: 0;
}

.time {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
  display: block;
}

.profile-content {
  text-align: center;
  padding: 20px;
}

.signature {
  color: #909399;
  margin: 15px 0;
}
</style>