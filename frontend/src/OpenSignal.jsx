import { useState, useEffect, useRef } from 'react';
import {
  Plus, X, ArrowRight, Briefcase, Sparkles,
  ChevronRight, Radio, ArrowUpRight, Copy, Check,
  GitBranch, MapPin, TrendingUp, Zap, Mail, Wand2
} from 'lucide-react';
import { classifyDomain, transformToProjectShape } from "./api";


// ───────────────────────────────────────────────────────────
// LIVE DATA — powered by ClickHouse + Hybrid Classifier
// ───────────────────────────────────────────────────────────


// ───────────────────────────────────────────────────────────
// MAIN
// ───────────────────────────────────────────────────────────

export default function OpenSignalApp() {
  const [domains, setDomains] = useState([]);
  const [domainStatus, setDomainStatus] = useState({});
  const [results, setResults] = useState({});
  const [input, setInput] = useState('');
  const [activeDomain, setActiveDomain] = useState(null);
  const [activeProject, setActiveProject] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500&family=Instrument+Serif&display=swap';
    document.head.appendChild(link);
    return () => { if (document.head.contains(link)) document.head.removeChild(link); };
  }, []);

  const analyzeDomain = async (domain) => {
    setDomainStatus((s) => ({ ...s, [domain]: 'analyzing' }));
    try {
      const backendData = await classifyDomain(domain);
      const transformed = transformToProjectShape(domain, backendData);
      setResults((r) => ({ ...r, [domain]: transformed }));
      setDomainStatus((s) => ({ ...s, [domain]: 'done' }));
    } catch (err) {
      console.error('Analysis failed:', err);
      setResults((r) => ({ ...r, [domain]: { company: domain.split('.')[0], description: 'Could not reach the data source. Check server logs.', hq: '—', totalJobs: 0, projects: [] } }));
      setDomainStatus((s) => ({ ...s, [domain]: 'error' }));
    }
  };

  const addDomain = (raw) => {
    const source = raw !== undefined ? raw : input;
    const cleaned = source.trim().toLowerCase()
      .replace(/^https?:\/\//, '')
      .replace(/^www\./, '')
      .replace(/\/.*$/, '');
    if (!cleaned || !cleaned.includes('.') || domains.includes(cleaned)) return;
    setDomains((d) => [...d, cleaned]);
    setInput('');
    setActiveDomain((cur) => cur ?? cleaned);
    analyzeDomain(cleaned);
    inputRef.current?.focus();
  };

  const removeDomain = (d) => {
    const remaining = domains.filter((x) => x !== d);
    setDomains(remaining);
    setDomainStatus((s) => { const n = { ...s }; delete n[d]; return n; });
    setResults((r) => { const n = { ...r }; delete n[d]; return n; });
    if (activeDomain === d) {
      setActiveDomain(remaining[0] ?? null);
      setActiveProject(0);
    }
  };

  const loadExample = () => {
    ['wiz.io', 'snyk.io', 'crowdstrike.com'].forEach((d, i) =>
      setTimeout(() => addDomain(d), i * 350)
    );
  };

  const activeData = activeDomain ? results[activeDomain] : null;
  const activeStatus = activeDomain ? domainStatus[activeDomain] : null;
  const activeProjectData = activeData?.projects[activeProject];

  return (
    <div
      className="w-full h-screen flex flex-col overflow-hidden relative"
      style={{
        fontFamily: "'Geist', system-ui, sans-serif",
        background: 'linear-gradient(180deg, #F4F2FB 0%, #F7F5FA 100%)',
        color: '#18181B',
      }}
    >
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full opacity-40 blur-3xl"
          style={{ background: 'radial-gradient(circle, #6366F1 0%, transparent 70%)' }} />
        <div className="absolute -bottom-40 -right-40 w-[700px] h-[700px] rounded-full opacity-30 blur-3xl"
          style={{ background: 'radial-gradient(circle, #A855F7 0%, transparent 70%)' }} />
        <div className="absolute top-1/3 right-1/3 w-[400px] h-[400px] rounded-full opacity-20 blur-3xl"
          style={{ background: 'radial-gradient(circle, #EC4899 0%, transparent 70%)' }} />
      </div>

      <nav className="relative z-10 border-b border-indigo-200/40 bg-white/60 backdrop-blur-md shrink-0">
        <div className="px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="relative w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-600 via-violet-600 to-fuchsia-600 flex items-center justify-center shadow-lg shadow-indigo-600/40">
              <Radio className="w-4 h-4 text-white" strokeWidth={2.5} />
              <div className="absolute inset-0 rounded-lg ring-1 ring-white/20" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-semibold tracking-tight text-[15px] text-zinc-900">Tech Projects</span>
              <span className="text-[10px] text-indigo-600 font-mono uppercase tracking-widest">reo.dev</span>
            </div>
          </div>
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-[11px] font-semibold text-white shadow-sm">SK</div>
        </div>
      </nav>

      <div className="relative z-10 flex-1 flex overflow-hidden">
        <aside className="w-[260px] shrink-0 border-r border-indigo-200/50 bg-white/70 backdrop-blur-sm flex flex-col overflow-hidden">
          <div className="p-5">
            <div className={`flex items-center gap-2 px-3 h-11 rounded-lg bg-white border transition-all ${
              input ? 'border-indigo-400 shadow-[0_0_0_3px_rgba(99,102,241,0.12)]' : 'border-zinc-200 hover:border-zinc-300'
            }`}>
              <span className="text-indigo-400 text-[13px] font-mono select-none">→</span>
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addDomain()}
                placeholder="Enter a domain"
                autoFocus
                className="flex-1 bg-transparent outline-none text-[13px] text-zinc-900 placeholder:text-zinc-400 min-w-0"
                style={{ fontFamily: "'Geist Mono', monospace" }}
              />
              <button
                onClick={() => addDomain()}
                disabled={!input.trim()}
                className="w-6 h-6 shrink-0 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white disabled:bg-zinc-100 disabled:text-zinc-300 transition-all flex items-center justify-center"
              >
                <Plus className="w-3.5 h-3.5" strokeWidth={2.5} />
              </button>
            </div>
            {domains.length === 0 && (
              <button onClick={loadExample}
                className="mt-3 text-[11px] text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1 group">
                <Sparkles className="w-3 h-3" />
                Try an example
                <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
              </button>
            )}
          </div>
          <div className="flex-1 overflow-y-auto px-3 pb-4">
            <div className="space-y-1">
              {domains.map((d) => (
                <DomainItem key={d} domain={d} status={domainStatus[d]} data={results[d]}
                  active={d === activeDomain}
                  onClick={() => { setActiveDomain(d); setActiveProject(0); }}
                  onRemove={() => removeDomain(d)} />
              ))}
            </div>
          </div>
        </aside>

        <main className="flex-1 overflow-y-auto">
          {!activeDomain ? (
            <EmptyState />
          ) : activeStatus === 'analyzing' ? (
            <ScannerView domain={activeDomain} />
          ) : activeStatus === 'error' ? (
            <ErrorView domain={activeDomain} />
          ) : (
            <ProjectsView data={activeData} domain={activeDomain}
              activeProject={activeProject} setActiveProject={setActiveProject} />
          )}
        </main>

        <aside className="w-[360px] shrink-0 border-l border-indigo-200/50 bg-white/70 backdrop-blur-sm overflow-y-auto">
          {activeStatus === 'done' && activeProjectData ? (
            <ProjectDetail project={activeProjectData} />
          ) : (
            <DetailPlaceholder loading={activeStatus === 'analyzing'} />
          )}
        </aside>
      </div>

      <style>{`
        @keyframes pulse-ring { 0% { transform: scale(0.55); opacity: 0.9; } 100% { transform: scale(1.15); opacity: 0; } }
        @keyframes pulse-dot { 0%, 100% { opacity: 0.4; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1.2); } }
        @keyframes sweep-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes orbit { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(300%); } }
        @keyframes rise { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes sparkle { 0%, 100% { opacity: 0.6; } 50% { opacity: 1; } }
      `}</style>
    </div>
  );
}

// ───────────────────────────────────────────────────────────
// LEFT
// ───────────────────────────────────────────────────────────

function DomainItem({ domain, status, data, active, onClick, onRemove }) {
  return (
    <div onClick={onClick}
      className={`relative group cursor-pointer rounded-lg border transition-all overflow-hidden ${
        active ? 'bg-gradient-to-br from-indigo-600 to-violet-600 border-indigo-600 shadow-lg shadow-indigo-600/25'
               : 'bg-white border-zinc-200 hover:border-indigo-300'
      }`}>
      <div className="px-3 py-2.5 flex items-center gap-2.5">
        <div className={`w-6 h-6 rounded-md shrink-0 flex items-center justify-center font-bold text-[10px] ${
          active ? 'bg-white/25 text-white ring-1 ring-white/40' : 'bg-gradient-to-br from-indigo-500 to-violet-600 text-white'
        }`}>
          {(data?.company?.[0] ?? domain[0]).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className={`text-[12px] truncate ${active ? 'text-white' : 'text-zinc-800'}`}
            style={{ fontFamily: "'Geist Mono', monospace" }}>{domain}</div>
        </div>
        {status === 'analyzing' && (
          <div className="flex items-center gap-0.5 shrink-0">
            {[0, 1, 2].map((i) => (
              <div key={i}
                className={`w-1 h-1 rounded-full animate-pulse ${active ? 'bg-amber-200' : 'bg-amber-400'}`}
                style={{ animationDelay: `${i * 200}ms` }} />
            ))}
          </div>
        )}
        <button onClick={(e) => { e.stopPropagation(); onRemove(); }}
          className={`w-4 h-4 rounded flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ${
            active ? 'hover:bg-white/20 text-white' : 'hover:bg-zinc-100 text-zinc-400'
          }`}>
          <X className="w-3 h-3" />
        </button>
      </div>
      {status === 'analyzing' && (
        <div className="absolute bottom-0 left-0 right-0 h-[2px] overflow-hidden">
          <div className="h-full w-1/2 bg-gradient-to-r from-transparent via-indigo-400 to-transparent"
            style={{ animation: 'shimmer 1.5s ease-in-out infinite' }} />
        </div>
      )}
    </div>
  );
}

// ───────────────────────────────────────────────────────────
// EMPTY
// ───────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="h-full flex items-center justify-center px-8">
      <div className="max-w-md text-center">
        <h1 className="text-[48px] leading-[1.05] text-zinc-900 mb-4"
          style={{ fontFamily: "'Instrument Serif', serif", letterSpacing: '-0.02em' }}>
          What is every company <br />
          <em className="text-indigo-700">actually</em> building?
        </h1>
        <p className="text-[14px] text-zinc-500 leading-relaxed max-w-sm mx-auto">
          Add a domain. We'll surface the projects worth knowing and the people behind them.
        </p>
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────────────────
// SCANNER
// ───────────────────────────────────────────────────────────

function ErrorView({ domain }) {
  return (
    <div className="h-full flex items-center justify-center px-8">
      <div className="max-w-sm text-center">
        <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
          <span className="text-red-500 text-xl font-bold">!</span>
        </div>
        <h2 className="text-[18px] font-semibold text-zinc-800 mb-2">Could not load data</h2>
        <p className="text-[13px] text-zinc-500 leading-relaxed">
          Failed to classify <span className="font-mono text-zinc-700">{domain}</span>.<br />
          The server may be unavailable or the domain has no active jobs.
        </p>
      </div>
    </div>
  );
}

function ScannerView({ domain }) {
  const lines = [
    'Reading careers pages',
    'Finding patterns in the data',
    'Mapping teams and structure',
    'Surfacing the right people',
  ];
  const [lineIdx, setLineIdx] = useState(0);
  useEffect(() => {
    setLineIdx(0);
    const id = setInterval(() => setLineIdx((i) => (i + 1) % lines.length), 900);
    return () => clearInterval(id);
  }, [domain]);

  return (
    <div className="h-full flex flex-col items-center justify-center p-10">
      <div className="relative w-72 h-72 mb-8">
        <div className="absolute inset-0 rounded-full border border-indigo-300" style={{ animation: 'pulse-ring 2s ease-out infinite' }} />
        <div className="absolute inset-0 rounded-full border border-violet-300" style={{ animation: 'pulse-ring 2s ease-out infinite 0.66s' }} />
        <div className="absolute inset-0 rounded-full border border-fuchsia-300" style={{ animation: 'pulse-ring 2s ease-out infinite 1.33s' }} />
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 288 288" style={{ animation: 'sweep-spin 3s linear infinite' }}>
          <defs>
            <linearGradient id="sweepGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#6366F1" stopOpacity="0" />
              <stop offset="100%" stopColor="#6366F1" stopOpacity="1" />
            </linearGradient>
          </defs>
          <path d="M 144 144 L 144 24 A 120 120 0 0 1 248 96 Z" fill="url(#sweepGrad)" opacity="0.35" />
        </svg>
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 288 288">
          <circle cx="144" cy="144" r="135" fill="none" stroke="#6366F1" strokeWidth="1" strokeDasharray="2 6" opacity="0.45" />
          <circle cx="144" cy="144" r="100" fill="none" stroke="#A855F7" strokeWidth="1" strokeDasharray="1 4" opacity="0.35" />
        </svg>
        <div className="absolute inset-10 rounded-full bg-white border border-indigo-200 shadow-[0_0_60px_rgba(99,102,241,0.4)] flex flex-col items-center justify-center">
          <div className="text-[13px] font-semibold text-zinc-900" style={{ fontFamily: "'Geist Mono', monospace" }}>{domain}</div>
          <div className="text-[10px] text-indigo-600 font-semibold tracking-widest uppercase mt-1.5 flex items-center gap-1.5">
            <span className="inline-block w-1 h-1 rounded-full bg-indigo-500" style={{ animation: 'pulse-dot 1s ease-in-out infinite' }} />
            Scanning
          </div>
        </div>
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="absolute inset-0" style={{ animation: 'orbit 4s linear infinite', animationDelay: `${i * 0.66}s` }}>
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 rounded-full bg-gradient-to-br from-indigo-500 to-fuchsia-500 shadow-md shadow-indigo-500/50" />
          </div>
        ))}
      </div>
      <div className="h-5 relative w-80 text-center">
        {lines.map((l, i) => (
          <div key={i} className="absolute inset-0 text-[13px] text-zinc-500 transition-opacity duration-500"
            style={{ opacity: lineIdx === i ? 1 : 0 }}>{l}…</div>
        ))}
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────────────────
// PROJECTS (hero)
// ───────────────────────────────────────────────────────────

function ProjectsView({ data, domain, activeProject, setActiveProject }) {
  const [projectFilter, setProjectFilter] = useState('');
  const [timeFilter, setTimeFilter] = useState('');

  const filteredProjects = data.projects.filter(p => {
    if (projectFilter && p.name !== projectFilter) return false;
    
    if (timeFilter) {
      if (!p.latest_job_date) return false;
      const jobDate = new Date(p.latest_job_date);
      const diffTime = Math.abs(new Date() - jobDate);
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
      if (diffDays > parseInt(timeFilter)) return false;
    }
    
    return true;
  });

  return (
    <div className="p-8 max-w-3xl mx-auto" style={{ animation: 'rise 0.4s ease-out' }}>
      <div className="mb-8">
        <h1 className="text-[40px] leading-none tracking-tight text-zinc-900 mb-2"
          style={{ fontFamily: "'Instrument Serif', serif", letterSpacing: '-0.02em' }}>
          {data.company}
        </h1>
        <div className="flex items-center gap-2 text-[12px] text-zinc-500">
          <a href={`https://${domain}`} target="_blank" rel="noopener noreferrer"
            className="hover:text-indigo-700 font-mono flex items-center gap-0.5 transition-colors">
            {domain}<ArrowUpRight className="w-3 h-3" />
          </a>
          <span className="text-zinc-300">·</span>
          <span>{data.description}</span>
        </div>
      </div>

      <div className="mb-4">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-1 h-5 rounded-full bg-gradient-to-b from-indigo-500 via-violet-500 to-fuchsia-500" />
          <h2 className="text-[18px] font-semibold tracking-tight text-zinc-900">Active tech projects</h2>
          
          <div className="ml-auto flex items-center gap-2 relative">
             <select 
               value={projectFilter} 
               onChange={(e) => setProjectFilter(e.target.value)} 
               className="px-2 py-1.5 bg-white border border-zinc-200 rounded-md text-[12px] w-48 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-shadow text-zinc-700"
             >
               <option value="">All Projects</option>
               {Object.entries(
                 data.projects.reduce((acc, p) => {
                   const d = p.domain || "Other Projects";
                   acc[d] = acc[d] || [];
                   if (!acc[d].includes(p.name)) acc[d].push(p.name);
                   return acc;
                 }, {})
               ).map(([domain, names], i) => (
                 <optgroup key={i} label={domain}>
                   {names.map((name, j) => (
                     <option key={`${i}-${j}`} value={name}>{name}</option>
                   ))}
                 </optgroup>
               ))}
             </select>
             
             <select 
               value={timeFilter} 
               onChange={(e) => setTimeFilter(e.target.value)} 
               className="px-2 py-1.5 bg-white border border-zinc-200 rounded-md text-[12px] w-36 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition-shadow text-zinc-700"
             >
               <option value="">Any time</option>
               <option value="7">Last 7 days</option>
               <option value="30">Last 30 days</option>
               <option value="60">Last 2 months</option>
               <option value="90">Last 3 months</option>
               <option value="180">Last 6 months</option>
             </select>
          </div>
        </div>
        <p className="text-[12px] text-zinc-500 ml-3">
          These are the {data.projects.length} initiatives {data.company} is actively building right now.
        </p>
      </div>

      <div className="space-y-2.5">
        {filteredProjects.map((p, i) => (
          <ProjectCard key={i} project={p} active={data.projects.indexOf(p) === activeProject} onClick={() => setActiveProject(data.projects.indexOf(p))} />
        ))}
        {filteredProjects.length === 0 && (
          <div className="text-[13px] text-zinc-500 text-center py-10 border border-dashed border-zinc-200 rounded-xl bg-zinc-50/50">
            No projects match your filter.
          </div>
        )}
      </div>
    </div>
  );
}

function ProjectCard({ project, active, onClick }) {
  return (
    <button onClick={onClick}
      className={`relative w-full text-left rounded-xl border p-5 transition-all overflow-hidden group ${
        active ? 'bg-white border-indigo-400 shadow-xl shadow-indigo-600/10'
               : 'bg-white/70 border-zinc-200 hover:border-indigo-200 hover:bg-white'
      }`}>
      {active && <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-indigo-500 via-violet-500 to-fuchsia-500" />}

      <div className="flex items-start justify-between gap-3 mb-1">
        <h3 className={`text-[16px] font-semibold tracking-tight leading-snug ${active ? 'text-indigo-900' : 'text-zinc-900'}`}>
          {project.name}
        </h3>
        <SignalStrength strength={project.strength} />
      </div>

      <div className="flex items-center gap-2 mb-4">
        <p className="text-[12.5px] text-zinc-500 leading-relaxed">{project.description}</p>
        {project.recency && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 font-medium border border-amber-200/50 whitespace-nowrap">
            {project.recency}
          </span>
        )}
      </div>

      <div className="flex items-baseline gap-3 mb-2">
        <span className="text-[10px] font-semibold text-zinc-400 tracking-wider uppercase shrink-0 w-16">Built with</span>
        <div className="flex flex-wrap gap-x-2 gap-y-0.5 text-[11.5px] text-zinc-700">
          {project.techStack.map((t, i) => (
            <span key={t} className="inline-flex items-center gap-2">
              <span style={{ fontFamily: "'Geist Mono', monospace" }}>{t}</span>
              {i < project.techStack.length - 1 && <span className="text-zinc-300">·</span>}
            </span>
          ))}
        </div>
      </div>

      <div className="flex items-baseline gap-3 mb-4">
        <span className="text-[10px] font-semibold text-zinc-400 tracking-wider uppercase shrink-0 w-16">Team</span>
        <div className="flex items-center gap-1.5 text-[11.5px] text-zinc-700">
          <GitBranch className="w-3 h-3 text-violet-500" />
          <span className="font-medium">{project.team.name}</span>
          <span className="text-zinc-300">·</span>
          <span className="text-zinc-500">{project.team.location}</span>
          {project.team.growing && (
            <>
              <span className="text-zinc-300">·</span>
              <TrendingUp className="w-3 h-3 text-emerald-600" />
              <span className="text-emerald-600 font-medium">growing</span>
            </>
          )}
        </div>
      </div>

      <div className="h-px bg-zinc-100 mb-3" />

      {project.people?.length > 0 ? (
        <div>
          <div className="text-[10px] font-semibold text-zinc-400 tracking-wider uppercase mb-2">Who's on it</div>
          <div className="space-y-1.5">
            {project.people.map((p, i) => (
              <div key={i} className="flex items-center gap-2.5">
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-400 to-violet-500 flex items-center justify-center text-[9px] font-bold text-white shrink-0">
                  {p.name.split(' ').map((n) => n[0]).slice(0, 2).join('')}
                </div>
                <div className="flex-1 min-w-0 flex items-baseline gap-1.5 text-[12px]">
                  <span className="font-semibold text-zinc-900 truncate">{p.name}</span>
                  <span className="text-zinc-300">·</span>
                  <span className="text-zinc-500 truncate">{p.role}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : project.jobCount ? (
        <div>
          <div className="text-[10px] font-semibold text-zinc-400 tracking-wider uppercase mb-2">Signal strength</div>
          <div className="flex items-center gap-2 text-[12px]">
            <Briefcase className="w-3.5 h-3.5 text-indigo-500" />
            <span className="font-semibold text-zinc-800">{project.jobCount} JDs</span>
            <span className="text-zinc-400">matched this project</span>
          </div>
        </div>
      ) : null}

      {active && (
        <div className="mt-4 pt-3 border-t border-zinc-100 flex items-center gap-1.5 text-[11px] text-indigo-600 font-medium">
          <Zap className="w-3 h-3" />
          <span>Evidence & signals in the right panel</span>
          <ChevronRight className="w-3.5 h-3.5 ml-auto" />
        </div>
      )}
    </button>
  );
}

function SignalStrength({ strength }) {
  const levels = { strong: 3, likely: 2, early: 1 };
  const n = levels[strength] ?? 1;
  const label = strength === 'strong' ? 'Strong signal' : strength === 'likely' ? 'Likely' : 'Early signal';
  const colorClass = strength === 'strong' ? 'bg-emerald-500' : strength === 'likely' ? 'bg-indigo-500' : 'bg-amber-400';
  return (
    <div className="shrink-0 flex items-center gap-1.5 pt-1" title={label}>
      <span className="text-[10px] text-zinc-500 font-medium">{label}</span>
      <div className="flex items-center gap-[3px]">
        {[1, 2, 3].map((i) => (
          <div key={i} className={`w-1 h-1 rounded-full ${i <= n ? colorClass : 'bg-zinc-200'}`} />
        ))}
      </div>
    </div>
  );
}

// ───────────────────────────────────────────────────────────
// RIGHT: OUTREACH COMPOSER (the logical next step)
// ───────────────────────────────────────────────────────────

function DetailPlaceholder({ loading }) {
  return (
    <div className="h-full flex flex-col items-center justify-center px-8 py-12 text-center">
      <div className="text-[12px] text-zinc-400 leading-relaxed max-w-[220px]">
        {loading ? 'Waiting for the scan to finish.' : 'Pick a project to see the draft outreach.'}
      </div>
    </div>
  );
}

function ProjectDetail({ project }) {
  const defaultRecipient = project.people?.[0] || { name: 'Generic HM', role: 'Hiring Manager' };
  const [recipient, setRecipient] = useState(defaultRecipient);
  const [copied, setCopied] = useState(false);
  const [showAllTech, setShowAllTech] = useState(false);
  const [showAllSignals, setShowAllSignals] = useState(false);
  const [showAllJobs, setShowAllJobs] = useState(false);

  useEffect(() => {
    setRecipient(project.people?.[0] || { name: 'Generic HM', role: 'Hiring Manager' });
    setCopied(false);
    setShowAllTech(false);
    setShowAllSignals(false);
    setShowAllJobs(false);
  }, [project]);

  const personalizedBody = project.outreach?.body?.replace(
    /Hi \[Name\]\,/,
    `Hi ${recipient.name.split(' ')[0]},`
  ) || '';

  const handleCopy = () => {
    const text = `Subject: ${project.outreach?.subject}\n\n${personalizedBody}\n\n--- Evidence ---\n${project.signals.join('\n')}`;
    navigator.clipboard?.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenInMail = () => {
    const subject = encodeURIComponent(project.outreach?.subject || '');
    const body = encodeURIComponent(personalizedBody);
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  };

  return (
    <div className="flex flex-col h-full" style={{ animation: 'rise 0.35s ease-out' }}>
      {/* Top: signal context */}
      <div className="p-5 border-b border-zinc-200/70">
        <div className="flex items-center gap-1.5 mb-2">
          <Zap className="w-3 h-3 text-indigo-600" />
          <span className="text-[10px] font-semibold text-indigo-700 tracking-widest uppercase">
            Why this matters
          </span>
        </div>
        <ul className="space-y-1.5">
          {(showAllSignals ? project.signals : (project.signals || []).slice(0, 3)).map((s, i) => (
            <li key={i} className="flex items-start gap-2 text-[11.5px] text-zinc-600 leading-relaxed">
              <div className="w-1 h-1 rounded-full bg-indigo-500 mt-[7px] shrink-0" />
              {s}
            </li>
          ))}
        </ul>
        {project.signals?.length > 3 && (
          <button 
            onClick={() => setShowAllSignals(!showAllSignals)}
            className="mt-2 text-[11px] font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
          >
            {showAllSignals ? 'Show less' : `+ ${project.signals.length - 3} more`}
          </button>
        )}
      </div>

      {/* Top Technologies */}
      {project.topTechnologies?.length > 0 && (
        <div className="p-5 border-b border-zinc-200/70 bg-zinc-50/50">
          <div className="text-[10px] font-semibold text-zinc-500 tracking-widest uppercase mb-2">
            Top Technologies
          </div>
          <div className="flex flex-wrap gap-1.5">
            {(showAllTech ? project.topTechnologies : project.topTechnologies.slice(0, 8)).map((tech, i) => (
              <span key={i} className="inline-flex items-center px-2 py-1 rounded bg-white border border-zinc-200 text-[10px] font-medium text-zinc-700 shadow-sm">
                {tech.replace(/-/g, ' ')}
              </span>
            ))}
            {project.topTechnologies.length > 8 && (
              <button 
                onClick={() => setShowAllTech(!showAllTech)}
                className="inline-flex items-center px-2 py-1 rounded bg-indigo-50 border border-indigo-100 text-[10px] font-semibold text-indigo-600 shadow-sm hover:bg-indigo-100 transition-colors"
              >
                {showAllTech ? 'Show less' : `+ ${project.topTechnologies.length - 8} more`}
              </button>
            )}
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        
        {/* Evidence & Jobs */}
        <div className="flex flex-col p-5 border-b border-zinc-200/70 bg-zinc-50/50">
          <div className="flex items-center gap-1.5 mb-3">
            <div className="relative">
              <Briefcase className="w-3.5 h-3.5 text-violet-600" />
            </div>
            <span className="text-[10px] font-semibold text-violet-700 tracking-widest uppercase">
              Job Links (Proof)
            </span>
          </div>

          {/* Jobs list with links */}
          {project.jobs?.length > 0 ? (
            <div className="space-y-2">
              {(showAllJobs ? project.jobs : project.jobs.slice(0, 3)).map((j, i) => (
                <div key={i} className="text-[11.5px] text-zinc-700 flex items-start gap-2">
                  <Briefcase className="w-3 h-3 text-zinc-400 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium">{j.title}</div>
                    {j.url && (
                      <a href={j.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline flex items-center gap-0.5 mt-0.5 text-[11px]">
                        View Posting <ArrowUpRight className="w-2.5 h-2.5" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
              {project.jobs?.length > 3 && (
                <button 
                  onClick={() => setShowAllJobs(!showAllJobs)}
                  className="mt-2 text-[11px] font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
                >
                  {showAllJobs ? 'Show less' : `+ ${project.jobs.length - 3} more`}
                </button>
              )}
            </div>
          ) : (
            <div className="text-[11px] text-zinc-500">No active job links found.</div>
          )}
        </div>

        {/* Outreach composer */}
        <div className="flex flex-col p-5">
          <div className="flex items-center gap-1.5 mb-3">
            <div className="relative">
              <Wand2 className="w-3.5 h-3.5 text-violet-600" />
              <Sparkles
                className="absolute -top-1 -right-1 w-2 h-2 text-fuchsia-500"
                style={{ animation: 'sparkle 1.8s ease-in-out infinite' }}
              />
            </div>
            <span className="text-[10px] font-semibold text-violet-700 tracking-widest uppercase">
              Draft outreach
            </span>
            <span className="ml-auto text-[9px] font-medium text-zinc-400 font-mono">
              AI-drafted
            </span>
          </div>

          {/* Recipient picker */}
          <div className="mb-3">
            <div className="text-[10px] font-semibold text-zinc-400 tracking-wider uppercase mb-1.5">To</div>
            <div className="space-y-1">
              {(project.people || []).map((p, i) => {
                const selected = recipient.name === p.name;
                return (
                  <button
                    key={i}
                    onClick={() => setRecipient(p)}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md border text-left transition-all ${
                      selected
                        ? 'bg-indigo-50 border-indigo-300'
                        : 'bg-white border-zinc-200 hover:border-indigo-200'
                    }`}
                  >
                    <div className={`w-5 h-5 rounded-full bg-gradient-to-br from-indigo-400 to-violet-500 flex items-center justify-center text-[8px] font-bold text-white shrink-0 ${selected ? 'ring-2 ring-indigo-300' : ''}`}>
                      {p.name.split(' ').map((n) => n[0]).slice(0, 2).join('')}
                    </div>
                    <div className="flex-1 min-w-0 flex items-baseline gap-1.5">
                      {p.url ? (
                        <a href={p.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className={`text-[11.5px] font-semibold truncate hover:underline ${selected ? 'text-indigo-900' : 'text-zinc-800'}`}>
                          {p.name}
                        </a>
                      ) : (
                        <span className={`text-[11.5px] font-semibold truncate ${selected ? 'text-indigo-900' : 'text-zinc-800'}`}>
                          {p.name}
                        </span>
                      )}
                      <span className="text-zinc-300 text-[11px]">·</span>
                      <span className="text-[11px] text-zinc-500 truncate">{p.role}</span>
                    </div>
                    {selected && <Check className="w-3 h-3 text-indigo-600 shrink-0" strokeWidth={3} />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Message card */}
          <div className="rounded-xl border border-violet-200 bg-gradient-to-br from-white via-white to-violet-50/40 overflow-hidden flex flex-col mb-3">
            <div className="px-4 py-2.5 border-b border-violet-100 bg-gradient-to-r from-indigo-50/60 to-violet-50/60">
              <div className="text-[9px] font-semibold text-violet-600 tracking-widest uppercase mb-0.5">Subject</div>
              <div className="text-[13px] font-semibold text-zinc-900">{project.outreach?.subject}</div>
            </div>
            <div className="px-4 py-3">
              <pre className="text-[12.5px] text-zinc-700 leading-relaxed whitespace-pre-wrap font-sans">
                {personalizedBody}
              </pre>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleOpenInMail}
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-700 hover:to-violet-700 text-white text-[12.5px] font-semibold transition-all shadow-md shadow-indigo-600/25"
            >
              <Mail className="w-3.5 h-3.5" />
              Open in mail
            </button>
            <button
              onClick={handleCopy}
              className={`inline-flex items-center justify-center gap-1 px-3 py-2.5 rounded-lg border text-[12px] font-semibold transition-all ${
                copied
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                  : 'bg-white border-zinc-200 text-zinc-700 hover:border-indigo-300 hover:text-indigo-700'
              }`}
            >
              {copied ? <><Check className="w-3 h-3" strokeWidth={3} />Copied</> : <><Copy className="w-3 h-3" />Copy</>}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
