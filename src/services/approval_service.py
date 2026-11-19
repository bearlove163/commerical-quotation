"""
审批流控制与基线锁定服务 (Approval & Baseline Locking Service)
支撑 ApprovalDialog 业务操作：
类比 HIS 电子病历签名与封存，实现成本编制、技术复核、商务总监终审与基线加锁全生命周期
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import uuid


class ApprovalStage(str, Enum):
    STAGE_0_DRAFT = "DRAFT"                               # 编制中草稿
    STAGE_1_SUBMITTED = "SUBMITTED"                       # 商务员提交审批
    STAGE_2_TECH_REVIEWED = "TECH_REVIEWED"               # 总工/技术部审核通过
    STAGE_3_COMMERCIAL_APPROVED = "COMMERCIAL_APPROVED"   # 商务总监终审批准
    STAGE_4_FROZEN_LOCKED = "FROZEN_LOCKED"               # 封标锁定（只读不可改）
    REJECTED = "REJECTED"                                 # 已驳回修改


@dataclass
class AuditRecord:
    record_id: str
    stage: ApprovalStage
    operator: str
    action: str
    comment: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ProjectApprovalWorkflow:
    workflow_id: str
    project_code: str
    version_tag: str
    current_stage: ApprovalStage = ApprovalStage.STAGE_0_DRAFT
    audit_history: List[AuditRecord] = field(default_factory=list)
    is_locked: bool = False


class ApprovalService:
    """多级在线流程审签与基线行级锁定服务"""

    def __init__(self):
        self._workflows: Dict[str, ProjectApprovalWorkflow] = {}

    def get_or_create_workflow(self, project_code: str, version_tag: str) -> ProjectApprovalWorkflow:
        key = f"{project_code}_{version_tag}"
        if key not in self._workflows:
            wf = ProjectApprovalWorkflow(
                workflow_id=str(uuid.uuid4()),
                project_code=project_code,
                version_tag=version_tag,
            )
            self._workflows[key] = wf
        return self._workflows[key]

    def submit_for_review(self, project_code: str, version_tag: str, operator: str, comment: str = ""):
        wf = self.get_or_create_workflow(project_code, version_tag)
        if wf.is_locked:
            raise PermissionError(f"版本 {version_tag} 已封存锁定，无法提交审批！")
        
        wf.current_stage = ApprovalStage.STAGE_1_SUBMITTED
        wf.audit_history.append(AuditRecord(
            record_id=str(uuid.uuid4()),
            stage=wf.current_stage,
            operator=operator,
            action="SUBMIT_FOR_REVIEW",
            comment=comment or "商务测算完成，提请技术及商务复核",
        ))

    def technical_review(self, project_code: str, version_tag: str, operator: str, approve: bool, comment: str):
        wf = self.get_or_create_workflow(project_code, version_tag)
        if wf.is_locked:
            raise PermissionError("已锁定的基线不可进行审批变更")

        if approve:
            wf.current_stage = ApprovalStage.STAGE_2_TECH_REVIEWED
            action = "TECH_APPROVE"
        else:
            wf.current_stage = ApprovalStage.REJECTED
            action = "TECH_REJECT"

        wf.audit_history.append(AuditRecord(
            record_id=str(uuid.uuid4()),
            stage=wf.current_stage,
            operator=operator,
            action=action,
            comment=comment,
        ))

    def commercial_final_approve(self, project_code: str, version_tag: str, operator: str, approve: bool, comment: str):
        wf = self.get_or_create_workflow(project_code, version_tag)
        if wf.is_locked:
            raise PermissionError("已锁定的基线不可进行审批变更")

        if approve:
            wf.current_stage = ApprovalStage.STAGE_3_COMMERCIAL_APPROVED
            action = "COMMERCIAL_APPROVE"
        else:
            wf.current_stage = ApprovalStage.REJECTED
            action = "COMMERCIAL_REJECT"

        wf.audit_history.append(AuditRecord(
            record_id=str(uuid.uuid4()),
            stage=wf.current_stage,
            operator=operator,
            action=action,
            comment=comment,
        ))

    def freeze_and_seal(self, project_code: str, version_tag: str, operator: str, comment: str = "投标封存"):
        """终局操作：封存加锁，任何单元格和构件变动将被数据库拦截"""
        wf = self.get_or_create_workflow(project_code, version_tag)
        if wf.current_stage != ApprovalStage.STAGE_3_COMMERCIAL_APPROVED:
            raise ValueError("只有经过商务总监终审批准的版本方可执行终局封存锁定！")

        wf.current_stage = ApprovalStage.STAGE_4_FROZEN_LOCKED
        wf.is_locked = True
        wf.audit_history.append(AuditRecord(
            record_id=str(uuid.uuid4()),
            stage=wf.current_stage,
            operator=operator,
            action="FREEZE_AND_SEAL",
            comment=comment,
        ))

    def check_edit_permission(self, project_code: str, version_tag: str):
        """校验是否允许编辑。若已锁定则抛出 PermissionError"""
        wf = self.get_or_create_workflow(project_code, version_tag)
        if wf.is_locked:
            raise PermissionError(f"项目 {project_code} 版本 {version_tag} 处于【{wf.current_stage.value}】状态，已行级锁定，严禁修改！")
