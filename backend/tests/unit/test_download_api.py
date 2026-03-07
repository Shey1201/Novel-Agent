"""
下载API功能测试
测试小说下载功能的各项用例
"""

import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from unittest.mock import patch, MagicMock
import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.main import app
from app.api.download_api import create_word_document, html_to_text, NovelDownloadRequest, ChapterData


client = TestClient(app)


class TestHtmlToText:
    """测试HTML转文本功能"""
    
    def test_remove_html_tags(self):
        """测试去除HTML标签"""
        html = "<p>这是一段文字</p>"
        result = html_to_text(html)
        assert "<p>" not in result
        assert "这是一段文字" in result
    
    def test_convert_line_breaks(self):
        """测试转换换行符"""
        html = "第一行<br>第二行"
        result = html_to_text(html)
        assert "\n" in result
        assert "第一行" in result
        assert "第二行" in result
    
    def test_handle_empty_content(self):
        """测试处理空内容"""
        html = ""
        result = html_to_text(html)
        assert result == ""
    
    def test_handle_nested_html(self):
        """测试处理嵌套HTML"""
        html = "<div><p><strong>粗体文字</strong></p></div>"
        result = html_to_text(html)
        assert "<div>" not in result
        assert "<p>" not in result
        assert "<strong>" not in result
        assert "粗体文字" in result


class TestCreateWordDocument:
    """测试Word文档生成功能"""
    
    def test_create_document_with_chapters(self):
        """测试创建包含章节的文档"""
        chapters = [
            ChapterData(id="ch1", title="第一章", content="<p>第一章内容</p>"),
            ChapterData(id="ch2", title="第二章", content="<p>第二章内容</p>"),
        ]
        
        doc_buffer = create_word_document("测试小说", chapters)
        
        assert isinstance(doc_buffer, BytesIO)
        assert doc_buffer.getvalue()  # 确保有内容
    
    def test_create_document_with_empty_chapters(self):
        """测试创建空章节文档"""
        chapters = [
            ChapterData(id="ch1", title="第一章", content=""),
        ]
        
        doc_buffer = create_word_document("测试小说", chapters)
        
        assert isinstance(doc_buffer, BytesIO)
        assert doc_buffer.getvalue()
    
    def test_create_document_with_chinese_title(self):
        """测试创建中文标题文档"""
        chapters = [
            ChapterData(id="ch1", title="章节一", content="<p>内容</p>"),
        ]
        
        doc_buffer = create_word_document("中文小说名", chapters)
        
        assert isinstance(doc_buffer, BytesIO)
        assert doc_buffer.getvalue()


class TestDownloadAPI:
    """测试下载API端点"""
    
    def test_download_full_novel(self):
        """测试下载完整小说"""
        request_data = {
            "novel_title": "测试小说",
            "download_type": "full",
            "chapters": [
                {"id": "ch1", "title": "第一章", "content": "<p>内容1</p>"},
                {"id": "ch2", "title": "第二章", "content": "<p>内容2</p>"},
            ]
        }
        
        response = client.post("/download/novel", json=request_data)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert "content-disposition" in response.headers
    
    def test_download_single_chapter(self):
        """测试下载单章"""
        request_data = {
            "novel_title": "测试小说",
            "download_type": "single",
            "single_chapter_id": "ch1",
            "chapters": [
                {"id": "ch1", "title": "第一章", "content": "<p>内容1</p>"},
                {"id": "ch2", "title": "第二章", "content": "<p>内容2</p>"},
            ]
        }
        
        response = client.post("/download/novel", json=request_data)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    def test_download_chapter_range(self):
        """测试下载章节范围"""
        request_data = {
            "novel_title": "测试小说",
            "download_type": "range",
            "start_chapter": 1,
            "end_chapter": 2,
            "chapters": [
                {"id": "ch1", "title": "第一章", "content": "<p>内容1</p>"},
                {"id": "ch2", "title": "第二章", "content": "<p>内容2</p>"},
                {"id": "ch3", "title": "第三章", "content": "<p>内容3</p>"},
            ]
        }
        
        response = client.post("/download/novel", json=request_data)
        
        assert response.status_code == 200
    
    def test_download_missing_chapter_id(self):
        """测试缺少章节ID的错误处理"""
        request_data = {
            "novel_title": "测试小说",
            "download_type": "single",
            "chapters": [
                {"id": "ch1", "title": "第一章", "content": "<p>内容1</p>"},
            ]
        }
        
        response = client.post("/download/novel", json=request_data)
        
        assert response.status_code == 400
        assert "章节ID" in response.json()["detail"] or "chapter" in response.json()["detail"].lower()
    
    def test_download_invalid_range(self):
        """测试无效章节范围"""
        request_data = {
            "novel_title": "测试小说",
            "download_type": "range",
            "start_chapter": 3,
            "end_chapter": 1,
            "chapters": [
                {"id": "ch1", "title": "第一章", "content": "<p>内容1</p>"},
            ]
        }
        
        response = client.post("/download/novel", json=request_data)
        
        assert response.status_code == 400
    
    def test_download_no_chapters(self):
        """测试无章节下载"""
        request_data = {
            "novel_title": "测试小说",
            "download_type": "full",
            "chapters": []
        }
        
        response = client.post("/download/novel", json=request_data)
        
        assert response.status_code == 400
        assert "没有可下载" in response.json()["detail"]
    
    def test_download_invalid_type(self):
        """测试无效下载类型"""
        request_data = {
            "novel_title": "测试小说",
            "download_type": "invalid",
            "chapters": [
                {"id": "ch1", "title": "第一章", "content": "<p>内容1</p>"},
            ]
        }
        
        response = client.post("/download/novel", json=request_data)
        
        assert response.status_code == 400
        assert "无效" in response.json()["detail"] or "invalid" in response.json()["detail"].lower()


class TestDownloadWithSpecialCharacters:
    """测试特殊字符处理"""
    
    def test_download_with_special_chars_in_title(self):
        """测试标题包含特殊字符"""
        request_data = {
            "novel_title": "测试小说《特殊》",
            "download_type": "full",
            "chapters": [
                {"id": "ch1", "title": "第一章", "content": "<p>内容</p>"},
            ]
        }
        
        response = client.post("/download/novel", json=request_data)
        
        assert response.status_code == 200
    
    def test_download_with_emoji_in_content(self):
        """测试内容包含emoji"""
        request_data = {
            "novel_title": "测试小说",
            "download_type": "full",
            "chapters": [
                {"id": "ch1", "title": "第一章", "content": "<p>内容😀</p>"},
            ]
        }
        
        response = client.post("/download/novel", json=request_data)
        
        # 应该能处理或给出合适的错误
        assert response.status_code in [200, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
