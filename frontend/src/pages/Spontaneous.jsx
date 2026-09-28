import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { userApi } from '../services/api'
import api from '../services/api'
import { Building2, MapPin, Briefcase, Users, Copy, X, Loader2, Send, Search, ExternalLink, Mail, Globe } from 'lucide-react'

const spontaneousApi = {
  getCompanies: (city, limit = 30) =>
    api.get('/spontaneous/companies', { params: { city, limit } }),
  generateLetter: (data) =>
    api.post('/spontaneous/cover-letter', data),
}

function LetterModal({ company, onClose }) {
  const [letter, setLetter] = useState('')
  const [source, setSource] = useState('')
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    spontaneousApi.generateLetter({
      company_name: company.name,
      company_address: [company.address, company.city].filter(Boolean).join(', '),
      sector_label: company.sector_label,
    })
      .then(res => { setLetter(res.data.cover_letter); setSource(res.data.source || '') })
      .catch(() => setError('Erreur lors de la génération. Réessaie.'))
      .finally(() => setLoading(false))
  }, [])

  const handleCopy = () => {
    navigator.clipboard.writeText(letter)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Lettre de motivation spontanée</h2>
            <p className="text-sm text-gray-500 mt-0.5">{company.name}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 size={28} className="animate-spin text-blue-600" />
              <p className="text-sm text-gray-500">Génération de ta lettre personnalisée...</p>
            </div>
          )}
          {error && <p className="text-red-500 text-sm text-center py-8">{error}</p>}
          {letter && (
            <>
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="text-sm font-medium text-gray-700">Ta lettre :</p>
                  {source === 'template' && (
                    <p className="text-xs text-amber-600 mt-0.5">Générée par template — personnalise-la avant envoi</p>
                  )}
                </div>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
                >
                  <Copy size={13} />
                  {copied ? 'Copié !' : 'Copier'}
                </button>
              </div>
              <pre className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 border border-gray-200 rounded-lg p-4 leading-relaxed font-sans">
                {letter}
              </pre>
            </>
          )}
        </div>

        <div className="p-6 border-t space-y-3">
          {letter && (
            <div className="flex gap-2">
              <button
                onClick={handleCopy}
                className="btn-primary flex items-center gap-2 flex-1 justify-center"
              >
                <Copy size={15} />
                {copied ? 'Copié !' : 'Copier la lettre'}
              </button>
              <a
                href={`https://www.google.com/search?q="${encodeURIComponent(company.name)}"+email+recrutement+contact`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary flex items-center gap-2 flex-1 justify-center text-sm"
              >
                <Mail size={14} />
                Trouver l'email
              </a>
            </div>
          )}
          <div className="flex gap-2">
            <a
              href={`https://www.google.com/search?q="${encodeURIComponent(company.name)}"+site+officiel`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-secondary flex items-center gap-2 flex-1 justify-center text-sm"
            >
              <Globe size={14} />
              Site officiel
            </a>
            <button onClick={onClose} className="btn-secondary flex-1 text-sm">Fermer</button>
          </div>
          <p className="text-xs text-gray-400 text-center">
            Copie la lettre → trouve l'email → envoie ta candidature
          </p>
        </div>
      </div>
    </div>
  )
}

function CompanyCard({ company, onApply }) {
  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <h3 className="font-semibold text-gray-900 text-sm">{company.name}</h3>
            {company.size_label && (
              <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                <Users size={10} className="inline mr-1" />
                {company.size_label}
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-3 text-xs text-gray-500 mt-1">
            {company.sector_label && (
              <span className="flex items-center gap-1">
                <Briefcase size={11} />
                {company.sector_label}
              </span>
            )}
            {(company.city || company.address) && (
              <span className="flex items-center gap-1">
                <MapPin size={11} />
                {company.city || company.address}
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="mt-4 pt-3 border-t border-gray-100 space-y-2">
        {/* Trouver le site et l'email */}
        <div className="flex gap-2">
          <a
            href={`https://www.google.com/search?q="${encodeURIComponent(company.name)}"+site+officiel`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary text-xs flex items-center gap-1 flex-1 justify-center"
          >
            <Globe size={12} />
            Site web
          </a>
          <a
            href={`https://www.google.com/search?q="${encodeURIComponent(company.name)}"+email+recrutement+contact`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary text-xs flex items-center gap-1 flex-1 justify-center"
          >
            <Mail size={12} />
            Trouver l'email
          </a>
          <a
            href={`https://www.pappers.fr/recherche?q=${encodeURIComponent(company.siret || company.name)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary text-xs flex items-center gap-1 flex-1 justify-center"
          >
            <ExternalLink size={12} />
            Fiche
          </a>
        </div>
        <button
          onClick={() => onApply(company)}
          className="btn-primary text-sm flex items-center gap-2 w-full justify-center"
        >
          <Send size={14} />
          Générer ma lettre de candidature
        </button>
      </div>
    </div>
  )
}

export default function Spontaneous() {
  const { user } = useAuth()
  const [city, setCity] = useState('')
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [modalCompany, setModalCompany] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (user?.target_city) {
      setCity(user.target_city)
    } else {
      userApi.getMe().then(res => {
        if (res.data.target_city) setCity(res.data.target_city)
      }).catch(() => {})
    }
  }, [])

  const handleSearch = async () => {
    if (!city.trim()) return
    setLoading(true)
    setError('')
    setCompanies([])
    try {
      const res = await spontaneousApi.getCompanies(city.trim())
      setCompanies(res.data)
      setSearched(true)
      if (res.data.length === 0) {
        setError(`Aucune PME IT trouvée près de "${city}". Essaie une grande ville proche (Paris, Lyon, Bordeaux...).`)
      }
    } catch {
      setError('Erreur lors de la recherche. Réessaie.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4 md:p-8">
      {modalCompany && (
        <LetterModal company={modalCompany} onClose={() => setModalCompany(null)} />
      )}

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Candidature spontanée</h1>
        <p className="text-gray-500 mt-1 text-sm">
          Trouve des PME IT qui recrutent dans ton domaine et génère une lettre personnalisée par IA
        </p>
      </div>

      <div className="card mb-6">
        <div className="flex gap-3">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Ville ou région de recherche
            </label>
            <input
              className="input-field w-full"
              placeholder="Ex: Paris, Lyon, Bordeaux..."
              value={city}
              onChange={e => setCity(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleSearch}
              disabled={loading || !city.trim()}
              className="btn-primary flex items-center gap-2 h-[42px] px-5"
            >
              {loading
                ? <Loader2 size={16} className="animate-spin" />
                : <Search size={16} />
              }
              {loading ? 'Recherche...' : 'Chercher'}
            </button>
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Recherche dans le registre officiel des entreprises françaises (SIRENE) — PME de 10 à 249 salariés dans les secteurs IT
        </p>
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}

      {companies.length > 0 && (
        <div className="mb-4 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            <span className="font-semibold text-gray-900">{companies.length}</span> PME IT trouvées près de <span className="font-medium">{city}</span>
          </p>
        </div>
      )}

      {companies.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {companies.map((company, i) => (
            <CompanyCard
              key={company.siret || i}
              company={company}
              onApply={setModalCompany}
            />
          ))}
        </div>
      )}

      {!loading && !searched && (
        <div className="text-center py-16 card">
          <Building2 size={40} className="text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">Entre une ville pour trouver des PME IT à démarcher</p>
          <p className="text-sm text-gray-400 mt-1">
            Les entreprises sont issues du registre SIRENE — données officielles et à jour
          </p>
        </div>
      )}
    </div>
  )
}
