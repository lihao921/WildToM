# ToM QA 验证器 - 标注任务说明

> ⚠️ **警告声明**
> 
> 本仓库为私人项目，包含专有数据和代码：
> - 未经授权，严禁传播、分享或散布本仓库的任何内容
> - 严禁对外泄露任何项目相关信息
> - 仅供项目成员内部使用

## 一、项目背景与任务目标

- 构建高质量"心理理论（Theory of Mind, ToM）"多模态问答数据集，推动人工智能理解和推理人类心理状态的能力。标注数据将用于评测多模态大模型，助力AI在社会认知、情感理解等领域的进步。
- **本标注任务**：通过人工验证和反馈，确保每个视频场景下的ToM问题及其答案、证据等信息准确、充分。

## 二、问题类型与一阶/二阶定义及举例

- **意图/欲望/情感/知识/信念问题**：需结合视频、对白、场景描述等多模态证据进行判断。
- **一阶（First-order ToM）**：直接推测某角色的心理状态。
- **二阶（Second-order ToM）**：推测某角色对他人心理状态的看法（"我认为你认为……"）。

### 各类型一阶/二阶QA例子

- **意图（Intention）**  
  - 一阶：Alex在争吵后打算做什么？  
  - 二阶：Brian认为Alex保持沉默想要达到什么目的？

- **欲望（Desire）**  
  - 一阶：Brian在这次对话中想从Alex那里得到什么？  
  - 二阶：Alex认为Brian想让他承认什么？

- **情感（Emotion）**  
  - 一阶：当Brian指责他时，Alex感受如何？  
  - 二阶：Brian认为Alex对他的指责有什么感受？

- **知识（Knowledge）**  
  - 一阶：Brian对Alex在家庭中的角色了解多少？  
  - 二阶：Alex认为Brian了解他的什么感受？

- **信念（Belief）**  
  - 一阶：Alex对Brian离开的原因有什么看法？  
  - 二阶：Brian认为Alex对他（Brian）的动机有什么看法？

## 三、标注原则与操作细则

1. **ToM推理判断**：只有涉及心理状态推理的问答才属于ToM范畴，常规互动可直接"删除"。
2. **合理性判断**：
   - 问题和答案都合理且准确：**保留**。
   - 问题合理但答案不准确/不充分/有歧义：**保留**，并在feedback中说明问题或建议。
   - 问题本身不合理或不属于ToM范畴：**删除**。
3. **反馈填写**：如有不确定、模糊、建议改进的地方，请在feedback中简要说明。
4. **标注流程**：
   - 阅读场景描述和对话，理解情境。
   - 逐条阅读问题和答案，判断是否为ToM推理问题。
   - 判断合理性与准确性，选择"保留"或"删除"。
   - 如有需要，填写反馈说明。
   - 保存并进入下一个问题/场景。

## 四、环境部署与运行

### 1. 前置要求
- Python 3.8 或更高版本
- Conda 包管理器 ([Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 [Anaconda](https://www.anaconda.com/download))
- Git （可选）

### 2. 克隆项目 （如果获得项目文件夹，跳过此步骤）
```bash
# 克隆代码仓库
git clone <你的仓库地址>
cd tom_qa_verifier
```

### 3. 环境配置
```bash
# 创建并激活conda环境
conda create -n tomqa python=3.8
conda activate tomqa

# 安装依赖包
pip install -r requirements.txt
```

### 4. 目录配置
1. 确保以下目录存在且有读写权限：
```
tom_qa_verifier/
├── videos/           # 存放视频文件
├── feedback/         # 存放标注反馈
├── config/          # 配置文件目录
└── static/          # 静态资源目录
```

2. 如目录不存在，手动创建：
```bash
mkdir -p videos feedback config static
```

### 5. 启动应用
```bash
# 进入源码目录
cd src

# 启动Streamlit应用
streamlit run app.py
```

### 6. 首次使用配置
1. 应用启动后，在浏览器中打开显示的地址（默认为 http://localhost:8501）

2. 解压数据文件
   - 在`data/`目录下找到以下压缩包：
     * `filtering_results_with_speaker_mapping.zip`
     * `gpt_captions_nano.zip`
   - 将它们解压到原目录下

3. 配置路径（在侧边栏中设置）
   - **视频目录路径**：
     * 填入`videos/`目录的路径
   
   - **QA数据路径**：
     * 填入解压后的`feedback_i`文件夹路径  (请联系作者获取)
     * 其中`i`为分配给你的编号
     * 示例：`J:\Code\paper3\data\tom_qa_verifier\data\filtering_results\feedback_1`
   
   - **Caption文件路径**：
     * 填入解压后的`gpt_captions_nano`文件夹的绝对路径
     * 示例：`J:\Code\paper3\data\tom_qa_verifier\data\gpt_captions_nano`

4. 配置完成后，即可开始标注工作

## 五、目录结构

```
├── src/                # 主程序与功能代码
├── feedback/           # 标注反馈自动保存目录
├── config/             # 配置文件
├── videos/             # 视频文件目录（可选）
├── static/             # 静态资源
├── requirements.txt    # 依赖包
├── README.md           # 本说明文档
```

## 六、联系方式

如有疑问或建议，请联系项目负责人：  
- 邮箱：sc.lihao@whu.edu.cn  

---

> **感谢您的认真标注，您的每一条反馈都对项目至关重要！** 

## 发布说明

- 版本：1.0.0
- 最后更新：[当前日期]
- 支持平台：Windows、macOS、Linux 