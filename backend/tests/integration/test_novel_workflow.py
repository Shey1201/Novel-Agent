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
        
        response = client.post("/api/novel/draft", json=draft_data)
        assert response.status_code == 200
        assert response.json()["novel_id"] == "workflow-test"
        
        # 2. 读取草稿
        response = client.get("/api/novel/draft", params={
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
        
        response = client.post("/api/novel/draft", json=updated_draft)
        assert response.status_code == 200
        
        # 4. 验证更新
        response = client.get("/api/novel/draft", params={
            "novel_id": "workflow-test",
            "chapter_id": "ch-1"
        })
        assert response.status_code == 200
        assert "更新后的内容" in response.json()["content"]
    
    def test_novel_export_workflow(self):
        """测试小说导出流程"""
        # 1. 先保存草稿
        draft_data = {
            "novel_id": "export-test",
            "chapter_id": "ch-1",
            "content": "<p>导出测试内容</p>"
        }
        
        response = client.post("/api/novel/draft", json=draft_data)
        assert response.status_code == 200
        
        # 2. 导出为Word
        response = client.get("/api/novel/export/word", params={
            "novel_id": "export-test",
            "chapter_id": "ch-1"
        })
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    def test_download_after_save_workflow(self):
        """测试保存后下载的完整流程"""
        # 1. 保存多个章节
        chapters = [
            {"id": "ch1", "title": "第一章", "content": "<p>第一章内容</p>"},
            {"id": "ch2", "title": "第二章", "content": "<p>第二章内容</p>"},
        ]
        
        for ch in chapters:
            draft = {
                "novel_id": "download-test",
                "chapter_id": ch["id"],
                "content": ch["content"]
            }
            response = client.post("/api/novel/draft", json=draft)
            assert response.status_code == 200
        
        # 2. 下载完整小说
        download_request = {
            "novel_title": "下载测试小说",
            "download_type": "full",
            "chapters": chapters
        }
        
        response = client.post("/download/novel", json=download_request)
        assert response.status_code == 200
        
        # 3. 下载单章
        download_request = {
            "novel_title": "下载测试小说",
            "download_type": "single",
            "single_chapter_id": "ch1",
            "chapters": chapters
        }
        
        response = client.post("/download/novel", json=download_request)
        assert response.status_code == 200
        
        # 4. 下载章节范围
        download_request = {
            "novel_title": "下载测试小说",
            "download_type": "range",
            "start_chapter": 1,
            "end_chapter": 2,
            "chapters": chapters
        }
        
        response = client.post("/download/novel", json=download_request)
        assert response.status_code == 200


class TestErrorHandlingWorkflow:
    """测试错误处理流程"""
    
    def test_nonexistent_novel_handling(self):
        """测试不存在的novel处理"""
        response = client.get("/api/novel/draft", params={
            "novel_id": "nonexistent",
            "chapter_id": "ch-1"
        })
        
        # 应该返回空内容而不是错误
        assert response.status_code == 200
        assert response.json()["source"] == "empty"
    
    def test_invalid_chapter_id_handling(self):
        """测试无效章节ID处理"""
        response = client.get("/api/novel/draft", params={
            "novel_id": "test",
            "chapter_id": ""
        })
        
        # 应该优雅处理
        assert response.status_code in [200, 422]
    
    def test_concurrent_save_handling(self):
        """测试并发保存处理"""
        draft = {
            "novel_id": "concurrent-test",
            "chapter_id": "ch-1",
            "content": "<p>并发测试</p>"
        }
        
        # 快速连续保存两次
        response1 = client.post("/api/novel/draft", json=draft)
        response2 = client.post("/api/novel/draft", json=draft)
        
        # 两次都应该成功
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestDataIntegrityWorkflow:
    """测试数据完整性流程"""
    
    def test_special_characters_preservation(self):
        """测试特殊字符保留"""
        special_content = "<p>特殊字符：&lt;&gt;&amp;\"'</p>"
        
        draft = {
            "novel_id": "special-chars",
            "chapter_id": "ch-1",
            "content": special_content
        }
        
        # 保存
        response = client.post("/api/novel/draft", json=draft)
        assert response.status_code == 200
        
        # 读取
        response = client.get("/api/novel/draft", params={
            "novel_id": "special-chars",
            "chapter_id": "ch-1"
        })
        
        assert response.status_code == 200
        # 内容应该被保留
        assert "&lt;" in response.json()["content"] or "<" in response.json()["content"]
    
    def test_large_content_handling(self):
        """测试大内容处理"""
        # 生成大段内容
        large_content = "<p>" + "这是一个长段落。" * 1000 + "</p>"
        
        draft = {
            "novel_id": "large-content",
            "chapter_id": "ch-1",
            "content": large_content
        }
        
        response = client.post("/api/novel/draft", json=draft)
        assert response.status_code == 200
        
        # 验证能正确读取
        response = client.get("/api/novel/draft", params={
            "novel_id": "large-content",
            "chapter_id": "ch-1"
        })
        
        assert response.status_code == 200
        assert len(response.json()["content"]) > 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
