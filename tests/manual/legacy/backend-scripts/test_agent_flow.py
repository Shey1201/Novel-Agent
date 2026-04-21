"""
Agent 流程测试脚本
测试 Agent 工作流并测量 API 响应时间
"""
import time
import json
import requests
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
TEST_OUTLINE = "一个关于青春成长的故事，主角是一名高中生，在面对高考和家庭期望的压力下，逐渐找到自己的人生方向。"

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(label, value, is_time=False):
    """打印结果"""
    if is_time:
        print(f"  {label}: {value:.2f}秒")
    else:
        print(f"  {label}: {value}")

def test_api_endpoint(endpoint, payload, description):
    """测试 API 端点并测量时间"""
    print_header(f"测试: {description}")
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            json=payload,
            timeout=120  # 2分钟超时
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print_result("状态码", response.status_code)
            print_result("耗时", elapsed, is_time=True)
            return response.json(), elapsed
        else:
            print_result("状态码", f"{response.status_code} - 错误")
            print_result("耗时", elapsed, is_time=True)
            print_result("错误", response.text[:200])
            return None, elapsed
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print_result("状态码", "超时")
        print_result("耗时", elapsed, is_time=True)
        return None, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print_result("状态码", "异常")
        print_result("耗时", elapsed, is_time=True)
        print_result("错误", str(e)[:200])
        return None, elapsed

def test_single_agent(agent_name, payload, endpoint):
    """测试单个 Agent"""
    print_header(f"测试单个 Agent: {agent_name}")
    
    result, elapsed = test_api_endpoint(endpoint, payload, f"{agent_name} Agent")
    
    if result:
        print(f"\n  返回数据键: {list(result.keys())}")
        # 打印部分结果
        for key in result.keys():
            if key in ["draft_text", "plan_text", "edited_text", "final_text"]:
                text = result.get(key, "")
                if text:
                    preview = text[:100] + "..." if len(text) > 100 else text
                    print(f"    {key}: {preview}")
    
    return result, elapsed

def test_full_workflow():
    """测试完整的工作流"""
    print_header("测试完整 Agent 工作流")
    
    payload = {
        "outline": TEST_OUTLINE,
        "story_id": "test-story",
        "chapter_id": "test-chapter-001",
        "auto_confirm": True  # 自动确认全部步骤
    }
    
    result, elapsed = test_api_endpoint(
        "/api/generate-chapter/start",
        payload,
        "完整章节生成流程"
    )
    
    if result:
        print("\n  工作流详情:")
        print_result("当前步骤", result.get("step", ""))
        print_result("状态", result.get("status", ""))
        print_result("需要确认", result.get("requires_confirmation", False))
        
        if result.get("content"):
            content = result.get("content", "")
            print(f"\n  生成内容预览 (前200字):")
            print(f"  {content[:200]}...")
    
    return result, elapsed

def test_simplified_endpoint():
    """测试简化版生成接口"""
    print_header("测试简化版生成接口")
    
    payload = {
        "outline": TEST_OUTLINE,
        "story_id": "demo-story",
        "auto_confirm": True
    }
    
    result, elapsed = test_api_endpoint(
        "/api/generate_chapter",
        payload,
        "简化章节生成"
    )
    
    if result:
        print("\n  生成结果:")
        print_result("Plan 长度", len(result.get("plan_text", "")))
        print_result("Draft 长度", len(result.get("draft_text", "")))
        print_result("Edited 长度", len(result.get("edited_text", "")))
        print_result("Final 长度", len(result.get("final_text", "")))
        
        # 打印 Agent 日志
        logs = result.get("agent_logs", [])
        print(f"\n  Agent 执行日志 ({len(logs)} 个):")
        for log in logs:
            if isinstance(log, dict):
                print(f"    - {log.get('agent', 'unknown')}: {log.get('message', '')}")
    
    return result, elapsed

def run_performance_test():
    """运行性能测试"""
    print_header("性能测试 - 多次请求")
    
    results = []
    
    for i in range(3):
        print(f"\n  第 {i+1} 次请求...")
        
        payload = {
            "outline": f"{TEST_OUTLINE} (测试 {i+1})",
            "story_id": f"test-story-{i+1}",
            "auto_confirm": True
        }
        
        result, elapsed = test_api_endpoint(
            "/api/generate_chapter",
            payload,
            f"性能测试 {i+1}/3"
        )
        
        if result:
            results.append(elapsed)
            print_result("请求耗时", elapsed, is_time=True)
        else:
            print(f"  请求失败")
    
    if results:
        print_header("性能测试结果")
        avg_time = sum(results) / len(results)
        min_time = min(results)
        max_time = max(results)
        
        print_result("平均耗时", avg_time, is_time=True)
        print_result("最快耗时", min_time, is_time=True)
        print_result("最慢耗时", max_time, is_time=True)
        print_result("成功次数", f"{len(results)}/3")

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  Agent 流程测试")
    print("  测试时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    # 检查服务器是否运行
    print("\n检查服务器连接...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        print(f"  服务器状态: 正常运行 (状态码: {response.status_code})")
    except Exception as e:
        print(f"  服务器状态: 无法连接 - {str(e)}")
        print("\n请确保服务器正在运行:")
        print("  cd backend && uvicorn app.main:app --reload")
        return
    
    # 测试完整工作流
    test_full_workflow()
    
    # 测试简化版
    print("\n")
    test_simplified_endpoint()
    
    # 性能测试
    print("\n")
    run_performance_test()
    
    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()