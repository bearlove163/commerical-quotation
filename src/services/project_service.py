"""
项目生命周期与版本基线管理服务 (Project & Version Service)
支撑 ProjectDialog 业务操作：立项、国内外模式互斥切换、商务数据基线版本树派生与锁定
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import uuid

from src.database.models.base_models import BusinessMode


class VersionStatus(str, Enum):
    ACTIVE_DRAFT = "ACTIVE_DRAFT"           # 活跃编辑态
    SUBMITTED = "SUBMITTED"                 # 已提审
    APPROVED = "APPROVED"                   # 已审批
    LOCKED_FROZEN = "LOCKED_FROZEN"         # 已封存（只读不可篡改）
    HISTORICAL = "HISTORICAL"               # 历史归档


@dataclass
class ProjectVersion:
    version_id: str
    version_tag: str                        # 例如 V1.0, V1.1, V1.2
    version_desc: str                       # 例如 "内部底线成本版", "首次投标报价版"
    parent_version_tag: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: VersionStatus = VersionStatus.ACTIVE_DRAFT
    material_snapshot_id: str = "MAT-2026-01-29"
    fab_norm_version: str = "FAB-2026-V1"
    install_norm_version: str = "INS-2026-V1"
    target_profit_rate: float = -0.0715
    mgmt_fee_rate: float = 0.085


@dataclass
class ProjectEntity:
    project_id: str
    project_code: str                       # 例如 ZJNORTH
    project_name: str
    business_mode: BusinessMode
    country_code: str = "CN"                # 国内CN或海外国别 (如 SA, ID, AE)
    created_at: datetime = field(default_factory=datetime.now)
    current_version_tag: str = "V1.0"
    version_tree: Dict[str, ProjectVersion] = field(default_factory=dict)


class ProjectService:
    """项目生命周期与多版本基线服务"""

    def __init__(self):
        self._projects: Dict[str, ProjectEntity] = {}

    def create_project(
        self,
        project_code: str,
        project_name: str,
        business_mode: BusinessMode,
        initial_version_tag: str = "V1.0",
        initial_version_desc: str = "内部底线成本基线版",
        country_code: str = "CN",
    ) -> ProjectEntity:
        """项目立项并初始化首个基线版本"""
        project_id = str(uuid.uuid4())
        
        # 首个版本
        init_ver = ProjectVersion(
            version_id=str(uuid.uuid4()),
            version_tag=initial_version_tag,
            version_desc=initial_version_desc,
            parent_version_tag=None,
            status=VersionStatus.ACTIVE_DRAFT,
        )

        project = ProjectEntity(
            project_id=project_id,
            project_code=project_code,
            project_name=project_name,
            business_mode=business_mode,
            country_code=country_code,
            current_version_tag=initial_version_tag,
            version_tree={initial_version_tag: init_ver},
        )
        self._projects[project_code] = project
        return project

    def get_project(self, project_code: str) -> Optional[ProjectEntity]:
        return self._projects.get(project_code)

    def switch_business_mode(self, project_code: str, new_mode: BusinessMode) -> ProjectEntity:
        """切换项目业务模式（国内两票制 vs 境外贸易 Incoterms 2020）"""
        project = self._projects.get(project_code)
        if not project:
            raise ValueError(f"项目 {project_code} 不存在")

        current_ver = project.version_tree[project.current_version_tag]
        if current_ver.status in (VersionStatus.LOCKED_FROZEN, VersionStatus.APPROVED):
            raise PermissionError(f"当前版本 {current_ver.version_tag} 已锁定或已审批，禁止变更业务模式，请派生新版本！")

        project.business_mode = new_mode
        return project

    def branch_version(
        self,
        project_code: str,
        new_version_tag: str,
        version_desc: str,
        freeze_parent: bool = True,
    ) -> ProjectVersion:
        """从当前活跃版本派生新的基线版本 (Branch New Version)"""
        project = self._projects.get(project_code)
        if not project:
            raise ValueError(f"项目 {project_code} 不存在")

        if new_version_tag in project.version_tree:
            raise ValueError(f"版本号 {new_version_tag} 已存在于项目中")

        parent_ver = project.version_tree[project.current_version_tag]
        if freeze_parent:
            parent_ver.status = VersionStatus.LOCKED_FROZEN

        new_ver = ProjectVersion(
            version_id=str(uuid.uuid4()),
            version_tag=new_version_tag,
            version_desc=version_desc,
            parent_version_tag=parent_ver.version_tag,
            status=VersionStatus.ACTIVE_DRAFT,
            material_snapshot_id=parent_ver.material_snapshot_id,
            fab_norm_version=parent_ver.fab_norm_version,
            install_norm_version=parent_ver.install_norm_version,
            target_profit_rate=parent_ver.target_profit_rate,
            mgmt_fee_rate=parent_ver.mgmt_fee_rate,
        )

        project.version_tree[new_version_tag] = new_ver
        project.current_version_tag = new_version_tag
        return new_ver

    def freeze_version(self, project_code: str, version_tag: str) -> ProjectVersion:
        """封存指定版本使其不可篡改 (Lock Baseline)"""
        project = self._projects.get(project_code)
        if not project or version_tag not in project.version_tree:
            raise ValueError(f"项目或版本不存在: {project_code} - {version_tag}")

        ver = project.version_tree[version_tag]
        ver.status = VersionStatus.LOCKED_FROZEN
        return ver
