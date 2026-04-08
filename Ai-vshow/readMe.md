## 📂 项目结构

本项目采用模块化设计，结构清晰，易于维护和扩展。


AI-vshow/
│
├── .env # 环境变量配置文件 (Appium, OpenAI等)
├── requirements.txt # Python依赖库列表
├── main.py # 测试执行器主入口 (集成Allure)
│
├── test_cases/ # 📁 测试用例目录
│ ├── init.py
│ ├── loader.py # 测试用例加载器
│ └── *.json # 具体的测试用例文件 (如: live_stream_test.json)
│
├── src/ # 📁 核心源代码
│ ├── init.py
│ │
│ ├── config/ # 📁 配置管理
│ │ └── settings.py # Pydantic设置模型，统一管理所有配置
│ │
│ ├── drivers/ # 📁 设备驱动层
│ │ ├── appium_driver.py # Appium会话管理
│ │ └── element_handler.py # UI元素提取与弹窗处理
│ │
│ ├── actions/ # 📁 基础操作层
│ │ └── mobile_actions.py # 封装点击、滑动、输入等原子操作
│ │
│ ├── utils/ # 📁 工具库
│ │ └── image_processor.py # 图片处理工具 (如: Base64编码)
│ │
│ └── agents/ # 📁 AI智能体核心
│ ├── init.py
│ ├── state.py # 定义LangGraph状态和测试用例数据结构
│ ├── workflow.py # 定义LangGraph工作流 (StateGraph)
│ │
│ └── nodes/ # 📁 工作流节点
│ ├── screenshot_node.py # 截图与UI元素提取节点
│ ├── planner_node.py # LLM规划节点
│ └── executor_node.py # 动作执行节点
│
└── allure-results/ # 📁 (运行后自动生成) Allure测试结果数据