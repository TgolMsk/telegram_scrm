<template>
  <el-button
      :type="row?.process_result !== 1 ? 'info' : 'primary'"
      :disabled="isLoading"
      :loading="isLoading"
      round
      @click="start_process"
  >
    {{ row?.process_result === 1 ? '停止' : '启动' }}
  </el-button>
</template>

<script lang="ts">
import { defineComponent, ref } from "vue";
import { inject } from 'vue';
import { ElMessage } from 'element-plus'
import { startProcess } from './api'

export default defineComponent({
  name: "Telegram_process",
  setup() {
    const { row } = inject('get:scope')()
    const isLoading = ref(false)

    const start_process = async () => {
      if (isLoading.value) return

      isLoading.value = true
      try {
        await startProcess(row.id)
        row.process_result = row.process_result === 1 ? 3 : 1
        ElMessage.success('操作成功')
      } catch (error) {
        ElMessage.error('操作失败')
      } finally {
        // 添加500ms缓冲防止快速连续点击
        setTimeout(() => {
          isLoading.value = false
        }, 500)
      }
    }

    return { row, isLoading, start_process }
  }
});
</script>