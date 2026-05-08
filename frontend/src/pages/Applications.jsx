import { useState, useEffect } from 'react'
import { applicationsApi } from '../services/api'
import { Briefcase, ExternalLink, FileText, Mail, Trash2, ChevronDown, ChevronUp, Edit } from 'lucide-react'

const STATUS_LABELS = {
  sent: 'Envoyée',
  interview: 'Entretien',
  accepted: 'Acceptée',
  rejected: 'Refusée',
  follow_up: 'Relance',
}

const STATUS_OPTIONS = Object.entries(STATUS_LABELS)

function StatusBadge({ status }) {
  return <span className={`badge-${status}`}>{STATUS_LABELS[status] || status}</span>
}

function ApplicationCard({ app, onUpdate, onDelete }) {
  const [expanded, setExpanded] = useState(false)
  const [loadingLetter, setLoadingLetter] = useState(false)
  const [loadingEmail, setLoadingEmail] = useState(false)
  const [letter, setLetter] = useState(app.cover_letter || '')
  const [email, setEmail] = useState('')
  const [updating, setUpdating] = useState(false)
  const [status, setStatus] = useState(app.status)

  const handleStatusChange = async (newStatus) => {
    setUpdating(true)
    try {
      await onUpdate(app.id, { status: newStatus })
      setStatus(newStatus)
    } finally {
      setUpdating(false)
    }
  }

  const handleGenerateLetter = async () => {
    setLoadingLetter(true)
    try {
      const res = await applicationsApi.generateLetter(app.id)
      setLetter(res.data.cover_letter)
    } finally {
      setLoadingLetter(false)
    }
  }

  const handleGenerateEmail = async () => {
    setLoadingEmail(true)
    try {
      const res = await applicationsApi.generateEmail(app.id)
      setEmail(res.data.email)
    } finally {
      setLoadingEmail(false)
    }
  }

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-gray-900">{app.job_title}</h3>
            <StatusBadge status={status} />
            {app.match_score !== null && (
              <span className="text-xs text-gray-500">Match: {app.match_score}%</span>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {app.company} {app.location ? `· ${app.location}` : ''}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Envoyée le {new Date(app.sent_at).toLocaleDateString('fr-FR')}
          </p>
          {app.email_sent_to ? (
            <span className="inline-flex items-center gap-1 text-xs bg-green-50 text-green-700 border border-green-200 px-2 py-1 rounded-full mt-1">
              <Mail size={11} />
              Email envoyé au recruteur · {app.email_sent_to}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-xs bg-yellow-50 text-yellow-700 border border-yellow-200 px-2 py-1 rounded-full mt-1">
              <ExternalLink size={11} />
              À postuler manuellement sur le site
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {app.job_url && (
            <a href={app.job_url} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-blue-600 transition-colors">
              <ExternalLink size={16} />
            </a>
          )}
          <button onClick={() => onDelete(app.id)} className="text-gray-400 hover:text-red-600 transition-colors">
            <Trash2 size={16} />
          </button>
          <button onClick={() => setExpanded(!expanded)} className="text-gray-400 hover:text-gray-600 transition-colors">
            {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-100 space-y-4">
          {/* Status Update */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Mettre à jour le statut</label>
            <div className="flex flex-wrap gap-2">
              {STATUS_OPTIONS.map(([value, label]) => (
                <button
                  key={value}
                  onClick={() => handleStatusChange(value)}
                  disabled={updating || status === value}
                  className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                    status === value
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Cover Letter */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700 flex items-center gap-1">
                <FileText size={14} />
                Lettre de motivation
              </label>
              <button
                onClick={handleGenerateLetter}
                disabled={loadingLetter}
                className="text-xs text-blue-600 hover:underline"
              >
                {loadingLetter ? 'Génération...' : 'Régénérer avec IA'}
              </button>
            </div>
            {letter ? (
              <pre className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap font-sans max-h-48 overflow-y-auto">
                {letter}
              </pre>
            ) : (
              <button onClick={handleGenerateLetter} disabled={loadingLetter} className="btn-secondary text-sm w-full">
                {loadingLetter ? 'Génération en cours...' : 'Générer la lettre de motivation'}
              </button>
            )}
          </div>

          {/* Email */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-gray-700 flex items-center gap-1">
                <Mail size={14} />
                Email de candidature
              </label>
            </div>
            {email ? (
              <pre className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap font-sans max-h-36 overflow-y-auto">
                {email}
              </pre>
            ) : (
              <button onClick={handleGenerateEmail} disabled={loadingEmail} className="btn-secondary text-sm w-full">
                {loadingEmail ? 'Génération...' : 'Générer l\'email'}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function Applications() {
  const [apps, setApps] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  const fetchApps = async () => {
    try {
      const res = await applicationsApi.list()
      setApps(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchApps() }, [])

  const handleUpdate = async (id, data) => {
    await applicationsApi.update(id, data)
    setApps(prev => prev.map(a => a.id === id ? { ...a, ...data } : a))
  }

  const handleDelete = async (id) => {
    if (!confirm('Supprimer cette candidature ?')) return
    await applicationsApi.delete(id)
    setApps(prev => prev.filter(a => a.id !== id))
  }

  const filtered = filter === 'all' ? apps : apps.filter(a => a.status === filter)

  const counts = apps.reduce((acc, a) => {
    acc[a.status] = (acc[a.status] || 0) + 1
    return acc
  }, {})

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Mes candidatures</h1>
        <p className="text-gray-500 mt-1">{apps.length} candidature(s) au total</p>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap mb-6">
        {[['all', 'Toutes', apps.length], ...Object.entries(STATUS_LABELS).map(([k, v]) => [k, v, counts[k] || 0])].map(([value, label, count]) => (
          <button
            key={value}
            onClick={() => setFilter(value)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === value ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {label} <span className="ml-1 opacity-70">({count})</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 card">
          <Briefcase size={40} className="text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">Aucune candidature</p>
          <p className="text-sm text-gray-400 mt-1">
            {filter === 'all' ? 'Postulez à des offres depuis la page Offres' : `Aucune candidature avec le statut "${STATUS_LABELS[filter]}"`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((app) => (
            <ApplicationCard
              key={app.id}
              app={app}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}
