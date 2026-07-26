import React, { useState, useEffect, useRef, useCallback } from 'react'

/**
 * ================================================================
 * React 主组件 — AI原生产品设计工作流前端
 * ================================================================
 * 负责人: 于金永
 * 技术栈: React 18 + Vite + Tailwind CSS
 *
 * 页面结构:
 *   <Header />          — 标题 + 简介
 *   <ConfigPanel />     — 产品选择 + 平台勾选 + Key输入 + 开始按钮
 *   <AgentDashboard />  — 4张Agent卡片 + 进度条
 *   <ResultPanel />     — 报告显示
 *
 * 状态机: idle → running → done/error
 * ================================================================
 */

// ── 配置常量 ──
const AGENT_INFO = {
  super_brain:      { name: '超级智囊',   emoji: '🔍', color: 'blue' },
  user_avatar:      { name: '用户替身',   emoji: '👤', color: 'purple' },
  competitor_scout: { name: '竞品侦察兵', emoji: '🕵️', color: 'amber' },
  industry_expert:  { name: '行业专家',   emoji: '🧠', color: 'emerald' },
}

const AGENT_PHASE_MAP = {
  super_brain:      'Phase1',
  competitor_scout: 'Phase1',
  user_avatar:      'Phase2',
  industry_expert:  'Phase2',
}

// ── 帮助函数 ──
const statusBadge = (status) => {
  const m = {
    waiting: ['bg-gray-100 text-gray-500', '⏳ 等待中'],
    running: ['bg-blue-100 text-blue-700 animate-pulse', '⏳ 分析中...'],
    done:    ['bg-green-100 text-green-700', '✅ 已完成'],
    error:   ['bg-red-100 text-red-700', '❌ 出错'],
  }
  const [cls, label] = m[status] || m.waiting
  return { cls, label }
}

// ── Header ──
function Header() {
  return (
    <header className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-lg">
      <div className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">🎧</span>
          <h1 className="text-2xl font-bold">AI原生产品设计工作流</h1>
        </div>
        <p className="text-blue-100 text-sm ml-1">
          为 Soundcore Liberty 系列打造的智能洞察引擎 — 输入产品名，自动爬取多平台评价，4个AI Agent 协作分析，生成产品洞察报告
        </p>
      </div>
    </header>
  )
}

// ── 预设产品选择 / API Key 输入 / 平台勾选 ──
function ConfigPanel({ onStart, pipelineState }) {
  const [product, setProduct] = useState('Soundcore Liberty 5 Pro Max')
  const [customProduct, setCustomProduct] = useState('')
  const [platforms, setPlatforms] = useState(['reddit', 'amazon', 'bilibili', 'jd'])
  const [apiKey, setApiKey] = useState('')
  const [presets, setPresets] = useState([])
  const [availablePlatforms, setAvailablePlatforms] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/preset-products')
      .then(r => r.json())
      .then(d => {
        setPresets(d.products || [])
        setAvailablePlatforms(Object.entries(d.platforms || {}).map(([k, v]) => ({ key: k, ...v })))
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const selectPreset = (p) => { setProduct(p); setCustomProduct('') }
  const togglePlatform = (k) => {
    setPlatforms(prev =>
      prev.includes(k) ? prev.filter(x => x !== k) : [...prev, k]
    )
  }

  const canStart = pipelineState === 'idle' || pipelineState === 'done' || pipelineState === 'error'

  const handleStart = () => {
    if (!canStart) return
    const finalProduct = customProduct.trim() || product
    if (!finalProduct) return alert('请选择或输入产品名称')
    if (platforms.length === 0) return alert('请至少选择一个平台')
    onStart({ product: finalProduct, platforms, api_key: apiKey })
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">⚙️ 分析配置</h2>

      {/* 预设产品 */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-600 mb-2">选择产品</label>
        <div className="flex flex-wrap gap-2">
          {presets.map(p => (
            <button key={p}
              onClick={() => selectPreset(p)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                product === p && !customProduct
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >{p}</button>
          ))}
        </div>
        <input type="text"
          placeholder="或自定义产品名..."
          value={customProduct}
          onChange={e => { setCustomProduct(e.target.value); setProduct(e.target.value ? '' : presets[0]) }}
          className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </div>

      {/* 平台勾选 */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-600 mb-2">数据平台</label>
        <div className="flex flex-wrap gap-3">
          {availablePlatforms.map(p => (
            <label key={p.key} className="flex items-center gap-1.5 cursor-pointer text-sm">
              <input type="checkbox"
                checked={platforms.includes(p.key)}
                onChange={() => togglePlatform(p.key)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-400"
              />
              <span className="text-gray-700">{p.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* API Key */}
      <div className="mb-5">
        <label className="block text-sm font-medium text-gray-600 mb-1">DeepSeek API Key</label>
        <input type="password"
          placeholder="留空将使用服务器环境变量中的配置（若有）"
          value={apiKey}
          onChange={e => setApiKey(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <p className="text-xs text-gray-400 mt-0.5">
          可在 https://platform.deepseek.com/ 获取
        </p>
      </div>

      <button onClick={handleStart}
        disabled={!canStart}
        className={`w-full py-2.5 rounded-lg font-medium transition-all text-sm ${
          canStart
            ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm active:scale-[0.98]'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
        }`}
      >
        {canStart ? '🚀 开始分析' : pipelineState === 'running' ? '⏳ 分析进行中...' : '⏳ 请等待...'}
      </button>
    </div>
  )
}

// ── Agent 卡片 ──
function AgentCard({ agentKey, info, agentState }) {
  const { cls, label } = statusBadge(agentState?.status || 'waiting')
  const running = agentState?.status === 'running'

  return (
    <div className={`bg-white rounded-xl shadow-sm border p-5 transition-all ${
      running ? 'border-blue-300 ring-2 ring-blue-100' : 'border-gray-200'
    }`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{info.emoji}</span>
          <span className="font-semibold text-gray-800">{info.name}</span>
        </div>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>{label}</span>
      </div>
      <p className="text-xs text-gray-400">
        {AGENT_PHASE_MAP[agentKey] === 'Phase1' ? 'Phase 1（并行）' : 'Phase 2（并行）'}
      </p>
    </div>
  )
}

// ── Agent 仪表盘（4张卡片 + 进度条）──
function AgentDashboard({ agents, progress, pipelineState, message }) {
  const running = pipelineState === 'running'

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">📊 分析进度</h2>

      {/* 进度条 */}
      <div className="mb-5">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>{message || '等待开始...'}</span>
          <span>{Math.round(progress * 100)}%</span>
        </div>
        <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all duration-500 ${
            running ? 'bg-gradient-to-r from-blue-500 to-indigo-500' : 'bg-gray-300'
          }`}
            style={{ width: `${Math.round(progress * 100)}%` }}
          />
        </div>
      </div>

      {/* 4张 Agent 卡片 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {Object.entries(AGENT_INFO).map(([key, info]) => (
          <AgentCard key={key} agentKey={key} info={info} agentState={agents?.[key]} />
        ))}
      </div>
    </div>
  )
}

// ── 报告展示（Markdown渲染）──
function ResultPanel({ reportContent, pipelineState, stats, onReset }) {
  if (pipelineState !== 'done' || !reportContent) return null

  const lines = reportContent.split('\n')
  const total = stats?.total ?? 0

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">📄 产品洞察报告</h2>
        <div className="flex gap-2">
          <span className="text-xs text-gray-400 self-center">{total} 条评价分析</span>
          <button onClick={onReset}
            className="px-4 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >🔄 重新分析</button>
        </div>
      </div>

      <div className="border border-gray-200 rounded-lg p-5 bg-gray-50/50 max-h-[70vh] overflow-y-auto">
        {lines.map((line, i) => {
          // 基础 Markdown 渲染（支持标题、列表、分隔线、引用、表格）
          if (line.startsWith('# ')) return <h1 key={i} className="text-xl font-bold text-gray-900 mt-4 mb-2">{line.slice(2)}</h1>
          if (line.startsWith('## ')) return <h2 key={i} className="text-lg font-semibold text-gray-800 mt-5 mb-2">{line.slice(3)}</h2>
          if (line.startsWith('### ')) return <h3 key={i} className="text-base font-semibold text-gray-700 mt-4 mb-1">{line.slice(4)}</h3>
          if (line.startsWith('---')) return <hr key={i} className="my-4 border-gray-200" />
          if (line.startsWith('> ')) return <blockquote key={i} className="border-l-4 border-blue-300 pl-3 py-1 my-1 text-sm text-gray-600 italic bg-blue-50/50 rounded-r">{line.slice(2)}</blockquote>
          if (line.startsWith('| ')) return <p key={i} className="text-sm text-gray-700 font-mono">{line}</p>
          if (line.startsWith('- ') || line.startsWith('* ')) return <li key={i} className="ml-4 text-sm text-gray-700 list-disc">{line.slice(2)}</li>
          if (line.trim() === '') return <div key={i} className="h-2" />
          return <p key={i} className="text-sm text-gray-700 my-1 leading-relaxed">{line}</p>
        })}
      </div>
    </div>
  )
}

// ── 错误提示 ──
function ErrorPanel({ message, onReset }) {
  if (!message) return null
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">❌</span>
        <span className="font-semibold text-red-800">分析出错</span>
      </div>
      <p className="text-sm text-red-600 ml-7 mb-3">{message}</p>
      <button onClick={onReset}
        className="ml-7 px-4 py-1.5 text-sm bg-white border border-red-200 text-red-700 rounded-lg hover:bg-red-50 transition-colors"
      >🔄 重新尝试</button>
    </div>
  )
}

// ═══════════════════════════════════════════════
// App 主组件
// ═══════════════════════════════════════════════

export default function App() {
  const [pipelineState, setPipelineState] = useState('idle') // idle | running | done | error
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState('')
  const [agents, setAgents] = useState(null)
  const [stats, setStats] = useState(null)
  const [reportContent, setReportContent] = useState('')
  const wsRef = useRef(null)
  const pollingRef = useRef(null)

  const reset = useCallback(() => {
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null }
    if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null }
    setPipelineState('idle'); setProgress(0); setMessage(''); setAgents(null)
    setStats(null); setReportContent('')
  }, [])

  const connectWS = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/progress`
    try {
      const ws = new WebSocket(wsUrl)
      ws.onopen = () => console.log('WS 已连接')
      ws.onmessage = (ev) => {
        try {
          const d = JSON.parse(ev.data)
          if (d.state) setPipelineState(d.state)
          if (d.progress !== undefined) setProgress(d.progress)
          if (d.message) setMessage(d.message)
          if (d.agents) setAgents(d.agents)
          if (d.stats) setStats(d.stats)
        } catch (e) {}
      }
      ws.onclose = () => { wsRef.current = null }
      ws.onerror = () => { ws.close() }
      wsRef.current = ws
    } catch (e) {}
  }, [])

  // 轮询 fallback（WS 连接失败时）
  const startPolling = useCallback(() => {
    const poll = () => {
      fetch('/api/status')
        .then(r => r.json())
        .then(d => {
          if (d.state) setPipelineState(d.state)
          if (d.progress !== undefined) setProgress(d.progress)
          if (d.message) setMessage(d.message)
          if (d.agents) setAgents(d.agents)
          if (d.stats) setStats(d.stats)
          if (d.state === 'done' || d.state === 'error') {
            clearInterval(pollingRef.current)
            pollingRef.current = null
            // 拿到报告内容
            if (d.state === 'done' && d.report_path) {
              const reportName = d.report_path.split(/[/\\]/).pop()
              fetch(`/api/report/${encodeURIComponent(reportName)}`)
                .then(r => r.json())
                .then(rd => { if (rd.content) setReportContent(rd.content) })
                .catch(() => {})
            }
          }
        })
        .catch(() => {})
    }
    poll()
    pollingRef.current = setInterval(poll, 1500)
  }, [])

  // 停止轮询
  const stopPolling = useCallback(() => {
    if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null }
  }, [])

  const handleStart = useCallback(async (config) => {
    reset()
    setPipelineState('running')
    // 先尝试 WS 连接
    connectWS()
    // 同时启动 HTTP 轮询作为备用
    startPolling()
    try {
      const resp = await fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      if (!resp.ok) {
        const err = await resp.json()
        setPipelineState('error')
        setMessage(err.detail || '启动失败')
        stopPolling()
      }
    } catch (e) {
      setPipelineState('error')
      setMessage('网络错误：无法连接后端服务')
      stopPolling()
    }
  }, [reset, connectWS, startPolling, stopPolling])

  // 完成时获取报告
  useEffect(() => {
    if (pipelineState === 'done' && !reportContent) {
      fetch('/api/status')
        .then(r => r.json())
        .then(d => {
          if (d.report_path) {
            const reportName = d.report_path.split(/[/\\]/).pop()
            fetch(`/api/report/${encodeURIComponent(reportName)}`)
              .then(r => r.json())
              .then(rd => { if (rd.content) setReportContent(rd.content) })
              .catch(() => {})
          }
        })
        .catch(() => {})
    }
  }, [pipelineState, reportContent])

  return (
    <div className="min-h-screen bg-gray-50 pb-10">
      <Header />
      <main className="max-w-4xl mx-auto px-4 mt-6 space-y-5">
        <ConfigPanel onStart={handleStart} pipelineState={pipelineState} />
        <AgentDashboard agents={agents} progress={progress} pipelineState={pipelineState} message={message} />
        <ErrorPanel message={pipelineState === 'error' ? message : null} onReset={reset} />
        <ResultPanel reportContent={reportContent} pipelineState={pipelineState} stats={stats} onReset={reset} />
      </main>
    </div>
  )
}
