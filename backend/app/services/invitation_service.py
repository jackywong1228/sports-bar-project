"""会员邀请服务"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Member, MemberLevel
from app.models.member_invitation import MemberInvitation


class InvitationService:
    """会员邀请服务 - 管理邀请码生成和使用"""

    def __init__(self, db: Session):
        self.db = db

    def generate_invite(self, member: Member) -> Dict:
        """
        生成邀请码

        检查月度配额 → 生成邀请码 → 返回码+剩余次数
        """
        level = member.level
        if not level:
            return {"success": False, "reason": "会员等级信息缺失"}

        monthly_limit = getattr(level, 'monthly_invite_count', 0) or 0
        if monthly_limit <= 0:
            return {"success": False, "reason": "当前等级无邀请权限"}

        # 检查本月已用次数
        current_month = datetime.now().strftime('%Y-%m')
        used_count = self.db.query(func.count(MemberInvitation.id)).filter(
            MemberInvitation.inviter_id == member.id,
            MemberInvitation.invite_month == current_month
        ).scalar()

        if used_count >= monthly_limit:
            return {
                "success": False,
                "reason": f"本月邀请次数已用完（{monthly_limit}次/月）",
                "used": used_count,
                "limit": monthly_limit
            }

        # 生成邀请码（8位短码）
        invite_code = uuid.uuid4().hex[:8].upper()
        expire_at = datetime.now() + timedelta(days=7)

        invitation = MemberInvitation(
            inviter_id=member.id,
            invite_code=invite_code,
            invite_month=current_month,
            status='pending',
            expire_at=expire_at
        )
        self.db.add(invitation)
        self.db.commit()

        return {
            "success": True,
            "invite_code": invite_code,
            "expire_at": expire_at.isoformat(),
            "remaining": monthly_limit - used_count - 1
        }

    def accept_invite(self, code: str, invitee_member: Member) -> Dict:
        """使用邀请码"""
        invitation = self.db.query(MemberInvitation).filter(
            MemberInvitation.invite_code == code
        ).first()

        if not invitation:
            return {"success": False, "reason": "邀请码不存在"}

        if invitation.status != 'pending':
            return {"success": False, "reason": "邀请码已使用或已过期"}

        if invitation.expire_at < datetime.now():
            invitation.status = 'expired'
            self.db.commit()
            return {"success": False, "reason": "邀请码已过期"}

        if invitation.inviter_id == invitee_member.id:
            return {"success": False, "reason": "不能使用自己的邀请码"}

        # 标记已使用
        invitation.status = 'used'
        invitation.invitee_id = invitee_member.id
        invitation.used_at = datetime.now()
        self.db.commit()

        # 获取邀请人信息
        inviter = self.db.query(Member).filter(Member.id == invitation.inviter_id).first()

        return {
            "success": True,
            "inviter_name": inviter.nickname or inviter.phone if inviter else "未知",
            "message": "邀请码使用成功"
        }

    def get_monthly_stats(self, member_id: int) -> Dict:
        """获取本月邀请统计"""
        member = self.db.query(Member).filter(Member.id == member_id).first()
        if not member or not member.level:
            return {"used": 0, "limit": 0, "remaining": 0}

        monthly_limit = getattr(member.level, 'monthly_invite_count', 0) or 0
        current_month = datetime.now().strftime('%Y-%m')

        used_count = self.db.query(func.count(MemberInvitation.id)).filter(
            MemberInvitation.inviter_id == member_id,
            MemberInvitation.invite_month == current_month
        ).scalar()

        return {
            "used": used_count,
            "limit": monthly_limit,
            "remaining": max(0, monthly_limit - used_count),
            "month": current_month
        }

    def get_history(self, member_id: int, page: int = 1, page_size: int = 20) -> Dict:
        """获取邀请记录列表"""
        query = self.db.query(MemberInvitation).filter(
            MemberInvitation.inviter_id == member_id
        ).order_by(MemberInvitation.created_at.desc())

        total = query.count()
        records = query.offset((page - 1) * page_size).limit(page_size).all()

        items = []
        for inv in records:
            invitee = None
            if inv.invitee_id:
                invitee = self.db.query(Member).filter(Member.id == inv.invitee_id).first()

            items.append({
                "id": inv.id,
                "invite_code": inv.invite_code,
                "invite_month": inv.invite_month,
                "status": inv.status,
                "invitee_name": (invitee.nickname or invitee.phone) if invitee else None,
                "invitee_avatar": invitee.avatar if invitee else None,
                "used_at": inv.used_at.isoformat() if inv.used_at else None,
                "expire_at": inv.expire_at.isoformat(),
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
            })

        return {
            "total": total,
            "items": items
        }
