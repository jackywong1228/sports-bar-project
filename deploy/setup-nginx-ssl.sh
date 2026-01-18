#!/bin/bash
# Sports Bar Nginx 和 SSL 配置脚本

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

echo -e "\n${YELLOW}[1/4] 配置 Nginx...${NC}"
cp ${PROJECT_DIR}/deploy/nginx-sports-bar.conf /etc/nginx/sites-available/sports-bar

# 删除默认配置（如果存在）
rm -f /etc/nginx/sites-enabled/default

# 启用新配置
ln -sf /etc/nginx/sites-available/sports-bar /etc/nginx/sites-enabled/

echo -e "\n${YELLOW}[2/4] 测试 Nginx 配置...${NC}"
nginx -t

echo -e "\n${YELLOW}[3/4] 重启 Nginx...${NC}"
systemctl restart nginx

echo -e "\n${YELLOW}[4/4] 配置 SSL 证书...${NC}"
echo -e "${YELLOW}请确保域名 ${DOMAIN} 已解析到服务器 IP${NC}"
echo -e "${YELLOW}正在申请 Let's Encrypt 证书...${NC}"

certbot --nginx -d ${DOMAIN} -d www.${DOMAIN} --non-interactive --agree-tos --email admin@${DOMAIN} || {
    echo -e "${RED}SSL 证书申请失败，可能是域名未解析${NC}"
    echo -e "${YELLOW}请手动执行: certbot --nginx -d ${DOMAIN}${NC}"
}

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  配置完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n访问地址:"
echo -e "  管理后台: https://${DOMAIN}"
echo -e "  API文档: https://${DOMAIN}/api/v1/docs"
echo -e "\n默认管理员账号:"
echo -e "  用户名: admin"
echo -e "  密码: admin123"
