#!/bin/bash
# Sports Bar 后端配置脚本
# 在上传代码后执行

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="/var/www/sports-bar-project"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  配置后端服务${NC}"
echo -e "${GREEN}========================================${NC}"

cd ${PROJECT_DIR}/backend

echo -e "\n${YELLOW}[1/5] 创建 Python 虚拟环境...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "\n${YELLOW}[2/5] 安装 Python 依赖...${NC}"
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo -e "\n${YELLOW}[3/5] 配置环境变量...${NC}"
if [ ! -f .env ]; then
    cp ${PROJECT_DIR}/deploy/backend.env .env
    echo -e "${GREEN}.env 文件已创建，请稍后修改微信配置${NC}"
else
    echo -e "${YELLOW}.env 文件已存在，跳过${NC}"
fi

echo -e "\n${YELLOW}[4/5] 初始化数据库...${NC}"
python init_data.py

echo -e "\n${YELLOW}[5/5] 配置 Systemd 服务...${NC}"
cp ${PROJECT_DIR}/deploy/sports-bar.service /etc/systemd/system/
systemctl daemon-reload
systemctl start sports-bar
systemctl enable sports-bar

echo -e "\n${GREEN}后端服务配置完成!${NC}"
echo -e "查看状态: systemctl status sports-bar"
echo -e "查看日志: journalctl -u sports-bar -f"
