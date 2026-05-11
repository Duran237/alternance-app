import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { statsApi, jobsApi, automationApi, applicationsApi } from '../services/api'
import { Send, Calendar, XCircle, CheckCircle, TrendingUp, Search, Bell, ArrowRight, Moon, Zap, ChevronDown, ChevronUp, X, Copy, ExternalLink } from 'lucide-react'

function ApplyModal({ application, onClose }) {
  const [copied, setCopied] = useState(false)
  const emailSent = !!application.email_sent_to

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Candidature enregistrée</h2>
            <p className="text-sm text-gray-500 mt-0.5">{application.job_title} — {application.company}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>

        <div className={`px-6 py-3 text-sm font-medium flex items-center gap-2 ${emailSent ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-700'}`}>
          <CheckCircle size={16} />
          {emailSent ? `Email envoyé au recruteur (${application.email_sent_to})` : 'Copie ta lettre et postule sur le site de l\'offre'}
        </div>

        {application.cover_letter && (
          <div className="flex-1 overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-700">Ta lettre de motivation :</p>
              <button
                onClick={() => { navigator.clipboard.writeText(application.cover_letter); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
              >
                <Copy size={13} />{copied ? 'Copié !' : 'Copier'}
              </button>
            </div>
            <pre className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 border border-gray-200 rounded-lg p-4 leading-relaxed font-sans">
              {application.cover_letter}
            </pre>
          </div>
        )}

        <div className="p-6 border-t flex gap-3">
          {application.job_url && (
            <a href={application.job_url} target="_blank" rel="noopener noreferrer"
              className="btn-primary flex items-center gap-2 text-sm">
              <ExternalLink size={14} />Voir l'offre
            </a>
          )}
          <button onClick={onClose} className="btn-secondary text-sm">Fermer</button>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, icon: Icon, color, bg }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`w-12 h-12 ${bg} rounded-xl flex items-center justify-center flex-shrink-0`}>
        <Icon size={22} className={color} />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  )
}

function NightReports({ reports }) {
  const [expanded, setExpanded] = useState(false)
  const [applying, setApplying] = useState(null)
  const [appliedIds, setAppliedIds] = useState(new Set())
  const [modal, setModal] = useState(null)

  // Filter reports from last 12h (night session: 2h–7h)
  const cutoff = new Date(Date.now() - 12 * 60 * 60 * 1000)
  const nightReports = reports.filter(r => new Date(r.run_at) >= cutoff)

  if (nightReports.length === 0) return null

  const totalJobs = nightReports.reduce((s, r) => s + r.new_jobs_found, 0)
  const totalCompatible = nightReports.reduce((s, r) => s + r.compatible_jobs, 0)
  const totalDrafts = nightReports.reduce((s, r) => s + r.drafts_prepared, 0)

  if (totalDrafts === 0 && totalJobs === 0 && totalCompatible === 0) return null

  const fmt = (dateStr) => {
    const d = new Date(dateStr)
    return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
  }

  const handleApply = async (job) => {
    if (!job.id || appliedIds.has(job.id)) return
    setApplying(job.id)
    try {
      const res = await applicationsApi.create({ job_id: job.id, generate_letter: true })
      setAppliedIds(prev => new Set([...prev, job.id]))
      setModal(res.data)
    } catch (e) {
      if (e.response?.status === 409) {
        setAppliedIds(prev => new Set([...prev, job.id]))
      }
    } finally {
      setApplying(null)
    }
  }

  // Dédupliquer les top_jobs de tous les rapports (par titre+entreprise)
  const seen = new Set()
  const allTopJobs = nightReports.flatMap(r => r.top_jobs || []).filter(job => {
    const key = `${job.title}|${job.company}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  }).sort((a, b) => b.score - a.score).slice(0, 8)

  return (
    <>
    {modal && <ApplyModal application={modal} onClose={() => setModal(null)} />}
    <div className="card bg-gradient-to-r from-indigo-50 to-blue-50 border-indigo-200 mb-6">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-start gap-3 flex-1">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center flex-shrink-0">
            <Moon size={18} className="text-white" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h2 className="font-semibold text-gray-900">Rapport de nuit</h2>
              <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
                {nightReports.length} passage{nightReports.length > 1 ? 's' : ''}
              </span>
            </div>
            <p className="text-sm text-gray-600 mt-0.5">
              <span className="font-medium text-blue-700">{totalJobs} nouvelles offres</span>
              {' · '}
              <span className="font-medium text-green-700">{totalCompatible} compatibles</span>
              {' · '}
              <span className="font-medium text-purple-700">{totalDrafts} candidatures prêtes</span>
            </p>
          </div>
        </div>
        {totalDrafts > 0 && (
          <Link
            to="/automation"
            className="btn-primary text-sm flex items-center gap-1 flex-shrink-0"
          >
            <Zap size={14} />
            Valider
          </Link>
        )}
      </div>

      {/* Top offres compatibles */}
      {allTopJobs.length > 0 && (
        <div className="mt-2 space-y-1.5">
          {allTopJobs.map((job, i) => {
            const already = appliedIds.has(job.id)
            return (
              <div key={i} className="flex items-center justify-between bg-white/70 rounded-lg px-3 py-2 gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-900 truncate">{job.title}</p>
                  <p className="text-xs text-gray-500 truncate">{job.company}{job.location ? ` · ${job.location}` : ''}</p>
                </div>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full flex-shrink-0 ${
                  job.score >= 70 ? 'bg-green-100 text-green-700' :
                  job.score >= 40 ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {job.score}%
                </span>
                {job.id && (
                  already ? (
                    <span className="text-xs text-green-600 font-medium flex-shrink-0 flex items-center gap-1">
                      <CheckCircle size={12} /> Postulé
                    </span>
                  ) : (
                    <button
                      onClick={() => handleApply(job)}
                      disabled={applying === job.id}
                      className="text-xs bg-indigo-600 text-white px-2 py-1 rounded-lg hover:bg-indigo-700 flex-shrink-0 disabled:opacity-50"
                    >
                      {applying === job.id ? '...' : 'Postuler'}
                    </button>
                  )
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Détail par passage */}
      {nightReports.length > 1 && (
        <button
          onClick={() => setExpanded(e => !e)}
          className="mt-3 text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
        >
          {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {expanded ? 'Masquer les passages' : 'Voir les détails par passage'}
        </button>
      )}

      {expanded && (
        <div className="mt-2 space-y-1">
          {nightReports.map(r => (
            <div key={r.id} className="flex items-center gap-3 text-xs bg-white/50 rounded px-3 py-1.5">
              <span className="font-mono text-gray-400 w-10 flex-shrink-0">{fmt(r.run_at)}</span>
              <span className="text-blue-600">{r.new_jobs_found} offres</span>
              <span className="text-gray-300">·</span>
              <span className="text-green-600">{r.compatible_jobs} compatibles</span>
              <span className="text-gray-300">·</span>
              <span className="text-purple-600">{r.drafts_prepared} brouillons</span>
            </div>
          ))}
        </div>
      )}
    </div>
    </>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [recommended, setRecommended] = useState([])
  const [nightReports, setNightReports] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      statsApi.get(),
      jobsApi.recommended(),
      automationApi.getHistory(),
    ]).then(([statsRes, jobsRes, historyRes]) => {
      setStats(statsRes.data)
      setRecommended(jobsRes.data.slice(0, 5))
      setNightReports(historyRes.data || [])
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>
  )

  return (
    <div className="p-4 md:p-8">
      <div className="mb-6 md:mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Bonjour, {user?.name?.split(' ')[0]} 👋</h1>
        <p className="text-gray-500 mt-1">Voici un aperçu de ta recherche d'alternance</p>
      </div>

      {/* Rapports nocturnes */}
      <NightReports reports={nightReports} />

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Candidatures" value={stats.total_applications} icon={Send} color="text-blue-600" bg="bg-blue-50" />
          <StatCard label="Entretiens" value={stats.interviews} icon={Calendar} color="text-yellow-600" bg="bg-yellow-50" />
          <StatCard label="Refus" value={stats.rejected} icon={XCircle} color="text-red-600" bg="bg-red-50" />
          <StatCard label="Acceptées" value={stats.accepted} icon={CheckCircle} color="text-green-600" bg="bg-green-50" />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Response Rate */}
        {stats && (
          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp size={18} className="text-blue-600" />
              Taux de performance
            </h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Taux de réponse</span>
                  <span className="font-medium">{stats.response_rate}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: `${stats.response_rate}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Taux d'entretien</span>
                  <span className="font-medium">{stats.interview_rate}%</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-yellow-500 rounded-full" style={{ width: `${stats.interview_rate}%` }} />
                </div>
              </div>
            </div>
            {stats.total_applications === 0 && (
              <p className="text-sm text-gray-400 mt-4 text-center">
                Commencez à postuler pour voir vos statistiques
              </p>
            )}
          </div>
        )}

        {/* Recommended Jobs */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <Search size={18} className="text-blue-600" />
              Offres recommandées
            </h2>
            <Link to="/jobs" className="text-blue-600 text-sm hover:underline flex items-center gap-1">
              Voir tout <ArrowRight size={14} />
            </Link>
          </div>

          {recommended.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-400 text-sm">Aucune offre trouvée</p>
              <Link to="/jobs" className="btn-primary mt-3 inline-flex items-center gap-2 text-sm">
                <Search size={14} />
                Rechercher des offres
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {recommended.map((job) => (
                <div key={job.id} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm text-gray-900 truncate">{job.title}</p>
                    <p className="text-xs text-gray-500 truncate">{job.company} · {job.location}</p>
                  </div>
                  {job.match_score !== null && (
                    <span className={`text-xs font-semibold px-2 py-1 rounded-full ml-2 flex-shrink-0 ${
                      job.match_score >= 70 ? 'bg-green-100 text-green-700' :
                      job.match_score >= 40 ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {job.match_score}%
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick actions */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link to="/jobs" className="card hover:shadow-md transition-shadow flex items-center gap-3 cursor-pointer">
          <Search size={20} className="text-blue-600" />
          <div>
            <p className="font-medium text-sm">Rechercher des offres</p>
            <p className="text-xs text-gray-500">Scraping automatique</p>
          </div>
        </Link>
        <Link to="/applications" className="card hover:shadow-md transition-shadow flex items-center gap-3 cursor-pointer">
          <Send size={20} className="text-green-600" />
          <div>
            <p className="font-medium text-sm">Mes candidatures</p>
            <p className="text-xs text-gray-500">Suivi en temps réel</p>
          </div>
        </Link>
        <Link to="/profile" className="card hover:shadow-md transition-shadow flex items-center gap-3 cursor-pointer">
          <Bell size={20} className="text-purple-600" />
          <div>
            <p className="font-medium text-sm">Mon profil</p>
            <p className="text-xs text-gray-500">CV et compétences</p>
          </div>
        </Link>
      </div>
    </div>
  )
}
