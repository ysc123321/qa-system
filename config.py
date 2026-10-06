# -*- coding: utf-8 -*-
"""全局配置：DeepSeek API、路径、检索参数、课程列表（含关键词）"""
import os

# ===== 1. DeepSeek API =====
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL   = "deepseek-chat"

# ===== 2. 路径配置 =====
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "data")
INDEX_DIR = os.path.join(BASE_DIR, "index")

# ===== 3. 切分与检索参数 =====
CHUNK_SIZE    = 500
CHUNK_OVERLAP = 80
TOP_K         = 5

# ===== 4. 课程列表（含课程识别关键词）=====
# 新增课程：加一行 + 建 data/子文件夹 + 放资料 + 重建索引
COURSES = {
    "电磁场": {
        "label": "工程电磁场",
        "data_subdir": "电磁场",
        "keywords": [
            "电场", "电荷", "电位", "电容", "高斯定理", "高斯面",
            "散度", "旋度", "梯度", "静电场", "介电常数", "极化",
            "镜像法", "电轴", "偶极", "电通量", "库仑", "电力线",
            "等位面", "等位线", "电位移", "矢量分析", "拉普拉斯",
            "泊松方程", "麦克斯韦", "电磁场", "磁场", "磁通", "磁链",
            "分界面", "边界条件", "唯一性定理", "分离变量",
            "有限差分", "亥姆霍兹", "标量场", "矢量场", "通量",
        ],
    },
    "电机": {
        "label": "电机与拖动基础",
        "data_subdir": "电机",
        "keywords": [
            "电机", "转矩", "转速", "励磁", "电枢", "变压器",
            "绕组", "异步", "同步", "直流电机", "交流电机", "拖动",
            "电动机", "发电机", "功率因数", "效率", "机械特性",
            "调速", "启动", "制动", "电磁转矩", "空载", "负载",
            "铭牌", "绝缘", "铁芯", "气隙", "谐波", "绕线式",
            "鼠笼式", "转差率", "同步转速", "额定功率",
        ],
    },
}