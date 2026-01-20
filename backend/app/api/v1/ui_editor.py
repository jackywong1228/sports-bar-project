"""UI可视化编辑器API"""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.ui_editor import UIPageConfig, UIBlockConfig, UIMenuItem, UIConfigVersion
from app.schemas.response import ResponseModel

router = APIRouter()


# ==================== 页面配置管理 ====================

@router.get("/pages", response_model=ResponseModel)
async def get_pages(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取页面配置列表"""
    query = db.query(UIPageConfig).filter(UIPageConfig.is_deleted == False)

    if status:
        query = query.filter(UIPageConfig.status == status)

    pages = query.order_by(UIPageConfig.id).all()

    return ResponseModel(data=[{
        "id": page.id,
        "page_code": page.page_code,
        "page_name": page.page_name,
        "page_type": page.page_type,
        "blocks_config": page.blocks_config,
        "style_config": page.style_config,
        "version": page.version,
        "status": page.status,
        "published_at": page.published_at.strftime("%Y-%m-%d %H:%M") if page.published_at else None,
        "updated_at": page.updated_at.strftime("%Y-%m-%d %H:%M") if page.updated_at else None
    } for page in pages])


@router.get("/pages/{page_code}", response_model=ResponseModel)
async def get_page_detail(
    page_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取页面配置详情（包含区块和菜单项）"""
    page = db.query(UIPageConfig).filter(
        UIPageConfig.page_code == page_code,
        UIPageConfig.is_deleted == False
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="页面配置不存在")

    # 获取该页面的区块配置
    blocks = db.query(UIBlockConfig).filter(
        UIBlockConfig.page_code == page_code,
        UIBlockConfig.is_deleted == False
    ).order_by(UIBlockConfig.sort_order).all()

    # 获取菜单项
    menu_items = db.query(UIMenuItem).filter(
        UIMenuItem.is_deleted == False
    ).order_by(UIMenuItem.menu_type, UIMenuItem.sort_order).all()

    return ResponseModel(data={
        "page": {
            "id": page.id,
            "page_code": page.page_code,
            "page_name": page.page_name,
            "page_type": page.page_type,
            "blocks_config": page.blocks_config,
            "style_config": page.style_config,
            "version": page.version,
            "status": page.status
        },
        "blocks": [{
            "id": block.id,
            "block_code": block.block_code,
            "block_name": block.block_name,
            "block_type": block.block_type,
            "config": block.config,
            "style_config": block.style_config,
            "data_source": block.data_source,
            "sort_order": block.sort_order,
            "is_active": block.is_active
        } for block in blocks],
        "menuItems": [{
            "id": item.id,
            "menu_code": item.menu_code,
            "menu_type": item.menu_type,
            "block_id": item.block_id,
            "title": item.title,
            "subtitle": item.subtitle,
            "icon": item.icon,
            "icon_active": item.icon_active,
            "link_type": item.link_type,
            "link_value": item.link_value,
            "link_params": item.link_params,
            "show_condition": item.show_condition,
            "badge_type": item.badge_type,
            "badge_value": item.badge_value,
            "sort_order": item.sort_order,
            "is_visible": item.is_visible
        } for item in menu_items]
    })


@router.post("/pages", response_model=ResponseModel)
async def create_page(
    page_code: str = Body(...),
    page_name: str = Body(...),
    page_type: str = Body("normal"),
    blocks_config: Optional[List[dict]] = Body(None),
    style_config: Optional[dict] = Body(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """创建页面配置"""
    # 检查编码是否已存在
    existing = db.query(UIPageConfig).filter(
        UIPageConfig.page_code == page_code,
        UIPageConfig.is_deleted == False
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="页面编码已存在")

    page = UIPageConfig(
        page_code=page_code,
        page_name=page_name,
        page_type=page_type,
        blocks_config=blocks_config or [],
        style_config=style_config or {
            "backgroundColor": "#F5F7F5",
            "navigationBarColor": "#1A5D3A",
            "navigationBarTextStyle": "white"
        }
    )

    db.add(page)
    db.commit()
    db.refresh(page)

    return ResponseModel(data={"id": page.id}, message="创建成功")


@router.put("/pages/{page_code}", response_model=ResponseModel)
async def update_page_config(
    page_code: str,
    page_name: Optional[str] = Body(None),
    blocks_config: Optional[List[dict]] = Body(None),
    style_config: Optional[dict] = Body(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """更新页面配置"""
    page = db.query(UIPageConfig).filter(
        UIPageConfig.page_code == page_code,
        UIPageConfig.is_deleted == False
    ).first()

    if not page:
        raise HTTPException(status_code=404, detail="页面配置不存在")

    if page_name is not None:
        page.page_name = page_name
    if blocks_config is not None:
        page.blocks_config = blocks_config
    if style_config is not None:
        page.style_config = style_config

    page.status = "draft"  # 修改后变为草稿状态
    db.commit()

    return ResponseModel(message="更新成功")


# ==================== 区块配置管理 ====================

@router.get("/blocks", response_model=ResponseModel)
async def get_blocks(
    page_code: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取区块配置列表"""
    query = db.query(UIBlockConfig).filter(UIBlockConfig.is_deleted == False)

    if page_code:
        query = query.filter(UIBlockConfig.page_code == page_code)

    blocks = query.order_by(UIBlockConfig.sort_order).all()

    return ResponseModel(data=[{
        "id": block.id,
        "block_code": block.block_code,
        "block_name": block.block_name,
        "page_code": block.page_code,
        "block_type": block.block_type,
        "config": block.config,
        "style_config": block.style_config,
        "data_source": block.data_source,
        "sort_order": block.sort_order,
        "is_active": block.is_active
    } for block in blocks])


@router.post("/blocks", response_model=ResponseModel)
async def create_block(
    block_code: str = Body(...),
    block_name: str = Body(...),
    page_code: str = Body(...),
    block_type: str = Body(...),
    config: Optional[dict] = Body(None),
    style_config: Optional[dict] = Body(None),
    data_source: Optional[dict] = Body(None),
    sort_order: int = Body(0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """创建区块配置"""
    block = UIBlockConfig(
        block_code=block_code,
        block_name=block_name,
        page_code=page_code,
        block_type=block_type,
        config=config,
        style_config=style_config,
        data_source=data_source,
        sort_order=sort_order
    )

    db.add(block)
    db.commit()
    db.refresh(block)

    return ResponseModel(data={"id": block.id}, message="创建成功")


@router.put("/blocks/{block_id}", response_model=ResponseModel)
async def update_block(
    block_id: int,
    block_name: Optional[str] = Body(None),
    config: Optional[dict] = Body(None),
    style_config: Optional[dict] = Body(None),
    data_source: Optional[dict] = Body(None),
    sort_order: Optional[int] = Body(None),
    is_active: Optional[bool] = Body(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """更新区块配置"""
    block = db.query(UIBlockConfig).filter(
        UIBlockConfig.id == block_id,
        UIBlockConfig.is_deleted == False
    ).first()

    if not block:
        raise HTTPException(status_code=404, detail="区块配置不存在")

    if block_name is not None:
        block.block_name = block_name
    if config is not None:
        block.config = config
    if style_config is not None:
        block.style_config = style_config
    if data_source is not None:
        block.data_source = data_source
    if sort_order is not None:
        block.sort_order = sort_order
    if is_active is not None:
        block.is_active = is_active

    db.commit()

    return ResponseModel(message="更新成功")


@router.delete("/blocks/{block_id}", response_model=ResponseModel)
async def delete_block(
    block_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """删除区块配置"""
    block = db.query(UIBlockConfig).filter(
        UIBlockConfig.id == block_id,
        UIBlockConfig.is_deleted == False
    ).first()

    if not block:
        raise HTTPException(status_code=404, detail="区块配置不存在")

    block.is_deleted = True
    block.deleted_at = datetime.now()
    db.commit()

    return ResponseModel(message="删除成功")


# ==================== 菜单项管理 ====================

@router.get("/menu-items", response_model=ResponseModel)
async def get_menu_items(
    menu_type: Optional[str] = None,
    block_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取菜单项列表"""
    query = db.query(UIMenuItem).filter(UIMenuItem.is_deleted == False)

    if menu_type:
        query = query.filter(UIMenuItem.menu_type == menu_type)
    if block_id:
        query = query.filter(UIMenuItem.block_id == block_id)

    items = query.order_by(UIMenuItem.sort_order).all()

    return ResponseModel(data=[{
        "id": item.id,
        "menu_code": item.menu_code,
        "menu_type": item.menu_type,
        "block_id": item.block_id,
        "title": item.title,
        "subtitle": item.subtitle,
        "icon": item.icon,
        "icon_active": item.icon_active,
        "link_type": item.link_type,
        "link_value": item.link_value,
        "link_params": item.link_params,
        "show_condition": item.show_condition,
        "badge_type": item.badge_type,
        "badge_value": item.badge_value,
        "sort_order": item.sort_order,
        "is_visible": item.is_visible,
        "is_active": item.is_active
    } for item in items])


@router.post("/menu-items", response_model=ResponseModel)
async def create_menu_item(
    menu_code: str = Body(...),
    menu_type: str = Body(...),
    title: str = Body(...),
    block_id: Optional[int] = Body(None),
    subtitle: Optional[str] = Body(None),
    icon: Optional[str] = Body(None),
    icon_active: Optional[str] = Body(None),
    link_type: str = Body("page"),
    link_value: Optional[str] = Body(None),
    link_params: Optional[dict] = Body(None),
    show_condition: Optional[dict] = Body(None),
    badge_type: Optional[str] = Body(None),
    badge_value: Optional[str] = Body(None),
    sort_order: int = Body(0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """创建菜单项"""
    item = UIMenuItem(
        menu_code=menu_code,
        menu_type=menu_type,
        title=title,
        block_id=block_id,
        subtitle=subtitle,
        icon=icon,
        icon_active=icon_active,
        link_type=link_type,
        link_value=link_value,
        link_params=link_params,
        show_condition=show_condition,
        badge_type=badge_type,
        badge_value=badge_value,
        sort_order=sort_order
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return ResponseModel(data={"id": item.id}, message="创建成功")


@router.put("/menu-items/{item_id}", response_model=ResponseModel)
async def update_menu_item(
    item_id: int,
    title: Optional[str] = Body(None),
    subtitle: Optional[str] = Body(None),
    icon: Optional[str] = Body(None),
    icon_active: Optional[str] = Body(None),
    link_type: Optional[str] = Body(None),
    link_value: Optional[str] = Body(None),
    link_params: Optional[dict] = Body(None),
    show_condition: Optional[dict] = Body(None),
    badge_type: Optional[str] = Body(None),
    badge_value: Optional[str] = Body(None),
    sort_order: Optional[int] = Body(None),
    is_visible: Optional[bool] = Body(None),
    is_active: Optional[bool] = Body(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """更新菜单项"""
    item = db.query(UIMenuItem).filter(
        UIMenuItem.id == item_id,
        UIMenuItem.is_deleted == False
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="菜单项不存在")

    # 更新字段
    update_fields = {
        'title': title, 'subtitle': subtitle, 'icon': icon,
        'icon_active': icon_active, 'link_type': link_type,
        'link_value': link_value, 'link_params': link_params,
        'show_condition': show_condition, 'badge_type': badge_type,
        'badge_value': badge_value, 'sort_order': sort_order,
        'is_visible': is_visible, 'is_active': is_active
    }

    for field, value in update_fields.items():
        if value is not None:
            setattr(item, field, value)

    db.commit()

    return ResponseModel(message="更新成功")


@router.delete("/menu-items/{item_id}", response_model=ResponseModel)
async def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """删除菜单项"""
    item = db.query(UIMenuItem).filter(
        UIMenuItem.id == item_id,
        UIMenuItem.is_deleted == False
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="菜单项不存在")

    item.is_deleted = True
    item.deleted_at = datetime.now()
    db.commit()

    return ResponseModel(message="删除成功")


@router.put("/menu-items/batch-sort", response_model=ResponseModel)
async def batch_sort_menu_items(
    items: List[dict] = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """批量更新菜单项排序"""
    for item_data in items:
        item = db.query(UIMenuItem).filter(
            UIMenuItem.id == item_data['id'],
            UIMenuItem.is_deleted == False
        ).first()
        if item:
            item.sort_order = item_data['sort_order']

    db.commit()

    return ResponseModel(message="排序更新成功")


# ==================== 发布管理 ====================

@router.post("/publish", response_model=ResponseModel)
async def publish_config(
    publish_note: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """发布配置"""
    # 获取所有页面、区块、菜单项配置
    pages = db.query(UIPageConfig).filter(UIPageConfig.is_deleted == False).all()
    blocks = db.query(UIBlockConfig).filter(UIBlockConfig.is_deleted == False).all()
    menu_items = db.query(UIMenuItem).filter(UIMenuItem.is_deleted == False).all()

    # 创建配置快照
    config_snapshot = {
        "pages": [{
            "page_code": p.page_code,
            "page_name": p.page_name,
            "page_type": p.page_type,
            "blocks_config": p.blocks_config,
            "style_config": p.style_config
        } for p in pages],
        "blocks": [{
            "block_code": b.block_code,
            "block_name": b.block_name,
            "page_code": b.page_code,
            "block_type": b.block_type,
            "config": b.config,
            "style_config": b.style_config,
            "data_source": b.data_source,
            "sort_order": b.sort_order,
            "is_active": b.is_active
        } for b in blocks],
        "menuItems": [{
            "menu_code": m.menu_code,
            "menu_type": m.menu_type,
            "block_id": m.block_id,
            "title": m.title,
            "subtitle": m.subtitle,
            "icon": m.icon,
            "icon_active": m.icon_active,
            "link_type": m.link_type,
            "link_value": m.link_value,
            "link_params": m.link_params,
            "show_condition": m.show_condition,
            "sort_order": m.sort_order,
            "is_visible": m.is_visible
        } for m in menu_items],
        "publishedAt": datetime.now().isoformat()
    }

    # 取消之前的当前版本
    db.query(UIConfigVersion).filter(UIConfigVersion.is_current == True).update({"is_current": False})

    # 获取最新版本号
    latest_version = db.query(UIConfigVersion).order_by(UIConfigVersion.version.desc()).first()
    new_version = (latest_version.version + 1) if latest_version else 1

    # 创建新版本
    version = UIConfigVersion(
        version=new_version,
        version_name=f"v{new_version}",
        config_snapshot=config_snapshot,
        published_by=current_user.id,
        publish_note=publish_note,
        is_current=True
    )
    db.add(version)

    # 更新所有页面状态为已发布
    for page in pages:
        page.status = "published"
        page.published_at = datetime.now()
        page.version = new_version

    db.commit()

    return ResponseModel(data={"version": new_version}, message="发布成功")


@router.get("/versions", response_model=ResponseModel)
async def get_versions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """获取版本历史列表"""
    versions = db.query(UIConfigVersion).order_by(UIConfigVersion.version.desc()).limit(20).all()

    return ResponseModel(data=[{
        "id": v.id,
        "version": v.version,
        "version_name": v.version_name,
        "published_by": v.published_by,
        "publish_note": v.publish_note,
        "is_current": v.is_current,
        "created_at": v.created_at.strftime("%Y-%m-%d %H:%M") if v.created_at else None
    } for v in versions])


@router.post("/versions/{version_id}/rollback", response_model=ResponseModel)
async def rollback_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """回滚到指定版本"""
    version = db.query(UIConfigVersion).filter(UIConfigVersion.id == version_id).first()

    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    # 更新当前版本标记
    db.query(UIConfigVersion).filter(UIConfigVersion.is_current == True).update({"is_current": False})
    version.is_current = True

    db.commit()

    return ResponseModel(message="回滚成功")


# ==================== 初始化数据 ====================

@router.post("/init-default-data", response_model=ResponseModel)
async def init_default_data(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """初始化默认配置数据"""
    # 检查是否已有数据
    existing_page = db.query(UIPageConfig).filter(UIPageConfig.page_code == "home").first()
    if existing_page:
        return ResponseModel(message="默认数据已存在，跳过初始化")

    # 创建首页配置
    home_page = UIPageConfig(
        page_code="home",
        page_name="首页",
        page_type="tabbar",
        blocks_config=[
            {"block_code": "banner", "visible": True, "sort_order": 1},
            {"block_code": "quick_entry", "visible": True, "sort_order": 2},
            {"block_code": "hot_venues", "visible": True, "sort_order": 3},
            {"block_code": "hot_activities", "visible": True, "sort_order": 4},
            {"block_code": "hot_coaches", "visible": True, "sort_order": 5}
        ],
        style_config={
            "backgroundColor": "#F5F7F5",
            "navigationBarColor": "#1A5D3A",
            "navigationBarTextStyle": "white"
        },
        status="published",
        published_at=datetime.now()
    )
    db.add(home_page)
    db.flush()

    # 创建区块配置
    blocks_data = [
        UIBlockConfig(
            block_code="banner", block_name="轮播图", page_code="home", block_type="banner",
            config={"height": 360, "autoplay": True, "interval": 3000, "indicatorDots": True, "circular": True},
            style_config={"marginTop": 0, "marginBottom": 0},
            sort_order=1
        ),
        UIBlockConfig(
            block_code="quick_entry", block_name="快捷入口", page_code="home", block_type="quick_entry",
            config={"columns": 4, "showText": True, "iconSize": 80},
            style_config={"marginTop": -15, "marginBottom": 0, "paddingHorizontal": 24, "backgroundColor": "#FFFFFF", "borderRadius": 16},
            sort_order=2
        ),
        UIBlockConfig(
            block_code="hot_venues", block_name="热门场馆", page_code="home", block_type="scroll",
            config={"limit": 4, "showMore": True},
            style_config={"marginTop": 24, "paddingHorizontal": 24, "backgroundColor": "#FFFFFF", "borderRadius": 16},
            data_source={"type": "api", "api": "/member/venues", "params": {"limit": 4}},
            sort_order=3
        ),
        UIBlockConfig(
            block_code="hot_activities", block_name="热门活动", page_code="home", block_type="list",
            config={"limit": 3, "showMore": True, "cardStyle": "horizontal"},
            style_config={"marginTop": 24, "paddingHorizontal": 24, "backgroundColor": "#FFFFFF", "borderRadius": 16},
            data_source={"type": "api", "api": "/member/activities", "params": {"limit": 3}},
            sort_order=4
        ),
        UIBlockConfig(
            block_code="hot_coaches", block_name="推荐教练", page_code="home", block_type="list",
            config={"limit": 4, "showMore": True},
            style_config={"marginTop": 24, "paddingHorizontal": 24, "backgroundColor": "#FFFFFF", "borderRadius": 16},
            data_source={"type": "api", "api": "/member/coaches", "params": {"limit": 4}},
            sort_order=5
        )
    ]
    for block in blocks_data:
        db.add(block)
    db.flush()

    # 获取 quick_entry 区块的 ID
    quick_entry_block = db.query(UIBlockConfig).filter(
        UIBlockConfig.block_code == "quick_entry",
        UIBlockConfig.page_code == "home"
    ).first()
    quick_entry_block_id = quick_entry_block.id if quick_entry_block else None

    # 创建快捷入口菜单项（使用小程序本地图标路径）
    quick_entries = [
        ("venue", "场馆预约", "/assets/icons/venue-entry.png", "tab", "/pages/venue/venue", 0),
        ("coach", "教练预约", "/assets/icons/coach-entry.png", "page", "/pages/coach-list/coach-list", 1),
        ("food", "在线点餐", "/assets/icons/food-entry.png", "page", "/pages/food/food", 2),
        ("activity", "活动报名", "/assets/icons/activity-entry.png", "tab", "/pages/activity/activity", 3),
        ("team", "组队广场", "/assets/icons/team-entry.png", "page", "/pages/team/team", 4),
        ("mall", "积分商城", "/assets/icons/mall-entry.png", "page", "/pages/mall/mall", 5),
        ("member", "会员中心", "/assets/icons/member-entry.png", "page", "/pages/member/member", 6),
        ("coupon", "我的券包", "/assets/icons/coupon-entry.png", "page", "/pages/coupons/coupons", 7)
    ]
    for code, title, icon, link_type, link_value, sort_order in quick_entries:
        item = UIMenuItem(
            menu_code=code, menu_type="quick_entry", title=title, icon=icon,
            link_type=link_type, link_value=link_value, sort_order=sort_order,
            block_id=quick_entry_block_id, is_visible=True
        )
        db.add(item)

    # 创建TabBar菜单项（使用小程序本地图标路径）
    tabbar_items = [
        ("tabbar_home", "首页", "/assets/icons/home.png", "/assets/icons/home-active.png", "/pages/index/index", 0),
        ("tabbar_venue", "预约", "/assets/icons/venue.png", "/assets/icons/venue-active.png", "/pages/venue/venue", 1),
        ("tabbar_activity", "活动", "/assets/icons/activity.png", "/assets/icons/activity-active.png", "/pages/activity/activity", 2),
        ("tabbar_profile", "我的", "/assets/icons/user.png", "/assets/icons/user-active.png", "/pages/profile/profile", 3)
    ]
    for code, title, icon, icon_active, link_value, sort_order in tabbar_items:
        item = UIMenuItem(
            menu_code=code, menu_type="tabbar", title=title, icon=icon, icon_active=icon_active,
            link_type="tab", link_value=link_value, sort_order=sort_order, is_visible=True
        )
        db.add(item)

    db.flush()

    # 自动创建并发布第一个版本
    pages = db.query(UIPageConfig).filter(UIPageConfig.is_deleted == False).all()
    blocks = db.query(UIBlockConfig).filter(UIBlockConfig.is_deleted == False).all()
    menu_items = db.query(UIMenuItem).filter(UIMenuItem.is_deleted == False).all()

    config_snapshot = {
        "pages": [{
            "page_code": p.page_code,
            "page_name": p.page_name,
            "page_type": p.page_type,
            "blocks_config": p.blocks_config,
            "style_config": p.style_config
        } for p in pages],
        "blocks": [{
            "block_code": b.block_code,
            "block_name": b.block_name,
            "page_code": b.page_code,
            "block_type": b.block_type,
            "config": b.config,
            "style_config": b.style_config,
            "data_source": b.data_source,
            "sort_order": b.sort_order,
            "is_active": b.is_active
        } for b in blocks],
        "menuItems": [{
            "menu_code": m.menu_code,
            "menu_type": m.menu_type,
            "block_id": m.block_id,
            "title": m.title,
            "subtitle": m.subtitle,
            "icon": m.icon,
            "icon_active": m.icon_active,
            "link_type": m.link_type,
            "link_value": m.link_value,
            "link_params": m.link_params,
            "show_condition": m.show_condition,
            "sort_order": m.sort_order,
            "is_visible": m.is_visible
        } for m in menu_items if m.menu_type != "tabbar"],
        "tabBar": [{
            "menu_code": m.menu_code,
            "menu_type": m.menu_type,
            "title": m.title,
            "icon": m.icon,
            "icon_active": m.icon_active,
            "link_type": m.link_type,
            "link_value": m.link_value,
            "sort_order": m.sort_order,
            "is_visible": m.is_visible
        } for m in menu_items if m.menu_type == "tabbar"],
        "publishedAt": datetime.now().isoformat()
    }

    version = UIConfigVersion(
        version=1,
        version_name="v1",
        config_snapshot=config_snapshot,
        published_by=current_user.id,
        publish_note="初始化默认配置",
        is_current=True
    )
    db.add(version)

    db.commit()

    return ResponseModel(message="默认数据初始化成功，已自动发布")
