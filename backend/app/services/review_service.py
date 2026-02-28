"""评论与积分服务"""
from datetime import datetime, date
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Member
from app.models.review import ServiceReview, ReviewPointConfig
from app.models.member import PointRecord


class ReviewService:
    """评论业务服务"""

    def __init__(self, db: Session):
        self.db = db

    def submit_review(
        self,
        member: Member,
        order_type: str,
        order_id: int,
        rating: int,
        content: Optional[str] = None,
        images: Optional[str] = None
    ) -> Dict:
        """
        提交评论并发放积分

        Args:
            member: 会员对象
            order_type: 订单类型 (reservation/food/mall)
            order_id: 订单ID
            rating: 评分 1-5
            content: 评论内容
            images: 图片JSON数组字符串

        Returns:
            评论结果
        """
        # 检查是否已评论
        existing = self.db.query(ServiceReview).filter(
            ServiceReview.member_id == member.id,
            ServiceReview.order_type == order_type,
            ServiceReview.order_id == order_id,
            ServiceReview.is_deleted == False
        ).first()

        if existing:
            return {"success": False, "message": "该订单已评论"}

        # 计算积分
        has_content = bool(content and content.strip())
        has_images = bool(images and images != '[]')
        points = self.calculate_points(has_content, has_images)

        # 检查今日评论次数
        can_earn_points = self._check_daily_limit(member.id)

        # 创建评论
        review = ServiceReview(
            member_id=member.id,
            order_type=order_type,
            order_id=order_id,
            rating=rating,
            content=content,
            images=images,
            points_awarded=points if can_earn_points else 0,
            points_settled=can_earn_points
        )
        self.db.add(review)

        # 发放积分
        if can_earn_points and points > 0:
            member.point_balance = (member.point_balance or 0) + points
            point_record = PointRecord(
                member_id=member.id,
                type='income',
                amount=points,
                balance=member.point_balance,
                source='review',
                remark=f'评论{order_type}订单#{order_id}获得积分'
            )
            self.db.add(point_record)

        self.db.commit()
        self.db.refresh(review)

        return {
            "success": True,
            "review_id": review.id,
            "points_awarded": review.points_awarded,
            "message": f"评论成功，获得{review.points_awarded}积分" if review.points_awarded > 0 else "评论成功"
        }

    def calculate_points(self, has_content: bool, has_images: bool) -> int:
        """根据配置计算积分"""
        config = self.db.query(ReviewPointConfig).filter(
            ReviewPointConfig.is_active == True
        ).first()

        if not config:
            return 5  # 默认值

        points = config.base_points
        if has_content:
            points += config.text_bonus
        if has_images:
            points += config.image_bonus

        return points

    def _check_daily_limit(self, member_id: int) -> bool:
        """检查今日评论是否已达上限"""
        config = self.db.query(ReviewPointConfig).filter(
            ReviewPointConfig.is_active == True
        ).first()

        if not config:
            return True

        today = date.today()
        today_count = self.db.query(func.count(ServiceReview.id)).filter(
            ServiceReview.member_id == member_id,
            ServiceReview.points_settled == True,
            func.date(ServiceReview.created_at) == today,
            ServiceReview.is_deleted == False
        ).scalar()

        return today_count < config.max_daily_reviews
