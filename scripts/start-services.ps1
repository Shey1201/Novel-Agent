# Novel Agent Studio 服务启动脚本
# 用于启动所有依赖服务 (Qdrant, Neo4j, Redis)

param(
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Status
)

function Show-Status {
    Write-Host "`n📊 服务状态检查..." -ForegroundColor Cyan
    
    $services = @(
        @{Name="Qdrant"; Port=6333; Url="http://localhost:6333/healthz"},
        @{Name="Neo4j"; Port=7474; Url="http://localhost:7474"},
        @{Name="Redis"; Port=6379; Url=$null}
    )
    
    foreach ($svc in $services) {
        $portCheck = Test-NetConnection -ComputerName localhost -Port $svc.Port -WarningAction SilentlyContinue
        if ($portCheck.TcpTestSucceeded) {
            Write-Host "  ✅ $($svc.Name) - 运行中 (端口: $($svc.Port))" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $($svc.Name) - 未运行 (端口: $($svc.Port))" -ForegroundColor Red
        }
    }
}

function Start-Services {
    Write-Host "`n🚀 启动 Novel Agent Studio 依赖服务..." -ForegroundColor Cyan
    
    # 检查 Docker 是否运行
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ Docker 未安装或未运行" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  📦 启动 Qdrant (向量数据库)..." -ForegroundColor Yellow
    Write-Host "  📦 启动 Neo4j (知识图谱)..." -ForegroundColor Yellow
    Write-Host "  📦 启动 Redis (缓存)..." -ForegroundColor Yellow
    
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ 服务启动成功！" -ForegroundColor Green
        Write-Host "`n📍 访问地址:" -ForegroundColor Cyan
        Write-Host "  • Qdrant Dashboard: http://localhost:6333/dashboard" -ForegroundColor White
        Write-Host "  • Neo4j Browser: http://localhost:7474" -ForegroundColor White
        Write-Host "    用户名: neo4j" -ForegroundColor Gray
        Write-Host "    密码: novelagent123" -ForegroundColor Gray
        Write-Host "  • Redis: localhost:6379" -ForegroundColor White
        
        Write-Host "`n⏳ 等待服务就绪..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        Show-Status
    } else {
        Write-Host "`n❌ 服务启动失败" -ForegroundColor Red
    }
}

function Stop-Services {
    Write-Host "`n🛑 停止 Novel Agent Studio 依赖服务..." -ForegroundColor Cyan
    docker-compose down
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 服务已停止" -ForegroundColor Green
    } else {
        Write-Host "❌ 停止服务失败" -ForegroundColor Red
    }
}

# 主逻辑
if ($Status) {
    Show-Status
} elseif ($Stop) {
    Stop-Services
} elseif ($Restart) {
    Stop-Services
    Start-Sleep -Seconds 2
    Start-Services
} else {
    Start-Services
}

Write-Host "`n💡 提示: 使用 -Stop 参数停止服务，-Restart 重启服务，-Status 查看状态" -ForegroundColor Gray
