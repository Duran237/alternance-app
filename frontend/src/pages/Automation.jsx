import { useState, useEffect } from 'react'
import { automationApi } from '../services/api'
import {
  Moon, Play, RefreshCw, CheckCircle, XCircle, ExternalLink,
  Briefcase, Clock, TrendingUp, FileText, Zap
} from 'lucide-react'

function ReportCard({ report }) {
  const date = new Date(report.run_at)
  const isToday = new Date().toDateString() === date.toDateString()

  return (
    <div className="card border-l-4 border-blue-500">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Moon size={18} className="text-blue-600" />
            <h3 className="font-semibold text-gray-900">
              Rapport {isToday ? "d'aujourd'hui" : "du " + date.toLocaleDateString('fr-FR')}
            </h3>
          </div>
          <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
            <Clock size={12} />
            Exécuté à {date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
            {report.keywords_used && ` · mots-clés : "${report.keywords_used}"`}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center p-3 bg-blue-50 rounded-xl">
          <p className="text-2xl font-bold text-blue-700">{report.new_jobs_found}</p>
          <p className="text-xs text-blue-600 mt-1">Nouvelles offres</p>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-xl">
          <p className="text-2xl font-bold text-green-700">{report.compatible_jobs}</p>
          <p className="text-xs text-green-600 mt-1">Compatibles</p>
        </div>
        <div className="text-center p-3 bg-purple-50 rounded-xl">
          <p className="text-2xl font-bold text-purple-700">{report.drafts_prepared}</p>
          <p className="text-xs text-purple-600 mt-1">Candidatures prêtes</p>
        </div>
      </div>

      {report.top_jobs?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Meilleures offres trouvées</p>
          <div className="space-y-2">
            {report.top_jobs.map((job, i) => (
              <div key={i} className="flex items-center justify-between py-1.5 px-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-800">{job.title}</p>
                  <p className="text-xs text-gray-500">{job.company}{job.location ? ` · ${job.location}` : ''}</p>
                </div>
                <span className={`text-xs font-bold px-2 py-1 rounded-full ${
                  job.score >= 70 ? 'bg-green-100 text-green-700' :
                  job.score >= 40 ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {job.score}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function DraftCard({ draft, onValidate, onDiscard }) {
  const [showLetter, setShowLetter] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleValidate = async () => {
    setLoading(true)
    try { await onValidate(draft.id) } finally { setLoading(false) }
  }

  const handleDiscard = async () => {
    setLoading(true)
    try { await onDiscard(draft.id) } finally { setLoading(false) }
  }

  return (
    <div className="card border border-purple-200 bg-purple-50/30">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-purple-100 text-purple-700 text-xs font-semibold px-2 py-0.5 rounded-full flex items-center gap-1">
              <Zap size={10} />
              Prête à envoyer
            </span>
            {draft.match_score && (
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                draft.match_score >= 70 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
              }`}>
                {draft.match_score}% match
              </span>
            )}
          </div>
          <h3 className="font-semibold text-gray-900">{draft.job_title}</h3>
          <p className="text-sm text-gray-500">{draft.company}{draft.location ? ` · ${draft.location}` : ''}</p>
        </div>
        {draft.job_url && (
          <a href={draft.job_url} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-blue-600 flex-shrink-0">
            <ExternalLink size={16} />
          </a>
        )}
      </div>

      {draft.cover_letter && (
        <div className="mt-3">
          <button
            onClick={() => setShowLetter(!showLetter)}
            className="text-xs text-blue-600 hover:underline flex items-center gap-1"
          >
            <FileText size={12} />
            {showLetter ? 'Masquer' : 'Voir'} la lettre de motivation générée
          </button>
          {showLetter && (
            <pre className="mt-2 bg-white border border-gray-200 rounded-lg p-4 text-xs text-gray-700 whitespace-pre-wrap font-sans max-h-40 overflow-y-auto">
              {draft.cover_letter}
            </pre>
          )}
        </div>
      )}

      <div className="flex gap-2 mt-4 pt-3 border-t border-purple-100">
        <button
          onClick={handleValidate}
          disabled={loading}
          className="btn-primary text-sm flex items-center gap-1 flex-1 justify-center"
        >
          <CheckCircle size={14} />
          Valider & Marquer envoyée
        </button>
        <button
          onClick={handleDiscard}
          disabled={loading}
          className="btn-secondary text-sm flex items-center gap-1 px-3"
        >
          <XCircle size={14} />
          Ignorer
        </button>
      </div>
    </div>
  )
}

export default function Automation() {
  const [latestReport, setLatestReport] = useState(null)
  const [history, setHistory] = useState([])
  const [drafts, setDrafts] = useState([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [tab, setTab] = useState('drafts')

  const loadData = async () => {
    try {
      const [reportRes, historyRes, draftsRes] = await Promise.all([
        automationApi.getLatestReport(),
        automationApi.getHistory(),
        automationApi.getDrafts(),
      ])
      setLatestReport(reportRes.data)
      setHistory(historyRes.data)
      setDrafts(draftsRes.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const handleRunNow = async () => {
    setRunning(true)
    try {
      const res = await automationApi.runNow()
      setLatestReport(res.data)
      await loadData()
    } finally {
      setRunning(false)
    }
  }

  const handleValidate = async (id) => {
    await automationApi.validateDraft(id)
    setDrafts(prev => prev.filter(d => d.id !== id))
  }

  const handleDiscard = async (id) => {
    await automationApi.discardDraft(id)
    setDrafts(prev => prev.filter(d => d.id !== id))
  }

  return (
    <div className="p-8">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Moon size={24} className="text-blue-600" />
            Mode automatique nocturne
          </h1>
          <p className="text-gray-500 mt-1">
            Chaque nuit à 2h00, l'app scanne les offres et prépare tes candidatures.
          </p>
        </div>
        <button
          onClick={handleRunNow}
          disabled={running}
          className="btn-primary flex items-center gap-2"
        >
          {running ? <RefreshCw size={16} className="animate-spin" /> : <Play size={16} />}
          {running ? 'En cours...' : 'Lancer maintenant'}
        </button>
      </div>

      {/* Explication */}
      <div className="card bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-center text-sm">
          {[
            { icon: '🔍', label: 'Scan des offres', desc: 'Indeed, HelloWork...' },
            { icon: '🧠', label: 'Analyse & matching', desc: 'Score de compatibilité' },
            { icon: '✍️', label: 'Génération lettres', desc: 'Personnalisées par IA' },
            { icon: '📋', label: 'Candidatures prêtes', desc: 'Tu valides au matin' },
          ].map(({ icon, label, desc }) => (
            <div key={label}>
              <div className="text-2xl mb-1">{icon}</div>
              <p className="font-medium text-gray-800">{label}</p>
              <p className="text-gray-500 text-xs">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : (
        <>
          {/* Tabs */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setTab('drafts')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === 'drafts' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
            >
              Candidatures à valider
              {drafts.length > 0 && (
                <span className="ml-2 bg-purple-500 text-white text-xs rounded-full px-1.5 py-0.5">{drafts.length}</span>
              )}
            </button>
            <button
              onClick={() => setTab('reports')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === 'reports' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
            >
              Historique des rapports
            </button>
          </div>

          {tab === 'drafts' && (
            <>
              {drafts.length === 0 ? (
                <div className="card text-center py-16">
                  <Briefcase size={40} className="text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 font-medium">Aucune candidature en attente</p>
                  <p className="text-sm text-gray-400 mt-1">Lancez le mode automatique pour préparer des candidatures</p>
                  <button onClick={handleRunNow} disabled={running} className="btn-primary mt-4 flex items-center gap-2 mx-auto">
                    <Play size={16} />
                    Lancer maintenant
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <p className="text-sm text-gray-500">{drafts.length} candidature(s) préparée(s), prêtes à valider</p>
                  {drafts.map((draft) => (
                    <DraftCard
                      key={draft.id}
                      draft={draft}
                      onValidate={handleValidate}
                      onDiscard={handleDiscard}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {tab === 'reports' && (
            <>
              {history.length === 0 ? (
                <div className="card text-center py-16">
                  <TrendingUp size={40} className="text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500 font-medium">Aucun rapport disponible</p>
                  <p className="text-sm text-gray-400 mt-1">Le premier rapport apparaîtra après la première exécution</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {history.map((report) => (
                    <ReportCard key={report.id} report={report} />
                  ))}
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
