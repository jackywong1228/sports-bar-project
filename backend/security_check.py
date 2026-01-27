#!/usr/bin/env python3
"""
生产环境安全配置检查脚本
在部署前运行此脚本，确保所有安全配置正确
"""
import os
import sys
from pathlib import Path

def check_env_file():
    """检查 .env 文件配置"""
    print("=" * 60)
    print("检查 .env 文件配置...")
    print("=" * 60)

    env_file = Path(".env")
    if not env_file.exists():
        print("[X] 错误: .env 文件不存在")
        print("   请复制 .env.production.example 为 .env 并修改配置")
        return False

    with open(env_file, encoding='utf-8') as f:
        env_content = f.read()

    issues = []

    # 检查 SECRET_KEY
    if "your-secret-key-here-change-in-production" in env_content:
        issues.append("SECRET_KEY 仍使用默认值，请生成随机密钥")
    elif "SECRET_KEY=" not in env_content:
        issues.append("未配置 SECRET_KEY")

    # 检查 DEBUG 模式
    if "DEBUG=True" in env_content:
        issues.append("[!]  警告: DEBUG 模式为 True，生产环境应设置为 False")

    # 检查数据库密码
    if "DATABASE_URL=mysql+pymysql://root:" in env_content:
        issues.append("[!]  警告: 数据库使用 root 用户，建议创建专用用户")
    if ":123456@" in env_content or ":password@" in env_content:
        issues.append("数据库密码过于简单，请使用强密码")

    # 检查微信配置
    required_wechat_configs = [
        "WECHAT_APP_ID",
        "WECHAT_APP_SECRET",
        "WECHAT_MCH_ID",
        "WECHAT_API_KEY",
        "WECHAT_SERIAL_NO",
        "WECHAT_NOTIFY_URL"
    ]

    for config in required_wechat_configs:
        if f"{config}=" not in env_content or f"{config}=\n" in env_content or f"{config}=''" in env_content:
            issues.append(f"未配置 {config}")

    if issues:
        print("[X] 发现以下问题:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("[OK] .env 文件配置正常")
        return True

def check_cert_files():
    """检查证书文件"""
    print("\n" + "=" * 60)
    print("检查证书文件...")
    print("=" * 60)

    cert_dir = Path("certs")
    required_certs = [
        "apiclient_key.pem",
        "pub_key.pem"
    ]

    issues = []

    if not cert_dir.exists():
        issues.append("certs 目录不存在")
    else:
        for cert_file in required_certs:
            cert_path = cert_dir / cert_file
            if not cert_path.exists():
                issues.append(f"证书文件 {cert_file} 不存在")
            else:
                # 检查文件权限（仅在 Unix 系统）
                if os.name != 'nt':
                    stat_info = cert_path.stat()
                    mode = stat_info.st_mode & 0o777
                    if mode != 0o600:
                        issues.append(f"证书文件 {cert_file} 权限不正确 (当前: {oct(mode)}, 应为: 0o600)")

    if issues:
        print("[X] 发现以下问题:")
        for issue in issues:
            print(f"   - {issue}")
        if os.name != 'nt':
            print("\n修复命令:")
            print("   chmod 600 certs/*.pem")
        return False
    else:
        print("[OK] 证书文件配置正常")
        return True

def check_gitignore():
    """检查 .gitignore 配置"""
    print("\n" + "=" * 60)
    print("检查 .gitignore 配置...")
    print("=" * 60)

    gitignore_file = Path("../.gitignore")
    if not gitignore_file.exists():
        print("[X] 错误: .gitignore 文件不存在")
        return False

    with open(gitignore_file, encoding='utf-8') as f:
        gitignore_content = f.read()

    required_patterns = [
        ".env",
        "*.pem",
        "*.key"
    ]

    issues = []
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            issues.append(f"缺少 {pattern} 忽略规则")

    if issues:
        print("[X] 发现以下问题:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("[OK] .gitignore 配置正常")
        return True

def check_dependencies():
    """检查依赖版本"""
    print("\n" + "=" * 60)
    print("检查 Python 依赖...")
    print("=" * 60)

    try:
        import pkg_resources
        requirements_file = Path("requirements.txt")

        if not requirements_file.exists():
            print("[X] 错误: requirements.txt 不存在")
            return False

        print("[OK] 依赖文件存在")
        print("   建议运行: pip-audit 检查安全漏洞")
        return True
    except Exception as e:
        print(f"[!]  警告: 无法检查依赖 - {e}")
        return True

def main():
    print("\n" + "=" * 60)
    print("生产环境安全配置检查")
    print("=" * 60 + "\n")

    # 切换到 backend 目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    results = []
    results.append(("环境变量配置", check_env_file()))
    results.append(("证书文件", check_cert_files()))
    results.append(("Git 忽略配置", check_gitignore()))
    results.append(("依赖检查", check_dependencies()))

    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "[OK] 通过" if passed else "[X] 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)

    if all_passed:
        print("[OK] 所有检查通过，可以部署到生产环境")
        print("\n部署前最后确认:")
        print("  1. 确保服务器已配置 HTTPS")
        print("  2. 确保防火墙规则正确")
        print("  3. 确保数据库已备份")
        print("  4. 在微信公众平台配置服务器域名")
        return 0
    else:
        print("[X] 检查未通过，请修复上述问题后再部署")
        print("\n详细修复指南请查看: SECURITY.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
