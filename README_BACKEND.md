# SAGE 商业潜力分析系统 - 后端开发文档

## 1. 概述
SAGE 是一个基于大语言模型（LLM）和联网搜索技术的全行业通用商业分析引擎。它能够自动识别项目赛道，抓取全网市场情报，并从风险投资（VC）合伙人的视角生成深度研报。

## 2. 核心模块说明

- **`agent.py`**: 核心逻辑调度中心，包含 `BusinessResearcher` 类。实现了赛道感知、动态关键词生成及多阶段分析流水线。
- **`config.py`**: 全局配置中心，定义 API 密钥、模型参数及系统提示词。
- **`utils.py`**: 基础工具库。封装了 PDF 文本提取、Google 搜索（Serper API）及 JSON 数据清洗逻辑。

## 3. 快速上手

### 环境准备
确保已安装 `requirements.txt` 中的依赖：
```bash
pip install -r requirements.txt
```

### Python 调用示例
你可以通过以下代码在自己的服务中快速集成商业分析功能：

```python
import logging
from agent import BusinessResearcher
import config

# 初始化日志（推荐）
logging.basicConfig(level=logging.INFO)

# 1. 初始化研究员智能体
# 也可以直接传递 key，或在 config.py 中预设
researcher = BusinessResearcher(api_key=config.LLM_API_KEY)

# 2. 执行分析流水线
# 输入：PDF 文件路径
# 输出：结构化的 JSON 字典
pdf_path = "path/to/your/bp.pdf"
report = researcher.analyze_bp_pipeline(pdf_path)

# 3. 处理结果
if "error" not in report:
    print(f"识别赛道: {report['industry_analysis']['detected_industry']}")
    print(f"风险点: {report['risk_assessment']}")
else:
    print(f"分析失败: {report['error']}")
```

## 4. 数据 Schema 说明

输出结果遵循严格的 JSON 格式：

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `industry_analysis` | dict | 包含识别出的赛道、市场规模、CAGR 及数据来源 |
| `competitors` | list | 商业化竞品及替代品分析列表 |
| `funding_ecosystem` | dict | 赛道融资热度及趋势摘要 |
| `pain_point_validation` | dict | 基于全网舆论的痛点真实性评分及理由 |
| `public_sentiment` | dict | 辩证的公众舆情分析（收益 vs 担忧） |
| `risk_assessment` | list | 尖锐的 VC 级风险点列表 |

## 5. 异常处理
- **网络异常**: `utils.py` 内部实现了重试与超时机制（15s）。
- **解析异常**: 若 LLM 返回非标准格式，`agent.py` 会通过 `clean_json_string` 强制提取并填充兜底空模板，确保主程序不中断。
