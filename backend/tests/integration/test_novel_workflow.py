"""
小说工作流程集成测试
测试从前端到后端的完整工作流程
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.main import app


client = TestClient(app)


class TestNovelWorkflow:
    """测试小说工作流程"""
    
    def test_complete_novel_creation_workflow(self):
        """测试完整的小说创建流程"""
        # 1. 创建小说草稿
        draft_data = {
            "novel_id": "workflow-test",
            "chapter_id": "ch-1",
            "content": "<p>这是第一章的内容</p>"
        }
        
        response = client.post("/api/novels/draft", json=draft_data)
        assert response.status_code == 200
        assert response.json()["novel_id"] == "workflow-test"
        
        # 2. 读取草稿
        response = client.get("/api/novels/draft", params={
            "novel_id": "workflow-test",
            "chapter_id": "ch-1"
        })
        assert response.status_code == 200
        assert "这是第一章的内容" in response.json()["content"]
        
        # 3. 更新草稿
        updated_draft = {
            "novel_id": "workflow-test",
            "chapter_id": "ch-1",
            "content": "<p>这是更新后的内容</p>"
        }
        
        response = client.post("/api/novels/draft", json=updated_draft)
        assert response.status_code == 200
        
        # 4. 验证更新
        response = client.get("/api/novels/draft", params={
            "novel_id": "workflow-test",
            "chapter_id": "ch-1"
        })
        assert response.status_code == 200
        assert "更新后的内容" in response.json()["content"]
    
    def test_export_word_workflow(self):
        """测试导出Word文档流程"""
        # 1. 先创建草稿
        draft_data = {
            "novel_id": "export-test",
            "chapter_id": "ch-1",
            "content": "<p>导出的内容</p>"
        }
        
        response = client.post("/api/novels/draft", json=draft_data)
        assert response.status_code == 200
        
        # 2. 导出Word
        response = client.get("/api/novels/export/word", params={
            "novel_id": "export-test",
            "chapter_id": "ch-1"
        })
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    def test_concurrent_draft_editing(self):
        """测试并发编辑草稿"""
        import threading
        import time
        
        results = []
        
        def save_draft(thread_id):
            draft_data = {
                "novel_id": "concurrent-test",
                "chapter_id": "ch-1",
                "content": f"<p>线程{thread_id}的内容</p>"
            }
            response = client.post("/api/novels/draft", json=draft_data)
            results.append((thread_id, response.status_code))
        
        # 创建多个线程同时保存
        threads = []
        for i in range(5):
            t = threading.Thread(target=save_draft, args=(i,))
            threads.append(t)
        
        # 启动所有线程
        for t in threads:
            t.start()
            time.sleep(0.01)  # 稍微错开启动时间
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证所有请求都成功
        assert len(results) == 5
        for thread_id, status_code in results:
            assert status_code == 200, f"线程{thread_id}失败"
    
    def test_draft_persistence(self):
        """测试草稿持久化"""
        # 1. 创建草稿
        draft_data = {
            "novel_id": "persistence-test",
            "chapter_id": "ch-1",
            "content": "<p>持久化测试内容</p>"
        }
        
        response = client.post("/api/novels/draft", json=draft_data)
        assert response.status_code == 200
        
        # 2. 多次读取验证持久化
        for _ in range(3):
            response = client.get("/api/novels/draft", params={
                "novel_id": "persistence-test",
                "chapter_id": "ch-1"
            })
            assert response.status_code == 200
            assert "持久化测试内容" in response.json()["content"]
    
    def test_invalid_novel_id_handling(self):
        """测试无效小说ID处理"""
        # 尝试读取不存在的小说
        response = client.get("/api/novels/draft", params={
            "novel_id": "non-existent-novel",
            "chapter_id": "ch-1"
        })
        # 应该返回404或空内容
        assert response.status_code in [200, 404]
    
    def test_empty_content_handling(self):
        """测试空内容处理"""
        draft_data = {
            "novel_id": "empty-test",
            "chapter_id": "ch-1",
            "content": ""
        }
        
        response = client.post("/api/novels/draft", json=draft_data)
        assert response.status_code == 200
        
        # 读取空内容
        response = client.get("/api/novels/draft", params={
            "novel_id": "empty-test",
            "chapter_id": "ch-1"
        })
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
