/**
 * AI Config API Route
 * 处理 /api/settings/ai 请求
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
      chat_model: '',
      api_key: '',
      base_url: '',
      is_active: false
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
        chat_model: '',
        api_key: '',
        base_url: '',
        is_active: false
      });
    }
    
    return NextResponse.json({
      chat_model: data.chat_model ?? '',
      api_key: data.api_key ?? '',
      base_url: data.base_url ?? '',
      is_active: data.is_active ?? false
    });
  } catch (error) {
    console.error('Error in GET /api/settings/ai:', error);
    return NextResponse.json({
      chat_model: '',
      api_key: '',
      base_url: '',
      is_active: false
    });
  }
}

// PUT 请求处理
export async function PUT(request: NextRequest) {
  const supabase = getSupabase();
  
  if (!supabase) {
    return NextResponse.json({ message: 'AI 配置已更新（仅内存）' });
  }
  
  try {
    const body = await request.json();
    const updateData: any = {};
    
    if (body.chat_model !== undefined) updateData.chat_model = body.chat_model;
    if (body.api_key !== undefined) updateData.api_key = body.api_key;
    if (body.base_url !== undefined) updateData.base_url = body.base_url;
    if (body.is_active !== undefined) updateData.is_active = body.is_active;
    
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
    
    return NextResponse.json({ message: 'AI 配置已更新' });
  } catch (error) {
    console.error('Error in PUT /api/settings/ai:', error);
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
