import { supabase } from '@/lib/supabase';
import type { Novel, Chapter, Agent, StoryAssetItem, NovelCategory, WorldBible } from '@/store/novelStore';

// 用户认证
export async function signUp(email: string, password: string) {
  const { data, error } = await supabase.auth.signUp({ email, password });
  if (error) throw error;
  return data;
}

export async function signIn(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
  return data;
}

export async function signOut() {
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}

export async function getCurrentUser() {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
}

// 小说相关操作
export async function getNovels() {
  const { data, error } = await supabase
    .from('novels')
    .select('*')
    .order('updated_at', { ascending: false });
  
  if (error) throw error;
  return data || [];
}

export async function createNovel(novel: Partial<Novel>) {
  const { data, error } = await supabase
    .from('novels')
    .insert([novel])
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

export async function updateNovel(id: string, updates: Partial<Novel>) {
  const { data, error } = await supabase
    .from('novels')
    .update(updates)
    .eq('id', id)
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

export async function deleteNovel(id: string) {
  const { error } = await supabase
    .from('novels')
    .delete()
    .eq('id', id);
  
  if (error) throw error;
}

// 章节相关操作
export async function getChapters(novelId: string) {
  const { data, error } = await supabase
    .from('chapters')
    .select('*')
    .eq('novel_id', novelId)
    .order('order_index', { ascending: true });
  
  if (error) throw error;
  return data || [];
}

export async function createChapter(chapter: Partial<Chapter>) {
  const { data, error } = await supabase
    .from('chapters')
    .insert([chapter])
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

export async function updateChapter(id: string, updates: Partial<Chapter>) {
  const { data, error } = await supabase
    .from('chapters')
    .update(updates)
    .eq('id', id)
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

export async function deleteChapter(id: string) {
  const { error } = await supabase
    .from('chapters')
    .delete()
    .eq('id', id);
  
  if (error) throw error;
}

// Agent 配置相关操作（适配优化后的数据库结构）
export async function getAgentConfigs() {
  const { data, error } = await supabase
    .from('agents')  // 表名从 agent_configs 改为 agents
    .select('*')
    .is('deleted_at', null)  // 过滤已删除的记录
    .order('created_at', { ascending: true });

  if (error) throw error;
  return data || [];
}

export async function updateAgentConfig(agentId: string, updates: Partial<Agent>) {
  const { data, error } = await supabase
    .from('agents')  // 表名从 agent_configs 改为 agents
    .update(updates)
    .eq('agent_id', agentId)
    .is('deleted_at', null)  // 只更新未删除的记录
    .select()
    .single();

  if (error) throw error;
  return data;
}

// 分类相关操作
export async function getCategories() {
  const { data, error } = await supabase
    .from('categories')
    .select('*')
    .order('created_at', { ascending: true });
  
  if (error) throw error;
  return data || [];
}

export async function createCategory(category: Partial<NovelCategory>) {
  const { data, error } = await supabase
    .from('categories')
    .insert([category])
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

export async function updateCategory(id: string, updates: Partial<NovelCategory>) {
  const { data, error } = await supabase
    .from('categories')
    .update(updates)
    .eq('id', id)
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

export async function deleteCategory(id: string) {
  const { error } = await supabase
    .from('categories')
    .delete()
    .eq('id', id);
  
  if (error) throw error;
}

// 世界设定相关操作
export async function getWorldBible(novelId: string) {
  const { data, error } = await supabase
    .from('world_bibles')
    .select('*')
    .eq('novel_id', novelId)
    .single();
  
  if (error && error.code !== 'PGRST116') throw error; // PGRST116 = no rows
  return data;
}

export async function upsertWorldBible(worldBible: Partial<WorldBible> & { novel_id: string }) {
  const { data, error } = await supabase
    .from('world_bibles')
    .upsert([worldBible])
    .select()
    .single();
  
  if (error) throw error;
  return data;
}

// 用户设置相关操作（适配优化后的数据库结构 - 使用 settings 表）
export async function getUserSettings() {
  const { data, error } = await supabase
    .from('settings')  // 表名从 user_settings 改为 settings
    .select('*')
    .is('deleted_at', null)  // 过滤已删除的记录
    .single();

  if (error && error.code !== 'PGRST116') throw error;
  return data;
}

export async function upsertUserSettings(settings: Record<string, unknown>) {
  const { data, error } = await supabase
    .from('settings')  // 表名从 user_settings 改为 settings
    .upsert([settings])
    .select()
    .single();

  if (error) throw error;
  return data;
}
