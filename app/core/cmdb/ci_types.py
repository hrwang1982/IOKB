"""
CMDB预置配置项类型定义
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AttributeSchema:
    """属性Schema定义"""
    name: str
    label: str
    type: str  # string, number, boolean, date, json, enum, user, ci_ref
    required: bool = False
    default: Any = None
    options: Optional[List[Dict[str, Any]]] = None  # enum类型的选项 [{"label": "A", "value": "a"}]
    description: str = ""
    
    # UI 展示
    group: str = "基本信息"  # 分组名称
    order: int = 0         # 排序权重
    widget: str = "input"  # 控件类型: input, select, datepicker, user-selector, ci-selector, textarea, number
    placeholder: str = ""
    hidden: bool = False
    readonly: bool = False
    
    # 数据验证
    unique: bool = False
    regex: str = ""
    min_val: float = None
    max_val: float = None
    
    # 引用配置
    ref_type: str = ""      # 引用类型 (User, Department, CI类型编码)
    ref_filter: Dict = None # 引用过滤条件


@dataclass
class CITypeDefinition:
    """配置项类型定义"""
    code: str
    name: str
    icon: str
    description: str
    category: str  # infrastructure, virtualization, container, application
    attributes: List[AttributeSchema]


# ==================== 预置配置项类型 ====================

# ----------------- 基础设施类 -----------------

SERVER_CI_TYPE = CITypeDefinition(
    code="server",
    name="物理服务器",
    icon="server",
    description="物理服务器设备",
    category="infrastructure",
    attributes=[
        # 基本信息
        AttributeSchema("vendor", "厂商", "string", group="基本信息", widget="input", order=1),
        AttributeSchema("model", "型号", "string", group="基本信息", widget="input", order=2),
        AttributeSchema("serial_number", "序列号", "string", required=True, unique=True, group="基本信息", widget="input", order=3, placeholder="输入设备SN号"),
        AttributeSchema("asset_tag", "资产标签", "string", unique=True, group="基本信息", widget="input", order=4),
        AttributeSchema("purchase_date", "采购日期", "date", group="基本信息", widget="datepicker", order=5),
        AttributeSchema("warranty_expire_date", "维保到期日", "date", group="基本信息", widget="datepicker", order=6),
        
        # 硬件配置
        AttributeSchema("cpu_model", "CPU型号", "string", group="硬件配置", widget="input", order=10),
        AttributeSchema("cpu_count", "CPU颗数", "number", group="硬件配置", widget="number", min_val=1, order=11),
        AttributeSchema("cpu_cores", "单颗核心数", "number", group="硬件配置", widget="number", min_val=1, order=12),
        AttributeSchema("memory_gb", "内存(GB)", "number", group="硬件配置", widget="number", min_val=1, order=13),
        AttributeSchema("disk_tb", "磁盘(TB)", "number", group="硬件配置", widget="number", order=14),
        
        # 网络信息
        AttributeSchema("management_ip", "管理IP", "string", required=True, unique=True, group="网络信息", widget="input", regex=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", order=20),
        AttributeSchema("business_ip", "业务IP", "string", group="网络信息", widget="input", regex=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", order=21),
        AttributeSchema("mac_address", "MAC地址", "string", group="网络信息", widget="input", order=22),
        
        # 位置信息
        AttributeSchema("location", "机房位置", "string", group="位置信息", widget="input", order=30),
        AttributeSchema("rack", "机架号", "string", group="位置信息", widget="input", order=31),
        AttributeSchema("u_position", "U位", "number", group="位置信息", widget="number", order=32),
        
        # 管理信息
        AttributeSchema("admin", "管理员", "user", group="管理信息", widget="user-selector", order=40),
        AttributeSchema("status_desc", "状态描述", "string", group="管理信息", widget="textarea", order=41),
    ],
)

NETWORK_CI_TYPE = CITypeDefinition(
    code="network",
    name="网络设备",
    icon="router",
    description="包括交换机、路由器、防火墙等网络设备",
    category="infrastructure",
    attributes=[
        AttributeSchema("device_type", "设备类型", "enum", required=True, group="基本信息", widget="select", order=1, 
                       options=[
                           {"label": "交换机", "value": "Switch"},
                           {"label": "路由器", "value": "Router"},
                           {"label": "防火墙", "value": "Firewall"},
                           {"label": "负载均衡", "value": "LoadBalancer"}
                       ]),
        AttributeSchema("vendor", "厂商", "string", group="基本信息", widget="input", order=2),
        AttributeSchema("model", "型号", "string", group="基本信息", widget="input", order=3),
        AttributeSchema("serial_number", "序列号", "string", unique=True, group="基本信息", widget="input", order=4),
        AttributeSchema("firmware_version", "固件版本", "string", group="基本信息", widget="input", order=5),
        
        AttributeSchema("management_ip", "管理IP", "string", required=True, unique=True, group="网络信息", widget="input", order=10),
        AttributeSchema("port_count", "端口数量", "number", group="规格参数", widget="number", order=11),
        
        AttributeSchema("location", "机房位置", "string", group="位置信息", widget="input", order=20),
        AttributeSchema("rack", "机架号", "string", group="位置信息", widget="input", order=21),
    ],
)

STORAGE_CI_TYPE = CITypeDefinition(
    code="storage",
    name="存储设备",
    icon="database",
    description="SAN、NAS等存储设备",
    category="infrastructure",
    attributes=[
        AttributeSchema("storage_type", "存储类型", "enum", required=True, group="基本信息", widget="select", order=1,
                       options=[{"label": "SAN", "value": "SAN"}, {"label": "NAS", "value": "NAS"}, {"label": "Object", "value": "Object"}]),
        AttributeSchema("vendor", "厂商", "string", group="基本信息", widget="input", order=2),
        AttributeSchema("model", "型号", "string", group="基本信息", widget="input", order=3),
        
        AttributeSchema("total_capacity", "总容量(TB)", "number", group="容量信息", widget="number", order=10),
        AttributeSchema("used_capacity", "已用容量(TB)", "number", group="容量信息", widget="number", order=11),
        AttributeSchema("available_capacity", "可用容量(TB)", "number", group="容量信息", widget="number", order=12),
        
        AttributeSchema("management_ip", "管理IP", "string", group="网络信息", widget="input", order=20),
        AttributeSchema("location", "机房位置", "string", group="位置信息", widget="input", order=30),
    ],
)

# ----------------- 操作系统类 -----------------

OS_LINUX_CI_TYPE = CITypeDefinition(
    code="os_linux",
    name="Linux系统",
    icon="linux",
    description="Linux操作系统",
    category="infrastructure",
    attributes=[
        AttributeSchema("hostname", "主机名", "string", required=True, unique=True, group="基本信息", widget="input", order=1),
        AttributeSchema("distribution", "发行版", "enum", group="基本信息", widget="select", order=2,
                       options=[{"label": "CentOS", "value": "CentOS"}, {"label": "Ubuntu", "value": "Ubuntu"}, {"label": "RedHat", "value": "RedHat"}, {"label": "Debian", "value": "Debian"}]),
        AttributeSchema("os_version", "系统版本", "string", group="基本信息", widget="input", order=3),
        AttributeSchema("kernel_version", "内核版本", "string", group="基本信息", widget="input", order=4),
        
        AttributeSchema("ip_address", "IP地址", "string", required=True, group="网络信息", widget="input", order=10),
        AttributeSchema("mac_address", "MAC地址", "string", group="网络信息", widget="input", order=11),
        
        AttributeSchema("cpu_cores", "CPU核心数", "number", group="资源规格", widget="number", order=20),
        AttributeSchema("memory_gb", "内存(GB)", "number", group="资源规格", widget="number", order=21),
        AttributeSchema("disk_gb", "磁盘(GB)", "number", group="资源规格", widget="number", order=22),
        
        AttributeSchema("install_date", "安装时间", "date", group="管理信息", widget="datepicker", order=30),
    ],
)

OS_WINDOWS_CI_TYPE = CITypeDefinition(
    code="os_windows",
    name="Windows系统",
    icon="windows",
    description="Windows操作系统",
    category="infrastructure",
    attributes=[
        AttributeSchema("hostname", "主机名", "string", required=True, unique=True, group="基本信息", widget="input", order=1),
        AttributeSchema("version", "系统版本", "enum", group="基本信息", widget="select", order=2,
                       options=[{"label": "Server 2012", "value": "Server 2012"}, {"label": "Server 2016", "value": "Server 2016"}, {"label": "Server 2019", "value": "Server 2019"}, {"label": "Server 2022", "value": "Server 2022"}]),
        AttributeSchema("edition", "版本类型", "string", group="基本信息", widget="input", order=3),
        AttributeSchema("build_number", "Build号", "string", group="基本信息", widget="input", order=4),
        
        AttributeSchema("ip_address", "IP地址", "string", required=True, group="网络信息", widget="input", order=10),
        
        AttributeSchema("cpu_cores", "CPU核心数", "number", group="资源规格", widget="number", order=20),
        AttributeSchema("memory_gb", "内存(GB)", "number", group="资源规格", widget="number", order=21),
        AttributeSchema("disk_gb", "磁盘(GB)", "number", group="资源规格", widget="number", order=22),
    ],
)

# ----------------- 虚拟化类 -----------------

VMWARE_VCENTER_CI_TYPE = CITypeDefinition(
    code="vmware_vcenter",
    name="vCenter集群",
    icon="vmware",
    description="VMware vCenter Server",
    category="virtualization",
    attributes=[
        AttributeSchema("name", "vCenter名称", "string", required=True, group="基本信息", widget="input", order=1),
        AttributeSchema("version", "版本", "string", group="基本信息", widget="input", order=2),
        AttributeSchema("api_address", "API地址", "string", required=True, group="基本信息", widget="input", order=3),
        
        AttributeSchema("datacenter_count", "数据中心数", "number", group="规模统计", widget="number", readonly=True, order=10),
        AttributeSchema("cluster_count", "集群数", "number", group="规模统计", widget="number", readonly=True, order=11),
        AttributeSchema("host_count", "主机数", "number", group="规模统计", widget="number", readonly=True, order=12),
        AttributeSchema("vm_count", "虚拟机数", "number", group="规模统计", widget="number", readonly=True, order=13),
    ],
)

VMWARE_ESXI_CI_TYPE = CITypeDefinition(
    code="vmware_esxi",
    name="ESXi主机",
    icon="vmware",
    description="VMware ESXi主机",
    category="virtualization",
    attributes=[
        AttributeSchema("hostname", "主机名", "string", required=True, unique=True, group="基本信息", widget="input", order=1),
        AttributeSchema("version", "ESXi版本", "string", group="基本信息", widget="input", order=2),
        AttributeSchema("management_ip", "管理IP", "string", group="基本信息", widget="input", order=3),
        AttributeSchema("cluster_name", "所属集群", "string", group="基本信息", widget="input", order=4),
        
        AttributeSchema("cpu_model", "CPU型号", "string", group="硬件信息", widget="input", order=10),
        AttributeSchema("cpu_cores", "逻辑CPU数", "number", group="硬件信息", widget="number", order=11),
        AttributeSchema("memory_gb", "物理内存(GB)", "number", group="硬件信息", widget="number", order=12),
        
        AttributeSchema("vcenter", "所属vCenter", "ci_ref", group="关联信息", widget="ci-selector", ref_type="vmware_vcenter", order=20),
    ],
)

# ----------------- 容器类 -----------------

K8S_CLUSTER_CI_TYPE = CITypeDefinition(
    code="k8s_cluster",
    name="K8s集群",
    icon="kubernetes",
    description="Kubernetes集群",
    category="container",
    attributes=[
        AttributeSchema("cluster_name", "集群名称", "string", required=True, unique=True, group="基本信息", widget="input", order=1),
        AttributeSchema("version", "K8s版本", "string", group="基本信息", widget="input", order=2),
        AttributeSchema("distribution", "发行版", "enum", group="基本信息", widget="select", order=3,
                        options=[{"label": "Vanilla", "value": "Vanilla"}, {"label": "OpenShift", "value": "OpenShift"}, {"label": "Rancher", "value": "Rancher"}, {"label": "ACK", "value": "ACK"}, {"label": "TKE", "value": "TKE"}]),
        AttributeSchema("api_server_url", "API Server URL", "string", group="基本信息", widget="input", order=4),
        
        AttributeSchema("node_count", "节点数量", "number", group="规模统计", widget="number", readonly=True, order=10),
        AttributeSchema("pod_count", "Pod数量", "number", group="规模统计", widget="number", readonly=True, order=11),
    ],
)

K8S_POD_CI_TYPE = CITypeDefinition(
    code="k8s_pod",
    name="K8s Pod",
    icon="kubernetes",
    description="Kubernetes Pod",
    category="container",
    attributes=[
        AttributeSchema("pod_name", "Pod名称", "string", required=True, group="基本信息", widget="input", order=1),
        AttributeSchema("namespace", "命名空间", "string", required=True, group="基本信息", widget="input", order=2),
        AttributeSchema("cluster", "所属集群", "ci_ref", group="基本信息", widget="ci-selector", ref_type="k8s_cluster", order=3),
        
        AttributeSchema("pod_ip", "Pod IP", "string", group="运行信息", widget="input", order=10),
        AttributeSchema("node_name", "所在节点", "string", group="运行信息", widget="input", order=11),
        AttributeSchema("status", "状态", "enum", group="运行信息", widget="select", order=12,
                        options=[{"label": "Running", "value": "Running"}, {"label": "Pending", "value": "Pending"}, {"label": "Failed", "value": "Failed"}, {"label": "Succeeded", "value": "Succeeded"}]),
        
        AttributeSchema("restart_count", "重启次数", "number", group="监控指标", widget="number", order=20),
        AttributeSchema("cpu_usage", "CPU使用(m)", "number", group="监控指标", widget="number", order=21),
        AttributeSchema("memory_usage", "内存使用(Mi)", "number", group="监控指标", widget="number", order=22),
    ],
)

# ----------------- 应用类 -----------------

DATABASE_CI_TYPE = CITypeDefinition(
    code="database",
    name="数据库",
    icon="database",
    description="数据库服务实例",
    category="application",
    attributes=[
        AttributeSchema("instance_name", "实例名称", "string", required=True, group="基本信息", widget="input", order=1),
        AttributeSchema("db_type", "数据库类型", "enum", required=True, group="基本信息", widget="select", order=2,
                        options=[{"label": "MySQL", "value": "MySQL"}, {"label": "PostgreSQL", "value": "PostgreSQL"}, {"label": "Oracle", "value": "Oracle"}, {"label": "Redis", "value": "Redis"}, {"label": "MongoDB", "value": "MongoDB"}]),
        AttributeSchema("version", "版本", "string", group="基本信息", widget="input", order=3),
        AttributeSchema("port", "端口", "number", group="基本信息", widget="number", order=4),
        
        AttributeSchema("vip", "访问IP(VIP)", "string", group="连接信息", widget="input", order=10),
        AttributeSchema("connection_string", "连接串", "string", group="连接信息", widget="textarea", order=11),
        
        AttributeSchema("architecture", "架构模式", "enum", group="架构信息", widget="select", order=20,
                        options=[{"label": "单机", "value": "Standalone"}, {"label": "主从", "value": "Master-Slave"}, {"label": "集群", "value": "Cluster"}]),
        AttributeSchema("host", "关联主机", "ci_ref", group="架构信息", widget="ci-selector", ref_type="server", order=21),
        
        AttributeSchema("admin", "DBA负责人", "user", group="管理信息", widget="user-selector", order=30),
        AttributeSchema("app_system", "归属系统", "string", group="管理信息", widget="input", order=31),
    ],
)

APPLICATION_CI_TYPE = CITypeDefinition(
    code="application",
    name="业务应用",
    icon="app",
    description="业务应用系统",
    category="application",
    attributes=[
        AttributeSchema("app_code", "应用编码", "string", required=True, unique=True, group="基本信息", widget="input", order=1),
        AttributeSchema("app_name", "应用名称", "string", required=True, group="基本信息", widget="input", order=2),
        AttributeSchema("level", "重要级别", "enum", group="基本信息", widget="select", order=3,
                        options=[{"label": "核心", "value": "P0"}, {"label": "重要", "value": "P1"}, {"label": "一般", "value": "P2"}]),
        
        AttributeSchema("department", "所属部门", "string", group="组织架构", widget="input", order=10),
        AttributeSchema("product_owner", "产品负责人", "user", group="组织架构", widget="user-selector", order=11),
        AttributeSchema("tech_owner", "技术负责人", "user", group="组织架构", widget="user-selector", order=12),
        
        AttributeSchema("access_url", "访问地址", "string", group="部署信息", widget="input", order=20),
        AttributeSchema("repo_url", "代码仓库", "string", group="部署信息", widget="input", order=21),
        
        AttributeSchema("description", "应用描述", "string", group="其他", widget="textarea", order=30),
    ],
)


# 所有预置类型列表
PRESET_CI_TYPES = [
    # 基础设施
    SERVER_CI_TYPE,
    NETWORK_CI_TYPE,
    STORAGE_CI_TYPE,
    OS_LINUX_CI_TYPE,
    OS_WINDOWS_CI_TYPE,
    # 虚拟化
    VMWARE_VCENTER_CI_TYPE,
    VMWARE_ESXI_CI_TYPE,
    # 容器
    K8S_CLUSTER_CI_TYPE,
    K8S_POD_CI_TYPE,
    # 应用
    DATABASE_CI_TYPE,
    APPLICATION_CI_TYPE,
]


def get_ci_type_by_code(code: str) -> Optional[CITypeDefinition]:
    """根据编码获取CI类型定义"""
    for ci_type in PRESET_CI_TYPES:
        if ci_type.code == code:
            return ci_type
    return None


def get_ci_types_by_category(category: str) -> List[CITypeDefinition]:
    """根据分类获取CI类型列表"""
    return [ct for ct in PRESET_CI_TYPES if ct.category == category]
