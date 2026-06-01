# OpenStock — DCF 估值分析仪表板

基于 **Streamlit** 构建的自动化 DCF（Discounted Cash Flow，现金流折现）估值分析工具，用于快速评估公司内在价值。

---

## 功能概述

- 自动获取公司财务数据（通过 Finnhub API）
- 计算自由现金流并进行折现估值
- 交互式 Streamlit 仪表板，可视化展示估值结果

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r scripts/dcf_dashboard/requirements.txt
```

### 2. 配置 API 密钥

本工具使用 [Finnhub](https://finnhub.io/) 获取市场数据，需要设置 API 密钥：

**PowerShell：**
```powershell
$env:FINNHUB_API_KEY = "your_finnhub_api_key"
```

**CMD：**
```cmd
set FINNHUB_API_KEY=your_finnhub_api_key
```

> 可在 [Finnhub 官网](https://finnhub.io/) 免费申请 API 密钥。

### 3. 启动仪表板

```bash
streamlit run scripts/dcf_dashboard/dcf_dashboard.py
```

启动后浏览器将自动打开仪表板页面（默认 `http://localhost:8501`）。

---

## 项目结构

```
├── scripts/
│   └── dcf_dashboard/
│       ├── dcf_dashboard.py   # 主程序入口
│       ├── requirements.txt   # Python 依赖列表
│       └── README.md          # 详细说明文档
└── README.md                  # 本文件
```

---

## 注意事项

- 确保已正确设置 `FINNHUB_API_KEY` 环境变量，否则数据获取将失败
- 免费 API 计划存在调用频率限制，频繁请求可能触发限流
- 详细参数说明与模型假设请查阅 `scripts/dcf_dashboard/README.md`

---

## 许可证

本项目基于 [LICENSE](./LICENSE) 文件中规定的条款发布。
