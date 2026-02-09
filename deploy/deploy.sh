#!/bin/bash
# Sports Bar 生产环境部署脚本
# 前提: 基础环境已安装（deploy-server.sh），代码已在 /var/www/sports-bar-project
# 用法: bash deploy/deploy.sh [step]
#   无参数: 执行全部步骤
#   backend: 仅部署后端
#   frontend: 仅构建前端
#   nginx: 仅配置 Nginx + SSL
#   verify: 仅验证部署状态

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_DIR="/var/www/sports-bar-project"
STEP=${1:-all}

print_header() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  $1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

print_step() {
    echo -e "\n${YELLOW}[$1] $2${NC}"
}

# ========== 后端部署 ==========
deploy_backend() {
    print_header "部署后端服务"
    cd ${PROJECT_DIR}/backend

    print_step "1/5" "创建 Python 虚拟环境..."
    if [ ! -d venv ]; then
        python3 -m venv venv
        echo -e "${GREEN}虚拟环境已创建${NC}"
    else
        echo -e "${YELLOW}虚拟环境已存在，跳过${NC}"
    fi
    source venv/bin/activate

    print_step "2/5" "安装 Python 依赖..."
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

    print_step "3/5" "配置环境变量..."
    if [ ! -f .env ]; then
        cp ${PROJECT_DIR}/deploy/backend.env .env
        # 自动生成 SECRET_KEY
        SECRET=$(openssl rand -hex 32)
        sed -i "s/your-secret-key-change-this-in-production/${SECRET}/" .env
        echo -e "${GREEN}.env 已创建，SECRET_KEY 已自动生成${NC}"
        echo -e "${RED}请手动编辑 .env 填写微信 AppID/AppSecret!${NC}"
    else
        echo -e "${YELLOW}.env 已存在，跳过${NC}"
    fi

    print_step "4/5" "初始化数据库..."
    python init_data.py

    print_step "5/5" "配置并启动 systemd 服务..."
    cp ${PROJECT_DIR}/deploy/sports-bar.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl restart sports-bar
    systemctl enable sports-bar

    echo -e "${GREEN}后端部署完成!${NC}"
    systemctl status sports-bar --no-pager
}

# ========== 前端构建 ==========
deploy_frontend() {
    print_header "构建管理后台前端"
    cd ${PROJECT_DIR}/admin-frontend

    print_step "1/2" "安装 npm 依赖..."
    npm install

    print_step "2/2" "构建前端..."
    npm run build

    echo -e "${GREEN}前端构建完成! 产物: ${PROJECT_DIR}/admin-frontend/dist${NC}"
}

# ========== Nginx + SSL ==========
deploy_nginx() {
    print_header "配置 Nginx + SSL"

    print_step "1/4" "部署 SSL 证书..."
    mkdir -p /etc/nginx/ssl
    if [ -f ${PROJECT_DIR}/yunlifang.cloud_bundle.crt ] && [ -f ${PROJECT_DIR}/yunlifang.cloud.key ]; then
        cp ${PROJECT_DIR}/yunlifang.cloud_bundle.crt /etc/nginx/ssl/
        cp ${PROJECT_DIR}/yunlifang.cloud.key /etc/nginx/ssl/
        chmod 600 /etc/nginx/ssl/yunlifang.cloud.key
        echo -e "${GREEN}SSL 证书已部署${NC}"
    else
        echo -e "${RED}错误: SSL 证书文件不存在!${NC}"
        exit 1
    fi

    print_step "2/4" "配置 Nginx..."
    cp ${PROJECT_DIR}/nginx-ssl.conf /etc/nginx/sites-available/sports-bar
    rm -f /etc/nginx/sites-enabled/default
    ln -sf /etc/nginx/sites-available/sports-bar /etc/nginx/sites-enabled/

    print_step "3/4" "测试 Nginx 配置..."
    nginx -t

    print_step "4/4" "重启 Nginx..."
    systemctl restart nginx

    echo -e "${GREEN}Nginx + SSL 配置完成!${NC}"
}

# ========== 验证部署 ==========
verify_deployment() {
    print_header "验证部署状态"
    ERRORS=0

    echo -e "\n${YELLOW}检查服务状态...${NC}"
    if systemctl is-active --quiet sports-bar; then
        echo -e "  ${GREEN}✓ sports-bar 服务运行中${NC}"
    else
        echo -e "  ${RED}✗ sports-bar 服务未运行${NC}"
        ERRORS=$((ERRORS+1))
    fi

    if systemctl is-active --quiet nginx; then
        echo -e "  ${GREEN}✓ nginx 服务运行中${NC}"
    else
        echo -e "  ${RED}✗ nginx 服务未运行${NC}"
        ERRORS=$((ERRORS+1))
    fi

    echo -e "\n${YELLOW}检查端口...${NC}"
    if ss -tlnp | grep -q ':8000'; then
        echo -e "  ${GREEN}✓ 后端 :8000 监听中${NC}"
    else
        echo -e "  ${RED}✗ 后端 :8000 未监听${NC}"
        ERRORS=$((ERRORS+1))
    fi

    if ss -tlnp | grep -q ':443'; then
        echo -e "  ${GREEN}✓ HTTPS :443 监听中${NC}"
    else
        echo -e "  ${RED}✗ HTTPS :443 未监听${NC}"
        ERRORS=$((ERRORS+1))
    fi

    echo -e "\n${YELLOW}检查 HTTPS 访问...${NC}"
    HTTP_CODE=$(curl -sk -o /dev/null -w "%{http_code}" https://localhost 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "  ${GREEN}✓ HTTPS 前端可访问 (HTTP $HTTP_CODE)${NC}"
    else
        echo -e "  ${RED}✗ HTTPS 前端不可访问 (HTTP $HTTP_CODE)${NC}"
        ERRORS=$((ERRORS+1))
    fi

    API_CODE=$(curl -sk -o /dev/null -w "%{http_code}" https://localhost/api/v1/docs 2>/dev/null || echo "000")
    if [ "$API_CODE" = "200" ]; then
        echo -e "  ${GREEN}✓ API 文档可访问 (HTTP $API_CODE)${NC}"
    else
        echo -e "  ${RED}✗ API 文档不可访问 (HTTP $API_CODE)${NC}"
        ERRORS=$((ERRORS+1))
    fi

    echo -e "\n${YELLOW}检查文件...${NC}"
    if [ -d ${PROJECT_DIR}/admin-frontend/dist ]; then
        echo -e "  ${GREEN}✓ 前端构建产物存在${NC}"
    else
        echo -e "  ${RED}✗ 前端构建产物不存在${NC}"
        ERRORS=$((ERRORS+1))
    fi

    if [ -f ${PROJECT_DIR}/backend/.env ]; then
        if grep -q "DEBUG=False" ${PROJECT_DIR}/backend/.env; then
            echo -e "  ${GREEN}✓ DEBUG=False 已设置${NC}"
        else
            echo -e "  ${RED}✗ DEBUG 未设置为 False!${NC}"
            ERRORS=$((ERRORS+1))
        fi
    fi

    echo ""
    if [ $ERRORS -eq 0 ]; then
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  所有检查通过! 部署成功!${NC}"
        echo -e "${GREEN}========================================${NC}"
    else
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}  发现 ${ERRORS} 个问题，请检查!${NC}"
        echo -e "${RED}========================================${NC}"
    fi

    echo -e "\n访问地址:"
    echo -e "  管理后台: https://yunlifang.cloud"
    echo -e "  API文档:  https://yunlifang.cloud/api/v1/docs"
    echo -e "  默认账号: admin / admin123"
}

# ========== 主流程 ==========
case $STEP in
    backend)
        deploy_backend
        ;;
    frontend)
        deploy_frontend
        ;;
    nginx)
        deploy_nginx
        ;;
    verify)
        verify_deployment
        ;;
    all)
        print_header "Sports Bar 全量部署"
        echo -e "开始时间: $(date)"

        deploy_backend
        deploy_frontend
        deploy_nginx
        verify_deployment

        echo -e "\n完成时间: $(date)"
        ;;
    *)
        echo "用法: bash deploy/deploy.sh [backend|frontend|nginx|verify|all]"
        exit 1
        ;;
esac
