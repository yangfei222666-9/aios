"""
ReAct Agent - 基于 LangGraph 的智能 Agent
集成 MCP 工具协议
"""
import os
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
import requests
from dotenv import load_dotenv

load_dotenv()

# MCP Server 地址
WEATHER_SERVER = "http://localhost:8001"
WRITE_SERVER = "http://localhost:8002"
AMAP_SERVER = "http://localhost:8003"


class MCPClient:
    """MCP 客户端 - 统一调用 MCP Server"""
    
    @staticmethod
    def call_weather(city: str) -> str:
        """查询天气"""
        try:
            response = requests.post(
                f"{WEATHER_SERVER}/weather",
                json={"city": city},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return (
                f"{data['city']}天气：\n"
                f"温度：{data['temperature']}°C（体感{data['feels_like']}°C）\n"
                f"湿度：{data['humidity']}%\n"
                f"天气：{data['description']}\n"
                f"风速：{data['wind_speed']} m/s"
            )
        except Exception as e:
            return f"查询天气失败：{str(e)}"
    
    @staticmethod
    def write_file(filename: str, content: str) -> str:
        """写入文件"""
        try:
            response = requests.post(
                f"{WRITE_SERVER}/write",
                json={"filename": filename, "content": content},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]
        except Exception as e:
            return f"写入文件失败：{str(e)}"
    
    @staticmethod
    def read_file(filename: str) -> str:
        """读取文件"""
        try:
            response = requests.post(
                f"{WRITE_SERVER}/read",
                json={"filename": filename},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data["content"]
        except Exception as e:
            return f"读取文件失败：{str(e)}"
    
    @staticmethod
    def search_place(keywords: str, city: Optional[str] = None) -> str:
        """搜索地点"""
        try:
            response = requests.post(
                f"{AMAP_SERVER}/search",
                json={"keywords": keywords, "city": city, "limit": 5},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not data["places"]:
                return "未找到相关地点"
            
            result = f"找到 {data['count']} 个地点：\n"
            for i, place in enumerate(data["places"], 1):
                result += f"{i}. {place['name']}\n   地址：{place['address']}\n"
            
            return result
        except Exception as e:
            return f"搜索地点失败：{str(e)}"


# 定义工具
tools = [
    Tool(
        name="weather",
        func=MCPClient.call_weather,
        description="查询城市天气。输入：城市名（如'北京'、'上海'）"
    ),
    Tool(
        name="write_file",
        func=lambda args: MCPClient.write_file(args.split("|")[0], args.split("|")[1]),
        description="写入文件。输入格式：'文件名|内容'（用|分隔）"
    ),
    Tool(
        name="read_file",
        func=MCPClient.read_file,
        description="读取文件。输入：文件名"
    ),
    Tool(
        name="search_place",
        func=lambda args: MCPClient.search_place(
            args.split("|")[0],
            args.split("|")[1] if "|" in args else None
        ),
        description="搜索地点。输入格式：'关键词|城市'（城市可选，用|分隔）"
    )
]


class ReactAgent:
    """ReAct Agent"""
    
    def __init__(self, model_name: str = "qwen-plus"):
        """初始化 Agent"""
        # 注意：这里需要实际的 LLM 实现
        # 由于没有通义千问的 LangChain 集成，这里用伪代码
        from langchain_community.chat_models import ChatOpenAI
        
        # 实际使用时需要替换为通义千问的实现
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 创建 ReAct Agent
        self.memory = MemorySaver()
        self.agent = create_react_agent(
            self.llm,
            tools,
            checkpointer=self.memory
        )
        
        self.thread_id = "default"
    
    def chat(self, message: str) -> str:
        """对话"""
        try:
            config = {"configurable": {"thread_id": self.thread_id}}
            
            result = self.agent.invoke(
                {"messages": [HumanMessage(content=message)]},
                config=config
            )
            
            # 提取最后一条 AI 消息
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    return msg.content
            
            return "无响应"
        
        except Exception as e:
            return f"Agent 错误：{str(e)}"


def main():
    """测试 Agent"""
    print("🤖 ReAct Agent 启动")
    print("=" * 50)
    
    agent = ReactAgent()
    
    # 测试对话
    test_queries = [
        "北京今天天气怎么样？",
        "帮我写一个文件 test.txt，内容是'Hello MCP'",
        "读取 test.txt 的内容",
        "搜索北京的咖啡馆"
    ]
    
    for query in test_queries:
        print(f"\n用户：{query}")
        response = agent.chat(query)
        print(f"Agent：{response}")
        print("-" * 50)


if __name__ == "__main__":
    main()
