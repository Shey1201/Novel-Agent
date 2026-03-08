import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// 在测试环境中使用 mock 客户端
const isTestEnvironment = process.env.NODE_ENV === 'test' || process.env.JEST_WORKER_ID !== undefined;

if (!isTestEnvironment && (!supabaseUrl || !supabaseAnonKey)) {
  throw new Error('Missing Supabase environment variables');
}

// 创建 mock 客户端用于测试
const createMockClient = () => {
  return {
    from: () => ({
      select: () => ({ data: [], error: null }),
      insert: () => ({ error: null }),
      update: () => ({ error: null }),
      delete: () => ({ error: null }),
      upsert: () => ({ error: null }),
      eq: () => ({ data: [], error: null }),
      neq: () => ({ data: [], error: null }),
      single: () => ({ data: null, error: null }),
    }),
    auth: {
      getUser: () => Promise.resolve({ data: { user: null }, error: null }),
      signInWithPassword: () => Promise.resolve({ data: null, error: null }),
      signUp: () => Promise.resolve({ data: null, error: null }),
      signOut: () => Promise.resolve({ error: null }),
      onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
    },
  } as any;
};

export const supabase = isTestEnvironment 
  ? createMockClient() 
  : createClient(supabaseUrl!, supabaseAnonKey!);
