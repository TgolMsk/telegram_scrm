import { CrudOptions, AddReq, DelReq, EditReq, dict, CrudExpose, UserPageQuery, CreateCrudOptionsRet} from '@fast-crud/fast-crud';
import _ from 'lodash-es';
import * as api from './api';
import { request } from '/@/utils/service';
import {auth} from "/@/utils/authFunction";
import {useRoute} from "vue-router";
import {dictionary} from "/@/utils/dictionary";
import Account_sendmessage from "/@/views/telegram_contact/sendmessage.vue";

//此处为crudOptions配置
export default function ({ crudExpose}: { crudExpose: CrudExpose}): CreateCrudOptionsRet {
    const pageRequest = async (query: any) => {
        const route = useRoute()
        if (route?.params?.account) {
            if (route.params.account) {
                const contactId = route.params.account
                if(contactId==="account"){
                    return await api.GetList(query);
                }
                if(contactId){
                    query.account= contactId
                }
            }
        }


        return await api.GetList(query);
    };
    const editRequest = async ({ form, row }: EditReq) => {
        if (row.id) {
            form.id = row.id;
        }
        return await api.UpdateObj(form);
    };
    const delRequest = async ({ row }: DelReq) => {
        return await api.DelObj(row.id);
    };
    const addRequest = async ({ form }: AddReq) => {
        return await api.AddObj(form);
    };

    const exportRequest = async (query: UserPageQuery) => {
        return await api.exportData(query)
    };

    return {
        crudOptions: {
            request: {
                pageRequest,
                addRequest,
                editRequest,
                delRequest,
            },
            actionbar: {
                buttons: {
                    export:{
                        // 注释编号:django-vue3-admin-crud210716:注意这个auth里面的值，最好是使用index.vue文件里面的name值并加上请求动作的单词
                        show: auth('CrudDemoModelViewSet:Export'),
                        text:"导出",//按钮文字
                        title:"导出",//鼠标停留显示的信息
                        click(){
                            return exportRequest(crudExpose.getSearchFormData())
                            // return exportRequest(crudExpose!.getSearchFormData())    // 注意这个crudExpose!.getSearchFormData()，一些低版本的环境是需要添加!的
                        }
                    },
                    add: {
                        show: auth('CrudDemoModelViewSet:Create'),
                    },
                }
            },
            rowHandle: {
                //固定右侧
                fixed: 'right',
                width: 200,
                buttons: {
                    view: {
                        type: 'text',
                        order: 1,
                        show: auth('TelegramContactModelViewSet:Retrieve')
                    },
                    edit: {
                        type: 'text',
                        order: 2,
                        show: auth('TelegramContactModelViewSet:Update')
                    },
                    copy: {
                        type: 'text',
                        order: 3,
                        show: auth('TelegramContactModelViewSet:Copy')
                    },
                    remove: {
                        type: 'text',
                        order: 4,
                        show: auth('TelegramContactModelViewSet:Delete')
                    },
                },
            },
            columns: {
                account_list: {
                    title: "发起会话",
                    type: "text",
                    column: {
                        component: {
                            //引用自定义组件
                            name: Account_sendmessage,
                        }
                    },
                    form: {
                        show:false,
                    },

                },
                contact_id: {
                    title: '用户ID',
                    type: 'number',
                    search: { show: true },
                    form: {
                       show:false,
                    }
                },
                user_status: {
                    title: '最近在线时间',
                    type: 'text',
                    form: {
                        show:false,
                    },
                    search: { show: true }
                },
                phone_number: {
                    title: '手机号',
                    type: 'text',
                    form: {
                        show:false,
                    },
                },
                username: {
                    title: '用户名',
                    type: 'text',
                    form: {
                        show:false,
                    },
                },
                first_name: {
                    title: '名字', type: 'text' ,
                    form: {
                        show:false,
                    },
                },
                last_name: {
                    title: '姓氏', type: 'text' ,
                    form: {
                        show:false,
                    },
                },
                remark: {
                    title: '备注名称', type: 'text',
                    form: {
                        show:false,
                    },
                },
                premium: {
                    title: '会员状态',
                    type: 'dict-switch',
                    form: {
                        show:false,
                    },
                },
                last_interaction: {
                    title: '最后互动',
                    type: 'datetime',
                    form: {
                        show:false,
                    },
                },
                message_count: {
                    title: '消息总数',
                    type: 'number',
                    form: {
                        show:false,
                    },
                },
                schedule_enabled: {
                    title: '定时消息',
                    type: 'dict-switch',
                    dict: dict({
                        data: dictionary('button_status_bool'),
                    }),
                },
                ai_chat_switch: {
                    title: 'AI回复',
                    type: 'dict-switch',
                    dict: dict({
                        data: dictionary('button_status_bool'),
                    }),
                },
                ai_reply_delay_config: {
                    title: '延迟设置',
                    type: 'text',
                    column: {
                    },
                    form: {
                    }
                },
                ai_session_id: {
                    title: 'AI会话ID',
                    type: 'text',
                    column: {
                        show: false
                    },

                }
            }
        },
    };
}