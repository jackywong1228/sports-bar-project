"""UI素材管理API"""
import os
import uuid
import json
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.ui_asset import UIIcon, UITheme, UIImage
from app.schemas.response import ResponseModel

router = APIRouter()

# ==================== 图标管理 ====================

@router.get("/icons", response_model=ResponseModel)
async def get_icons(
    app_type: Optional[str] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取图标列表"""
    query = db.query(UIIcon).filter(UIIcon.is_deleted == False)

    if app_type:
        query = query.filter(UIIcon.app_type == app_type)
    if category:
        query = query.filter(UIIcon.category == category)
    if keyword:
        query = query.filter(UIIcon.name.contains(keyword))

    icons = query.order_by(UIIcon.sort_order, UIIcon.id).all()

    return ResponseModel(data=[{
        "id": icon.id,
        "code": icon.code,
        "name": icon.name,
        "app_type": icon.app_type,
        "category": icon.category,
        "icon_normal": icon.icon_normal,
        "icon_active": icon.icon_active,
        "description": icon.description,
        "sort_order": icon.sort_order,
        "is_active": icon.is_active,
        "created_at": icon.created_at.strftime("%Y-%m-%d %H:%M") if icon.created_at else None,
        "updated_at": icon.updated_at.strftime("%Y-%m-%d %H:%M") if icon.updated_at else None
    } for icon in icons])


@router.post("/icons", response_model=ResponseModel)
async def create_icon(
    code: str,
    name: str,
    app_type: str,
    category: str = "tabbar",
    icon_normal: Optional[str] = None,
    icon_active: Optional[str] = None,
    description: Optional[str] = None,
    sort_order: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建图标"""
    # 检查编码是否已存在
    existing = db.query(UIIcon).filter(
        UIIcon.code == code,
        UIIcon.app_type == app_type,
        UIIcon.is_deleted == False
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该图标编码已存在")

    icon = UIIcon(
        code=code,
        name=name,
        app_type=app_type,
        category=category,
        icon_normal=icon_normal,
        icon_active=icon_active,
        description=description,
        sort_order=sort_order
    )

    db.add(icon)
    db.commit()
    db.refresh(icon)

    return ResponseModel(data={"id": icon.id}, message="创建成功")


@router.put("/icons/{icon_id}", response_model=ResponseModel)
async def update_icon(
    icon_id: int,
    name: Optional[str] = None,
    category: Optional[str] = None,
    icon_normal: Optional[str] = None,
    icon_active: Optional[str] = None,
    description: Optional[str] = None,
    sort_order: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新图标"""
    icon = db.query(UIIcon).filter(UIIcon.id == icon_id, UIIcon.is_deleted == False).first()

    if not icon:
        raise HTTPException(status_code=404, detail="图标不存在")

    if name is not None:
        icon.name = name
    if category is not None:
        icon.category = category
    if icon_normal is not None:
        icon.icon_normal = icon_normal
    if icon_active is not None:
        icon.icon_active = icon_active
    if description is not None:
        icon.description = description
    if sort_order is not None:
        icon.sort_order = sort_order
    if is_active is not None:
        icon.is_active = is_active

    db.commit()

    return ResponseModel(message="更新成功")


@router.delete("/icons/{icon_id}", response_model=ResponseModel)
async def delete_icon(
    icon_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除图标"""
    icon = db.query(UIIcon).filter(UIIcon.id == icon_id, UIIcon.is_deleted == False).first()

    if not icon:
        raise HTTPException(status_code=404, detail="图标不存在")

    icon.is_deleted = True
    icon.deleted_at = datetime.now()
    db.commit()

    return ResponseModel(message="删除成功")


# ==================== 主题配色管理 ====================

@router.get("/themes", response_model=ResponseModel)
async def get_themes(
    app_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取主题列表"""
    query = db.query(UITheme).filter(UITheme.is_deleted == False)

    if app_type:
        query = query.filter(UITheme.app_type == app_type)

    themes = query.order_by(UITheme.id).all()

    return ResponseModel(data=[{
        "id": theme.id,
        "code": theme.code,
        "name": theme.name,
        "app_type": theme.app_type,
        "colors": json.loads(theme.colors) if theme.colors else {},
        "preview_image": theme.preview_image,
        "description": theme.description,
        "is_current": theme.is_current,
        "is_active": theme.is_active,
        "created_at": theme.created_at.strftime("%Y-%m-%d %H:%M") if theme.created_at else None
    } for theme in themes])


@router.post("/themes", response_model=ResponseModel)
async def create_theme(
    code: str,
    name: str,
    app_type: str,
    colors: dict,
    preview_image: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建主题"""
    # 检查编码是否已存在
    existing = db.query(UITheme).filter(
        UITheme.code == code,
        UITheme.app_type == app_type,
        UITheme.is_deleted == False
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该主题编码已存在")

    theme = UITheme(
        code=code,
        name=name,
        app_type=app_type,
        colors=json.dumps(colors, ensure_ascii=False),
        preview_image=preview_image,
        description=description
    )

    db.add(theme)
    db.commit()
    db.refresh(theme)

    return ResponseModel(data={"id": theme.id}, message="创建成功")


@router.put("/themes/{theme_id}", response_model=ResponseModel)
async def update_theme(
    theme_id: int,
    name: Optional[str] = None,
    colors: Optional[dict] = None,
    preview_image: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新主题"""
    theme = db.query(UITheme).filter(UITheme.id == theme_id, UITheme.is_deleted == False).first()

    if not theme:
        raise HTTPException(status_code=404, detail="主题不存在")

    if name is not None:
        theme.name = name
    if colors is not None:
        theme.colors = json.dumps(colors, ensure_ascii=False)
    if preview_image is not None:
        theme.preview_image = preview_image
    if description is not None:
        theme.description = description
    if is_active is not None:
        theme.is_active = is_active

    db.commit()

    return ResponseModel(message="更新成功")


@router.put("/themes/{theme_id}/set-current", response_model=ResponseModel)
async def set_current_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """设置为当前主题"""
    theme = db.query(UITheme).filter(UITheme.id == theme_id, UITheme.is_deleted == False).first()

    if not theme:
        raise HTTPException(status_code=404, detail="主题不存在")

    # 取消同类型其他主题的当前状态
    db.query(UITheme).filter(
        UITheme.app_type == theme.app_type,
        UITheme.is_deleted == False
    ).update({"is_current": False})

    theme.is_current = True
    db.commit()

    return ResponseModel(message="设置成功")


@router.delete("/themes/{theme_id}", response_model=ResponseModel)
async def delete_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除主题"""
    theme = db.query(UITheme).filter(UITheme.id == theme_id, UITheme.is_deleted == False).first()

    if not theme:
        raise HTTPException(status_code=404, detail="主题不存在")

    if theme.is_current:
        raise HTTPException(status_code=400, detail="当前使用中的主题不能删除")

    theme.is_deleted = True
    theme.deleted_at = datetime.now()
    db.commit()

    return ResponseModel(message="删除成功")


# ==================== UI图片素材管理 ====================

@router.get("/images", response_model=ResponseModel)
async def get_images(
    app_type: Optional[str] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取图片素材列表"""
    query = db.query(UIImage).filter(UIImage.is_deleted == False)

    if app_type:
        query = query.filter(UIImage.app_type == app_type)
    if category:
        query = query.filter(UIImage.category == category)
    if keyword:
        query = query.filter(UIImage.name.contains(keyword))

    images = query.order_by(UIImage.sort_order, UIImage.id).all()

    return ResponseModel(data=[{
        "id": img.id,
        "code": img.code,
        "name": img.name,
        "app_type": img.app_type,
        "category": img.category,
        "image_url": img.image_url,
        "suggested_width": img.suggested_width,
        "suggested_height": img.suggested_height,
        "description": img.description,
        "sort_order": img.sort_order,
        "is_active": img.is_active,
        "created_at": img.created_at.strftime("%Y-%m-%d %H:%M") if img.created_at else None
    } for img in images])


@router.post("/images", response_model=ResponseModel)
async def create_image(
    code: str,
    name: str,
    app_type: str,
    image_url: str,
    category: str = "common",
    suggested_width: Optional[int] = None,
    suggested_height: Optional[int] = None,
    description: Optional[str] = None,
    sort_order: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建图片素材"""
    # 检查编码是否已存在
    existing = db.query(UIImage).filter(
        UIImage.code == code,
        UIImage.app_type == app_type,
        UIImage.is_deleted == False
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该图片编码已存在")

    image = UIImage(
        code=code,
        name=name,
        app_type=app_type,
        category=category,
        image_url=image_url,
        suggested_width=suggested_width,
        suggested_height=suggested_height,
        description=description,
        sort_order=sort_order
    )

    db.add(image)
    db.commit()
    db.refresh(image)

    return ResponseModel(data={"id": image.id}, message="创建成功")


@router.put("/images/{image_id}", response_model=ResponseModel)
async def update_image(
    image_id: int,
    name: Optional[str] = None,
    category: Optional[str] = None,
    image_url: Optional[str] = None,
    suggested_width: Optional[int] = None,
    suggested_height: Optional[int] = None,
    description: Optional[str] = None,
    sort_order: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新图片素材"""
    image = db.query(UIImage).filter(UIImage.id == image_id, UIImage.is_deleted == False).first()

    if not image:
        raise HTTPException(status_code=404, detail="图片素材不存在")

    if name is not None:
        image.name = name
    if category is not None:
        image.category = category
    if image_url is not None:
        image.image_url = image_url
    if suggested_width is not None:
        image.suggested_width = suggested_width
    if suggested_height is not None:
        image.suggested_height = suggested_height
    if description is not None:
        image.description = description
    if sort_order is not None:
        image.sort_order = sort_order
    if is_active is not None:
        image.is_active = is_active

    db.commit()

    return ResponseModel(message="更新成功")


@router.delete("/images/{image_id}", response_model=ResponseModel)
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除图片素材"""
    image = db.query(UIImage).filter(UIImage.id == image_id, UIImage.is_deleted == False).first()

    if not image:
        raise HTTPException(status_code=404, detail="图片素材不存在")

    image.is_deleted = True
    image.deleted_at = datetime.now()
    db.commit()

    return ResponseModel(message="删除成功")


# ==================== 图标分类和应用类型选项 ====================

@router.get("/options", response_model=ResponseModel)
async def get_options(current_user = Depends(get_current_user)):
    """获取选项列表"""
    return ResponseModel(data={
        "app_types": [
            {"label": "用户端小程序", "value": "user"},
            {"label": "教练端小程序", "value": "coach"},
            {"label": "管理后台", "value": "admin"}
        ],
        "icon_categories": [
            {"label": "底部导航栏", "value": "tabbar"},
            {"label": "菜单图标", "value": "menu"},
            {"label": "功能图标", "value": "function"},
            {"label": "其他图标", "value": "other"}
        ],
        "image_categories": [
            {"label": "背景图", "value": "background"},
            {"label": "空状态图", "value": "empty"},
            {"label": "图标图片", "value": "icon"},
            {"label": "Logo", "value": "logo"},
            {"label": "其他", "value": "other"}
        ]
    })
