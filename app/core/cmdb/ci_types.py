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
    type: str  # string, number, boolean, date, json, enum
    required: bool = False
    default: Any = None
    options: Optional[List[str]] = None  # enum类型的选项
    description: str = ""


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

# 基础设施类
STORAGE_CI_TYPE = CITypeDefinition(
    code="storage",
    name="存储设备",
    icon="database",
    description="包括SAN、NAS、对象存储等存储设备",
    category="infrastructure",
    attributes=[
        AttributeSchema("vendor", "厂商", "string"),
        AttributeSchema("model", "型号", "string"),
        AttributeSchema("capacity", "总容量(TB)", "number"),
        AttributeSchema("used_capacity", "已用容量(TB)", "number"),
        AttributeSchema("storage_type", "存储类型", "enum", options=["SAN", "NAS", "Object", "Block"]),
        AttributeSchema("ip", "管理IP", "string"),
        AttributeSchema("location", "机房位置", "string"),
        AttributeSchema("serial_number", "序列号", "string"),
    ],
)

NETWORK_CI_TYPE = CITypeDefinition(
    code="network",
    name="网络设备",
    icon="router",
    description="包括交换机、路由器、防火墙等网络设备",
    category="infrastructure",
    attributes=[
        AttributeSchema("vendor", "厂商", "string"),
        AttributeSchema("model", "型号", "string"),
        AttributeSchema("device_type", "设备类型", "enum", options=["Switch", "Router", "Firewall", "LoadBalancer"]),
        AttributeSchema("management_ip", "管理IP", "string"),
        AttributeSchema("port_count", "端口数量", "number"),
        AttributeSchema("location", "机房位置", "string"),
        AttributeSchema("serial_number", "序列号", "string"),
    ],
)

SERVER_CI_TYPE = CITypeDefinition(
    code="server",
    name="物理服务器",
    icon="server",
    description="物理服务器设备",
    category="infrastructure",
    attributes=[
        AttributeSchema("vendor", "厂商", "string"),
        AttributeSchema("model", "型号", "string"),
        AttributeSchema("cpu", "CPU型号", "string"),
        AttributeSchema("cpu_cores", "CPU核心数", "number"),
        AttributeSchema("memory_gb", "内存(GB)", "number"),
        AttributeSchema("disk_tb", "磁盘(TB)", "number"),
        AttributeSchema("management_ip", "管理IP", "string"),
        AttributeSchema("business_ip", "业务IP", "string"),
        AttributeSchema("location", "机房位置", "string"),
        AttributeSchema("rack", "机架位置", "string"),
        AttributeSchema("serial_number", "序列号", "string"),
    ],
)

# 操作系统类
OS_LINUX_CI_TYPE = CITypeDefinition(
    code="os_linux",
    name="Linux系统",
    icon="linux",
    description="Linux操作系统",
    category="infrastructure",
    attributes=[
        AttributeSchema("distribution", "发行版", "enum", options=["CentOS", "Ubuntu", "RedHat", "SUSE", "Debian", "Other"]),
        AttributeSchema("version", "版本", "string"),
        AttributeSchema("kernel_version", "内核版本", "string"),
        AttributeSchema("hostname", "主机名", "string"),
        AttributeSchema("ip_address", "IP地址", "string"),
        AttributeSchema("cpu_cores", "CPU核心数", "number"),
        AttributeSchema("memory_gb", "内存(GB)", "number"),
        AttributeSchema("disk_gb", "磁盘(GB)", "number"),
    ],
)

OS_WINDOWS_CI_TYPE = CITypeDefinition(
    code="os_windows",
    name="Windows系统",
    icon="windows",
    description="Windows操作系统",
    category="infrastructure",
    attributes=[
        AttributeSchema("version", "版本", "enum", options=["Server 2012", "Server 2016", "Server 2019", "Server 2022"]),
        AttributeSchema("edition", "版本类型", "enum", options=["Standard", "Datacenter", "Enterprise"]),
        AttributeSchema("hostname", "主机名", "string"),
        AttributeSchema("ip_address", "IP地址", "string"),
        AttributeSchema("cpu_cores", "CPU核心数", "number"),
        AttributeSchema("memory_gb", "内存(GB)", "number"),
        AttributeSchema("disk_gb", "磁盘(GB)", "number"),
    ],
)

# VMware虚拟化类
VMWARE_VCENTER_CI_TYPE = CITypeDefinition(
    code="vmware_vcenter",
    name="vCenter集群",
    icon="vmware",
    description="VMware vCenter Server",
    category="virtualization",
    attributes=[
        AttributeSchema("version", "版本", "string"),
        AttributeSchema("address", "地址", "string"),
        AttributeSchema("datacenter_count", "数据中心数量", "number"),
        AttributeSchema("cluster_count", "集群数量", "number"),
        AttributeSchema("host_count", "主机数量", "number"),
        AttributeSchema("vm_count", "虚拟机数量", "number"),
    ],
)

VMWARE_ESXI_CI_TYPE = CITypeDefinition(
    code="vmware_esxi",
    name="ESXi主机",
    icon="vmware",
    description="VMware ESXi主机",
    category="virtualization",
    attributes=[
        AttributeSchema("version", "版本", "string"),
        AttributeSchema("hostname", "主机名", "string"),
        AttributeSchema("ip_address", "IP地址", "string"),
        AttributeSchema("cpu_model", "CPU型号", "string"),
        AttributeSchema("cpu_cores", "CPU核心数", "number"),
        AttributeSchema("memory_gb", "内存(GB)", "number"),
        AttributeSchema("vm_count", "虚拟机数量", "number"),
        AttributeSchema("status", "状态", "enum", options=["connected", "disconnected", "maintenance"]),
    ],
)

VMWARE_VM_CI_TYPE = CITypeDefinition(
    code="vmware_vm",
    name="虚拟机",
    icon="desktop",
    description="VMware虚拟机",
    category="virtualization",
    attributes=[
        AttributeSchema("vm_name", "虚拟机名称", "string"),
        AttributeSchema("guest_os", "操作系统", "string"),
        AttributeSchema("ip_address", "IP地址", "string"),
        AttributeSchema("cpu_cores", "CPU核心数", "number"),
        AttributeSchema("memory_gb", "内存(GB)", "number"),
        AttributeSchema("disk_gb", "磁盘(GB)", "number"),
        AttributeSchema("power_state", "电源状态", "enum", options=["poweredOn", "poweredOff", "suspended"]),
        AttributeSchema("esxi_host", "所在ESXi主机", "string"),
    ],
)

# K8s容器类
K8S_CLUSTER_CI_TYPE = CITypeDefinition(
    code="k8s_cluster",
    name="K8s集群",
    icon="kubernetes",
    description="Kubernetes集群",
    category="container",
    attributes=[
        AttributeSchema("cluster_name", "集群名称", "string"),
        AttributeSchema("version", "K8s版本", "string"),
        AttributeSchema("api_server", "API Server地址", "string"),
        AttributeSchema("node_count", "节点数量", "number"),
        AttributeSchema("namespace_count", "命名空间数量", "number"),
        AttributeSchema("pod_count", "Pod数量", "number"),
        AttributeSchema("distribution", "发行版", "enum", options=["Vanilla", "OpenShift", "Rancher", "ACK", "TKE", "Other"]),
    ],
)

K8S_NODE_CI_TYPE = CITypeDefinition(
    code="k8s_node",
    name="K8s节点",
    icon="kubernetes",
    description="Kubernetes节点",
    category="container",
    attributes=[
        AttributeSchema("node_name", "节点名称", "string"),
        AttributeSchema("ip_address", "IP地址", "string"),
        AttributeSchema("role", "角色", "enum", options=["master", "worker"]),
        AttributeSchema("os_image", "操作系统", "string"),
        AttributeSchema("kubelet_version", "Kubelet版本", "string"),
        AttributeSchema("cpu_capacity", "CPU容量", "string"),
        AttributeSchema("memory_capacity", "内存容量", "string"),
        AttributeSchema("status", "状态", "enum", options=["Ready", "NotReady", "Unknown"]),
    ],
)

K8S_POD_CI_TYPE = CITypeDefinition(
    code="k8s_pod",
    name="K8s Pod",
    icon="kubernetes",
    description="Kubernetes Pod",
    category="container",
    attributes=[
        AttributeSchema("pod_name", "Pod名称", "string"),
        AttributeSchema("namespace", "命名空间", "string"),
        AttributeSchema("ip_address", "IP地址", "string"),
        AttributeSchema("node_name", "所在节点", "string"),
        AttributeSchema("status", "状态", "enum", options=["Running", "Pending", "Failed", "Succeeded"]),
        AttributeSchema("container_count", "容器数量", "number"),
        AttributeSchema("restart_count", "重启次数", "number"),
    ],
)

# Docker类
DOCKER_HOST_CI_TYPE = CITypeDefinition(
    code="docker_host",
    name="Docker主机",
    icon="docker",
    description="Docker宿主机",
    category="container",
    attributes=[
        AttributeSchema("hostname", "主机名", "string"),
        AttributeSchema("ip_address", "IP地址", "string"),
        AttributeSchema("docker_version", "Docker版本", "string"),
        AttributeSchema("os", "操作系统", "string"),
        AttributeSchema("container_count", "容器数量", "number"),
        AttributeSchema("image_count", "镜像数量", "number"),
    ],
)

DOCKER_CONTAINER_CI_TYPE = CITypeDefinition(
    code="docker_container",
    name="Docker容器",
    icon="docker",
    description="Docker容器",
    category="container",
    attributes=[
        AttributeSchema("container_name", "容器名称", "string"),
        AttributeSchema("container_id", "容器ID", "string"),
        AttributeSchema("image", "镜像", "string"),
        AttributeSchema("status", "状态", "enum", options=["running", "stopped", "paused", "exited"]),
        AttributeSchema("ports", "端口映射", "string"),
        AttributeSchema("created_at", "创建时间", "date"),
    ],
)

# 应用类
MIDDLEWARE_CI_TYPE = CITypeDefinition(
    code="middleware",
    name="中间件",
    icon="layers",
    description="中间件服务，如消息队列、缓存等",
    category="application",
    attributes=[
        AttributeSchema("middleware_type", "中间件类型", "enum", options=["Kafka", "RabbitMQ", "Redis", "Elasticsearch", "Nginx", "Tomcat", "Other"]),
        AttributeSchema("version", "版本", "string"),
        AttributeSchema("ip_address", "IP地址", "string"),
        AttributeSchema("port", "端口", "number"),
        AttributeSchema("cluster_mode", "集群模式", "boolean"),
        AttributeSchema("node_count", "节点数量", "number"),
    ],
)

DATABASE_CI_TYPE = CITypeDefinition(
    code="database",
    name="数据库",
    icon="database",
    description="数据库服务",
    category="application",
    attributes=[
        AttributeSchema("db_type", "数据库类型", "enum", options=["MySQL", "PostgreSQL", "Oracle", "SQLServer", "MongoDB", "Redis", "Other"]),
        AttributeSchema("version", "版本", "string"),
        AttributeSchema("ip_address", "IP地址", "string"),
        AttributeSchema("port", "端口", "number"),
        AttributeSchema("instance_name", "实例名", "string"),
        AttributeSchema("cluster_mode", "集群模式", "enum", options=["Standalone", "Master-Slave", "Cluster"]),
    ],
)

APPLICATION_CI_TYPE = CITypeDefinition(
    code="application",
    name="业务应用",
    icon="app",
    description="业务应用系统",
    category="application",
    attributes=[
        AttributeSchema("app_name", "应用名称", "string"),
        AttributeSchema("app_code", "应用编码", "string"),
        AttributeSchema("version", "版本", "string"),
        AttributeSchema("owner", "负责人", "string"),
        AttributeSchema("department", "所属部门", "string"),
        AttributeSchema("environment", "环境", "enum", options=["Production", "Staging", "Testing", "Development"]),
        AttributeSchema("url", "访问地址", "string"),
        AttributeSchema("description", "描述", "string"),
    ],
)


# 所有预置类型列表
PRESET_CI_TYPES = [
    # 基础设施
    STORAGE_CI_TYPE,
    NETWORK_CI_TYPE,
    SERVER_CI_TYPE,
    OS_LINUX_CI_TYPE,
    OS_WINDOWS_CI_TYPE,
    # 虚拟化
    VMWARE_VCENTER_CI_TYPE,
    VMWARE_ESXI_CI_TYPE,
    VMWARE_VM_CI_TYPE,
    # 容器
    K8S_CLUSTER_CI_TYPE,
    K8S_NODE_CI_TYPE,
    K8S_POD_CI_TYPE,
    DOCKER_HOST_CI_TYPE,
    DOCKER_CONTAINER_CI_TYPE,
    # 应用
    MIDDLEWARE_CI_TYPE,
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
