#!/bin/bash
# Sports Bar 前端构建脚本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="/var/www/sports-bar-project"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  构建管理后台前端${NC}"
echo -e "${GREEN}========================================${NC}"

cd ${PROJECT_DIR}/admin-frontend

echo -e "\n${YELLOW}[1/3] 安装 npm 依赖...${NC}"
npm install

echo -e "\n${YELLOW}[2/3] 检查生产环境配置...${NC}"
if [ ! -f .env.production ]; then
    cat > .env.production << 'EOF'
VITE_API_BASE_URL=/api/v1
EOF
    echo -e "${GREEN}.env.production 已创建${NC}"
else
    echo -e "${YELLOW}.env.production 已存在，跳过${NC}"
fi

echo -e "\n${YELLOW}[3/3] 构建前端...${NC}"
npm run build

echo -e "\n${GREEN}前端构建完成!${NC}"
echo -e "构建产物位于: ${PROJECT_DIR}/admin-frontend/dist"
