# Novel Agent Studio API 测试脚本

$baseUrl = "http://localhost:8000"

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Endpoint,
        [object]$Body = $null
    )
    
    Write-Host "`n🧪 测试: $Name" -ForegroundColor Cyan
    Write-Host "   $Method $Endpoint" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = "$baseUrl$Endpoint"
            Method = $Method
            ContentType = "application/json"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        Write-Host "   ✅ 成功" -ForegroundColor Green
        return $response
    } catch {
        Write-Host "   ❌ 失败: $_" -ForegroundColor Red
        return $null
    }
}

Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "   Novel Agent Studio API 测试" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue

# 1. 健康检查
Test-Endpoint -Name "健康检查" -Method "GET" -Endpoint "/health"

# 2. 创建小说
$novel = Test-Endpoint -Name "创建小说" -Method "POST" -Endpoint "/api/novel" -Body @{
    title = "测试小说"
    description = "API 测试用小说"
}

if ($novel) {
    $novelId = $novel.id
    
    # 3. 获取小说列表
    Test-Endpoint -Name "获取小说列表" -Method "GET" -Endpoint "/api/novels"
    
    # 4. 创建章节
    $chapter = Test-Endpoint -Name "创建章节" -Method "POST" -Endpoint "/api/novel/chapter" -Body @{
        novel_id = $novelId
        title = "第一章"
    }
    
    if ($chapter) {
        $chapterId = $chapter.chapter_id
        
        # 5. 保存草稿
        Test-Endpoint -Name "保存草稿" -Method "POST" -Endpoint "/api/novel/draft" -Body @{
            novel_id = $novelId
            chapter_id = $chapterId
            content = "这是测试内容"
        }
        
        # 6. 获取章节
        Test-Endpoint -Name "获取章节" -Method "GET" -Endpoint "/api/novel/$novelId/chapter/$chapterId"
    }
    
    # 7. Writers Room - 创建讨论
    $discussion = Test-Endpoint -Name "创建 Writers Room 讨论" -Method "POST" -Endpoint "/api/writers-room/discussions" -Body @{
        novel_id = $novelId
        title = "测试讨论"
        description = "讨论主角如何脱困"
        max_rounds = 5
    }
    
    if ($discussion) {
        $discussionId = $discussion.id
        
        # 8. 获取讨论状态
        Test-Endpoint -Name "获取讨论状态" -Method "GET" -Endpoint "/api/writers-room/discussions/$discussionId"
        
        # 9. 运行一轮讨论
        Test-Endpoint -Name "运行讨论轮次" -Method "POST" -Endpoint "/api/writers-room/discussions/$discussionId/round"
    }
}

# 10. 获取世界设定
Test-Endpoint -Name "获取世界设定" -Method "GET" -Endpoint "/api/world/demo-story"

Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "   API 测试完成" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
