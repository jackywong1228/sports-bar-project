#!/bin/bash
# Sports Bar 云服务器一键部署脚本
# 适用于 Ubuntu 22.04

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Sports Bar 服务器部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 配置变量
DOMAIN="yunlifang.cloud"
DB_NAME="sports_bar"
DB_USER="sports"
DB_PASS="SportsBar2026!"
PROJECT_DIR="/var/www/sports-bar-project"

echo -e "\n${YELLOW}[1/8] 更新系统并安装基础软件...${NC}"
apt update && apt upgrade -y
apt install -y git curl wget vim unzip software-properties-common

echo -e "\n${YELLOW}[2/8] 安装 Python 3.10...${NC}"
apt install -y python3 python3-pip python3-venv

echo -e "\n${YELLOW}[3/8] 安装 Node.js 18.x...${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

echo -e "\n${YELLOW}[4/8] 安装 MySQL 8.0...${NC}"
apt install -y mysql-server
systemctl start mysql
systemctl enable mysql

# 配置 MySQL
echo -e "\n${YELLOW}[4.1] 配置 MySQL 数据库...${NC}"
mysql -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';"
mysql -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"
echo -e "${GREEN}MySQL 数据库配置完成${NC}"

echo -e "\n${YELLOW}[5/8] 安装 Nginx...${NC}"
apt install -y nginx
systemctl start nginx
systemctl enable nginx

echo -e "\n${YELLOW}[6/8] 安装 Certbot (SSL证书)...${NC}"
apt install -y certbot python3-certbot-nginx

echo -e "\n${YELLOW}[7/8] 创建项目目录...${NC}"
mkdir -p ${PROJECT_DIR}
mkdir -p ${PROJECT_DIR}/backend/uploads
mkdir -p ${PROJECT_DIR}/backend/certs

echo -e "\n${YELLOW}[8/8] 配置防火墙...${NC}"
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  基础环境安装完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n接下来需要手动完成以下步骤:"
echo -e "1. 上传项目代码到 ${PROJECT_DIR}"
echo -e "2. 配置后端环境变量"
echo -e "3. 配置 Nginx"
echo -e "4. 配置 SSL 证书"
echo -e "\n数据库信息:"
echo -e "  数据库名: ${DB_NAME}"
echo -e "  用户名: ${DB_USER}"
echo -e "  密码: ${DB_PASS}"
echo -e "\nDATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASS}@localhost:3306/${DB_NAME}"
