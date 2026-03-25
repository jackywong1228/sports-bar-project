#!/usr/bin/env python3
"""午夜定时发券脚本 — 通过 cron 每日 0:00 执行

crontab 示例:
0 0 * * * /var/www/sports-bar-project/backend/venv/bin/python /var/www/sports-bar-project/backend/scripts/issue_coupons.py >> /var/log/coupon_issue.log 2>&1
"""
import sys
import os
from datetime import datetime

# 将 backend 目录加入 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models import Member
from app.models.member import MemberLevel
from app.services.monthly_coupon_service import MonthlyCouponService


def main():
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行定时发券")
    print(f"{'='*50}")

    db = SessionLocal()
    try:
        svc = MonthlyCouponService(db)

        # 1. SS 会员月度券（按订阅纪念日）
        ss_members = db.query(Member).join(MemberLevel).filter(
            MemberLevel.level_code == 'SS',
            Member.subscription_status == 'active',
            Member.member_expire_time > datetime.now(),
            Member.is_deleted == False
        ).all()

        ss_issued = 0
        for m in ss_members:
            result = svc.check_and_issue_monthly(m)
            if result:
                ss_issued += 1
                print(f"  SS月度券 -> 会员ID={m.id} ({m.nickname or m.phone})")

        print(f"SS月度券: 检查 {len(ss_members)} 人，发放 {ss_issued} 人")

        # 2. SSS 会员每日饮品券
        sss_members = db.query(Member).join(MemberLevel).filter(
            MemberLevel.level_code == 'SSS',
            Member.subscription_status == 'active',
            Member.member_expire_time > datetime.now(),
            Member.is_deleted == False
        ).all()

        sss_issued = 0
        for m in sss_members:
            result = svc.check_and_issue_daily(m)
            if result:
                sss_issued += 1
                print(f"  SSS日饮品券 -> 会员ID={m.id} ({m.nickname or m.phone})")

        print(f"SSS每日饮品券: 检查 {len(sss_members)} 人，发放 {sss_issued} 人")

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 发券完成")
    except Exception as e:
        print(f"发券异常: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
