AIvshow_/
│
├── .env                          # 环境变量 (保留)
├── requirements.txt              # 依赖列表
│
├── src/                          # 核心源代码目录
│   ├── __init__.py
│   │
│   ├── config/                   # 配置管理
│   │   ├── __init__.py
│   │   └── settings.py           # 所有配置项集中于此
│   │
│   ├── drivers/                  # 移动端驱动层
│   │   ├── __init__.py
│   │   ├── appium_driver.py      # Appium初始化、会话管理
│   │   └── element_handler.py    # UI元素提取、弹窗处理等
│   │
│   ├── actions/                  # 动作执行层
│   │   ├── __init__.py
│   │   ├── base_action.py        # 动作基类 (可选)
│   │   └── mobile_actions.py     # click_text, swipe, type_text 等具体动作
│   │
│   ├── agents/                   # 智能体核心
│   │   ├── __init__.py
│   │   ├── state.py              # AgentState 定义
│   │   ├── nodes/                # 工作流节点
│   │   │   ├── __init__.py
│   │   │   ├── screenshot_node.py
│   │   │   ├── planner_node.py   # LLM规划器
│   │   │   └── executor_node.py  # 动作执行器
│   │   └── workflow.py           # LangGraph工作流定义 (app = workflow.compile())
│   │
│   └── utils/                    # 通用工具
│       ├── __init__.py
│       ├── image_processor.py    # 图片压缩、Base64编码
│       └── xml_parser.py         # 页面源码解析 (可与element_handler合并)
│
├── tests/                        # 单元测试和集成测试 (强烈建议添加)
│   └── ...
│
└── main.py                       # 程序入口，负责加载配置、启动工作流