/**
 * Token Status API Route
 * 处理 /api/settings/token/status 请求
 */

import { NextRequest, NextResponse } from 'next/server';

// GET 请求处理
export async function GET(request: NextRequest) {
  // 简化处理，返回默认值
  return NextResponse.json({
    enabled: false,
    daily_limit: 50000,
    daily_used: 0,
    daily_remaining: 50000,
    usage_rate: 0.0
  });
}

// OPTIONS 请求处理（CORS）
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}
