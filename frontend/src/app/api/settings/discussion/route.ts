/**
 * Discussion Settings API Route
 * 处理 /api/settings/discussion 请求
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
      max_rounds: 2,
      max_tokens_per_response: 80,
      enable_short_mode: true
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
        max_rounds: 2,
        max_tokens_per_response: 80,
        enable_short_mode: true
      });
    }
    
    return NextResponse.json({
      max_rounds: data.discussion_max_rounds ?? 2,
      max_tokens_per_response: data.discussion_max_tokens ?? 80,
      enable_short_mode: data.discussion_enable_short_mode ?? true
    });
  } catch (error) {
    console.error('Error in GET /api/settings/discussion:', error);
    return NextResponse.json({
      max_rounds: 2,
      max_tokens_per_response: 80,
      enable_short_mode: true
    });
  }
}

// PUT 请求处理
export async function PUT(request: NextRequest) {
  const supabase = getSupabase();
  
  if (!supabase) {
    return NextResponse.json({ message: '讨论设置已更新（仅内存）' });
  }
  
  try {
    const body = await request.json();
    const updateData: any = {};
    
    if (body.max_rounds !== undefined) updateData.discussion_max_rounds = body.max_rounds;
    if (body.max_tokens_per_response !== undefined) updateData.discussion_max_tokens = body.max_tokens_per_response;
    if (body.enable_short_mode !== undefined) updateData.discussion_enable_short_mode = body.enable_short_mode;
    
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
    
    return NextResponse.json({ message: '讨论设置已更新' });
  } catch (error) {
    console.error('Error in PUT /api/settings/discussion:', error);
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
