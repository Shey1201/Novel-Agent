/**
 * Generation Settings API Route
 * 处理 /api/settings/generation 请求
 */

import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// 创建 Supabase 客户端
const getSupabase = () => {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
  
  if (!supabaseUrl || !supabaseKey) {
    return null;
  }
  
  return createClient(supabaseUrl, supabaseKey);
};

// GET 请求处理
export async function GET(request: NextRequest) {
  const supabase = getSupabase();
  
  if (!supabase) {
    return NextResponse.json({
      paragraph_length: 500,
      reader_interval: 3,
      enable_streaming: true
    });
  }
  
  try {
    const { data, error } = await supabase
      .from('settings')
      .select('*')
      .limit(1)
      .single();
    
    if (error || !data) {
      return NextResponse.json({
        paragraph_length: 500,
        reader_interval: 3,
        enable_streaming: true
      });
    }
    
    return NextResponse.json({
      paragraph_length: data.paragraph_length ?? 500,
      reader_interval: data.reader_interval ?? 3,
      enable_streaming: data.enable_streaming ?? true
    });
  } catch (error) {
    console.error('Error in GET /api/settings/generation:', error);
    return NextResponse.json({
      paragraph_length: 500,
      reader_interval: 3,
      enable_streaming: true
    });
  }
}

// PUT 请求处理
export async function PUT(request: NextRequest) {
  const supabase = getSupabase();
  
  if (!supabase) {
    return NextResponse.json({ message: '生成设置已更新（仅内存）' });
  }
  
  try {
    const body = await request.json();
    const updateData: any = {};
    
    if (body.paragraph_length !== undefined) updateData.paragraph_length = body.paragraph_length;
    if (body.reader_interval !== undefined) updateData.reader_interval = body.reader_interval;
    if (body.enable_streaming !== undefined) updateData.enable_streaming = body.enable_streaming;
    
    const { data: existing } = await supabase
      .from('settings')
      .select('id')
      .limit(1)
      .single();
    
    if (existing) {
      await supabase.from('settings').update(updateData).eq('id', existing.id);
    } else {
      await supabase.from('settings').insert(updateData);
    }
    
    return NextResponse.json({ message: '生成设置已更新' });
  } catch (error) {
    console.error('Error in PUT /api/settings/generation:', error);
    return NextResponse.json(
      { error: '更新失败' },
      { status: 500 }
    );
  }
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
