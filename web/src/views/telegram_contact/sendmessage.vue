<template>
  <div>
    <el-button type="success" :icon="ChatDotRound"   >发起聊天</el-button>
  </div>
</template>

<script lang="ts">
import {defineComponent, onMounted} from "vue";
import { inject } from 'vue';
import { Grid, ChatDotRound, Search, Share, Upload } from '@element-plus/icons-vue'

import {
  FullScreen,
  EditPen,
} from '@element-plus/icons-vue'
import { reactive, ref } from 'vue'
export default defineComponent(
    {
      name: "QrCodeScan",
      setup() {
        const getScope = inject('get:scope')
        const { index, row, mode} = getScope()
        return {
          row:row,
          FullScreen,
          EditPen,
          Grid,
          ChatDotRound
        };
      }
    });
</script>