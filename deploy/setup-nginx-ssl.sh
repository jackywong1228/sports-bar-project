#!/bin/bash
# Sports Bar Nginx + SSL 配置脚本
# 使用已购买的 SSL 证书（非 Let's Encrypt）

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DOMAIN="yunlifang.cloud"
PROJECT_DIR="/var/www/sports-bar-project"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  配置 Nginx 和 SSL 证书${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}[1/5] 部署 SSL 证书...${NC}"
mkdir -p /etc/nginx/ssl

if [ -f ${PROJECT_DIR}/yunlifang.cloud_bundle.crt ] && [ -f ${PROJECT_DIR}/yunlifang.cloud.key ]; then
    cp ${PROJECT_DIR}/yunlifang.cloud_bundle.crt /etc/nginx/ssl/
    cp ${PROJECT_DIR}/yunlifang.cloud.key /etc/nginx/ssl/
    chmod 600 /etc/nginx/ssl/yunlifang.cloud.key
    echo -e "${GREEN}SSL 证书已部署${NC}"
else
    echo -e "${RED}错误: SSL 证书文件不存在!${NC}"
    echo -e "请确保以下文件在 ${PROJECT_DIR}/ 目录:"
    echo -e "  - yunlifang.cloud_bundle.crt"
    echo -e "  - yunlifang.cloud.key"
    exit 1
fi

echo -e "\n${YELLOW}[2/5] 配置 Nginx...${NC}"
cp ${PROJECT_DIR}/nginx-ssl.conf /etc/nginx/sites-available/sports-bar

echo -e "\n${YELLOW}[3/5] 启用站点配置...${NC}"
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/sports-bar /etc/nginx/sites-enabled/

echo -e "\n${YELLOW}[4/5] 测试 Nginx 配置...${NC}"
nginx -t

echo -e "\n${YELLOW}[5/5] 重启 Nginx...${NC}"
systemctl restart nginx

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Nginx + SSL 配置完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n访问地址:"
echo -e "  管理后台: https://${DOMAIN}"
echo -e "  API文档:  https://${DOMAIN}/api/v1/docs"
