# COde BOster

该项目为南方科技大学2024年秋季学期创新实践I“基于大模型的代码优化”课题下的项目，项目主要使用TACO数据集，涵盖数据集导入，代码测试，大模型接口，结果评估等方面。

### 项目背景
当前代码优化工具的局限性
- 基于规则的代码优化工具缺少灵活性和上下文理解
- 通用的优化建议往往无法解决特定问题
- 对建议改进的验证机制不够完善
- 缺乏全面的性能评估框架

### 环境要求

```
langchain==0.3.7
langchain-community==0.3.5
langchain-core==0.3.15
langchain-openai==0.2.6
langchain-text-splitters==0.3.2
openai==1.54.3
qianfan==0.4.11
psycopg2~=2.9.9
datasets~=2.19.1
sqlalchemy~=2.0.34
numpy~=1.26.3
tqdm~=4.65.0
jsonlines~=4.0.0
```

### 项目结构
```plaintext
COBO      
  ├── config/       # 配置文件
  ├── database/     # 数据库建立及导入
  ├── evaluate/     # 数据库评测文件
  ├── models/       # 大模型接口
  ├── services/     # 基于数据集的service
  └── README.md     # 项目说明
```
### 使用说明

本项目支持两种形式的数据集使用，一种是数据库的，一种是基于huggingface数据集的。

基于数据库的使用特点是灵活多变，可以自行定义或组织数据集的内容以及方便调试和查看。

基于数据集的使用可以支持流式加载，不用将原本的数据集下载到本地，并且可以使用dataset的一系列功能，便于大模型的微调和训练

关于数据库的使用首先需要在huggingface上先完整下载所需的
[数据集](https://huggingface.co/datasets/BAAI/TACO/tree/main)，
接着使用`service.script.py`导入你想要的数据集，使用`evaluate.testcase_filter.py`过滤掉不能处理的解以及多余的测试用例，
使用`evaluate.testcase_updater.py`重新更新数据库内容。

数据库使用方面可以用evaluate_multiprocess先在每个问题随机挑选若干个解并测试他们的正确性，接着使用test_valid_solution精确测量他们的运行时间，使用significant_dataset_maker获取并制作进步空间超过0.1s的解集。

huggingface数据集使用方面可直接使用test.py，源代码可支持流式加载，无需指定本地数据集位置。

大模型接口目前可支持openai和qianfan模型，理论上可支持langchain框架的所有模型。

### 未来可能继续进行的工作
1. 时间测量方面，目前在标准IO上的时间测量是不准确的，可能会考虑使用docker进行时间测量
2. 数据集的进一步处理，目前数据集仅支持python，可能会考虑支持其他语言
3. 大模型接口的进一步完善，目前只支持openai和qianfan，可能会考虑支持更多的模型

### 联系方式

欢迎加入群聊：**498218841**

也可发送邮箱咨询：12211205@mail.sustech.edu.cn,联系人：**章恒谦**

