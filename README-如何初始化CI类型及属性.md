# CMDB 预置配置项类型扩展指南

本指南说明如何在代码层面预定义 CMDB 的配置项类型（CI Types），以便系统部署时自动初始化这些类型及其默认属性。

## 1. 核心文件位置

所有预置类型的定义均位于后端代码的以下文件中：

*   **文件路径**: [app/core/cmdb/ci_types.py](file:///app/core/cmdb/ci_types.py)
*   **核心类**: [CITypeDefinition](file:///app/core/cmdb/ci_types.py#39-49) (类型定义), [AttributeSchema](file:///app/core/cmdb/ci_types.py#9-37) (属性定义)
*   **注册列表**: `PRESET_CI_TYPES` (位于文件末尾)

## 2. 添加步骤

### 第一步：定义类型变量

在 [app/core/cmdb/ci_types.py](file:///app/core/cmdb/ci_types.py) 中，创建一个新的 [CITypeDefinition](file:///app/core/cmdb/ci_types.py#39-49) 实例。建议参照现有的 `SERVER_CI_TYPE` 或 `DATABASE_CI_TYPE` 进行定义。

```python
NEW_DEVICE_TYPE = CITypeDefinition(
    code="load_balancer",       # [必填] 类型编码，全局唯一，建议英文小写
    name="负载均衡器",          # [必填] 显示名称
    icon="network",             # [选填] 图标名称 (对应前端 lucide-react 图标)
    description="硬件或软件负载均衡设备",
    category="infrastructure",  # [必填] 分类: infrastructure, virtualization, container, application
    identifier_rule="{hostname}", # [选填] 唯一标识生成规则
    attributes=[
        # 在这里定义默认属性
        AttributeSchema(
            name="vip",         # 属性编码 (英)
            label="虚拟IP",      # 属性标签 (中)
            type="string",      # 类型: string, number, boolean, date, enum, user, ci_ref
            required=True,      # 是否必填
            unique=True,        # 是否唯一
            group="基本信息",    # UI分组
            widget="input",     # UI控件
            regex=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$" # 正则校验
        ),
        AttributeSchema(
            name="algorithm",
            label="调度算法",
            type="enum",
            group="配置信息",
            widget="select",
            options=[           # 枚举选项
                {"label": "轮询", "value": "rr"},
                {"label": "加权轮询", "value": "wrr"},
                {"label": "最小连接", "value": "lc"}
            ]
        )
    ]
)
```

### 第二步：注册到列表

在文件末尾的 `PRESET_CI_TYPES` 列表中添加刚才定义的变量名。**如果不添加，系统将不会初始化该类型**。

```python
# ... 现有代码 ...

PRESET_CI_TYPES = [
    SERVER_CI_TYPE,
    NETWORK_CI_TYPE,
    # ... 其他现有类型 ...
    
    NEW_DEVICE_TYPE,  # <--- 添加这一行
]
```

## 3. 属性配置详解

[AttributeSchema](file:///app/core/cmdb/ci_types.py#9-37) 支持丰富的配置参数：

| 参数名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| `name` | str | 属性的唯一编码 | `cpu_count` |
| `label` | str | 前端显示的名称 | `CPU核心数` |
| [type](file:///app/api/cmdb.py#181-201) | str | `string`, `number`, `boolean`, [date](file:///app/core/cmdb/service.py#166-194), `enum` (枚举), `user` (用户选择), `ci_ref` (关联其他CI) | `number` |
| `required` | bool | 是否必填 | `True` |
| [default](file:///app/core/cmdb/kafka.py#43-93) | Any | 默认值 | `0` |
| `group` | str | 详情页属性分组名称 | `硬件配置` |
| `widget` | str | `input`, `textarea`, `select`, `number`, `datepicker`, `user-selector`, `ci-selector` | `input` |
| `unique` | bool | 数据库级唯一校验 | `True` |
| `regex` | str | 正则表达式校验 | `^\d{3}$` |
| `options` | list | 枚举选项列表 (`type='enum'` 时必填) | `[{"label":"A","value":"a"}]` |
| `ref_type` | str | 关联的 CI 类型编码 (`type='ci_ref'` 时必填) | `server` |

## 4. 生效机制

1.  **触发时机**：当调用“获取配置项类型列表”接口 (`GET /api/v1/cmdb/types`) 时，系统会自动检查并初始化。
2.  **增量更新**：
    *   如果数据库中**不存在**该类型编码：系统会**创建**该类型及其所有属性。
    *   如果已存在但**属性为空**：系统会**补充**默认属性。
    *   如果已存在且**已有属性**：为防止覆盖用户的手动修改，系统**默认跳过**更新（仅在日志中记录）。
    *(注：如需强制更新现有类型的定义，需在数据库中删除该类型或修改初始化逻辑)*
