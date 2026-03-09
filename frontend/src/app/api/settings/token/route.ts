/**
 * Token Settings API Route
 * 处理 /api/settings/token 请求
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
      enabled: false,
      daily_limit: 50000,
      warning_threshold: 0.8,
      budget_allocation: {
        planner: 0.10,
        discussion: 0.13,
        conflict: 0.07,
        writing: 0.47,
        editor: 0.13,
        reader: 0.07,
        summary: 0.03,
      }
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
        enabled: false,
        daily_limit: 50000,
        warning_threshold: 0.8,
        budget_allocation: {
          planner: 0.10,
          discussion: 0.13,
          conflict: 0.07,
          writing: 0.47,
          editor: 0.13,
          reader: 0.07,
          summary: 0.03,
        }
      });
    }
    
    return NextResponse.json({
      enabled: data.token_enabled ?? false,
      daily_limit: data.token_daily_limit ?? 50000,
      warning_threshold: data.token_warning_threshold ?? 0.8,
      budget_allocation: data.token_budget_allocation ?? {
        planner: 0.10,
        discussion: 0.13,
        conflict: 0.07,
        writing: 0.47,
        editor: 0.13,
        reader: 0.07,
        summary: 0.03,
      }
    });
  } catch (error) {
    console.error('Error in GET /api/settings/token:', error);
    return NextResponse.json({
      enabled: false,
      daily_limit: 50000,
      warning_threshold: 0.8,
      budget_allocation: {
        planner: 0.10,
        discussion: 0.13,
        conflict: 0.07,
        writing: 0.47,
        editor: 0.13,
        reader: 0.07,
        summary: 0.03,
      }
    });
  }
}

// PUT 请求处理
export async function PUT(request: NextRequest) {
  const supabase = getSupabase();
  
  if (!supabase) {
    return NextResponse.json({ message: 'Token 设置已更新（仅内存）' });
  }
  
  try {
    const body = await request.json();
    const updateData: any = {};
    
    if (body.enabled !== undefined) updateData.token_enabled = body.enabled;
    if (body.daily_limit !== undefined) updateData.token_daily_limit = body.daily_limit;
    if (body.warning_threshold !== undefined) updateData.token_warning_threshold = body.warning_threshold;
    if (body.budget_allocation !== undefined) updateData.token_budget_allocation = body.budget_allocation;
    
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
    
    return NextResponse.json({ message: 'Token 设置已更新' });
  } catch (error) {
    console.error('Error in PUT /api/settings/token:', error);
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
