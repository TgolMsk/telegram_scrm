<template>
<!--  扫码-->
  <el-button type="primary" :icon="FullScreen"  v-if="row.login_mode === 2"  circle round @click="open_qr"/>
<!--  <el-button type="primary" :icon="EditPen"  v-if="row.login_mode === 1"  circle round />-->
<!-- 验证码登录 -->
  <el-button type="primary"   :icon="EditPen"  v-if="row.login_mode === 1"   @click="open" circle round />

  <router-link :to="{ name: 'TelegramContactModelViewSet', params: { account: 2 }}">
    用户详情
  </router-link>

</template>

<script lang="ts">
import {ElMessage, ElMessageBox} from 'element-plus'
import {defineComponent, onMounted} from "vue";
import { inject } from 'vue';
import QRCode from 'qrcode' // 引入二维码库
import {in_Code} from './api'
import { useRouter } from 'vue-router'

import {
  FullScreen,
  EditPen,
} from '@element-plus/icons-vue'
import { reactive, ref } from 'vue'
export default defineComponent(
    {
  name: "QrCodeScan",
  setup() {





    const open = () => {
      ElMessageBox.prompt('请输入Telegram客户端接收到的验证码', '验证码登录', {
        confirmButtonText: '提交',
        cancelButtonText: '取消',
      })
          .then(async ({value}) => {
            await in_Code(row.id,value)
            ElMessage({
              type: 'success',
              message: `提交成功`,
            })
          })
         }



    const getScope = inject('get:scope')
    const { index, row, mode} = getScope()
    const open_qr = async () => {
      try {
        // 实时获取当前登录二维码

        // 生成二维码的DataURL
        const qrDataUrl = await QRCode.toDataURL(row.qr_url)
        ElMessageBox.alert(
            `<img src="${qrDataUrl}" style="width: 300px; height: 300px; display: block; margin: 0 auto;">`,
            "有效期："+row.qr_expires,
            {
              dangerouslyUseHTMLString: true,
              customClass: 'qr-modal', // 可添加自定义class
              confirmButtonText: '关闭',
              center: true,
              closeOnClickModal: true,
            }


        )
      } catch (error) {
        ElMessageBox.alert('二维码生成失败，请重试', '错误')
      }
    }
    return {
      row:row,
      open_qr,
      FullScreen,
      EditPen,
      open
    };
  }
});
</script>