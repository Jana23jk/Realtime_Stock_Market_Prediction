import { useState, useEffect, useRef, useCallback } from 'react'
import axios from 'axios'
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import { LayoutDashboard, TrendingUp, TrendingDown, Briefcase, Newspaper,
         LogOut, Search, AlertCircle, RefreshCw, Activity, BarChart3, Zap,
         Plus, Trash2, Edit2, Check, X, Star, BookmarkPlus } from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
const api = axios.create({ baseURL: API_BASE, timeout: 120000 })

// Auth helper — attach JWT to every request
const authApi = (token) => axios.create({
  baseURL: API_BASE, timeout: 120000,
  headers: { Authorization: `Bearer ${token}` }
})

const ALL_NSE_STOCKS = [
  'RELIANCE','TCS','INFY','HDFCBANK','SBIN','WIPRO','ICICIBANK',
  'ADANIENT','TATAMOTORS','ZOMATO','BAJFINANCE','KOTAKBANK','AXISBANK',
  'SUNPHARMA','MARUTI','ASIANPAINT','TATASTEEL','LTIM','HINDUNILVR','ONGC'
]
const NAMES = {
  RELIANCE:'Reliance Industries', TCS:'Tata Consultancy', INFY:'Infosys Ltd',
  HDFCBANK:'HDFC Bank', SBIN:'State Bank of India', WIPRO:'Wipro Ltd',
  ICICIBANK:'ICICI Bank', ADANIENT:'Adani Enterprises', TATAMOTORS:'Tata Motors',
  ZOMATO:'Zomato Ltd', BAJFINANCE:'Bajaj Finance', KOTAKBANK:'Kotak Mahindra',
  AXISBANK:'Axis Bank', SUNPHARMA:'Sun Pharma', MARUTI:'Maruti Suzuki',
  ASIANPAINT:'Asian Paints', TATASTEEL:'Tata Steel', LTIM:'LTI Mindtree',
  HINDUNILVR:'HUL', ONGC:'ONGC Ltd'
}
const DURATIONS = ['1D','1W','1M','1Y']
const DUR_PERIOD = { '1D':'1d','1W':'5d','1M':'1mo','1Y':'1y' }

/* ── Helpers ── */
function Sk({ w='100%', h=16, r=6 }) {
  return <div className="sk" style={{ width:w, height:h, borderRadius:r }}/>
}
function Tip({ active, payload, label }) {
  if (!active||!payload?.length) return null
  return (
    <div style={{ background:'#1b2340',border:'1px solid rgba(255,255,255,.1)',borderRadius:9,padding:'9px 13px' }}>
      <div style={{ fontSize:'.68rem',color:'#8b95a9',marginBottom:3 }}>{label}</div>
      <div style={{ fontFamily:'JetBrains Mono,monospace',fontWeight:700,color:'#00d4aa',fontSize:'.9rem' }}>
        ₹{payload[0].value?.toLocaleString('en-IN')}
      </div>
    </div>
  )
}

/* ════════════════════════════════════════
   LOGIN / REGISTER
════════════════════════════════════════ */
function AuthPage({ onLogin }) {
  const [mode,  setMode]  = useState('login')   // login | register | reset
  const [name,  setName]  = useState('')
  const [email, setEmail] = useState('')
  const [pass,  setPass]  = useState('')
  const [err,   setErr]   = useState('')
  const [msg,   setMsg]   = useState('')
  const [busy,  setBusy]  = useState(false)

  const submit = async () => {
    if (!email||!pass||(mode==='register'&&!name)) { setErr('Please fill all fields.'); setMsg(''); return }
    setBusy(true); setErr(''); setMsg('')
    try {
      if (mode === 'reset') {
        const res = await api.post('/auth/reset-password', { email, new_password:pass })
        if (res.data.error) { setErr(res.data.error); setBusy(false); return }
        setMsg('Password reset successfully. You can now sign in.')
        setMode('login')
        setPass('')
        setBusy(false)
        return
      }

      const endpoint = mode==='login' ? '/auth/login' : '/auth/register'
      const payload  = mode==='login' ? { email, password:pass } : { name, email, password:pass }
      const res = await api.post(endpoint, payload)
      if (res.data.error) { setErr(res.data.error); setBusy(false); return }
      // Save token to localStorage for session persistence
      localStorage.setItem('stockai_token', res.data.token)
      localStorage.setItem('stockai_user',  JSON.stringify(res.data.user))
      onLogin(res.data.user, res.data.token)
    } catch(e) {
      setErr('Server error. Make sure backend is running.')
      setBusy(false)
    }
  }

  const demoLogin = async () => {
    setEmail('demo@stockai.in'); setPass('demo123'); setBusy(true); setErr(''); setMsg('')
    try {
      const res = await api.post('/auth/login', { email:'demo@stockai.in', password:'demo123' })
      if (res.data.error) { setErr(res.data.error); setBusy(false); return }
      localStorage.setItem('stockai_token', res.data.token)
      localStorage.setItem('stockai_user',  JSON.stringify(res.data.user))
      onLogin(res.data.user, res.data.token)
    } catch { setErr('Backend not running.'); setBusy(false) }
  }

  return (
    <div className="login-page">
      <div className="orb orb1"/><div className="orb orb2"/>
      <div className="login-card fade-up">
        <div className="login-brand">
          <div className="login-brand-icon">📈</div>
          <div>
            <div className="landing-logo-text" style={{ fontSize:'1.3rem' }}>BULL<span>SENSE</span></div>
            <div className="login-brand-tag" style={{ marginTop:2 }}>NSE AI Analytics</div>
          </div>
        </div>

        {/* Tab switcher */}
        <div style={{ display:'flex', background:'rgba(0,0,0,0.2)', borderRadius:10, padding:3, marginBottom:24, border:'1px solid rgba(255,255,255,0.05)' }}>
          {['login','register'].map(m => (
            <button key={m} onClick={()=>{setMode(m);setErr('');setMsg('')}}
              style={{ flex:1, padding:'8px', border:'none', borderRadius:8, cursor:'pointer',
                fontFamily:'Sora,sans-serif', fontSize:'.82rem', fontWeight:600, transition:'all .2s',
                background:mode===m?'#00d4aa':'transparent', color:mode===m?'#0b0a1c':'#8b95a9' }}>
              {m==='login'?'Sign In':'Create Account'}
            </button>
          ))}
        </div>

        <div className="login-h1">{mode==='login'?'Welcome back':mode==='register'?'Get started':'Reset Password'}</div>
        <div className="login-sub">{mode==='login'?'Sign in to your trading dashboard':mode==='register'?'Create your free account':'Enter your new password below'}</div>

        {mode==='register' && <>
          <label className="f-label">Full Name</label>
          <input className="f-input" placeholder="Arjun Sharma" value={name}
            onChange={e=>setName(e.target.value)} onKeyDown={e=>e.key==='Enter'&&submit()}/>
        </>}
        <label className="f-label">Email</label>
        <input className="f-input" type="email" placeholder="you@example.com" value={email}
          onChange={e=>setEmail(e.target.value)} onKeyDown={e=>e.key==='Enter'&&submit()}/>
        <label className="f-label">{mode === 'reset' ? 'New Password' : 'Password'}</label>
        <input className="f-input" type="password" placeholder="••••••••" value={pass}
          onChange={e=>setPass(e.target.value)} onKeyDown={e=>e.key==='Enter'&&submit()}/>

        {err && <div className="f-error">{err}</div>}
        {msg && <div style={{fontSize:'.78rem', color:'#00d4aa', marginBottom:12, fontWeight:600}}>{msg}</div>}
        
        <button className="btn-primary" onClick={submit} disabled={busy}>
          {busy ? <span className="spinner" style={{ width:14,height:14,margin:'0 auto',display:'block' }}/> : mode==='login'?'Sign In':mode==='register'?'Create Account':'Reset Password'}
        </button>

        {mode==='login' && <>
          <div style={{ textAlign:'right', marginTop:10, marginBottom:10 }}>
            <span style={{ fontSize:'.75rem', color:'#00d4aa', cursor:'pointer' }} onClick={()=>{setMode('reset');setErr('');setMsg('')}}>Forgot Password?</span>
          </div>
        </>}
        
        {mode==='reset' && (
          <div style={{ textAlign:'center', marginTop:16 }}>
             <span style={{ fontSize:'.75rem', color:'#8b95a9', cursor:'pointer' }} onClick={()=>{setMode('login');setErr('');setMsg('')}}>Back to Sign In</span>
          </div>
        )}
      </div>
    </div>
  )
}

/* ════════════════════════════════════════
   SIDEBAR
════════════════════════════════════════ */
function Sidebar({ tab, setTab, user, onLogout }) {
  const initials = user.name?.split(' ').map(w=>w[0]).join('').slice(0,2)||'U'
  const items = [
    { id:'dashboard', icon:<LayoutDashboard size={16}/>, label:'Dashboard' },
    { id:'stocks',    icon:<Activity        size={16}/>, label:'Stocks'    },
    { id:'portfolio', icon:<Briefcase       size={16}/>, label:'Portfolio' },
    { id:'news',      icon:<Newspaper       size={16}/>, label:'News'      },
  ]
  return (
    <aside className="sb">
      <div className="sb-head">
        <div className="sb-logo">
          <div className="sb-logo-icon" style={{ background:'#00d4aa', color:'#0b0a1c' }}>📈</div>
          <div>
            <div className="landing-logo-text" style={{ fontSize:'1rem' }}>BULL<span>SENSE</span></div>
            <div className="sb-logo-tag" style={{ color:'#00d4aa', marginTop:1 }}>NSE Analytics</div>
          </div>
        </div>
      </div>
      <div className="sb-user">
        <div className="sb-avatar">{initials}</div>
        <div><div className="sb-user-name">{user.name}</div><div className="sb-user-role">⭐ Premium</div></div>
      </div>
      <nav className="sb-nav">
        {items.map(it => (
          <div key={it.id} className={`nav-item ${tab===it.id?'active':''}`} onClick={()=>setTab(it.id)}>
            {it.icon} {it.label}
          </div>
        ))}
      </nav>
      <div className="sb-foot">
        <div className="logout-item" onClick={onLogout}><LogOut size={15}/> Sign Out</div>
      </div>
    </aside>
  )
}

/* ════════════════════════════════════════
   DASHBOARD
════════════════════════════════════════ */
function Dashboard({ stockData, user, watchlist }) {
  const all     = Object.values(stockData)
  const withSig = all.filter(d=>d?.signal&&!['Analyzing...','N/A'].includes(d.signal))
  const buys    = withSig.filter(d=>d.signal==='BUY').length
  const sells   = withSig.filter(d=>d.signal==='SELL').length
  const mood    = buys>sells?'Bullish':sells>buys?'Bearish':'Neutral'
  const moodC   = mood==='Bullish'?'#00d4aa':mood==='Bearish'?'#ff4d6d':'#f0b429'
  const topConf = [...withSig].sort((a,b)=>(b.analysis?.confidence||0)-(a.analysis?.confidence||0)).slice(0,5)
  const h = new Date().getHours()
  const greet = h<12?'Good morning':h<17?'Good afternoon':'Good evening'

  return (
    <div style={{ paddingBottom:32 }}>
      <div className="ph fade-up">
        <div>
          <div className="ph-title">{greet}, {user.name?.split(' ')[0]} 👋</div>
          <div className="ph-sub">{new Date().toLocaleDateString('en-IN',{weekday:'long',year:'numeric',month:'long',day:'numeric'})} · NSE Market Overview</div>
        </div>
        <div style={{ display:'flex',alignItems:'center',gap:7,background:'rgba(0,212,170,.08)',border:'1px solid rgba(0,212,170,.2)',borderRadius:99,padding:'7px 15px',fontSize:'.76rem',fontWeight:600,color:'#00d4aa' }}>
          <span style={{ width:7,height:7,borderRadius:'50%',background:'#00d4aa',animation:'pulse 1.5s infinite',display:'inline-block' }}/> Market Live
        </div>
      </div>
      <div className="dash-stats">
        {[
          { label:'Watching',    val:watchlist.length,   sub:'stocks in watchlist',             icon:'👁️', bg:'rgba(67,97,238,.12)',   c:'#738aff' },
          { label:'BUY Signals', val:buys||'—',          sub:`of ${withSig.length} analyzed`,   icon:'📈', bg:'rgba(0,212,170,.12)',   c:'#00d4aa' },
          { label:'SELL Signals',val:sells||'—',         sub:`of ${withSig.length} analyzed`,   icon:'📉', bg:'rgba(255,77,109,.12)',  c:'#ff4d6d' },
          { label:'Market Mood', val:mood,               sub:'AI consensus signal',             icon:'🧠', bg:'rgba(240,180,41,.12)',  c:moodC    },
        ].map((s,i) => (
          <div key={i} className={`scard fade-up-${i}`}>
            <div className="scard-icon" style={{ background:s.bg }}>{s.icon}</div>
            <div className="scard-label">{s.label}</div>
            <div className="scard-value" style={{ color:s.c }}>{s.val}</div>
            <div className="scard-sub">{s.sub}</div>
          </div>
        ))}
      </div>
      <div className="dash-row">
        <div className="sec-card fade-up-1">
          <div className="sec-head"><div className="sec-title"><Zap size={14} style={{ color:'#00d4aa' }}/> Top AI Confidence</div></div>
          {topConf.length===0
            ? <div style={{ padding:16 }}>{[0,1,2,3,4].map(i=><div key={i} style={{ marginBottom:10 }}><Sk h={42}/></div>)}</div>
            : topConf.map((d,i)=>(
              <div key={d.symbol} style={{ padding:'12px 18px',borderBottom:i<topConf.length-1?'1px solid rgba(255,255,255,.05)':'none',display:'flex',alignItems:'center',gap:12 }}>
                <div style={{ width:32,height:32,borderRadius:8,flexShrink:0,background:d.signal==='BUY'?'rgba(0,212,170,.12)':'rgba(255,77,109,.12)',display:'flex',alignItems:'center',justifyContent:'center' }}>
                  {d.signal==='BUY'?<TrendingUp size={15} color="#00d4aa"/>:<TrendingDown size={15} color="#ff4d6d"/>}
                </div>
                <div style={{ flex:1,minWidth:0 }}>
                  <div style={{ fontWeight:700,fontSize:'.86rem' }}>{d.symbol}</div>
                  <div style={{ fontSize:'.7rem',color:'#8b95a9',marginTop:1 }}>{NAMES[d.symbol]||''}</div>
                </div>
                <div style={{ textAlign:'right',flexShrink:0 }}>
                  <div style={{ fontFamily:'JetBrains Mono,monospace',fontWeight:700,fontSize:'.88rem' }}>₹{d.current_price?.toLocaleString('en-IN')}</div>
                  <div style={{ fontSize:'.7rem',fontWeight:700,color:d.signal==='BUY'?'#00d4aa':'#ff4d6d' }}>{Math.round((d.analysis?.confidence||0)*100)}% conf.</div>
                </div>
              </div>
            ))
          }
        </div>
        <div className="sec-card fade-up-2">
          <div className="sec-head"><div className="sec-title"><BarChart3 size={14} style={{ color:'#00d4aa' }}/> AI Signal Board</div></div>
          {withSig.length===0
            ? <div style={{ padding:16 }}>{[0,1,2,3,4].map(i=><div key={i} style={{ marginBottom:10 }}><Sk h={40}/></div>)}</div>
            : withSig.slice(0,8).map((d,i,arr)=>(
              <div key={d.symbol} style={{ padding:'11px 18px',borderBottom:i<arr.length-1?'1px solid rgba(255,255,255,.05)':'none',display:'flex',alignItems:'center',gap:12 }}>
                <div style={{ fontWeight:700,fontSize:'.84rem',width:86,flexShrink:0 }}>{d.symbol}</div>
                <div style={{ flex:1 }}>
                  <div style={{ height:4,background:'#0f1427',borderRadius:99,overflow:'hidden' }}>
                    <div style={{ height:'100%',borderRadius:99,transition:'width 1.2s ease',width:`${Math.round((d.analysis?.confidence||0)*100)}%`,background:d.signal==='BUY'?'#00d4aa':'#ff4d6d' }}/>
                  </div>
                  <div style={{ fontSize:'.64rem',color:'#3e4a5e',marginTop:2 }}>{Math.round((d.analysis?.confidence||0)*100)}%</div>
                </div>
                <span className={`pill ${d.signal==='BUY'?'buy':'sell'}`}>{d.signal}</span>
              </div>
            ))
          }
        </div>
      </div>
    </div>
  )
}

/* ════════════════════════════════════════
   STOCKS — with watchlist management
════════════════════════════════════════ */
function Stocks({ stockData, loading, fetchStock, fetchedRef, token, watchlist, setWatchlist }) {
  const [sel,        setSel]       = useState(watchlist[0]||'RELIANCE')
  const [search,     setSearch]    = useState('')
  const [dur,        setDur]       = useState('1M')
  const [chartData,  setChartData] = useState({})
  const [chartLoad,  setChartLoad] = useState({})
  const [searchErr,  setSearchErr] = useState('')
  const [validating, setValidating]= useState(false)
  const [showPicker, setShowPicker]= useState(false)   // watchlist picker modal

  // Filter for sidebar list
  const filtered = watchlist.filter(s => s.includes(search.toUpperCase().trim())||search==='')
  const data     = stockData[sel]
  const isLoad   = loading[sel]
  const sigClass = data?.signal==='BUY'?'buy':data?.signal==='SELL'?'sell':'wait'

  // Fetch chart per symbol+duration
  const chartKey = `${sel}_${dur}`
  useEffect(() => {
    if (!sel||chartData[chartKey]) return
    setChartLoad(p=>({...p,[chartKey]:true}))
    const qSym = sel.endsWith('.NS')?sel:sel+'.NS'
    api.get(`/history?symbol=${qSym}&period=${DUR_PERIOD[dur]}`)
      .then(r=>{ if(Array.isArray(r.data)) setChartData(p=>({...p,[chartKey]:r.data})) })
      .catch(()=>{})
      .finally(()=>setChartLoad(p=>({...p,[chartKey]:false})))
  },[sel,dur])

  const graph = chartData[chartKey]||[]

  const handleKey = async e => {
    if (e.key!=='Enter'||!search.trim()) return
    const raw = search.trim().toUpperCase()
    if (watchlist.includes(raw)) { setSel(raw); select(raw); setSearch(''); return }
    setSearchErr(''); setValidating(true)
    try {
      const qSym = raw.endsWith('.NS')||raw.startsWith('^')?raw:raw+'.NS'
      const res  = await api.get(`/quote?symbol=${qSym}`)
      if (res.data?.current_price) {
        await saveWatchlist([...watchlist, raw])
        setSel(raw); fetchedRef.current.delete(raw); fetchStock(raw); setSearch('')
      } else {
        setSearchErr(`"${raw}" not found on NSE.`)
      }
    } catch { setSearchErr('Could not validate symbol.') }
    finally { setValidating(false) }
  }

  const select = sym => { setSel(sym); if(!fetchedRef.current.has(sym)) fetchStock(sym) }

  const saveWatchlist = async (syms) => {
    setWatchlist(syms)
    if (token) {
      try { await authApi(token).post('/watchlist', { symbols:syms }) } catch {}
    }
  }

  const removeFromWatchlist = async (sym) => {
    const updated = watchlist.filter(s=>s!==sym)
    await saveWatchlist(updated)
    if (sel===sym) setSel(updated[0]||'')
    fetchedRef.current.delete(sym)
  }

  const addFromPicker = async (sym) => {
    if (!watchlist.includes(sym)) {
      const updated = [...watchlist, sym]
      await saveWatchlist(updated)
      if (!fetchedRef.current.has(sym)) fetchStock(sym)
    }
  }

  return (
    <div className="stocks-wrap">
      {/* ── Watchlist Picker Modal ── */}
      {showPicker && (
        <div style={{ position:'fixed',inset:0,background:'rgba(0,0,0,.7)',zIndex:1000,display:'flex',alignItems:'center',justifyContent:'center' }}
          onClick={()=>setShowPicker(false)}>
          <div style={{ background:'#161d31',border:'1px solid rgba(255,255,255,.12)',borderRadius:18,padding:24,width:480,maxHeight:'70vh',overflow:'auto' }}
            onClick={e=>e.stopPropagation()}>
            <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:18 }}>
              <div style={{ fontWeight:700,fontSize:'1rem' }}>📋 Manage Watchlist</div>
              <button onClick={()=>setShowPicker(false)} style={{ background:'none',border:'none',color:'#8b95a9',cursor:'pointer' }}><X size={18}/></button>
            </div>
            <div style={{ fontSize:'.75rem',color:'#8b95a9',marginBottom:14 }}>Select stocks to add to your watchlist (max 20)</div>
            <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr',gap:8 }}>
              {ALL_NSE_STOCKS.map(sym => {
                const inList = watchlist.includes(sym)
                return (
                  <div key={sym} onClick={()=>inList?removeFromWatchlist(sym):addFromPicker(sym)}
                    style={{ padding:'10px 14px',borderRadius:10,border:`1px solid ${inList?'rgba(0,212,170,.3)':'rgba(255,255,255,.07)'}`,
                      background:inList?'rgba(0,212,170,.08)':'transparent',cursor:'pointer',
                      display:'flex',alignItems:'center',justifyContent:'space-between',transition:'all .15s' }}>
                    <div>
                      <div style={{ fontWeight:700,fontSize:'.84rem',color:inList?'#00d4aa':'#e8eaf2' }}>{sym}</div>
                      <div style={{ fontSize:'.66rem',color:'#8b95a9' }}>{NAMES[sym]||'NSE'}</div>
                    </div>
                    {inList
                      ? <Check size={14} color="#00d4aa"/>
                      : <Plus size={14} color="#4a5568"/>}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── Left Stock List ── */}
      <div className="stocks-left">
        <div className="stocks-left-h">
          <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:10 }}>
            <div className="stocks-label">🇮🇳 My Watchlist</div>
            <button onClick={()=>setShowPicker(true)}
              style={{ display:'flex',alignItems:'center',gap:5,padding:'5px 10px',borderRadius:8,border:'1px solid rgba(0,212,170,.3)',background:'rgba(0,212,170,.08)',color:'#00d4aa',cursor:'pointer',fontSize:'.72rem',fontWeight:600 }}>
              <BookmarkPlus size={12}/> Edit
            </button>
          </div>
          <div className="search-wrap">
            {validating?<span className="spinner" style={{ width:13,height:13,flexShrink:0 }}/>:<Search size={13} color="#3e4a5e"/>}
            <input placeholder="Search or add symbol…" value={search}
              onChange={e=>{setSearch(e.target.value);setSearchErr('')}} onKeyDown={handleKey}/>
          </div>
          {searchErr && <div style={{ fontSize:'.7rem',color:'#ff4d6d',marginTop:6,lineHeight:1.4 }}>⚠ {searchErr}</div>}
        </div>
        <div className="stocks-list">
          {filtered.map(sym => {
            const d  = stockData[sym]
            const ld = loading[sym]
            return (
              <div key={sym} className={`sitem ${sel===sym?'active':''}`}>
                <div onClick={()=>select(sym)} style={{ flex:1 }}>
                  <div className="sitem-row">
                    <span className="sitem-sym">{sym}</span>
                    {ld?<span className="pill wait">…</span>
                      :d?.signal&&!['Analyzing...','N/A'].includes(d.signal)
                      ?<span className={`pill ${d.signal==='BUY'?'buy':'sell'}`}>{d.signal}</span>
                      :d&&!d.error?<span className="pill wait" style={{ fontSize:'.6rem' }}>analyzing</span>:null}
                  </div>
                  {ld?<Sk w="65%" h={18} r={4}/>
                    :d?.current_price
                    ?<div className="sitem-price">₹{d.current_price.toLocaleString('en-IN')}</div>
                    :<Sk w="55%" h={16} r={4}/>}
                  <div className="sitem-name">{NAMES[sym]||'NSE'}</div>
                </div>
                {!['RELIANCE','TCS','INFY','HDFCBANK','SBIN'].includes(sym) && (
                  <button onClick={()=>removeFromWatchlist(sym)}
                    style={{ background:'none',border:'none',color:'#3e4a5e',cursor:'pointer',padding:'4px',marginLeft:4,flexShrink:0 }}>
                    <X size={12}/>
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* ── Right Detail ── */}
      <div className="stocks-right">
        {!data?(
          <div className="empty-state"><Activity size={40} strokeWidth={1.2}/><span style={{ fontSize:'.92rem' }}>Select a stock</span></div>
        ):data.error?(
          <div className="empty-state" style={{ color:'#ff4d6d',gap:12 }}>
            <AlertCircle size={36}/>
            <div style={{ fontWeight:700,fontSize:'1.05rem' }}>Could not load {sel}</div>
            <div style={{ fontSize:'.82rem',color:'#8b95a9',maxWidth:340,textAlign:'center' }}>{data.error?.includes('fetch price')?<>Symbol not found on NSE.<br/>Check and try again.</>:data.error}</div>
            <div style={{ display:'flex',gap:10 }}>
              <button onClick={()=>{fetchedRef.current.delete(sel);fetchStock(sel)}}
                style={{ padding:'8px 18px',borderRadius:8,border:'1px solid rgba(255,77,109,.3)',background:'rgba(255,77,109,.1)',color:'#ff4d6d',cursor:'pointer',fontFamily:'Sora,sans-serif',display:'flex',alignItems:'center',gap:6,fontSize:'.82rem' }}>
                <RefreshCw size={12}/> Retry
              </button>
              <button onClick={()=>removeFromWatchlist(sel)}
                style={{ padding:'8px 18px',borderRadius:8,border:'1px solid rgba(255,255,255,.1)',background:'rgba(255,255,255,.05)',color:'#8b95a9',cursor:'pointer',fontFamily:'Sora,sans-serif',fontSize:'.82rem' }}>
                Remove
              </button>
            </div>
          </div>
        ):(
          <div className="detail">
            <div className="detail-header">
              <div>
                <div style={{ display:'flex',alignItems:'center',gap:10,marginBottom:4 }}>
                  <span className="detail-sym">{sel}</span>
                  <div className="live-badge"><span className="live-dot"/> LIVE</div>
                </div>
                <div className="detail-name">{NAMES[sel]||'NSE Listed'} · National Stock Exchange</div>
              </div>
              <div style={{ textAlign:'right' }}>
                {data.current_price?<div className="price-big">₹{data.current_price.toLocaleString('en-IN')}</div>:<Sk w={150} h={40} r={7}/>}
                <div className="price-label">Live Market Price</div>
              </div>
            </div>

            {data.signal&&!['Analyzing...','N/A'].includes(data.signal)?(
              <div className={`sig-box ${sigClass}`}>
                <div style={{ flexShrink:0 }}>
                  <div className="sig-label">AI Signal</div>
                  <div className="sig-dir">{data.signal==='BUY'?'↑ BUY':'↓ SELL'}</div>
                </div>
                {data.analysis?.confidence!=null&&(
                  <div className="conf-wrap">
                    <div style={{ fontSize:'.68rem',color:'#8b95a9',display:'flex',justifyContent:'space-between' }}>
                      <span>Confidence</span>
                      <span style={{ fontWeight:700,color:'#e8eaf2' }}>{Math.round(data.analysis.confidence*100)}%</span>
                    </div>
                    <div className="conf-track"><div className="conf-fill" style={{ width:`${Math.round(data.analysis.confidence*100)}%` }}/></div>
                  </div>
                )}
                {data.predicted_price&&data.predicted_price!=='N/A'&&(
                  <div className="proj-box">
                    <div className="proj-label">Next Day Est.</div>
                    <div className="proj-val">₹{Number(data.predicted_price).toLocaleString('en-IN')}</div>
                  </div>
                )}
              </div>
            ):isLoad?(
              <div className="sig-box wait" style={{ padding:'13px 16px' }}>
                <span className="spinner"/>
                <span style={{ fontSize:'.84rem',color:'#8b95a9' }}>
                  {isLoad==='predicting'?'🧠 Training AI model… (30–90s first time)':'Fetching market data…'}
                </span>
              </div>
            ):null}

            {data.sentiment&&(
              <div className="sent-row">
                <div className="sent-card">
                  <div className="sent-label">News Sentiment</div>
                  <div className={`sent-val ${data.sentiment.label?.toLowerCase()}`}>
                    {data.sentiment.label==='Bullish'?'🟢':data.sentiment.label==='Bearish'?'🔴':'🟡'} {data.sentiment.label}
                  </div>
                  <div className="sent-hint">{data.sentiment.count} headlines analyzed</div>
                </div>
                <div className="sent-card">
                  <div className="sent-label">Projected Price</div>
                  <div style={{ fontFamily:'JetBrains Mono,monospace',fontWeight:700,fontSize:'1rem',marginTop:4 }}>
                    {data.predicted_price&&data.predicted_price!=='N/A'?`₹${Number(data.predicted_price).toLocaleString('en-IN')}`:'—'}
                  </div>
                  <div className="sent-hint">Next trading day estimate</div>
                </div>
              </div>
            )}

            <div className="chart-card">
              <div className="chart-top">
                <span className="chart-lbl">Price History</span>
                <div className="dur-tabs">
                  {DURATIONS.map(d=>(
                    <button key={d} className={`dur-btn ${dur===d?'active':''}`} onClick={()=>setDur(d)}>{d}</button>
                  ))}
                </div>
              </div>
              {chartLoad[chartKey]?<Sk w="100%" h={200} r={8}/>
                :graph.length>0?(
                  <ResponsiveContainer width="100%" height={200}>
                    <AreaChart data={graph} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                      <defs>
                        <linearGradient id={`g-${sel}`} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%"  stopColor="#00d4aa" stopOpacity={.15}/>
                          <stop offset="95%" stopColor="#00d4aa" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="2 4" vertical={false} stroke="rgba(255,255,255,.04)"/>
                      <XAxis dataKey="date" stroke="#8b95a9" fontSize={11} tickLine={false} axisLine={false} minTickGap={20} tickMargin={8} />
                      <YAxis stroke="#8b95a9" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(val)=>`₹${val}`} domain={['auto','auto']} width={60} />
                      <Tooltip content={<Tip/>}/>
                      <Area type="monotone" dataKey="price" stroke="#00d4aa" strokeWidth={2}
                        fillOpacity={1} fill={`url(#g-${sel})`} dot={false} activeDot={{ r:4,fill:'#00d4aa' }}/>
                    </AreaChart>
                  </ResponsiveContainer>
                ):<div style={{ height:200,display:'flex',alignItems:'center',justifyContent:'center',color:'#3e4a5e',fontSize:'.84rem' }}>No chart data</div>}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

/* ════════════════════════════════════════
   PORTFOLIO — full CRUD with DB
════════════════════════════════════════ */
function Portfolio({ stockData, token }) {
  const [holdings,    setHoldings]   = useState([])
  const [loading,     setLoading]    = useState(true)
  const [showAdd,     setShowAdd]    = useState(false)
  const [editRow,     setEditRow]    = useState(null)    // sym being edited
  const [editQty,     setEditQty]    = useState('')
  const [editPrice,   setEditPrice]  = useState('')
  const [addSym,      setAddSym]     = useState('')
  const [addQty,      setAddQty]     = useState('')
  const [addPrice,    setAddPrice]   = useState('')
  const [addErr,      setAddErr]     = useState('')
  const [busy,        setBusy]       = useState(false)
  const aApi = authApi(token)

  useEffect(() => {
    aApi.get('/portfolio')
      .then(r => setHoldings(r.data.holdings||[]))
      .catch(() => setHoldings([]))
      .finally(() => setLoading(false))
  }, [])

  const rows = holdings.map(h => {
    const d       = stockData[h.sym]
    const live    = d?.current_price || h.buy_price
    const currVal = live * h.qty
    const invested= h.buy_price * h.qty
    const pnl     = currVal - invested
    const pct     = ((pnl/invested)*100).toFixed(2)
    return { ...h, live, currVal, invested, pnl, pct, signal:d?.signal }
  })
  const totInv  = rows.reduce((s,r)=>s+r.invested,0)
  const totCurr = rows.reduce((s,r)=>s+r.currVal, 0)
  const totPnl  = totCurr-totInv
  const totPct  = totInv>0?((totPnl/totInv)*100).toFixed(2):'0.00'

  const addHolding = async () => {
    if (!addSym||!addQty||!addPrice) { setAddErr('Fill all fields.'); return }
    const qty   = parseFloat(addQty)
    const price = parseFloat(addPrice)
    if (qty<=0||price<=0) { setAddErr('Qty and price must be > 0.'); return }
    setBusy(true); setAddErr('')
    try {
      const res = await aApi.post('/portfolio/add', { sym:addSym.toUpperCase(), qty, buy_price:price })
      if (res.data.error) { setAddErr(res.data.error); return }
      setHoldings(res.data.holdings)
      setAddSym(''); setAddQty(''); setAddPrice(''); setShowAdd(false)
    } catch { setAddErr('Failed to add. Check backend.') }
    finally { setBusy(false) }
  }

  const removeHolding = async (sym) => {
    try {
      const res = await aApi.delete(`/portfolio/${sym}`)
      setHoldings(res.data.holdings||[])
    } catch {}
  }

  const startEdit = (row) => {
    setEditRow(row.sym); setEditQty(String(row.qty)); setEditPrice(String(row.buy_price))
  }
  const saveEdit = async (sym) => {
    const qty   = parseFloat(editQty)
    const price = parseFloat(editPrice)
    if (!qty||!price||qty<=0||price<=0) return
    try {
      const res = await aApi.put(`/portfolio/${sym}`, { qty, buy_price:price })
      setHoldings(res.data.holdings||[])
      setEditRow(null)
    } catch {}
  }

  const recs = rows.filter(r=>r.signal&&!['Analyzing...','N/A'].includes(r.signal))

  return (
    <div className="pf-page">
      <div className="fade-up" style={{ marginBottom:20, display:'flex', justifyContent:'space-between', alignItems:'flex-start' }}>
        <div>
          <div className="ph-title">My Portfolio</div>
          <div className="ph-sub">Your NSE holdings · stored in database · AI-assisted analysis</div>
        </div>
        <button onClick={()=>setShowAdd(!showAdd)}
          style={{ display:'flex',alignItems:'center',gap:7,padding:'9px 18px',borderRadius:10,border:'none',background:'#00d4aa',color:'#0b0a1c',cursor:'pointer',fontFamily:'Sora,sans-serif',fontWeight:700,fontSize:'.84rem' }}>
          <Plus size={15}/> Add Stock
        </button>
      </div>

      {/* Add Stock Form */}
      {showAdd && (
        <div className="fade-up" style={{ background:'#161d31',border:'1px solid rgba(0,212,170,.2)',borderRadius:14,padding:20,marginBottom:20 }}>
          <div style={{ fontWeight:700,marginBottom:14,fontSize:'.9rem',color:'#00d4aa' }}>➕ Add New Holding</div>
          <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr 1fr auto',gap:12,alignItems:'end' }}>
            <div>
              <label className="f-label">NSE Symbol</label>
              <input className="f-input" placeholder="e.g. BAJFINANCE" value={addSym}
                onChange={e=>setAddSym(e.target.value.toUpperCase())} style={{ marginBottom:0 }}/>
            </div>
            <div>
              <label className="f-label">Quantity (shares)</label>
              <input className="f-input" type="number" placeholder="e.g. 50" value={addQty}
                onChange={e=>setAddQty(e.target.value)} style={{ marginBottom:0 }}/>
            </div>
            <div>
              <label className="f-label">Avg Buy Price (₹)</label>
              <input className="f-input" type="number" placeholder="e.g. 6800" value={addPrice}
                onChange={e=>setAddPrice(e.target.value)} style={{ marginBottom:0 }}/>
            </div>
            <button onClick={addHolding} disabled={busy}
              style={{ padding:'11px 20px',borderRadius:10,border:'none',background:'#00d4aa',color:'#0b0a1c',cursor:'pointer',fontFamily:'Sora,sans-serif',fontWeight:700,fontSize:'.84rem',display:'flex',alignItems:'center',gap:6 }}>
              {busy?<span className="spinner" style={{ width:13,height:13 }}/>:<><Check size={14}/> Add</>}
            </button>
          </div>
          {addErr && <div style={{ fontSize:'.76rem',color:'#ff4d6d',marginTop:10 }}>⚠ {addErr}</div>}
          <div style={{ fontSize:'.72rem',color:'#3e4a5e',marginTop:10 }}>
            💡 If you already hold a stock, adding again will update with weighted average price.
          </div>
        </div>
      )}

      {/* Summary Cards */}
      {!loading && rows.length > 0 && (
        <div className="pf-stats fade-up-1">
          {[
            { label:'Total Invested', val:`₹${totInv.toLocaleString('en-IN')}`,  sub:`${rows.length} holdings`,  icon:'💰', c:'#738aff' },
            { label:'Current Value',  val:`₹${totCurr.toLocaleString('en-IN')}`, sub:'Live prices',              icon:'📊', c:'#00d4aa' },
            { label:'Total P&L',      val:`${totPnl>=0?'+':'-'}₹${Math.abs(totPnl).toLocaleString('en-IN')}`, sub:`${totPct}% overall`, icon:totPnl>=0?'📈':'📉', c:totPnl>=0?'#00d4aa':'#ff4d6d' },
            { label:'AI BUY Signals', val:recs.filter(r=>r.signal==='BUY').length, sub:'In your holdings',      icon:'🧠', c:'#00d4aa' },
          ].map((c,i)=>(
            <div key={i} className="pfc">
              <div className="pfc-icon">{c.icon}</div>
              <div className="pfc-label">{c.label}</div>
              <div className="pfc-val" style={{ color:c.c }}>{c.val}</div>
              <div className="pfc-sub" style={{ color:c.c }}>{c.sub}</div>
            </div>
          ))}
        </div>
      )}

      {/* Holdings Table */}
      <div className="pf-table-wrap fade-up-2">
        <div className="pf-table-head">
          <div className="pf-table-title">📋 My Holdings</div>
          <div style={{ fontSize:'.72rem',color:'#8b95a9' }}>{rows.length} stocks · saved to MongoDB</div>
        </div>
        {loading ? (
          <div style={{ padding:24 }}>{[0,1,2].map(i=><div key={i} style={{ marginBottom:12 }}><Sk h={40}/></div>)}</div>
        ) : rows.length === 0 ? (
          <div style={{ padding:48,textAlign:'center',color:'#3e4a5e' }}>
            <div style={{ fontSize:'2rem',marginBottom:12 }}>📭</div>
            <div style={{ fontWeight:600,marginBottom:6 }}>No holdings yet</div>
            <div style={{ fontSize:'.84rem' }}>Click "Add Stock" to start tracking your portfolio</div>
          </div>
        ) : (
          <div style={{ overflowX:'auto' }}>
            <table className="pf-table">
              <thead>
                <tr>
                  <th>Stock</th><th>Qty</th><th>Avg Buy ₹</th>
                  <th>LTP ₹</th><th>Invested</th><th>Value</th>
                  <th>P&amp;L</th><th>Weight</th><th>Signal</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(r=>(
                  <tr key={r.sym}>
                    <td><div className="h-sym">{r.sym}</div><div className="h-name">{NAMES[r.sym]||''}</div></td>
                    <td>
                      {editRow===r.sym
                        ?<input type="number" value={editQty} onChange={e=>setEditQty(e.target.value)}
                          style={{ width:64,padding:'4px 6px',borderRadius:6,border:'1px solid rgba(240,180,41,.4)',background:'#0f1427',color:'#e8eaf2',fontFamily:'JetBrains Mono,monospace',fontSize:'.8rem' }}/>
                        :<span className="mono" style={{ color:'#8b95a9' }}>{r.qty}</span>}
                    </td>
                    <td>
                      {editRow===r.sym
                        ?<input type="number" value={editPrice} onChange={e=>setEditPrice(e.target.value)}
                          style={{ width:80,padding:'4px 6px',borderRadius:6,border:'1px solid rgba(240,180,41,.4)',background:'#0f1427',color:'#e8eaf2',fontFamily:'JetBrains Mono,monospace',fontSize:'.8rem' }}/>
                        :<span className="h-price">₹{r.buy_price.toLocaleString('en-IN')}</span>}
                    </td>
                    <td className="h-price">{stockData[r.sym]?.current_price?`₹${r.live.toLocaleString('en-IN')}`:<Sk w={55} h={12}/>}</td>
                    <td className="mono" style={{ color:'#8b95a9' }}>₹{r.invested.toLocaleString('en-IN')}</td>
                    <td className="h-price">₹{r.currVal.toLocaleString('en-IN')}</td>
                    <td>
                      <div className={r.pnl>=0?'pnl-p':'pnl-n'}>{r.pnl>=0?'+':'-'}₹{Math.abs(r.pnl).toLocaleString('en-IN')}</div>
                      <div style={{ fontSize:'.68rem',fontWeight:600,color:r.pnl>=0?'#00d4aa':'#ff4d6d' }}>{r.pnl>=0?'▲':'▼'} {Math.abs(parseFloat(r.pct)).toFixed(2)}%</div>
                    </td>
                    <td>
                      <div style={{ fontSize:'.72rem',color:'#8b95a9' }}>{((r.currVal/totCurr)*100).toFixed(1)}%</div>
                      <div className="alloc-bar"><div className="alloc-fill" style={{ width:`${(r.currVal/totCurr)*100}%` }}/></div>
                    </td>
                    <td>{r.signal&&!['Analyzing...','N/A'].includes(r.signal)?<span className={`pill ${r.signal==='BUY'?'buy':'sell'}`}>{r.signal}</span>:<Sk w={48} h={20} r={99}/>}</td>
                    <td>
                      <div style={{ display:'flex',gap:6 }}>
                        {editRow===r.sym?(
                          <>
                            <button onClick={()=>saveEdit(r.sym)}
                              style={{ padding:'5px 8px',borderRadius:6,border:'none',background:'rgba(0,212,170,.15)',color:'#00d4aa',cursor:'pointer' }}>
                              <Check size={12}/>
                            </button>
                            <button onClick={()=>setEditRow(null)}
                              style={{ padding:'5px 8px',borderRadius:6,border:'none',background:'rgba(255,255,255,.05)',color:'#8b95a9',cursor:'pointer' }}>
                              <X size={12}/>
                            </button>
                          </>
                        ):(
                          <>
                            <button onClick={()=>startEdit(r)}
                              style={{ padding:'5px 8px',borderRadius:6,border:'none',background:'rgba(255,255,255,.08)',color:'#00d4aa',cursor:'pointer' }}>
                              <Edit2 size={12}/>
                            </button>
                            <button onClick={()=>removeHolding(r.sym)}
                              style={{ padding:'5px 8px',borderRadius:6,border:'none',background:'rgba(255,77,109,.1)',color:'#ff4d6d',cursor:'pointer' }}>
                              <Trash2 size={12}/>
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* AI Recs */}
      {recs.length>0&&(
        <div className="ai-recs-wrap fade-up-3">
          <div className="pf-table-head">
            <div className="pf-table-title">🤖 AI Recommendations</div>
            <div style={{ fontSize:'.72rem',color:'#8b95a9' }}>Based on live XGBoost signals</div>
          </div>
          {recs.map(r=>(
            <div key={r.sym} className="ai-rec-row">
              <div className="ai-rec-icon" style={{ background:r.signal==='BUY'?'rgba(0,212,170,.12)':'rgba(255,77,109,.12)' }}>
                {r.signal==='BUY'?<TrendingUp size={14} color="#00d4aa"/>:<TrendingDown size={14} color="#ff4d6d"/>}
              </div>
              <div>
                <div className="ai-rec-sym">{r.sym} <span style={{ fontSize:'.7rem',color:'#8b95a9',fontWeight:400 }}>{NAMES[r.sym]}</span></div>
                <div className="ai-rec-note">{r.signal==='BUY'?'AI signals upward momentum':'AI signals potential decline — consider reviewing'}</div>
              </div>
              <span className={`pill ${r.signal==='BUY'?'buy':'sell'}`} style={{ marginLeft:'auto' }}>{r.signal}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ════════════════════════════════════════
   NEWS
════════════════════════════════════════ */
function News() {
  const [news,setNews]=useState([])
  const [busy,setBusy]=useState(true)
  useEffect(()=>{
    api.get('/news?market=IN').then(r=>setNews(Array.isArray(r.data)?r.data:[])).catch(()=>setNews([])).finally(()=>setBusy(false))
  },[])
  return (
    <div className="news-page">
      <div className="fade-up" style={{ marginBottom:0 }}>
        <div className="ph-title">Market News</div>
        <div className="ph-sub">Latest from NSE & Indian financial markets</div>
      </div>
      <div className="news-grid">
        {busy
          ?Array.from({length:6}).map((_,i)=>(
            <div key={i} className="news-card"><Sk h={140} r={0}/><div style={{ padding:14,display:'flex',flexDirection:'column',gap:7 }}><Sk w="38%" h={10}/><Sk h={13}/><Sk w="72%" h={13}/></div></div>
          ))
          :news.length>0
          ?news.map((item,i)=>(
            <div key={i} className="news-card" onClick={()=>item.link&&window.open(item.link,'_blank')}>
              {item.thumbnail&&<img src={item.thumbnail} alt="" className="news-img" onError={e=>{e.target.style.display='none'}}/>}
              <div className="news-body">
                <div className="news-date">{item.publisher?typeof item.publisher==='number'?new Date(item.publisher*1000).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'}):new Date(item.publisher).toLocaleDateString('en-IN'):'Recent'}</div>
                <div className="news-title">{item.title}</div>
              </div>
            </div>
          ))
          :<div style={{ color:'#3e4a5e',gridColumn:'1/-1',textAlign:'center',padding:'60px 0' }}>No news available.</div>}
      </div>
    </div>
  )
}

/* ════════════════════════════════════════
   LANDING PAGE
════════════════════════════════════════ */
function LandingPage({ onNavigate }) {
  return (
    <div className="landing-page">
      <div className="landing-bg-lines"/>

      <nav className="landing-nav fade-up">
        <div className="landing-logo">
          <span className="landing-logo-text">BULL<span>SENSE</span></span>
        </div>
        <div className="landing-right-nav">
          <button className="landing-nav-signin" onClick={() => onNavigate('auth')}>Sign In</button>
          <div className="landing-search-icon"><Search size={14} color="#e8eaf2" /></div>
        </div>
      </nav>

      <main className="landing-main-center">
        <div className="landing-content-center fade-up-1">
          <div className="landing-badge">
            <span className="badge-new">Live</span>
            <span>Real-time NSE AI Analytics</span>
            <span style={{marginLeft: 6}}>→</span>
          </div>

          <h1 className="landing-h1-center">Predict Market Trends<br/>with Precision AI</h1>
          <p className="landing-p-center">
            Leverage cutting-edge machine learning to analyze the National Stock Exchange (NSE). 
            Track live prices, gauge market sentiment, and make data-driven investment decisions confidently.
          </p>
          
          <div className="landing-actions-center">
            <button className="landing-btn" onClick={() => onNavigate('auth')}>Start Free Trial ↗</button>
            <button className="landing-btn outline" onClick={() => onNavigate('auth')}>▶ Watch Demo</button>
          </div>
        </div>
      </main>

      <div className="landing-footer fade-up-2">
        <div className="landing-stats">
          <div className="stat-item">
            <div className="stat-val">87%</div>
            <div className="stat-lbl">Model Accuracy</div>
          </div>
          <div className="stat-item">
            <div className="stat-val">50+</div>
            <div className="stat-lbl">NSE Stocks Covered</div>
          </div>
        </div>
        
        <div className="landing-bottom-card">
          <div className="bc-icon">📈</div>
          <div>
            <div className="bc-title">AI STOCK ASSISTANT</div>
            <div className="bc-desc">Harness the power of deep learning to<br/>optimize every facet of your trading strategy</div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ════════════════════════════════════════
   ROOT
════════════════════════════════════════ */
export default function App() {
  const [user,      setUser]      = useState(null)
  const [token,     setToken]     = useState(null)
  const [page,      setPage]      = useState('landing') // landing, auth, app
  const [tab,       setTab]       = useState('dashboard')
  const [stockData, setStockData] = useState({})
  const [loading,   setLoading]   = useState({})
  const [watchlist, setWatchlist] = useState(['RELIANCE','TCS','INFY','HDFCBANK','SBIN'])
  const fetchedRef = useRef(new Set())

  // Restore session from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem('stockai_token')
    const savedUser  = localStorage.getItem('stockai_user')
    if (savedToken && savedUser) {
      try {
        setToken(savedToken)
        setUser(JSON.parse(savedUser))
        setPage('app')
      } catch { localStorage.clear() }
    }
  }, [])

  // Load watchlist from DB after login
  useEffect(() => {
    if (!user||!token) return
    authApi(token).get('/watchlist')
      .then(r => { if(r.data?.symbols?.length) setWatchlist(r.data.symbols) })
      .catch(() => {})
  }, [user, token])

  const fetchStock = useCallback(async (sym) => {
    if (fetchedRef.current.has(sym)) return
    fetchedRef.current.add(sym)
    const qSym = sym.endsWith('.NS')?sym:sym+'.NS'
    setLoading(p=>({...p,[sym]:'quote'}))
    try {
      const qRes = await api.get(`/quote?symbol=${qSym}`).catch(()=>({data:{}}))
      setStockData(p=>({...p,[sym]:{ symbol:sym,current_price:qRes.data.current_price||null,predicted_price:'N/A',signal:'Analyzing...',graph_data:[],sentiment:null,analysis:null,factors:null,error:qRes.data.error||null }}))
    } catch(e) {
      setStockData(p=>({...p,[sym]:{symbol:sym,error:e.message}}))
      setLoading(p=>({...p,[sym]:false})); return
    }
    setLoading(p=>({...p,[sym]:'predicting'}))
    try {
      const pRes = await api.get(`/predict?stock=${qSym}`)
      if (pRes.data&&!pRes.data.error) {
        const d=pRes.data
        setStockData(p=>({...p,[sym]:{ ...p[sym],
          current_price:   d.current_price??p[sym]?.current_price,
          predicted_price: d.predicted_price??'N/A',
          signal:          d.prediction==='UP'?'BUY':'SELL',
          sentiment:{ label:d.sentiment?.score>0.05?'Bullish':d.sentiment?.score<-0.05?'Bearish':'Neutral',score:d.sentiment?.score||0,count:d.sentiment?.count||0 },
          analysis:{ confidence:d.confidence,primary_driver:d.feature_importance?.[0]?.feature||'Technical' },
          factors:{ accuracy:d.metrics?.accuracy,precision:d.metrics?.precision,roc_auc:d.metrics?.roc_auc },
        }}))
      } else {
        setStockData(p=>({...p,[sym]:{...p[sym],signal:'N/A',predError:pRes.data?.error}}))
      }
    } catch(e) {
      setStockData(p=>({...p,[sym]:{...p[sym],predError:e.message}}))
    } finally { setLoading(p=>({...p,[sym]:false})) }
  },[])

  // Fetch all watchlist stocks on login
  useEffect(() => {
    if (!user) return
    watchlist.forEach(s=>fetchStock(s))
  },[user])

  // Fetch new symbols when watchlist changes
  useEffect(() => {
    if (!user) return
    watchlist.forEach(s=>{ if(!fetchedRef.current.has(s)) fetchStock(s) })
  },[watchlist])

  // Live price poll — sequential
  useEffect(() => {
    if (!user) return
    let idx=0
    const iv=setInterval(async()=>{
      const sym=watchlist[idx%watchlist.length]; idx++
      try {
        const r=await api.get(`/quote?symbol=${sym}.NS`)
        if(r.data?.current_price&&!r.data?.error)
          setStockData(p=>p[sym]?({...p,[sym]:{...p[sym],current_price:r.data.current_price}}):p)
      } catch {}
    },4000)
    return ()=>clearInterval(iv)
  },[user,watchlist])

  const handleLogin = (u, t) => { setUser(u); setToken(t); setPage('app') }

  const handleLogout = () => {
    localStorage.removeItem('stockai_token')
    localStorage.removeItem('stockai_user')
    setUser(null); setToken(null); setStockData({})
    fetchedRef.current=new Set()
    setWatchlist(['RELIANCE','TCS','INFY','HDFCBANK','SBIN'])
    setPage('landing')
  }

  if (page === 'landing') return <LandingPage onNavigate={setPage}/>
  if (page === 'auth' || !user) return <AuthPage onLogin={handleLogin}/>

  return (
    <div className="shell">
      <Sidebar tab={tab} setTab={setTab} user={user} onLogout={handleLogout}/>
      <div className="main">
        {tab==='dashboard' && <Dashboard stockData={stockData} user={user} watchlist={watchlist}/>}
        {tab==='stocks'    && <Stocks stockData={stockData} loading={loading} fetchStock={fetchStock} fetchedRef={fetchedRef} token={token} watchlist={watchlist} setWatchlist={setWatchlist}/>}
        {tab==='portfolio' && <Portfolio stockData={stockData} token={token}/>}
        {tab==='news'      && <News/>}
      </div>
    </div>
  )
}
