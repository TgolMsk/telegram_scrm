import { CrudOptions, AddReq, DelReq, EditReq, dict, CrudExpose, UserPageQuery, CreateCrudOptionsRet} from '@fast-crud/fast-crud';
import _ from 'lodash-es';
import * as api from './api';
import { request } from '/@/utils/service';
import {auth} from "/@/utils/authFunction";
import QrCodeScan from "./verification.vue"
import Telegram_process from "./telegram_process.vue"
import {dictionary} from "/@/utils/dictionary";
import NewMessage from "./new_message.vue";

//此处为crudOptions配置
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
                    export: {
                        show: auth('TelegramViewSet:Export'),  // 修改权限标识
                        text: "导出",
                        title: "导出",
                        click() {
                            return exportRequest(crudExpose.getSearchFormData())
                        }
                    },
                    add: {
                        show: auth('TelegramModelViewSet:Create'),  // 修改权限标识
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
                        show: auth('TelegramModelViewSet:Retrieve')  // 修改权限标识
                    },
                    edit: {
                        type: 'text',
                        order: 2,
                        show: auth('TelegramModelViewSet:Update')  // 修改权限标识
                    },
                    copy: {
                        type: 'text',
                        order: 3,
                        show: auth('TelegramModelViewSet:Copy')  // 修改权限标识
                    },
                    remove: {
                        type: 'text',
                        order: 4,
                        show: auth('TelegramModelViewSet:Delete')  // 修改权限标识
                    },
                },
            },
            columns: {
                phone_number: {
                    title: 'TG手机号',
                    type: 'input',
                    search: { show: true },
                    column: {
                        minWidth: 160,
                        sortable: true,
                    },
                    form: {

                        rules: [
                            { required: true, message: '手机号必填' },
                            { pattern: /^\+\d{7,15}$/, message: '格式示例: +79991234567' }
                        ],
                        component: {
                            placeholder: '带国家代码的完整电话号码',
                        },
                        helper: '带国家代码的完整电话号码，例如+79991234567'
                    }
                },
                status: {
                    title: '连接状态',
                    type: 'dict-select',
                    dict: dict({
                        data: dictionary('telegram_account_status'),
                    }),
                    form: {
                    },
                    column: {
                        width: 120,
                    }
                },
                telegram_id: {
                    title: 'Telegram ID',
                    type: 'number',
                    column: {
                        width: 150,
                        sortable: true
                    },
                    form: {
                    show:false
                        },
                },
                session_string: {
                    title: '会话密钥',
                    type: 'textarea',
                    form: {
                        show:false,
                        component: {
                            showWordLimit: true,
                            rows: 3,
                            placeholder: 'Telethon生成的session字符串'
                        },
                        helper: '明文存储，请确保系统安全'
                    },
                    column: {
                        show: false // 敏感信息通常不在列表显示
                    }
                },
                qr_code: {
                    title: "扫码/验证码",
                    type: "text",
                    column: {
                        component: {
                            //引用自定义组件
                            name: QrCodeScan,
                        }
                    },
                    form: {
                        show:false,
                    },
                },
                last_active: {
                    title: '最后活跃',
                    type: 'datetime',
                    form: {
                        show:false,
                        component: {
                            format: 'YYYY-MM-DD HH:mm:ss',
                            valueFormat: 'YYYY-MM-DD HH:mm:ss'
                        }
                    },
                    column: {
                        show: false,
                        width: 180,
                        component: { name: 'fs-date-format', format: 'YYYY-MM-DD HH:mm' }
                    }
                },
                new_message: {
                    title: "消息",
                    type: "text",
                    column: {
                        component: {
                            //引用自定义组件
                            name: NewMessage,
                        }
                    },
                    form: {
                        show:false,
                    },
                },
                device_model: {
                    title: '设备标识',
                    type: 'input',
                    search: { show: true },
                    form: {
                        show:false,
                        component: {
                            placeholder: '例如: Telegram Desktop 4.2.3'
                        }
                    }
                },
                created_at: {
                    title: '创建时间',
                    type: 'datetime',
                    form: {
                        show:false,
                        component: {
                            disabled: true // 创建时间通常不可编辑
                        }
                    },
                    column: {
                        width: 180,
                        component: { name: 'fs-date-format', format: 'YYYY-MM-DD HH:mm' }
                    }
                },
                process_result: {
                    title: "进程控制",
                    type: "text",
                    column: {
                        component: {
                            //引用自定义组件
                            name: Telegram_process,
                        }
                    },
                    form: {
                        show:false,
                    },

                },
                login_mode: {
                    title: '登录模式',
                    type: 'dict-select',
                    dict: dict({
                        data: [
                            { label: '消息',value: 1 },
                            { label: '扫码' ,value: 2},
                            { label: '短信',value: 3 }
                        ]
                    }),
                    column: {
                        width: 100
                    }
                }
            }
        }
    }
}
