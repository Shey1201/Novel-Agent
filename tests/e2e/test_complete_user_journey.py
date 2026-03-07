"""
端到端用户旅程测试
模拟真实用户的完整使用流程
"""

import pytest
import requests
import os
import tempfile
from pathlib import Path


class TestCompleteUserJourney:
    """测试完整用户旅程"""
    
    BASE_URL = "http://127.0.0.1:8000"
    
    @pytest.fixture(scope="class")
    def base_url(self):
        """获取基础URL"""
        return self.BASE_URL
    
    def test_user_creates_novel_and_downloads(self, base_url):
        """测试用户创建小说并下载的完整流程"""
        novel_id = "journey-test-novel"
        
        # 1. 创建第一章
        chapter1_data = {
            "novel_id": novel_id,
            "chapter_id": f"{novel_id}-ch1",
            "content": "<h1>第一章：开始</h1><p>这是一个关于冒险的故事...</p>"
        }
        
        response = requests.post(f"{base_url}/api/novel/draft", json=chapter1_data)
        assert response.status_code == 200, f"创建第一章失败: {response.text}"
        print("✓ 第一章创建成功")
        
        # 2. 创建第二章
        chapter2_data = {
            "novel_id": novel_id,
            "chapter_id": f"{novel_id}-ch2",
            "content": "<h1>第二章：发展</h1><p>故事继续发展...</p>"
        }
        
        response = requests.post(f"{base_url}/api/novel/draft", json=chapter2_data)
        assert response.status_code == 200, f"创建第二章失败: {response.text}"
        print("✓ 第二章创建成功")
        
        # 3. 验证内容已保存
        response = requests.get(
            f"{base_url}/api/novel/draft",
            params={"novel_id": novel_id, "chapter_id": f"{novel_id}-ch1"}
        )
        assert response.status_code == 200
        assert "开始" in response.json()["content"]
        print("✓ 内容验证成功")
        
        # 4. 下载完整小说
        download_request = {
            "novel_title": "我的冒险小说",
            "download_type": "full",
            "chapters": [
                {"id": f"{novel_id}-ch1", "title": "第一章：开始", "content": chapter1_data["content"]},
                {"id": f"{novel_id}-ch2", "title": "第二章：发展", "content": chapter2_data["content"]}
            ]
        }
        
        response = requests.post(f"{base_url}/download/novel", json=download_request)
        assert response.status_code == 200, f"下载失败: {response.text}"
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        print("✓ 完整小说下载成功")
        
        # 5. 下载单章
        download_request["download_type"] = "single"
        download_request["single_chapter_id"] = f"{novel_id}-ch1"
        
        response = requests.post(f"{base_url}/download/novel", json=download_request)
        assert response.status_code == 200
        print("✓ 单章下载成功")
        
        # 6. 下载章节范围
        download_request["download_type"] = "range"
        download_request["start_chapter"] = 1
        download_request["end_chapter"] = 2
        
        response = requests.post(f"{base_url}/download/novel", json=download_request)
        assert response.status_code == 200
        print("✓ 章节范围下载成功")
    
    def test_user_updates_chapter_and_re_downloads(self, base_url):
        """测试用户更新章节后重新下载"""
        novel_id = "update-test-novel"
        chapter_id = f"{novel_id}-ch1"
        
        # 1. 初始创建
        initial_content = "<p>初始内容</p>"
        draft = {
            "novel_id": novel_id,
            "chapter_id": chapter_id,
            "content": initial_content
        }
        
        response = requests.post(f"{base_url}/api/novel/draft", json=draft)
        assert response.status_code == 200
        print("✓ 初始内容创建成功")
        
        # 2. 更新内容
        updated_content = "<p>更新后的内容，增加了更多细节...</p>"
        draft["content"] = updated_content
        
        response = requests.post(f"{base_url}/api/novel/draft", json=draft)
        assert response.status_code == 200
        print("✓ 内容更新成功")
        
        # 3. 验证更新
        response = requests.get(
            f"{base_url}/api/novel/draft",
            params={"novel_id": novel_id, "chapter_id": chapter_id}
        )
        assert response.status_code == 200
        assert "更新后的内容" in response.json()["content"]
        print("✓ 更新验证成功")
        
        # 4. 下载更新后的内容
        download_request = {
            "novel_title": "更新测试小说",
            "download_type": "single",
            "single_chapter_id": chapter_id,
            "chapters": [
                {"id": chapter_id, "title": "测试章节", "content": updated_content}
            ]
        }
        
        response = requests.post(f"{base_url}/download/novel", json=download_request)
        assert response.status_code == 200
        print("✓ 更新后下载成功")
    
    def test_error_recovery_journey(self, base_url):
        """测试错误恢复流程"""
        
        # 1. 尝试下载不存在的小说（应该优雅处理）
        download_request = {
            "novel_title": "不存在的小说",
            "download_type": "single",
            "single_chapter_id": "nonexistent",
            "chapters": []
        }
        
        response = requests.post(f"{base_url}/download/novel", json=download_request)
        # 应该返回400错误，提示没有可下载的章节
        assert response.status_code == 400
        assert "没有可下载" in response.json()["detail"]
        print("✓ 空章节下载正确处理")
        
        # 2. 尝试无效的范围
        download_request = {
            "novel_title": "测试小说",
            "download_type": "range",
            "start_chapter": 5,
            "end_chapter": 1,
            "chapters": [
                {"id": "ch1", "title": "第一章", "content": "<p>内容</p>"}
            ]
        }
        
        response = requests.post(f"{base_url}/download/novel", json=download_request)
        assert response.status_code == 400
        print("✓ 无效范围正确处理")
    
    def test_chinese_content_journey(self, base_url):
        """测试中文内容完整流程"""
        novel_id = "chinese-test"
        
        # 创建包含中文的内容
        chinese_content = """
        <h1>第一章：江湖风云</h1>
        <p>江湖，是一个充满传奇的地方。</p>
        <p>在这里，英雄豪杰辈出，各路侠客云集。</p>
        <p>这是一个关于勇气、智慧和正义的故事...</p>
        """
        
        draft = {
            "novel_id": novel_id,
            "chapter_id": f"{novel_id}-ch1",
            "content": chinese_content
        }
        
        response = requests.post(f"{base_url}/api/novel/draft", json=draft)
        assert response.status_code == 200
        print("✓ 中文内容创建成功")
        
        # 下载中文小说
        download_request = {
            "novel_title": "江湖风云录",
            "download_type": "full",
            "chapters": [
                {"id": f"{novel_id}-ch1", "title": "第一章：江湖风云", "content": chinese_content}
            ]
        }
        
        response = requests.post(f"{base_url}/download/novel", json=download_request)
        assert response.status_code == 200
        
        # 验证文件名包含中文
        content_disposition = response.headers.get("content-disposition", "")
        assert "江湖风云录" in content_disposition or "UTF-8" in content_disposition
        print("✓ 中文小说下载成功")


class TestPerformanceJourney:
    """测试性能相关场景"""
    
    BASE_URL = "http://127.0.0.1:8000"
    
    def test_large_novel_download(self):
        """测试大小说下载性能"""
        base_url = self.BASE_URL
        novel_id = "large-novel-test"
        
        # 创建包含大量内容的章节
        large_content = "<p>" + "这是一段很长的内容。" * 500 + "</p>"
        
        chapters = []
        for i in range(1, 4):  # 3个大章节
            chapter_id = f"{novel_id}-ch{i}"
            draft = {
                "novel_id": novel_id,
                "chapter_id": chapter_id,
                "content": f"<h1>第{i}章</h1>{large_content}"
            }
            
            response = requests.post(f"{base_url}/api/novel/draft", json=draft)
            assert response.status_code == 200
            
            chapters.append({
                "id": chapter_id,
                "title": f"第{i}章",
                "content": draft["content"]
            })
        
        print(f"✓ 创建了{len(chapters)}个大章节")
        
        # 下载完整小说
        download_request = {
            "novel_title": "大小说测试",
            "download_type": "full",
            "chapters": chapters
        }
        
        import time
        start_time = time.time()
        
        response = requests.post(f"{base_url}/download/novel", json=download_request)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert response.status_code == 200
        assert duration < 30, f"下载耗时过长: {duration}秒"  # 应该在30秒内完成
        
        print(f"✓ 大小说下载成功，耗时: {duration:.2f}秒")


if __name__ == "__main__":
    # 运行测试前确保服务已启动
    print("=" * 60)
    print("开始端到端测试")
    print("=" * 60)
    
    # 检查服务是否可用
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        print("✓ 后端服务已启动")
    except:
        print("⚠ 后端服务可能未启动，请确保服务在 http://127.0.0.1:8000 运行")
    
    pytest.main([__file__, "-v", "-s"])
