<template>
  <!--  扫码-->
  <el-button type="danger" :icon="BellFilled"  v-if="row.new_message === true"  circle round />
  <!-- 验证码登录 -->
  <el-button type="info"   :icon="BellFilled"  v-if="row.new_message === false"   circle round />
</template>

<script lang="ts">
import {ElMessage, ElMessageBox} from 'element-plus'
import {defineComponent, onMounted} from "vue";
import { inject } from 'vue';

import {
  BellFilled,
} from '@element-plus/icons-vue'
export default defineComponent(
    {
      name: "NewMessage",
      setup() {
        const getScope = inject('get:scope')
        const { index, row, mode} = getScope()
        return {
          row:row,
          BellFilled,
        };
      }
    });
</script>