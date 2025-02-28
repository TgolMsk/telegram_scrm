<template>
  <el-button
      type="primary"
      size="small"
      @click="handleClick">
    执行操作
  </el-button>
  <div>sss</div>
</template>

<script setup lang="ts">
import { inject } from 'vue';

const props = defineProps({
  row: {
    type: Object,
    required: true
  }
});

// 获取父组件注入的方法
const emitAction = inject('custom-action') as Function;

const handleClick = () => {
  // 直接调用父组件方法
  emitAction(props.row);
};
</script>