import { useState, useEffect } from 'react'
import { statsApi } from '../services/api'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import { BarChart2, TrendingUp, Bell, CheckCircle } from 'lucide-react'

const PIE_COLORS = {
  sent: '#3b82f6',
  interview: '#f59e0b',
  accepted: '#10b981',
  rejected: '#ef4444',
  follow_up: '#8b5cf6',
}

const PIE_LABELS = {
  sent: 'Envoyées',
  interview: 'Entretiens',
  accepted: 'Acceptées',
  rejected: 'Refusées',
  follow_up: 'Relances',
}

export default function Stats() {
  const [stats, setStats] = useState(null)
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([statsApi.get(), statsApi.notifications()]).then(([sRes, nRes]) => {
      setStats(sRes.data)
      setNotifications(nRes.data)
    }).finally(() => setLoading(false))
  }, [])

  const markRead = async (id) => {
    await statsApi.markRead(id)
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n))
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>
  )

  const pieData = stats ? [
    { name: 'Envoyées', value: stats.sent, key: 'sent' },
    { name: 'Entretiens', value: stats.interviews, key: 'interview' },
    { name: 'Acceptées', value: stats.accepted, key: 'accepted' },
    { name: 'Refusées', value: stats.rejected, key: 'rejected' },
    { name: 'Relances', value: stats.follow_up, key: 'follow_up' },
  ].filter(d => d.value > 0) : []

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Statistiques</h1>
        <p className="text-gray-500 mt-1">Analyse de votre recherche d'alternance</p>
      </div>

      {stats && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {[
              { label: 'Candidatures', value: stats.total_applications, color: 'text-blue-600', bg: 'bg-blue-50' },
              { label: 'Taux de réponse', value: `${stats.response_rate}%`, color: 'text-indigo-600', bg: 'bg-indigo-50' },
              { label: 'Taux d\'entretien', value: `${stats.interview_rate}%`, color: 'text-yellow-600', bg: 'bg-yellow-50' },
              { label: 'Acceptées', value: stats.accepted, color: 'text-green-600', bg: 'bg-green-50' },
            ].map(({ label, value, color, bg }) => (
              <div key={label} className="card text-center">
                <p className={`text-3xl font-bold ${color}`}>{value}</p>
                <p className="text-sm text-gray-500 mt-1">{label}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            {/* Pie Chart */}
            {pieData.length > 0 && (
              <div className="card">
                <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <BarChart2 size={18} className="text-blue-600" />
                  Répartition des candidatures
                </h2>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                      {pieData.map((entry) => (
                        <Cell key={entry.key} fill={PIE_COLORS[entry.key]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Monthly Activity */}
            {stats.applications_by_month?.length > 0 && (
              <div className="card">
                <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <TrendingUp size={18} className="text-blue-600" />
                  Activité mensuelle
                </h2>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={stats.applications_by_month}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" name="Candidatures" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Top Skills */}
          {stats.top_skills_demanded?.length > 0 && (
            <div className="card mb-6">
              <h2 className="font-semibold text-gray-900 mb-4">Technologies les plus demandées</h2>
              <div className="space-y-3">
                {stats.top_skills_demanded.map(({ skill, count }, i) => (
                  <div key={skill} className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 w-4">{i + 1}</span>
                    <span className="text-sm font-medium text-gray-700 w-24 truncate capitalize">{skill}</span>
                    <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${(count / stats.top_skills_demanded[0].count) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 w-8 text-right">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {stats.total_applications === 0 && (
            <div className="card text-center py-12">
              <BarChart2 size={48} className="text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 font-medium">Aucune statistique disponible</p>
              <p className="text-sm text-gray-400 mt-1">Commencez à postuler pour voir vos données</p>
            </div>
          )}
        </>
      )}

      {/* Notifications */}
      <div className="card">
        <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Bell size={18} className="text-blue-600" />
          Notifications
          {notifications.filter(n => !n.read).length > 0 && (
            <span className="bg-red-500 text-white text-xs rounded-full px-2 py-0.5">
              {notifications.filter(n => !n.read).length}
            </span>
          )}
        </h2>

        {notifications.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-6">Aucune notification</p>
        ) : (
          <div className="space-y-2">
            {notifications.map((notif) => (
              <div
                key={notif.id}
                className={`flex items-start justify-between p-3 rounded-lg ${notif.read ? 'bg-gray-50' : 'bg-blue-50 border border-blue-100'}`}
              >
                <div className="flex items-start gap-2">
                  <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${notif.read ? 'bg-gray-300' : 'bg-blue-500'}`} />
                  <p className="text-sm text-gray-700">{notif.message}</p>
                </div>
                {!notif.read && (
                  <button
                    onClick={() => markRead(notif.id)}
                    className="text-xs text-blue-600 hover:underline flex-shrink-0 ml-2 flex items-center gap-1"
                  >
                    <CheckCircle size={12} />
                    Lu
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
