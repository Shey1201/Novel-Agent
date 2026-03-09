/**
 * Token Reset API Route
 * 处理 /api/settings/token/reset 请求
 */

import { NextRequest, NextResponse } from 'next/server';

// POST 请求处理
export async function POST(request: NextRequest) {
  return NextResponse.json({ message: '每日 Token 使用已重置' });
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
