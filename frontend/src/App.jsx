/**
 * ================================================================
 * React 主组件 — AI原生产品设计工作流前端
 * ================================================================
 * 负责人: 同学
 * 技术栈: React 18 + Vite + Tailwind CSS + shadcn/ui
 *
 * 页面结构:
 *   <Header />          — 标题 + 简介
 *   <ConfigPanel />     — 产品选择 + 平台勾选 + Key输入 + 开始按钮
 *   <AgentDashboard />  — 4张Agent卡片 + 进度条
 *   <ResultPanel />     — 下载按钮 + 报告预览
 *
 * 状态机: idle → running → done → (点重新分析) → idle
 *
 * TODO: 此文件为骨架，具体UI逻辑待实现
 * ================================================================
 */

import React from 'react';

function App() {
  // ── 状态管理 ──
  // TODO: 用 React Context + useReducer 管理以下状态：
  //   - pipelineState: "idle" | "running" | "done"
  //   - progress: 0.0 ~ 1.0
  //   - agents: { super_brain: {status, text}, user_avatar: {...}, ... }
  //   - reportPath: string | null
  //   - stats: { total, platforms, avgRating } | null

  return (
    <div className="min-h-screen bg-gray-50">
      {/*
        TODO: 实现以下组件

        <Header />
        <ConfigPanel />
        <AgentDashboard />
        <ResultPanel />
        <Footer />
      */}
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-400 text-xl">
          🎧 AI原生产品设计工作流 — 前端待实现
        </p>
      </div>
    </div>
  );
}

export default App;
