import { useState } from 'react'
import { jobsApi, applicationsApi, userApi } from '../services/api'
import { Search, RefreshCw, ExternalLink, Send, MapPin, Building2, Zap, CheckCircle, User, Copy, X } from 'lucide-react'

function CoverLetterModal({ application, onClose }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(application.cover_letter || '')
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const isFranceTravail = application.job_url?.includes('francetravail.fr')
  const emailSent = !!application.email_sent_to

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Candidature enregistrée</h2>
            <p className="text-sm text-gray-500 mt-0.5">{application.job_title} — {application.company}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>

        {/* Status banner */}
        <div className={`px-6 py-3 text-sm font-medium flex items-center gap-2 ${
          emailSent
            ? 'bg-green-50 text-green-700'
            : isFranceTravail
            ? 'bg-blue-50 text-blue-700'
            : 'bg-yellow-50 text-yellow-700'
        }`}>
          <CheckCircle size={16} />
          {emailSent
            ? `Email envoyé directement au recruteur (${application.email_sent_to})`
            : isFranceTravail
            ? 'Offre France Travail — copie ta lettre puis postule sur le site'
            : 'Copie ta lettre puis postule sur le site de l\'offre'}
        </div>

        {/* Cover letter */}
        {application.cover_letter && (
          <div className="flex-1 overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-700">Ta lettre de motivation :</p>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
              >
                <Copy size={13} />
                {copied ? 'Copié !' : 'Copier'}
              </button>
            </div>
            <pre className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 border border-gray-200 rounded-lg p-4 leading-relaxed font-sans">
              {application.cover_letter}
            </pre>
          </div>
        )}

        {/* Actions */}
        <div className="p-6 border-t flex gap-3">
          {!emailSent && (
            <a
              href={application.job_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={handleCopy}
              className="btn-primary flex items-center gap-2 flex-1 justify-center"
            >
              <ExternalLink size={15} />
              {isFranceTravail ? 'Copier & ouvrir sur France Travail' : 'Copier & ouvrir l\'offre'}
            </a>
          )}
          <button onClick={onClose} className="btn-secondary flex-1">
            Fermer
          </button>
        </div>
      </div>
    </div>
  )
}

function MatchBadge({ score }) {
  if (score === null || score === undefined) return null
  const color = score >= 70 ? 'bg-green-100 text-green-700' : score >= 40 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600'
  return <span className={`text-xs font-bold px-2 py-1 rounded-full ${color}`}>{score}% match</span>
}

function JobCard({ job, onApply, applied, emailSentTo }) {
  const [applying, setApplying] = useState(false)

  const handleApply = async () => {
    setApplying(true)
    try {
      await onApply(job.id)
    } finally {
      setApplying(false)
    }
  }

  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <h3 className="font-semibold text-gray-900">{job.title}</h3>
            <MatchBadge score={job.match_score} />
          </div>
          <div className="flex items-center gap-4 text-sm text-gray-500 mt-1 flex-wrap">
            <span className="flex items-center gap-1">
              <Building2 size={13} />
              {job.company}
            </span>
            {job.location && (
              <span className="flex items-center gap-1">
                <MapPin size={13} />
                {job.location}
              </span>
            )}
            {job.salary && <span className="text-green-600 font-medium">{job.salary}</span>}
            {job.source === 'entreprise_directe' ? (
              <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded font-medium">✓ Site officiel</span>
            ) : job.source ? (
              <span className="bg-gray-100 text-gray-600 text-xs px-2 py-0.5 rounded">{job.source}</span>
            ) : null}
          </div>
          {job.skills_required?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-3">
              {job.skills_required.slice(0, 6).map((s) => (
                <span key={s} className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full flex items-center gap-1">
                  <Zap size={10} />
                  {s}
                </span>
              ))}
            </div>
          )}
          {job.description && (
            <p className="text-sm text-gray-600 mt-2 line-clamp-2">{job.description}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-100">
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-secondary text-sm flex items-center gap-1"
        >
          <ExternalLink size={14} />
          Voir l'offre
        </a>
        {applied ? (
          <span className="flex items-center gap-1 text-sm font-medium text-green-600">
            <CheckCircle size={16} />
            {emailSentTo ? `Email envoyé au recruteur` : 'Préparée — postule sur le site'}
          </span>
        ) : (
          <button
            onClick={handleApply}
            disabled={applying}
            className="btn-primary text-sm flex items-center gap-1"
          >
            <Send size={14} />
            {applying ? 'Envoi...' : 'Postuler'}
          </button>
        )}
      </div>
    </div>
  )
}

const ALL_SOURCES = ['HelloWork', 'Indeed', 'WTTJ', 'APEC', 'La Bonne Alternance', "L'Etudiant", 'JobTeaser', 'Sites entreprises']

const MAJOR_COMPANIES = [
  'Société Générale', 'BNP Paribas', 'Crédit Agricole', 'AXA', 'Natixis',
  'Thales', 'Airbus', 'Safran', 'Dassault Systèmes', 'Naval Group',
  'Capgemini', 'Sopra Steria', 'Atos', 'CGI', 'Accenture',
  'Orange', 'SFR', 'Bouygues Telecom', 'Eutelsat',
  'EDF', 'TotalEnergies', 'Engie', 'Veolia',
  'SNCF', 'RATP', 'Air France',
  'Renault', 'Stellantis', 'Michelin', 'Saint-Gobain',
  'Schneider Electric', 'Legrand', 'Eiffage', 'Vinci',
  'Decathlon', 'Carrefour', 'L\'Oréal', 'LVMH',
]

export default function Jobs() {
  const [jobs, setJobs] = useState([])
  const [scraping, setScraping] = useState(false)
  const [query, setQuery] = useState('')
  const [location, setLocation] = useState('')
  const [company, setCompany] = useState('')
  const [appliedIds, setAppliedIds] = useState(new Set())
  const [successMsg, setSuccessMsg] = useState('')
  const [scrapeMsg, setScrapeMsg] = useState('')
  const [sourcesFound, setSourcesFound] = useState([])

  const handleSearchFromProfile = async () => {
    try {
      const res = await userApi.getMe()
      const user = res.data
      const keywords = [
        ...(user.skills || []).slice(0, 5),
        ...(user.target_roles || []).slice(0, 2),
      ].join(' ')
      if (keywords) {
        setQuery(keywords)
        setLocation(user.target_city || '')
        await handleSearchWithKeywords(keywords, user.target_city || 'France', company)
      }
    } catch {}
  }

  const handleSearchWithKeywords = async (kw, loc, cmp = '') => {
    setScraping(true)
    setScrapeMsg('')
    setJobs([])
    setSourcesFound([])
    try {
      const res = await jobsApi.scrape(kw, loc || 'France', cmp)
      const results = res.data
      setJobs(results)
      const sources = [...new Set(results.map(j => j.source).filter(Boolean))]
      setSourcesFound(sources)
      const cmpLabel = cmp ? ` chez ${cmp}` : ''
      setScrapeMsg(`${results.length} offres trouvées en temps réel${cmpLabel}`)
    } catch {
      setScrapeMsg('Erreur lors du scraping.')
    } finally {
      setScraping(false)
    }
  }

  const handleSearch = async () => {
    if (!query.trim()) return
    setScraping(true)
    setScrapeMsg('')
    setJobs([])
    await handleSearchWithKeywords(query.trim(), location.trim(), company.trim())
  }

  const [applyResults, setApplyResults] = useState({})
  const [modalApp, setModalApp] = useState(null)

  const handleApply = async (jobId) => {
    const res = await applicationsApi.create({ job_id: jobId, generate_letter: true })
    setAppliedIds(prev => new Set([...prev, jobId]))
    setApplyResults(prev => ({ ...prev, [jobId]: res.data.email_sent_to || null }))
    setModalApp(res.data)
  }

  return (
    <div className="p-8">
      {modalApp && (
        <CoverLetterModal application={modalApp} onClose={() => setModalApp(null)} />
      )}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Offres d'alternance</h1>
        <p className="text-gray-500 mt-1">Recherche en temps réel sur {ALL_SOURCES.join(', ')}</p>
      </div>

      {successMsg && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4 text-sm flex items-center gap-2">
          <CheckCircle size={16} />
          {successMsg}
        </div>
      )}

      {/* Search Bar */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <input
            className="input-field sm:col-span-1"
            placeholder="Ex: administrateur réseau, cybersécurité, SOC..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <input
            className="input-field"
            placeholder="Ville (ex: Paris, Lyon...)"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button
            onClick={handleSearch}
            disabled={scraping || !query.trim()}
            className="btn-primary flex items-center justify-center gap-2"
          >
            <RefreshCw size={16} className={scraping ? 'animate-spin' : ''} />
            {scraping ? 'Recherche en cours...' : 'Rechercher'}
          </button>
        </div>

        {/* Company filter */}
        <div className="mt-3">
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Filtrer par entreprise (optionnel)
          </label>
          <div className="flex gap-2 flex-wrap">
            <input
              className="input-field flex-1 min-w-0 text-sm"
              placeholder="Ex: Thales, SNCF, Société Générale..."
              value={company}
              list="company-list"
              onChange={(e) => setCompany(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <datalist id="company-list">
              {MAJOR_COMPANIES.map(c => <option key={c} value={c} />)}
            </datalist>
            {company && (
              <button
                onClick={() => setCompany('')}
                className="text-xs text-gray-400 hover:text-gray-600 px-2"
              >
                ✕ Effacer
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-1 mt-2">
            {['Thales', 'SNCF', 'Société Générale', 'Capgemini', 'Orange', 'EDF', 'Airbus', 'Decathlon'].map(c => (
              <button
                key={c}
                onClick={() => setCompany(c === company ? '' : c)}
                className={`text-xs px-2 py-1 rounded-full border transition-colors ${
                  company === c
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'border-gray-200 text-gray-600 hover:border-blue-300 hover:text-blue-600'
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-3">
          <button
            onClick={handleSearchFromProfile}
            disabled={scraping}
            className="btn-secondary text-sm flex items-center gap-2"
          >
            <User size={14} />
            Rechercher selon mon profil CV
          </button>
        </div>
        {scraping && (
          <div className="mt-3 text-sm text-gray-500 flex items-center gap-2">
            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600" />
            Recherche en cours sur {ALL_SOURCES.length} sources (HelloWork, Indeed, WTTJ, APEC, LBA, L'Etudiant, JobTeaser)...
          </div>
        )}
        {scrapeMsg && !scraping && (
          <div className="mt-3">
            <p className="text-sm text-blue-600 font-medium">{scrapeMsg}</p>
            {sourcesFound.length > 0 && (
              <p className="text-xs text-gray-400 mt-1">
                Sources actives : {sourcesFound.join(' · ')}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Job List */}
      {jobs.length === 0 && !scraping ? (
        <div className="text-center py-16 card">
          <Search size={40} className="text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">Entrez des mots-clés et lancez la recherche</p>
          <p className="text-sm text-gray-400 mt-1">Les offres sont récupérées en direct depuis 7 sources dont des sites d'entreprises</p>
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.length > 0 && (
            <p className="text-sm text-gray-500 mb-2">{jobs.length} offre(s) trouvée(s)</p>
          )}
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onApply={handleApply}
              applied={appliedIds.has(job.id)}
              emailSentTo={applyResults[job.id]}
            />
          ))}
        </div>
      )}
    </div>
  )
}
