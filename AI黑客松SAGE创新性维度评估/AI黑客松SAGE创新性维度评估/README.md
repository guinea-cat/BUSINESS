# SAGE - AI应用创新性评估系统

![SAGE Logo](https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=AI%20hacking%20competition%20evaluation%20system%20logo%2C%20modern%20design%2C%20blue%20and%20green%20colors%2C%20professional%20appearance&image_size=square_hd)

## 项目简介

SAGE（Smart AI Hackathon Evaluation System）是一款专为黑客松比赛评委设计的AI项目评估工具，通过多维度分析为评委提供专业、客观的创新性评估报告。

## 核心功能

- **6维度评估框架**：技术选型与实现、系统架构与设计、工程化与可持续性、问题定义与价值、场景创新性、市场与生态契合度
- **双轨评分**：技术创新力（40%）+ 场景创新力（60%）
- **社会价值评估**：基础项评估（30分）+ 核心亮点项评估（70分）
- **AI辅助报告**：使用DeepSeek模型生成详细、专业的评估报告
- **评委支持**：提供核心追问问题、潜在风险点和关键考察维度
- **GitHub仓库分析**：直接输入GitHub链接进行项目分析

## 技术栈

- **前端**：HTML5, CSS3, JavaScript
- **后端**：Python 3.8+
- **AI模型**：DeepSeek
- **Web框架**：Gradio（可选）

## 快速开始

### 1. 环境配置

```bash
# 克隆仓库
git clone <repository-url>
cd AI黑客松SAGE创新性维度评估

# 安装依赖
pip install -r requirements.txt

# 设置环境变量（用于DeepSeek模型）
export DEEPSEEK_API_BASE=http://localhost:8000/v1
export DEEPSEEK_API_KEY=EMPTY
export DEEPSEEK_MODEL=Valdemardi/DeepSeek-R1-Distill-Qwen-32B-AWQ
```

### 2. 使用网页界面

1. 打开 `index.html` 文件即可访问网页界面
2. 在表单中输入GitHub仓库链接
3. 点击「开始分析」按钮
4. 等待分析完成，查看评估报告

### 3. 使用命令行工具

```bash
# 运行评估
python -m sage.evaluate --repo_url [GitHub仓库URL]

# 示例
python -m sage.evaluate --repo_url https://github.com/example/repo
```

## 评估体系

### 创新性评估（100分）

#### 技术创新力（40%）
- **技术选型与实现**（13%）：评估技术栈前沿程度和代码质量
- **系统架构与设计**（13%）：评估代码结构和设计模式
- **工程化与可持续性**（14%）：评估CI/CD、容器化、测试等工程实践

#### 场景创新力（60%）
- **问题定义与价值**（18%）：评估问题定义清晰度和价值主张
- **场景创新性**（24%）：评估应用场景新颖性和社会价值
- **市场与生态契合度**（18%）：评估与技术趋势的契合度

### 社会价值评估（100分）

#### 基础项评估（30分）
- **伦理安全合规性**：伦理红线检查、隐私与数据保护、算法公平性

#### 核心亮点项评估（70分）
- **社会影响深度**：解决具体社会问题、服务特定群体
- **环境可持续性**：环保、节能、可持续发展相关
- **公益普惠导向**：普惠性、可及性、非营利性项目
- **长期愿景与变革潜力**：有宏大愿景、寻求系统性变革

## 报告格式

系统生成的评估报告包含以下部分：

1. **项目概览与核心定位**：项目简介、创新类型判断、核心价值主张
2. **创新性总评**：总分解读、双轨分析、主要亮点、主要不足
3. **六维能力深度分析**：维度得分可视化、优势维度分析、短板维度分析
4. **核心维度专项分析**：技术创新力板块、场景创新力板块
5. **改进建议**：技术加固建议、场景深化建议、产品化推进建议
6. **评委关注点**：核心追问问题、潜在风险点、关键考察维度
7. **总结与评委建议**：总体评价、核心优势总结、最需改进之处

## 系统文件

- **SAGE_INNOVATION_EVALUATION_FINAL.md**：最终评估体系文档
- **SAGE_INNOVATION_EVALUATION_MODIFICATION_REPORT.md**：评估体系修改报告
- **SAGE_PROMPT_OPTIMIZATION.md**：提示词工程优化方案
- **index.html**：GitHub仓库分析网页界面
- **app.py**：Gradio应用程序代码
- **start_app.py**：启动Gradio服务器脚本

## 使用指南

### 网页界面使用

1. 打开 `index.html` 文件
2. 在「GitHub仓库URL」输入框中粘贴要分析的GitHub仓库链接
3. 选择是否启用DeepSeek模型优化报告
4. 点击「开始分析」按钮
5. 等待分析完成（通常需要30秒-2分钟）
6. 查看生成的评估报告

### 命令行使用

```bash
# 基本用法
python -m sage.evaluate --repo_url [GitHub仓库URL]

# 高级选项
python -m sage.evaluate --repo_url [GitHub仓库URL] --use_deepseek True --output_format markdown
```

## 配置选项

### DeepSeek模型配置

在 `.env` 文件中设置以下环境变量：

```
DEEPSEEK_API_BASE=http://localhost:8000/v1
DEEPSEEK_API_KEY=EMPTY
DEEPSEEK_MODEL=Valdemardi/DeepSeek-R1-Distill-Qwen-32B-AWQ
```

### 评估参数配置

可以在 `config.py` 文件中调整评估参数：

- 维度权重
- 评分标准
- 报告格式

## 案例分析

### 案例：Alzheimer-Chatbot

**评估结果**：
- **总分**：72.5/100
- **创新等级**：中等创新 ⭐⭐⭐
- **技术创新力**：28.5/40
- **场景创新力**：44.0/60

**核心亮点**：
1. **场景创新性突出**：聚焦阿尔茨海默症患者这一特定人群，社会价值高
2. **技术实现合理**：使用LangChain等现代AI框架，技术选型得当
3. **问题定义清晰**：明确解决阿尔茨海默症患者的陪伴需求

## 贡献指南

欢迎对SAGE项目进行贡献！您可以：

1. 提交Issue报告bug或提出新功能建议
2. 提交Pull Request改进代码
3. 分享使用经验和案例

## 许可证

本项目采用MIT许可证。详见 [LICENSE](LICENSE) 文件。

## 联系方式

- **项目维护者**：[Your Name]
- **邮箱**：[your-email@example.com]
- **GitHub**：[Your GitHub Profile]

---

**SAGE - 让黑客松评审更智能、更专业、更公平**