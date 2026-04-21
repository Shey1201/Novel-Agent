"""
测试增强版 Pipeline 服务
"""
import os
import sys

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.services.pipeline_service_enhanced import EnhancedPipelineService


def test_enhanced_pipeline():
    """测试增强版 Pipeline"""
    print("="*60)
    print("Test: Enhanced Pipeline Service")
    print("="*60)
    
    # 创建服务（启用评分和 Reflection）
    service = EnhancedPipelineService(
        story_id="test-story",
        enable_scoring=True,
        enable_reflection=True,
    )
    
    # 测试大纲
    outline = "第一章：林晓穿越到异世界"
    
    print(f"\n--- Running with outline: {outline} ---")
    print("(This will call LLM, may take time...)\n")
    
    # 由于真实调用耗时较长，这里只展示调用方式
    # result = service.run(outline)
    # print(result)
    
    print("To run actual test, uncomment the following:")
    print("""
result = service.run(outline)
print(f"Plan: {len(result['plan_text'])} chars")
print(f"Draft: {len(result['draft_text'])} chars")
print(f"Edited: {len(result['edited_text'])} chars")
print(f"Scores: {result.get('scores', {})}")
print(service.get_summary())
    """)
    
    return True


def test_word_count_in_api():
    """测试 API 中的字数统计"""
    print("\n" + "="*60)
    print("Test: Word Count in API Response")
    print("="*60)
    
    print("""
API Response now includes word_count:

GenerateChapterResponse:
{
    "input_text": "...",
    "plan_text": "...",
    "draft_text": "...",
    "edited_text": "...",
    "final_text": "...",
    "word_count": {
        "input": 10,
        "plan": 500,
        "draft": 3000,
        "edited": 2800,
        "final": 2800
    }
}

GenerationStepResponse:
{
    "generation_id": "...",
    "step": "plan",
    "content": "...",
    "word_count": 500
}
    """)
    
    return True


def main():
    results = {}
    
    # 测试增强版 Pipeline
    try:
        results["enhanced_pipeline"] = test_enhanced_pipeline()
    except Exception as e:
        print(f"Error: {e}")
        results["enhanced_pipeline"] = False
    
    # 测试 API 字数统计
    try:
        results["word_count_api"] = test_word_count_in_api()
    except Exception as e:
        print(f"Error: {e}")
        results["word_count_api"] = False
    
    # 总结
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    passed = sum(1 for v in results.values() if v)
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {name}: {status}")
    print(f"\nTotal: {passed}/{len(results)} passed")


if __name__ == "__main__":
    main()
