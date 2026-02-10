"""文件上传API"""
import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.api.deps import get_current_user, get_current_member
from app.schemas.response import ResponseModel

router = APIRouter()

# 上传配置
UPLOAD_DIR = "uploads"
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]


def detect_image_type(content: bytes) -> Optional[str]:
    """通过文件头 magic bytes 检测实际图片类型（不依赖 content_type）"""
    if len(content) < 12:
        return None
    if content[:3] == b'\xff\xd8\xff':
        return "image/jpeg"
    if content[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    if content[:4] == b'GIF8':
        return "image/gif"
    if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        return "image/webp"
    return None


ALLOWED_FILE_TYPES = ALLOWED_IMAGE_TYPES + ["application/pdf", "application/msword",
                                             "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def ensure_upload_dir(folder: str = ""):
    """确保上传目录存在"""
    path = os.path.join(UPLOAD_DIR, folder) if folder else UPLOAD_DIR
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def generate_filename(original_filename: str) -> str:
    """生成唯一文件名"""
    ext = os.path.splitext(original_filename)[1].lower()
    date_str = datetime.now().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:8]
    return f"{date_str}_{unique_id}{ext}"


@router.post("/image", response_model=ResponseModel)
async def upload_image(
    file: UploadFile = File(...),
    folder: str = "images",
    current_user = Depends(get_current_user)
):
    """上传单张图片"""
    # 验证文件类型
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="不支持的图片格式，请上传 JPG/PNG/GIF/WEBP 格式")

    # 读取文件内容
    content = await file.read()

    # 验证文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）")

    # 确保目录存在
    upload_path = ensure_upload_dir(folder)

    # 生成文件名并保存
    filename = generate_filename(file.filename or "image.jpg")
    file_path = os.path.join(upload_path, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # 返回相对URL
    relative_url = f"/{UPLOAD_DIR}/{folder}/{filename}"

    return ResponseModel(data={
        "url": relative_url,
        "filename": filename,
        "size": len(content),
        "content_type": file.content_type
    })


@router.post("/member-image", response_model=ResponseModel)
async def upload_member_image(
    file: UploadFile = File(...),
    current_member = Depends(get_current_member)
):
    """会员端上传图片（头像等）"""
    content = await file.read()

    # 通过文件头判断实际图片类型（wx.uploadFile 的 content_type 不可靠）
    actual_type = detect_image_type(content)
    if not actual_type:
        raise HTTPException(status_code=400, detail="不支持的图片格式，请上传 JPG/PNG/GIF/WEBP 格式")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）")

    # 根据实际类型决定扩展名
    ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}
    ext = ext_map.get(actual_type, ".jpg")

    upload_path = ensure_upload_dir("avatars")
    # 使用检测到的真实扩展名，而非原始文件名的扩展名
    date_str = datetime.now().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{date_str}_{unique_id}{ext}"
    file_path = os.path.join(upload_path, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    relative_url = f"/{UPLOAD_DIR}/avatars/{filename}"

    return ResponseModel(data={
        "url": relative_url,
        "filename": filename,
        "size": len(content),
        "content_type": actual_type
    })


@router.post("/images", response_model=ResponseModel)
async def upload_images(
    files: List[UploadFile] = File(...),
    folder: str = "images",
    current_user = Depends(get_current_user)
):
    """批量上传图片"""
    if len(files) > 9:
        raise HTTPException(status_code=400, detail="一次最多上传9张图片")

    results = []

    for file in files:
        # 验证文件类型
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            continue

        # 读取文件内容
        content = await file.read()

        # 验证文件大小
        if len(content) > MAX_FILE_SIZE:
            continue

        # 确保目录存在
        upload_path = ensure_upload_dir(folder)

        # 生成文件名并保存
        filename = generate_filename(file.filename or "image.jpg")
        file_path = os.path.join(upload_path, filename)

        with open(file_path, "wb") as f:
            f.write(content)

        relative_url = f"/{UPLOAD_DIR}/{folder}/{filename}"
        results.append({
            "url": relative_url,
            "filename": filename,
            "size": len(content)
        })

    return ResponseModel(data=results)


@router.post("/file", response_model=ResponseModel)
async def upload_file(
    file: UploadFile = File(...),
    folder: str = "files",
    current_user = Depends(get_current_user)
):
    """上传文件"""
    # 验证文件类型
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    # 读取文件内容
    content = await file.read()

    # 验证文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制（最大 {MAX_FILE_SIZE // 1024 // 1024}MB）")

    # 确保目录存在
    upload_path = ensure_upload_dir(folder)

    # 生成文件名并保存
    filename = generate_filename(file.filename or "file")
    file_path = os.path.join(upload_path, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    relative_url = f"/{UPLOAD_DIR}/{folder}/{filename}"

    return ResponseModel(data={
        "url": relative_url,
        "filename": filename,
        "original_name": file.filename,
        "size": len(content),
        "content_type": file.content_type
    })


@router.delete("/file", response_model=ResponseModel)
async def delete_file(
    path: str,
    current_user = Depends(get_current_user)
):
    """删除文件"""
    # 安全检查：确保路径在上传目录内
    if not path.startswith(f"/{UPLOAD_DIR}/"):
        raise HTTPException(status_code=400, detail="无效的文件路径")

    # 去掉开头的斜杠
    file_path = path.lstrip("/")

    if os.path.exists(file_path):
        os.remove(file_path)
        return ResponseModel(message="文件删除成功")
    else:
        raise HTTPException(status_code=404, detail="文件不存在")


@router.get("/config", response_model=ResponseModel)
async def get_upload_config():
    """获取上传配置"""
    return ResponseModel(data={
        "max_file_size": MAX_FILE_SIZE,
        "allowed_image_types": ALLOWED_IMAGE_TYPES,
        "allowed_file_types": ALLOWED_FILE_TYPES,
        "max_images_per_upload": 9
    })
