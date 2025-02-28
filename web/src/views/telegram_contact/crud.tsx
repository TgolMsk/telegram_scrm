import { CrudOptions, AddReq, DelReq, EditReq, dict, CrudExpose, UserPageQuery, CreateCrudOptionsRet} from '@fast-crud/fast-crud';
import _ from 'lodash-es';
import * as api from './api';
import { request } from '/@/utils/service';
import {auth} from "/@/utils/authFunction";

export default function ({ crudExpose}: { crudExpose: CrudExpose}): CreateCrudOptionsRet {
    const pageRequest = async (query: any) => {
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
                        show: auth('TelegramContactViewSet:Export'),
                        text:"导出",
                        title:"导出",
                        click(){
                            return exportRequest(crudExpose.getSearchFormData())
                        }
                    },
                    add: {
                        show: auth('TelegramContactViewSet:Create'),
                    },
                }
            },
            rowHandle: {
                fixed: 'right',
                width: 200,
                buttons: {
                    view: {
                        type: 'text',
                        order: 1,
                        show: auth('TelegramContactViewSet:Retrieve')
                    },
                    edit: {
                        type: 'text',
                        order: 2,
                        show: auth('TelegramContactViewSet:Update')
                    },
                    copy: {
                        type: 'text',
                        order: 3,
                        show: auth('TelegramContactViewSet:Copy')
                    },
                    remove: {
                        type: 'text',
                        order: 4,
                        show: auth('TelegramContactViewSet:Delete')
                    },
                },
            },
            columns: {
                account: {
                    title: '所属账号',
                    type: 'dict-select',
                    search: { show: true },
                    dict: dict({
                        url: '/api/TelegramModelViewSet/',
                        value: 'id',
                        label: 'username'
                    }),
                    form: {
                        rules: [{ required: true, message: '必须选择关联账号' }],
                        component: {
                            props: {
                                filterable: true,
                                remote: true,
                                remoteMethod: async (query: string) => {
                                    const res = await request({
                                        url: '/api/TelegramModelViewSet/',
                                        params: { search: query }
                                    });
                                    return res.data.map((item: any) => ({
                                        value: item.id,
                                        label: item.username
                                    }));
                                }
                            }
                        }
                    }
                },
                contact_id: {
                    title: '用户ID',
                    type: 'number',
                    search: { show: true },
                    form: {
                        rules: [{ required: true, message: '用户ID必填' }],
                        component: {
                            placeholder: 'Telegram用户唯一ID',
                            precision: 0
                        }
                    }
                },
                user_status: {
                    title: '最近在线时间',
                    type: 'text',
                    search: { show: true }
                },
                phone_number: {
                    title: '手机号',
                    type: 'text',
                    form: {
                        rules: [{
                            pattern: /^\+\d{1,3}\d{4,14}$/,
                            message: '格式：+国际区号号码（例如：+8613812345678）'
                        }]
                    }
                },
                username: {
                    title: '用户名',
                    type: 'text',
                    form: {
                        component: {
                            prefix: '@',
                            placeholder: '例如：zhangsan'
                        }
                    }
                },
                first_name: { title: '名字', type: 'text' },
                last_name: { title: '姓氏', type: 'text' },
                remark: { title: '备注名称', type: 'text' },
                premium: {
                    title: '会员状态',
                    type: 'dict-switch',
                    dict: dict({
                        data: [
                            { value: true, label: '会员' },
                            { value: false, label: '普通' }
                        ]
                    })
                },
                last_interaction: {
                    title: '最后互动',
                    type: 'datetime',
                    form: {
                        component: {
                            format: 'YYYY-MM-DD HH:mm:ss',
                            valueFormat: 'YYYY-MM-DD HH:mm:ss'
                        }
                    }
                },
                message_count: {
                    title: '消息总数',
                    type: 'number',
                    column: {
                        component: {
                            show: false
                        }
                    }
                },
                schedule_enabled: {
                    title: '定时消息',
                    type: 'dict-switch',
                    dict: dict({
                        data: [
                            { value: true, label: '启用' },
                            { value: false, label: '停用' }
                        ]
                    })
                },
                ai_chat_switch: {
                    title: 'AI回复',
                    type: 'dict-switch',
                    dict: dict({
                        data: [
                            { value: true, label: '开启' },
                            { value: false, label: '关闭' }
                        ]
                    })
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
                    form: {
                        show: false
                    }
                }
            }
        }
    };
}