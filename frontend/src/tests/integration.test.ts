/**
 * 前端集成测试
 * 测试前端与后端的集成是否正常
 */

import { supabase } from '../lib/supabase';

const TEST_USER_ID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';

interface TestResult {
  name: string;
  passed: boolean;
  message?: string;
}

class IntegrationTester {
  private results: TestResult[] = [];

  private log(name: string, passed: boolean, message?: string) {
    this.results.push({ name, passed, message });
    const status = passed ? '✅' : '❌';
    console.log(`${status} ${name}`, message || '');
  }

  async runAllTests() {
    console.log('🧪 开始运行集成测试...\n');

    await this.testTableStructure();
    await this.testSoftDelete();
    await this.testAgentsCRUD();
    await this.testAssetsCRUD();
    await this.testSettingsCRUD();
    await this.testDataMigration();

    this.printReport();
  }

  // ==================== 表结构测试 ====================

  async testTableStructure() {
    console.log('\n📋 表结构检查');
    console.log('─'.repeat(50));

    const tables = ['agents', 'assets', 'settings', 'messages'];
    
    for (const table of tables) {
      try {
        const { error } = await supabase
          .from(table)
          .select('count', { count: 'exact', head: true });
        
        this.log(`表存在: ${table}`, !error, error?.message);
      } catch (e) {
        this.log(`表存在: ${table}`, false, String(e));
      }
    }
  }

  // ==================== 软删除测试 ====================

  async testSoftDelete() {
    console.log('\n🗑️  软删除功能检查');
    console.log('─'.repeat(50));

    const tables = ['agents', 'assets', 'settings'];
    
    for (const table of tables) {
      try {
        const { error } = await supabase
          .from(table)
          .select('*')
          .is('deleted_at', null)
          .limit(1);
        
        this.log(`软删除查询: ${table}`, !error, error?.message);
      } catch (e) {
        this.log(`软删除查询: ${table}`, false, String(e));
      }
    }
  }

  // ==================== CRUD 测试 ====================

  async testAgentsCRUD() {
    console.log('\n🤖 Agents CRUD 测试');
    console.log('─'.repeat(50));

    try {
      // Create
      const { data: created, error: createError } = await supabase
        .from('agents')
        .insert({
          user_id: TEST_USER_ID,
          agent_id: `test-agent-${Date.now()}`,
          name: '测试Agent',
          role: 'writer',
          prompt: '你是一个测试Agent',
          temperature: 0.7,
          enabled: true,
          personality: 'creative'
        })
        .select()
        .single();

      if (createError || !created) {
        this.log('Agent 创建', false, createError?.message);
        return;
      }
      this.log('Agent 创建', true, `ID: ${created.id}`);

      // Read
      const { data: read, error: readError } = await supabase
        .from('agents')
        .select('*')
        .eq('id', created.id)
        .single();

      this.log('Agent 读取', !readError && !!read, readError?.message);

      // Update
      const { data: updated, error: updateError } = await supabase
        .from('agents')
        .update({ name: '更新的测试Agent' })
        .eq('id', created.id)
        .select()
        .single();

      this.log('Agent 更新', !updateError && updated?.name === '更新的测试Agent', updateError?.message);

      // Soft Delete
      const { error: deleteError } = await supabase
        .from('agents')
        .update({ deleted_at: new Date().toISOString() })
        .eq('id', created.id);

      this.log('Agent 软删除', !deleteError, deleteError?.message);

      // Verify soft delete
      const { data: afterDelete } = await supabase
        .from('agents')
        .select('*')
        .eq('id', created.id)
        .is('deleted_at', null)
        .single();

      this.log('软删除验证', !afterDelete, '已删除记录被正确过滤');

    } catch (e) {
      this.log('Agents CRUD', false, String(e));
    }
  }

  async testAssetsCRUD() {
    console.log('\n📦 Assets CRUD 测试');
    console.log('─'.repeat(50));

    try {
      // Create local asset
      const { data: localAsset, error: localError } = await supabase
        .from('assets')
        .insert({
          user_id: TEST_USER_ID,
          type: 'characters',
          name: '测试角色',
          content: { description: '这是一个测试角色' },
          is_global: false,
          color: '#ff0000'
        })
        .select()
        .single();

      this.log('本地 Asset 创建', !localError && !!localAsset, localError?.message);

      // Create global asset
      const { data: globalAsset, error: globalError } = await supabase
        .from('assets')
        .insert({
          user_id: TEST_USER_ID,
          type: 'worldbuilding',
          name: '测试世界观',
          description: '这是一个测试世界观',
          is_global: true,
          is_starred: true,
          color: '#00ff00'
        })
        .select()
        .single();

      this.log('全局 Asset 创建', !globalError && !!globalAsset, globalError?.message);

      // Query by type
      const { data: byType, error: typeError } = await supabase
        .from('assets')
        .select('*')
        .eq('type', 'characters')
        .is('deleted_at', null);

      this.log('按类型查询', !typeError, `找到 ${byType?.length || 0} 个角色`);

      // Query global
      const { data: global, error: globalQueryError } = await supabase
        .from('assets')
        .select('*')
        .eq('is_global', true)
        .is('deleted_at', null);

      this.log('全局 Asset 查询', !globalQueryError, `找到 ${global?.length || 0} 个全局资产`);

      // Cleanup
      if (localAsset) {
        await supabase
          .from('assets')
          .update({ deleted_at: new Date().toISOString() })
          .eq('id', localAsset.id);
      }
      if (globalAsset) {
        await supabase
          .from('assets')
          .update({ deleted_at: new Date().toISOString() })
          .eq('id', globalAsset.id);
      }

    } catch (e) {
      this.log('Assets CRUD', false, String(e));
    }
  }

  async testSettingsCRUD() {
    console.log('\n⚙️ Settings CRUD 测试');
    console.log('─'.repeat(50));

    try {
      // Create
      const { data: created, error: createError } = await supabase
        .from('settings')
        .insert({
          user_id: TEST_USER_ID,
          token_enabled: true,
          token_daily_limit: 100000,
          discussion_max_rounds: 3,
          constraints: ['禁止暴力', '禁止色情'],
          writing_mode: 'auto'
        })
        .select()
        .single();

      if (createError) {
        // 可能已经存在，尝试更新
        const { data: updated, error: updateError } = await supabase
          .from('settings')
          .update({ token_daily_limit: 150000 })
          .eq('user_id', TEST_USER_ID)
          .select()
          .single();

        this.log('Settings 更新', !updateError && updated?.token_daily_limit === 150000, updateError?.message);
      } else {
        this.log('Settings 创建', true, `ID: ${created.id}`);
      }

    } catch (e) {
      this.log('Settings CRUD', false, String(e));
    }
  }

  // ==================== 数据迁移验证 ====================

  async testDataMigration() {
    console.log('\n📊 数据迁移验证');
    console.log('─'.repeat(50));

    const tables = [
      { name: 'agents', minCount: 0 },
      { name: 'assets', minCount: 0 },
      { name: 'settings', minCount: 0 }
    ];

    for (const { name, minCount } of tables) {
      try {
        const { count, error } = await supabase
          .from(name)
          .select('*', { count: 'exact', head: true })
          .is('deleted_at', null);

        const actualCount = count || 0;
        this.log(
          `${name} 数据迁移`,
          !error && actualCount >= minCount,
          `记录数: ${actualCount}`
        );
      } catch (e) {
        this.log(`${name} 数据迁移`, false, String(e));
      }
    }
  }

  // ==================== 报告 ====================

  printReport() {
    console.log('\n' + '='.repeat(50));
    console.log('📈 测试报告');
    console.log('='.repeat(50));

    const total = this.results.length;
    const passed = this.results.filter(r => r.passed).length;
    const failed = total - passed;

    console.log(`\n总测试数: ${total}`);
    console.log(`✅ 通过: ${passed}`);
    console.log(`❌ 失败: ${failed}`);
    console.log(`通过率: ${total > 0 ? (passed / total * 100).toFixed(1) : 0}%`);

    if (failed > 0) {
      console.log('\n失败的测试:');
      this.results
        .filter(r => !r.passed)
        .forEach(r => {
          console.log(`  ❌ ${r.name}`);
          if (r.message) console.log(`     ${r.message}`);
        });
    }

    console.log('\n' + '='.repeat(50));
    if (failed === 0) {
      console.log('🎉 所有测试通过！');
    } else {
      console.log('⚠️ 部分测试失败，请检查问题。');
    }
    console.log('='.repeat(50));
  }
}

// 导出测试器
export const integrationTester = new IntegrationTester();

// 如果在浏览器环境中运行，自动执行测试
if (typeof window !== 'undefined') {
  // @ts-ignore
  window.runIntegrationTests = () => integrationTester.runAllTests();
  console.log('集成测试已加载。在控制台运行 runIntegrationTests() 开始测试。');
}
