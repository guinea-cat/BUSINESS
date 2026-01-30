"""提示词工程库 - 系统性的提示词模板和最佳实践

本模块提供专业、结构化的提示词模板，用于优化Deepseek模型的查询引导与性能提升。
通过构建清晰、专业的提示词工程库，实现更高效、准确的评估报告生成。
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class PromptTemplate:
    """提示词模板类"""
    name: str  # 模板名称
    description: str  # 模板描述
    system_prompt: str  # 系统提示词
    user_prompt_template: str  # 用户提示词模板
    parameters: List[str]  # 参数列表
    examples: List[Dict[str, str]]  # 示例
    category: str  # 分类
    version: str = "1.0"  # 版本
    default_params: Dict[str, Any] = field(default_factory=dict)  # 默认参数
    required_params: List[str] = field(default_factory=list)  # 必需参数
    scene_specific: bool = False  # 是否为场景特定模板
    applicable_scenes: List[str] = field(default_factory=list)  # 适用场景列表


class PromptEngineeringLibrary:
    """提示词工程库"""
    
    def __init__(self):
        """初始化提示词工程库"""
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, PromptTemplate]:
        """加载提示词模板"""
        templates = {}
        
        # 1. 创新性评估报告优化模板
        templates["innovation_report_optimizer"] = PromptTemplate(
            name="innovation_report_optimizer",
            description="优化AI应用创新性评估报告，生成详细、专业的评审报告",
            system_prompt="""你是一位资深的AI应用评审专家和技术分析师，负责将项目评估数据转化为极其详尽、深入、专业的评审报告。

## 核心要求
1. **深度思考模式**：在生成报告前，先对项目进行深度思考，分析其本质、创新点和潜在价值
2. **去模板化**：摆脱固定格式的限制，根据项目特点自由组织内容结构，突出项目的独特性
3. **深度分析**：每个维度分析必须充分展开，包含：
   - 现状详细描述（具体技术/特性）
   - 优点分析（2-3个具体优点，要有数据或事实支持）
   - 不足分析（1-2个具体不足，要切中要害）
   - 与同类项目的深度对比
   - 具体可行的改进方向建议
4. **针对性**：报告内容必须紧密结合项目本身的特点，避免泛泛而谈，要有具体的项目细节和案例
5. **AI幻觉防护**：基于事实和数据进行分析，避免产生AI幻觉，对于不确定的信息要明确标注

## 报告风格
- 语言专业严谨，但易于理解
- 评价客观公正，引用具体数据和事实
- 分析要深入透彻，不能流于表面
- 建议要具体可操作，有明确的实施路径
- 突出项目的实际价值和社会影响
- 结构清晰，逻辑连贯，层层递进

## 内容要求
- **项目本质分析**：深入理解项目的核心价值和创新本质
- **技术深度分析**：分析技术实现的创新点和技术选型的合理性
- **场景深度分析**：分析应用场景的创新性和社会价值
- **市场深度分析**：分析市场定位和竞争优势
- **风险深度分析**：分析项目面临的技术和商业风险
- **发展潜力分析**：分析项目的长期发展潜力和扩展空间

## 格式建议
- 使用Markdown格式，但不要拘泥于固定模板
- 善用表格、列表等形式增强可读性
- 每个章节都要有实质内容，禁止空泛描述
- 根据项目特点灵活组织内容结构""",

            user_prompt_template="""# 项目评估数据

## 基本信息
| 属性 | 值 |
|------|------|
| 项目名称 | {repo_name} |
| 项目描述 | {description} |
| 主要语言 | {language} |
| GitHub Star数 | {stars:,} |
| 项目URL | {repo_url} |

## 评估得分概览
| 指标 | 得分 | 满分 |
|------|------|------|
| **总分** | **{total_score:.1f}** | 100 |
| 创新等级 | {level} {level_stars} | - |
| 技术创新力 | {tech_innovation_score:.1f} | 40 |
| 场景创新力 | {scenario_innovation_score:.1f} | 60 |

## 六维度详细得分
{dim_table}

## 雷达图分析
{radar_analysis}

## 各维度详细分析数据
{analyses_text}

## 现有改进建议
### 技术加固
{tech_suggestions}

### 场景深化  
{scenario_suggestions}

### 产品化推进
{product_suggestions}

## 评委关注点
{judge_focus_points}

---

# 报告生成要求

**重要：你必须生成一份极其详细、专业的评审报告，总字数不少于4000字！**

请严格按照以下格式和要求输出报告：

---

# {repo_name} - AI应用创新性评审报告

## 一、项目概览与核心定位

### 1.1 项目简介
（详细描述项目是什么、解决什么问题、目标用户是谁，4-5句话）

### 1.2 创新类型判断
（判断是技术驱动型、场景驱动型还是综合型创新，说明判断依据，3-4句话）

### 1.3 核心价值主张
（项目的独特价值是什么，与竞品的差异化，3-4句话）

---

## 二、创新性总评

### 2.1 总分解读
（详细解读{total_score:.1f}分意味着什么，在同类项目中处于什么水平，4-5句话）

### 2.2 双轨分析：技术创新力 vs 场景创新力
（对比分析技术创新力{tech_innovation_score:.1f}/40和场景创新力{scenario_innovation_score:.1f}/60的表现，哪个更突出，为什么，5-6句话）

### 2.3 主要亮点（3个）
1. **亮点一**：（具体描述，2-3句话）
2. **亮点二**：（具体描述，2-3句话）
3. **亮点三**：（具体描述，2-3句话）

### 2.4 主要不足（2个）
1. **不足一**：（具体描述，2-3句话）
2. **不足二**：（具体描述，2-3句话）

---

## 三、六维能力雷达分析

### 3.1 维度得分可视化
（用ASCII进度条展示6个维度得分，格式如：技术选型：████████░░ 80分）

### 3.2 优势维度深度分析
（选择得分最高的2个维度，详细分析为什么表现好，有哪些具体体现，每个维度4-5句话）

### 3.3 短板维度深度分析
（选择得分最低的2个维度，详细分析为什么表现不佳，原因是什么，每个维度4-5句话）

### 3.4 维度均衡性评价
（分析6个维度是否均衡，是否存在明显的"木桶效应"，3-4句话）

---

## 四、详细维度分析

### 技术创新力板块（满分40分，得分{tech_innovation_score:.1f}分）

#### 4.1 技术选型与实现
**得分**：X/100 | **权重**：13%

**现状分析**：
（详细描述项目使用了哪些技术栈、框架、库，技术选型的特点，5-6句话）

**优点**：
- 优点1：（具体描述）
- 优点2：（具体描述）

**不足**：
- 不足1：（具体描述）

**与同类项目对比**：
（与同类AI应用的技术选型对比，2-3句话）

**改进方向**：
（具体的技术改进建议，2-3句话）

---

#### 4.2 系统架构与设计
**得分**：X/100 | **权重**：13%

**现状分析**：
（详细描述项目的架构模式、模块划分、代码组织，5-6句话）

**优点**：
- 优点1：（具体描述）
- 优点2：（具体描述）

**不足**：
- 不足1：（具体描述）

**架构评估**：
| 评估项 | 评价 |
|--------|------|
| 模块化程度 | 高/中/低 |
| 耦合度 | 高/中/低 |
| 可扩展性 | 好/中/差 |
| 代码复用性 | 好/中/差 |

**改进方向**：
（具体的架构改进建议，2-3句话）

---

#### 4.3 工程化与可持续性
**得分**：X/100 | **权重**：14%

**现状分析**：
（详细描述项目的工程化配置：CI/CD、测试、文档、部署，5-6句话）

**工程化检查清单**：
| 检查项 | 状态 |
|--------|------|
| CI/CD配置 | ✓/✗ |
| 自动化测试 | ✓/✗ |
| Docker支持 | ✓/✗ |
| 文档完善度 | 好/中/差 |
| 代码规范 | 好/中/差 |

**优点**：
- 优点1：（具体描述）

**不足**：
- 不足1：（具体描述）

**改进方向**：
（具体的工程化改进建议，2-3句话）

---

### 场景创新力板块（满分60分，得分{scenario_innovation_score:.1f}分）

#### 4.4 问题定义与价值
**得分**：X/100 | **权重**：18%

**现状分析**：
（详细描述项目定义的问题、目标用户、价值主张，5-6句话）

**问题定义评估**：
| 评估项 | 评价 |
|--------|------|
| 问题清晰度 | 高/中/低 |
| 用户画像清晰度 | 高/中/低 |
| 痛点挖掘深度 | 深/中/浅 |
| 价值主张独特性 | 高/中/低 |

**优点**：
- 优点1：（具体描述）

**不足**：
- 不足1：（具体描述）

**改进方向**：
（具体的改进建议，2-3句话）

---

#### 4.5 场景创新性（核心评估维度）
**得分**：X/100 | **权重**：24%（重点）

**⭐ 这是本报告的核心评估维度，需要重点关注 ⭐**

**现状分析**：
（详细描述项目的应用场景、创新点、服务的用户群体，6-8句话）

**场景创新性评估**：
| 评估项 | 评价 | 说明 |
|--------|------|------|
| 场景新颖性 | 高/中/低 | （说明） |
| 目标人群特殊性 | 高/中/低 | （说明） |
| 跨领域融合 | 有/无 | （说明） |
| 社会价值 | 高/中/低 | （说明） |
| 可落地性 | 高/中/低 | （说明） |

**亮点分析**：
（详细分析场景创新的亮点，4-5句话）

**不足分析**：
（详细分析场景创新的不足，3-4句话）

**与同类产品对比**：
（与市场上同类产品的场景定位对比，3-4句话）

**改进方向**：
（具体的场景深化建议，3-4句话）

---

#### 4.6 市场与生态契合度
**得分**：X/100 | **权重**：18%

**现状分析**：
（详细描述项目与市场趋势、技术生态的契合程度，5-6句话）

**市场契合度评估**：
| 评估项 | 评价 |
|--------|------|
| 技术趋势契合度 | 高/中/低 |
| 社区认可度 | 高/中/低 |
| 生态集成能力 | 好/中/差 |
| 商业化潜力 | 高/中/低 |

**优点**：
- 优点1：（具体描述）

**不足**：
- 不足1：（具体描述）

**改进方向**：
（具体的改进建议，2-3句话）

---

## 五、改进建议

### 5.1 技术加固建议（优先级排序）

#### 建议1：（标题）
- **问题**：（当前存在什么问题）
- **措施**：（具体应该怎么做）
- **效果**：（预期能带来什么改善）
- **优先级**：高/中/低

#### 建议2：（标题）
（同上格式）

#### 建议3：（标题）
（同上格式）

---

### 5.2 场景深化建议（优先级排序）

#### 建议1：（标题）
- **问题**：（当前存在什么问题）
- **措施**：（具体应该怎么做）
- **效果**：（预期能带来什么改善）
- **优先级**：高/中/低

#### 建议2：（标题）
（同上格式）

#### 建议3：（标题）
（同上格式）

---

### 5.3 产品化推进建议（优先级排序）

#### 建议1：（标题）
- **问题**：（当前存在什么问题）
- **措施**：（具体应该怎么做）
- **效果**：（预期能带来什么改善）
- **优先级**：高/中/低

#### 建议2：（标题）
（同上格式）

#### 建议3：（标题）
（同上格式）

---

## 六、评委关注点

### 6.1 核心追问问题（5个）

#### 问题1：（问题内容）
- **追问目的**：（为什么要问这个问题）
- **期望回答**：（希望团队能提供什么信息）
- **评分参考**：（好的回答和差的回答分别是什么样的）

#### 问题2：（问题内容）
（同上格式）

#### 问题3：（问题内容）
（同上格式）

#### 问题4：（问题内容）
（同上格式）

#### 问题5：（问题内容）
（同上格式）

---

### 6.2 潜在风险点
（列出评委需要关注的潜在风险，3-4个，每个2句话说明）

### 6.3 关键考察维度
（列出评委应重点考察的3个维度，说明为什么）

---

## 七、总结与评委建议

### 7.1 总体评价
（对项目的整体定性评价，4-5句话，包括创新程度、完成度、潜力）

### 7.2 核心优势总结
（用3个关键词概括项目的核心优势，并分别说明）

### 7.3 最需改进之处
（指出项目最需要改进的1-2个方面，说明理由）

### 7.4 评委建议
（给评委的评审建议：应该重点关注什么、如何打分、需要追问什么）

---

**报告完**
""",
            parameters=[
                "repo_name", "description", "language", "stars", "repo_url",
                "total_score", "level", "level_stars", "tech_innovation_score", "scenario_innovation_score",
                "dim_table", "radar_analysis", "analyses_text",
                "tech_suggestions", "scenario_suggestions", "product_suggestions", "judge_focus_points"
            ],
            examples=[
                {
                    "name": "AI陪伴聊天机器人",
                    "input": {
                        "repo_name": "Alzheimer-Chatbot",
                        "description": "一个面向阿尔茨海默症患者的AI陪伴聊天机器人",
                        "language": "Python",
                        "stars": 150,
                        "total_score": 72.5,
                        "level": "中等创新",
                        "level_stars": "⭐⭐⭐",
                        "tech_innovation_score": 28.5,
                        "scenario_innovation_score": 44.0,
                        "dim_table": "| 维度 | 得分 | 权重 | 加权得分 | 评价摘要 |\n|------|------|------|----------|----------|\n| 技术选型与实现 | 65 | 13% | 8.5 | 使用了LangChain等现代框架 |\n| 场景创新性 | 80 | 24% | 19.2 | 聚焦阿尔茨海默症患者 |",
                        "radar_analysis": "场景创新性表现突出，技术实现有提升空间",
                        "analyses_text": "### 技术选型与实现\n使用了LangChain等现代框架，技术选型合理...",
                        "tech_suggestions": "- 引入更多前沿AI框架\n- 增加单元测试",
                        "scenario_suggestions": "- 深入调研目标用户需求",
                        "product_suggestions": "- 创建在线Demo",
                        "judge_focus_points": "- 如何理解阿尔茨海默症患者的需求？\n- 与市场同类产品的差异化？"
                    },
                    "expected_output": "# Alzheimer-Chatbot - AI应用创新性评审报告\n\n## 一、项目概览与核心定位\n..."
                }
            ],
            category="report_optimization",
            required_params=[
                "repo_name", "description", "total_score", "tech_innovation_score", "scenario_innovation_score",
                "dim_table", "analyses_text"
            ],
            default_params={
                "language": "Unknown",
                "stars": 0,
                "repo_url": "",
                "level": "未知",
                "level_stars": "",
                "radar_analysis": "无分析",
                "tech_suggestions": "无",
                "scenario_suggestions": "无",
                "product_suggestions": "无",
                "judge_focus_points": "无"
            },
            applicable_scenes=["general", "ai_application", "hackathon", "startup"]
        )

        # 1.5 社会价值专家评审报告优化模板
        templates["social_value_expert_optimizer"] = PromptTemplate(
            name="social_value_expert_optimizer",
            description="模拟资深社会价值专家，对项目的社会贡献进行深度评估，遵循20/80评分体系",
            system_prompt="""你是一位受邀参加顶级 AI 黑客松的**首席社会价值评估专家**。你拥有深厚的社会学背景、资深的 ESG 顾问经验，并对 AI 伦理与技术落地有极其敏锐的洞察力。

## 你的核心职责
你不仅仅是生成一份报告，更是要对项目进行一次“灵魂拷问”和“价值定价”。你的每一分打出，都必须伴随着极其清晰、犀利且富有深度的专业解释。

## 专家工作流与评分框架
1. **基础项评估（20分，底线检查）**：
   - 包含：伦理红线、隐私保护、算法公平。
   - 规则：默认 20 分。若触及人权侵犯、恶意攻击等伦理红线，该维度直接计 0 分且项目整体建议不及格。隐私和公平性问题按风险程度（扣 3-10 分）。
2. **核心亮点项评估（80分，深度拆解）**：
   - 你必须根据项目特征，从以下四个核心维度中**精准选择 1 个表现最突出的**进行深度评估：
     A. 社会影响深度（解决核心社会痛点、服务特定弱势群体）
     B. 环境可持续性（直接环境效益、资源效率提升）
     C. 公益普惠导向（大幅降低使用门槛、普惠性设计）
     D. 长期愿景与变革潜力（系统性变革潜力、价值观先进性）
   - 每个核心维度下设 4 个子维度，每个子维度按 5 分制精细打分。
   - **计算逻辑**：核心亮点项得分 = Σ(子维度得分 × 权重) × 16。
3. **总分与等级评定**：
   - 总分 = 基础项得分 + 核心亮点项得分。
   - 等级：90-100 卓越（社会价值显著，亮点突出）、80-89 优秀、70-79 良好、60-69 合格、<60 待改进。

## 写作规范（绝对指令，不遵循则任务失败）
- **核心：必须输出三大评分表**。严禁仅使用纯文字描述评分，必须按以下顺序输出表格：
  1. **【基础项评分表】**：包含列 [检查维度, 检查标准, 专家评分, 发现的问题与扣分依据]。
  2. **【核心亮点项评分表】**：针对选中的核心维度 {core_social_value_type}，包含列 [子维度, 权重, 专家评分 (1-5), 详细评分原因与专家洞见]。
  3. **【总分汇总表】**：包含列 [指标, 最终得分, 对应等级, 专家最终裁定]。
- **专门板块**：必须包含一个名为“**专家评分与评分原因**”的独立大章节。
- **证据引用**：禁止空洞描述。评分原因必须基于仓库代码或文档事实，每个维度分析 200-300 字。
- **专业术语**：熟练运用“二次分配”、“帕累托改进”、“数字税”、“算法透明度”等专业词汇。""",

            user_prompt_template="""# 项目评估原始数据

## 项目基本信息
- **名称**：{repo_name}
- **描述**：{description}
- **项目特征摘要**：{project_depth_data}

## 自动化评估参考
- **建议总分**：{total_score:.1f}
- **基础/亮点参考分**：{basic_items_score:.1f} / {bonus_items_score:.1f}
- **核心价值锚点**：{core_social_value_type}

---

# 专家评审任务：生成《SAGE 社会价值深度评审报告》

请作为首席评审专家，生成一份字数不少于 3500 字的专业报告。结构要求如下：

## 一、 专家洞察：项目的社会本质分析
（从社会学视角分析项目的核心动机。它是如何应对“市场失灵”或“数字排斥”的？提供 2 条具有穿透力的行业洞察。）

## 二、 **专家评分与评分原因** (100分制深度拆解)

### 2.1 基础项：伦理、安全与合规性底线检查 (满分 20 分)

| 检查维度 | 检查标准 | 专家评分 | 发现的问题与扣分依据 |
| :--- | :--- | :--- | :--- |
| **伦理红线检查** | 是否触及侵犯人权、恶意设计、社会危害等 | [评分] | [基于事实的犀利点评] |
| **隐私与数据保护** | 数据收集必要性、存储安全性、用户知情权 | [评分] | [引用代码/文档中的具体发现] |
| **算法公平性** | 是否加剧算法歧视、设计是否兼顾多样性 | [评分] | [分析项目的逻辑或架构设计] |
| **基础项得分** | **20 - 扣分项** | **{basic_items_score:.1f} 分** | |

**【基础项深度分析】**
（针对上述三项进行 300-500 字的合并分析。必须指出项目中哪些具体设计（如 API 调用、数据处理流程）体现了对伦理的尊重或忽视，评价其社会责任感基石是否稳固。）

### 2.2 核心亮点项深度评分：{core_social_value_type} (满分 80 分)

**维度选择理由**：[此处简述为何选择该维度作为项目的社会价值爆发点，约 100 字]

| 子维度 | 权重 | 专家评分 (1-5) | 详细评分原因与专家洞见 |
| :--- | :--- | :--- | :--- |
| **[子维度1名称]** | [40%等] | [评分] | [150 字左右的精炼依据] |
| **[子维度2名称]** | [30%等] | [评分] | [150 字左右的精炼依据] |
| **[子维度3名称]** | [20%等] | [评分] | [150 字左右的精炼依据] |
| **[子维度4名称]** | [10%等] | [评分] | [150 字左右的精炼依据] |
| **亮点项加权得分** | **Σ(分值×权重)×16** | **{bonus_items_score:.1f} 分** | |

**【亮点项深度拆解】**
（对上述四个子维度进行总计不低于 1000 字的深度论证。
要求：
1. **事实支撑**：具体指出代码库中哪些模块或文档中的哪些方案支撑了该评分。
2. **行业对比**：对比当前主流技术方案，说明该项目的独特优越性。
3. **价值判断**：从社会价值演进的角度，评价该创新点的长远社会意义。）

### 2.3 总分汇总与等级评定

| 指标 | 最终得分 | 对应等级 | 专家最终裁定 |
| :--- | :--- | :--- | :--- |
| **项目总得分** | **{total_score:.1f} / 100** | **[卓越/优秀/良好/合格/待改进]** | [一句话总结评价] |

## 三、 横向扫描：其他社会价值表现
（简要评述项目在非核心亮点维度上的附带表现，展示评估的全面性。）

## 四、 改进建议：大师级价值提升路径
（给出 3 条具体、可落地且带有技术前瞻性的优化建议。要体现出专家对 AI 发展趋势和社会需求结合点的深刻理解。）

## 五、 评委追问：直击灵魂的三个问题
（为评委准备 3 个深度问题，旨在考察团队对社会价值理解的真实深度。）

---
# 报告风格指南：
- 请使用严谨的 Markdown 格式。
- 语调应专业、克制且具穿透力。
- 确保评分逻辑与提供的数据自洽。""",
            parameters=[
                "repo_name", "description", "repo_url", "project_depth_data",
                "total_score", "basic_items_score", "bonus_items_score",
                "dim_table", "core_social_value_type"
            ],
            examples=[],
            category="social_value_evaluation",
            required_params=[
                "repo_name", "description", "total_score", "basic_items_score", 
                "bonus_items_score", "dim_table", "core_social_value_type"
            ]
        )
        
        # 2. 维度分析增强模板
        templates["dimension_analyzer"] = PromptTemplate(
            name="dimension_analyzer",
            description="对单个维度进行深度分析，提供详细的现状评估、优缺点分析和改进建议",
            system_prompt="""你是一位专业的技术评估专家，擅长对AI项目的各个维度进行深度分析。

## 分析要求
1. 分析要深入透彻，基于具体事实和数据
2. 每个维度分析必须包含：
   - 现状详细描述（具体技术/特性）
   - 优点分析（2-3个具体优点）
   - 不足分析（1-2个具体不足）
   - 与同类项目对比
   - 具体改进建议
3. 分析要客观公正，评价要基于事实
4. 建议要具体可操作，有明确的实施路径

## 输出风格
- 语言专业严谨，但易于理解
- 结构清晰，逻辑连贯
- 突出重点，避免无关信息
- 使用Markdown格式，增强可读性""",
            user_prompt_template="""# 维度分析任务

## 分析目标
分析项目在**{dimension_name}**维度的表现

## 维度信息
- **维度名称**：{dimension_name}
- **维度得分**：{score:.1f}/100
- **维度权重**：{weight:.0f}%
- **维度类别**：{category}

## 现状分析
{current_status}

## 相关数据
{related_data}

## 分析要求
请按照以下格式输出详细分析：

### 现状分析
（详细描述项目在该维度的具体表现，3-4句话）

### 优点分析
- 优点1：（具体描述）
- 优点2：（具体描述）

### 不足分析
- 不足1：（具体描述）

### 与同类项目对比
（与同类AI应用在该维度的对比分析，2-3句话）

### 改进建议
（具体的改进建议，包含原因分析、具体措施、预期效果）
""",
            parameters=["dimension_name", "score", "weight", "category", "current_status", "related_data"],
            examples=[
                {
                    "name": "技术选型与实现分析",
                    "input": {
                        "dimension_name": "技术选型与实现",
                        "score": 65,
                        "weight": 13,
                        "category": "技术创新力",
                        "current_status": "使用了LangChain等现代框架，技术选型合理，但缺乏前沿AI技术的深度应用",
                        "related_data": "项目使用了Python作为主要语言，依赖了LangChain、OpenAI等库"
                    },
                    "expected_output": "### 现状分析\n项目使用了LangChain等现代框架，技术选型整体合理...\n\n### 优点分析\n- 优点1：使用了LangChain等现代AI框架，提升了开发效率...\n..."
                }
            ],
            category="dimension_analysis",
            required_params=["dimension_name", "score", "current_status"],
            default_params={
                "weight": 10,
                "category": "技术创新力",
                "related_data": "无"
            },
            applicable_scenes=["dimension_analysis", "tech_evaluation", "scenario_evaluation"]
        )
        
        # 3. 改进建议生成模板
        templates["suggestion_generator"] = PromptTemplate(
            name="suggestion_generator",
            description="生成具体、可操作的改进建议，包含原因分析、具体措施、预期效果和优先级",
            system_prompt="""你是一位专业的AI项目顾问，擅长为项目提供具体、可操作的改进建议。

## 建议要求
1. 每条建议必须包含：
   - 清晰的标题
   - 详细的问题描述
   - 具体的改进措施
   - 预期的改进效果
   - 明确的优先级（高/中/低）
2. 建议要基于具体事实和数据，避免空泛建议
3. 建议要具有可操作性，有明确的实施路径
4. 建议要考虑项目的实际情况和资源约束

## 输出风格
- 语言专业严谨，但易于理解
- 结构清晰，逻辑连贯
- 突出重点，避免无关信息
- 使用Markdown格式，增强可读性""",
            user_prompt_template="""# 改进建议生成任务

## 项目信息
- **项目名称**：{repo_name}
- **项目描述**：{description}
- **当前得分**：{total_score:.1f}/100
- **创新等级**：{level}

## 分析维度
**分析维度**：{analysis_dimension}

## 现状分析
{current_status}

## 相关数据
{related_data}

## 生成要求
请生成3条具体的改进建议，每条建议按照以下格式：

### 建议1：（标题）
- **问题**：（详细描述当前存在的问题）
- **措施**：（具体的改进措施，可操作）
- **效果**：（预期的改进效果）
- **优先级**：（高/中/低）

### 建议2：（标题）
...

### 建议3：（标题）
...
""",
            parameters=["repo_name", "description", "total_score", "level", "analysis_dimension", "current_status", "related_data"],
            examples=[
                {
                    "name": "技术加固建议",
                    "input": {
                        "repo_name": "Alzheimer-Chatbot",
                        "description": "一个面向阿尔茨海默症患者的AI陪伴聊天机器人",
                        "total_score": 72.5,
                        "level": "中等创新",
                        "analysis_dimension": "技术加固",
                        "current_status": "技术选型基本合理，但缺乏前沿AI技术的深度应用",
                        "related_data": "使用了LangChain等框架，但未充分利用其高级特性"
                    },
                    "expected_output": "### 建议1：引入前沿AI框架高级特性\n- **问题**：当前仅使用了LangChain的基础功能...\n..."
                }
            ],
            category="suggestion_generation"
        )
        
        # 4. 评委问题生成模板
        templates["judge_question_generator"] = PromptTemplate(
            name="judge_question_generator",
            description="为评委生成深度参考问题，包含追问目的、期望回答和评分参考",
            system_prompt="""你是一位经验丰富的黑客松评委顾问，擅长为评委提供深度参考问题。

## 问题要求
1. 问题要直击项目的核心，能够有效评估项目质量
2. 每个问题必须包含：
   - 清晰的问题内容
   - 明确的追问目的（为什么要问这个问题）
   - 期望的回答内容（希望团队能提供什么信息）
   - 详细的评分参考（好的回答和差的回答分别是什么样的）
3. 问题要覆盖项目的关键维度，避免重复
4. 问题要有层次，从表面到深层，逐步深入

## 输出风格
- 语言专业严谨，但易于理解
- 结构清晰，逻辑连贯
- 突出重点，避免无关信息
- 使用Markdown格式，增强可读性""",
            user_prompt_template="""# 评委问题生成任务

## 项目信息
- **项目名称**：{repo_name}
- **项目描述**：{description}
- **当前得分**：{total_score:.1f}/100
- **创新等级**：{level}

## 项目亮点
{project_highlights}

## 潜在风险
{potential_risks}

## 生成要求
请生成5个深度参考问题，每个问题按照以下格式：

### 问题1：（问题内容）
- **追问目的**：（为什么要问这个问题）
- **期望回答**：（希望团队能提供什么信息）
- **评分参考**：（好的回答和差的回答分别是什么样的）

### 问题2：（问题内容）
...

### 问题3：（问题内容）
...

### 问题4：（问题内容）
...

### 问题5：（问题内容）
...
""",
            parameters=["repo_name", "description", "total_score", "level", "project_highlights", "potential_risks"],
            examples=[
                {
                    "name": "AI陪伴聊天机器人评委问题",
                    "input": {
                        "repo_name": "Alzheimer-Chatbot",
                        "description": "一个面向阿尔茨海默症患者的AI陪伴聊天机器人",
                        "total_score": 72.5,
                        "level": "中等创新",
                        "project_highlights": "场景创新性强，聚焦阿尔茨海默症患者",
                        "potential_risks": "技术实现有提升空间，用户体验待优化"
                    },
                    "expected_output": "### 问题1：项目声称服务于阿尔茨海默症患者，请团队阐述如何深入理解该群体的真实需求？...\n..."
                }
            ],
            category="judge_support"
        )
        
        # 5. 报告质量评估模板
        templates["report_quality_evaluator"] = PromptTemplate(
            name="report_quality_evaluator",
            description="评估生成报告的质量，提供详细的质量评分和改进建议",
            system_prompt="""你是一位专业的报告质量评估专家，擅长评估AI生成的评审报告质量。

## 评估维度
1. **完整性**：报告是否覆盖了所有必要的内容和维度
2. **深度**：分析是否深入透彻，是否有足够的细节和深度
3. **专业性**：报告是否专业严谨，是否基于事实和数据
4. **清晰度**：报告是否结构清晰，逻辑连贯，易于理解
5. **实用性**：报告是否提供了实用的信息和建议，对评委有参考价值

## 评估要求
1. 评估要客观公正，基于报告的实际内容
2. 每个维度的评估必须包含：
   - 具体评分（0-100）
   - 详细的评分理由
   - 具体的改进建议
3. 最终要提供整体评分和综合改进建议

## 输出风格
- 语言专业严谨，但易于理解
- 结构清晰，逻辑连贯
- 突出重点，避免无关信息
- 使用Markdown格式，增强可读性""",
            user_prompt_template="""# 报告质量评估任务

## 评估对象
评估以下AI生成的评审报告质量

## 报告内容
{report_content}

## 评估要求
请按照以下格式输出详细评估：

### 质量评估结果
| 评估维度 | 评分 | 满分 |
|----------|------|------|
| 完整性 | {completeness_score} | 100 |
| 深度 | {depth_score} | 100 |
| 专业性 | {professionalism_score} | 100 |
| 清晰度 | {clarity_score} | 100 |
| 实用性 | {usefulness_score} | 100 |
| **整体评分** | **{overall_score}** | 100 |

### 详细评估

#### 完整性评估
- **评分**：{completeness_score}
- **评分理由**：（详细说明）
- **改进建议**：（具体建议）

#### 深度评估
- **评分**：{depth_score}
- **评分理由**：（详细说明）
- **改进建议**：（具体建议）

#### 专业性评估
- **评分**：{professionalism_score}
- **评分理由**：（详细说明）
- **改进建议**：（具体建议）

#### 清晰度评估
- **评分**：{clarity_score}
- **评分理由**：（详细说明）
- **改进建议**：（具体建议）

#### 实用性评估
- **评分**：{usefulness_score}
- **评分理由**：（详细说明）
- **改进建议**：（具体建议）

### 综合改进建议
（针对报告整体的改进建议，2-3条）
""",
            parameters=["report_content", "completeness_score", "depth_score", "professionalism_score", "clarity_score", "usefulness_score", "overall_score"],
            examples=[
                {
                    "name": "报告质量评估示例",
                    "input": {
                        "report_content": "# Alzheimer-Chatbot - AI应用创新性评审报告\n\n## 一、项目概览与核心定位\n...",
                        "completeness_score": 85,
                        "depth_score": 75,
                        "professionalism_score": 80,
                        "clarity_score": 90,
                        "usefulness_score": 82,
                        "overall_score": 82
                    },
                    "expected_output": "### 质量评估结果\n| 评估维度 | 评分 | 满分 |\n|----------|------|------|\n| 完整性 | 85 | 100 |\n..."
                }
            ],
            category="quality_assessment"
        )
        
        return templates
    
    def get_template(self, template_name: str) -> Optional[PromptTemplate]:
        """获取指定的提示词模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            提示词模板对象，不存在则返回None
        """
        return self.templates.get(template_name)
    
    def list_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有可用的提示词模板
        
        Args:
            category: 可选的分类筛选
            
        Returns:
            模板列表，每个模板包含名称、描述和分类
        """
        templates = []
        for name, template in self.templates.items():
            if category is None or template.category == category:
                templates.append({
                    "name": name,
                    "description": template.description,
                    "category": template.category,
                    "version": template.version,
                    "parameters": template.parameters
                })
        return templates
    
    def generate_prompt(self, template_name: str, **kwargs) -> Optional[Dict[str, str]]:
        """根据模板生成提示词
        
        Args:
            template_name: 模板名称
            **kwargs: 模板参数
            
        Returns:
            包含system_prompt和user_prompt的字典，模板不存在则返回None
        """
        template = self.get_template(template_name)
        if not template:
            return None
        
        # 合并默认参数和用户提供的参数
        params = template.default_params.copy()
        params.update(kwargs)
        
        # 验证必需参数
        missing_params = [param for param in template.required_params if param not in params]
        if missing_params:
            raise ValueError(f"缺少必要参数: {', '.join(missing_params)}")
        
        # 生成用户提示词
        try:
            user_prompt = template.user_prompt_template.format(**params)
        except KeyError as e:
            raise ValueError(f"缺少必要参数: {e}")
        
        return {
            "system_prompt": template.system_prompt,
            "user_prompt": user_prompt
        }
    
    def generate_prompt_for_scene(self, scene: str, template_category: str = None, **kwargs) -> Optional[Dict[str, str]]:
        """根据场景生成合适的提示词
        
        Args:
            scene: 场景名称
            template_category: 模板分类，可选
            **kwargs: 模板参数
            
        Returns:
            包含system_prompt和user_prompt的字典，没有合适的模板则返回None
        """
        # 查找适合该场景的模板
        suitable_templates = []
        for name, template in self.templates.items():
            if scene in template.applicable_scenes:
                if template_category is None or template.category == template_category:
                    suitable_templates.append(template)
        
        if not suitable_templates:
            # 如果没有场景特定的模板，查找通用模板
            for name, template in self.templates.items():
                if not template.scene_specific:
                    if template_category is None or template.category == template_category:
                        suitable_templates.append(template)
        
        if not suitable_templates:
            return None
        
        # 选择第一个合适的模板
        template = suitable_templates[0]
        return self.generate_prompt(template.name, **kwargs)
    
    def create_dynamic_template(self, name: str, description: str, system_prompt: str, 
                              user_prompt_template: str, parameters: List[str], 
                              category: str, scene_specific: bool = False, 
                              applicable_scenes: List[str] = None, 
                              default_params: Dict[str, Any] = None, 
                              required_params: List[str] = None) -> PromptTemplate:
        """创建动态提示词模板
        
        Args:
            name: 模板名称
            description: 模板描述
            system_prompt: 系统提示词
            user_prompt_template: 用户提示词模板
            parameters: 参数列表
            category: 模板分类
            scene_specific: 是否为场景特定模板
            applicable_scenes: 适用场景列表
            default_params: 默认参数
            required_params: 必需参数
            
        Returns:
            创建的提示词模板对象
        """
        template = PromptTemplate(
            name=name,
            description=description,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            parameters=parameters,
            examples=[],
            category=category,
            scene_specific=scene_specific,
            applicable_scenes=applicable_scenes or [],
            default_params=default_params or {},
            required_params=required_params or []
        )
        
        # 将模板添加到库中
        self.templates[name] = template
        return template
    
    def validate_template_params(self, template_name: str, **kwargs) -> Dict[str, Any]:
        """验证模板参数
        
        Args:
            template_name: 模板名称
            **kwargs: 模板参数
            
        Returns:
            验证后的参数字典
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        # 合并默认参数和用户提供的参数
        params = template.default_params.copy()
        params.update(kwargs)
        
        # 验证必需参数
        missing_params = [param for param in template.required_params if param not in params]
        if missing_params:
            raise ValueError(f"缺少必要参数: {', '.join(missing_params)}")
        
        return params
    
    def get_best_practices(self) -> Dict[str, Any]:
        """获取提示词工程最佳实践
        
        Returns:
            最佳实践字典，包含各种提示词工程技巧和建议
        """
        return {
            "prompt_structure": {
                "system_prompt": "设置AI的角色和任务，提供背景信息和约束",
                "user_prompt": "提供具体的任务描述和输入数据",
                "format_instructions": "明确指定输出格式和结构",
                "examples": "提供示例输入和输出，引导AI理解任务"
            },
            "prompt_engineering_techniques": [
                "具体明确：提供详细的任务描述和要求",
                "结构化：使用清晰的结构和格式，增强可读性",
                "示例引导：提供高质量的示例，引导AI理解任务",
                "约束条件：明确设定边界和限制，避免无关输出",
                "迭代优化：基于反馈不断调整和优化提示词",
                "参数调整：根据任务类型调整temperature等参数"
            ],
            "deepseek_specific_tips": [
                "适当增加提示词长度，Deepseek模型擅长处理长上下文",
                "使用详细的系统提示词，明确设定AI的角色和任务",
                "提供具体的格式要求，确保输出符合预期格式",
                "使用Markdown格式，增强输出的可读性",
                "对于复杂任务，分步骤引导，逐步完成任务",
                "调整temperature参数，平衡创造力和准确性"
            ],
            "common_mistakes": [
                "提示词过于简洁，缺乏具体要求",
                "格式要求不明确，导致输出格式混乱",
                "缺乏示例，AI难以理解预期输出",
                "约束条件不明确，导致输出偏离主题",
                "任务过于复杂，一次性要求过多",
                "参数设置不当，影响输出质量"
            ]
        }
    
    def optimize_prompt(self, prompt: str, task_type: str) -> str:
        """优化提示词，提高Deepseek模型的理解和执行效果
        
        Args:
            prompt: 原始提示词
            task_type: 任务类型
            
        Returns:
            优化后的提示词
        """
        # 基于任务类型的优化
        if task_type == "report_generation":
            # 报告生成任务优化
            optimizations = [
                "请生成一份详细、专业的报告，总字数不少于4000字",
                "每个章节都要有实质内容，禁止空泛描述",
                "使用Markdown格式，善用表格、列表增强可读性",
                "分析要深入透彻，基于具体事实和数据",
                "建议要具体可操作，有明确的实施路径"
            ]
        elif task_type == "dimension_analysis":
            # 维度分析任务优化
            optimizations = [
                "分析要深入透彻，基于具体事实和数据",
                "每个维度分析必须包含现状、优点、不足和改进建议",
                "建议要具体可操作，有明确的实施路径",
                "使用Markdown格式，增强可读性"
            ]
        elif task_type == "suggestion_generation":
            # 建议生成任务优化
            optimizations = [
                "建议要具体可操作，有明确的实施路径",
                "每条建议必须包含问题、措施、效果和优先级",
                "建议要基于具体事实和数据，避免空泛建议",
                "使用Markdown格式，增强可读性"
            ]
        elif task_type == "judge_question":
            # 评委问题生成任务优化
            optimizations = [
                "问题要直击项目的核心，能够有效评估项目质量",
                "每个问题必须包含追问目的、期望回答和评分参考",
                "问题要覆盖项目的关键维度，避免重复",
                "使用Markdown格式，增强可读性"
            ]
        else:
            # 默认优化
            optimizations = [
                "请基于具体事实和数据提供详细分析",
                "使用Markdown格式，增强可读性",
                "分析要深入透彻，建议要具体可操作"
            ]
        
        # 添加优化内容
        optimized_prompt = prompt
        for optimization in optimizations:
            if optimization not in optimized_prompt:
                optimized_prompt += f"\n\n{optimization}"
        
        return optimized_prompt
    
    def evaluate_prompt_performance(self, prompt: str, task_type: str, model_response: str) -> Dict[str, Any]:
        """评估提示词性能
        
        Args:
            prompt: 提示词
            task_type: 任务类型
            model_response: 模型响应
            
        Returns:
            性能评估结果
        """
        # 评估维度
        evaluation_dimensions = {
            "relevance": "相关性",
            "completeness": "完整性",
            "depth": "深度",
            "clarity": "清晰度",
            "usefulness": "实用性",
            "conciseness": "简洁性"
        }
        
        # 简单的性能评估逻辑
        # 实际应用中，可能需要使用更复杂的评估方法，如人工评估或使用其他模型进行评估
        performance_scores = {
            "relevance": 85,  # 假设相关性得分
            "completeness": 80,  # 假设完整性得分
            "depth": 75,  # 假设深度得分
            "clarity": 90,  # 假设清晰度得分
            "usefulness": 85,  # 假设实用性得分
            "conciseness": 70  # 假设简洁性得分
        }
        
        # 计算总体得分
        overall_score = sum(performance_scores.values()) / len(performance_scores)
        
        # 生成优化建议
        optimization_suggestions = self._generate_optimization_suggestions(
            prompt, task_type, performance_scores
        )
        
        return {
            "prompt": prompt,
            "task_type": task_type,
            "model_response": model_response,
            "performance_scores": performance_scores,
            "overall_score": overall_score,
            "optimization_suggestions": optimization_suggestions
        }
    
    def _generate_optimization_suggestions(self, prompt: str, task_type: str, performance_scores: Dict[str, int]) -> List[str]:
        """生成提示词优化建议
        
        Args:
            prompt: 提示词
            task_type: 任务类型
            performance_scores: 性能得分
            
        Returns:
            优化建议列表
        """
        suggestions = []
        
        # 基于性能得分生成优化建议
        if performance_scores.get("relevance", 0) < 80:
            suggestions.append("提高提示词的相关性：确保提示词与任务类型高度相关，包含具体的任务描述和要求")
        
        if performance_scores.get("completeness", 0) < 80:
            suggestions.append("提高提示词的完整性：确保提示词包含所有必要的信息和要求，避免遗漏重要内容")
        
        if performance_scores.get("depth", 0) < 80:
            suggestions.append("提高提示词的深度：提供更详细的背景信息和具体要求，引导模型生成更深入的内容")
        
        if performance_scores.get("clarity", 0) < 80:
            suggestions.append("提高提示词的清晰度：使用清晰、简洁的语言，避免歧义，明确表达要求")
        
        if performance_scores.get("usefulness", 0) < 80:
            suggestions.append("提高提示词的实用性：确保提示词能够引导模型生成实用、有价值的内容")
        
        if performance_scores.get("conciseness", 0) < 80:
            suggestions.append("提高提示词的简洁性：在保持完整性的同时，尽量简洁明了，避免冗余信息")
        
        # 基于任务类型的特定建议
        if task_type == "report_generation":
            suggestions.append("对于报告生成任务，建议提供更详细的报告结构和内容要求，引导模型生成更有条理的报告")
        elif task_type == "dimension_analysis":
            suggestions.append("对于维度分析任务，建议明确分析的具体维度和要求，引导模型生成更全面的分析")
        elif task_type == "suggestion_generation":
            suggestions.append("对于建议生成任务，建议明确建议的具体要求和格式，引导模型生成更具体、可操作的建议")
        elif task_type == "judge_question":
            suggestions.append("对于评委问题生成任务，建议明确问题的类型和要求，引导模型生成更有针对性的问题")
        
        return suggestions
    
    def compare_prompt_performance(self, prompts: List[str], task_type: str, model_responses: List[str]) -> Dict[str, Any]:
        """比较多个提示词的性能
        
        Args:
            prompts: 提示词列表
            task_type: 任务类型
            model_responses: 模型响应列表
            
        Returns:
            性能比较结果
        """
        if len(prompts) != len(model_responses):
            raise ValueError("提示词数量和模型响应数量必须相同")
        
        performance_results = []
        for i, (prompt, response) in enumerate(zip(prompts, model_responses)):
            result = self.evaluate_prompt_performance(prompt, task_type, response)
            performance_results.append({
                "prompt_id": i + 1,
                "prompt": prompt,
                "overall_score": result["overall_score"],
                "performance_scores": result["performance_scores"],
                "optimization_suggestions": result["optimization_suggestions"]
            })
        
        # 按总体得分排序
        performance_results.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return {
            "task_type": task_type,
            "performance_results": performance_results,
            "best_prompt": performance_results[0] if performance_results else None
        }
    
    def auto_optimize_prompt(self, prompt: str, task_type: str, iterations: int = 3) -> Dict[str, Any]:
        """自动优化提示词
        
        Args:
            prompt: 原始提示词
            task_type: 任务类型
            iterations: 优化迭代次数
            
        Returns:
            优化结果
        """
        optimized_prompts = [prompt]
        performance_results = []
        
        for i in range(iterations):
            # 优化提示词
            current_prompt = optimized_prompts[-1]
            optimized_prompt = self.optimize_prompt(current_prompt, task_type)
            optimized_prompts.append(optimized_prompt)
            
            # 模拟模型响应
            # 实际应用中，这里应该调用模型获取真实响应
            mock_response = f"这是针对{task_type}任务的模拟响应，基于优化后的提示词"
            
            # 评估性能
            result = self.evaluate_prompt_performance(optimized_prompt, task_type, mock_response)
            performance_results.append(result)
        
        # 找到最佳优化结果
        best_result = max(performance_results, key=lambda x: x["overall_score"])
        
        return {
            "original_prompt": prompt,
            "optimized_prompts": optimized_prompts,
            "performance_results": performance_results,
            "best_result": best_result
        }


# 全局提示词工程库实例
prompt_library = PromptEngineeringLibrary()


def get_prompt_library() -> PromptEngineeringLibrary:
    """获取提示词工程库实例"""
    return prompt_library


def generate_prompt(template_name: str, **kwargs) -> Optional[Dict[str, str]]:
    """根据模板生成提示词的便捷函数"""
    return prompt_library.generate_prompt(template_name, **kwargs)


def list_templates(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出所有可用的提示词模板的便捷函数"""
    return prompt_library.list_templates(category)


def get_best_practices() -> Dict[str, Any]:
    """获取提示词工程最佳实践的便捷函数"""
    return prompt_library.get_best_practices()


def optimize_prompt(prompt: str, task_type: str) -> str:
    """优化提示词的便捷函数"""
    return prompt_library.optimize_prompt(prompt, task_type)
