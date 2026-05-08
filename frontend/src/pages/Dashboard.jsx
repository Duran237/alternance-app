import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { statsApi, jobsApi, automationApi } from '../services/api'
import { Send, Calendar, XCircle, CheckCircle, TrendingUp, Search, Bell, ArrowRight, Moon, Zap } from 'lucide-react'

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

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [recommended, setRecommended] = useState([])
  const [nightReport, setNightReport] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      statsApi.get(),
      jobsApi.recommended(),
      automationApi.getLatestReport(),
    ]).then(([statsRes, jobsRes, reportRes]) => {
      setStats(statsRes.data)
      setRecommended(jobsRes.data.slice(0, 5))
      setNightReport(reportRes.data)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>
  )

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Bonjour, {user?.name?.split(' ')[0]} 👋</h1>
        <p className="text-gray-500 mt-1">Voici un aperçu de ta recherche d'alternance</p>
      </div>

      {/* Rapport nocturne */}
      {nightReport && nightReport.drafts_prepared > 0 && (
        <div className="card bg-gradient-to-r from-indigo-50 to-blue-50 border-indigo-200 mb-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center flex-shrink-0">
                <Moon size={18} className="text-white" />
              </div>
              <div>
                <h2 className="font-semibold text-gray-900">Rapport de nuit</h2>
                <p className="text-sm text-gray-600 mt-0.5">
                  <span className="font-medium text-blue-700">{nightReport.new_jobs_found} nouvelles offres</span>
                  {' · '}
                  <span className="font-medium text-green-700">{nightReport.compatible_jobs} compatibles</span>
                  {' · '}
                  <span className="font-medium text-purple-700">{nightReport.drafts_prepared} candidatures prêtes</span>
                </p>
              </div>
            </div>
            <Link
              to="/automation"
              className="btn-primary text-sm flex items-center gap-1 flex-shrink-0"
            >
              <Zap size={14} />
              Valider les candidatures
            </Link>
          </div>
        </div>
      )}

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
