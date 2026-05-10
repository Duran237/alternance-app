import { useState, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { useAuth } from '../contexts/AuthContext'
import { userApi, cvApi } from '../services/api'
import { User, Upload, Github, Linkedin, MapPin, Zap, CheckCircle, AlertCircle, X, GraduationCap, Briefcase } from 'lucide-react'

function Tag({ label, onRemove, color = 'blue' }) {
  const colors = {
    blue: 'bg-blue-100 text-blue-800',
    purple: 'bg-purple-100 text-purple-800',
  }
  return (
    <span className={`inline-flex items-center gap-1 text-sm px-3 py-1 rounded-full ${colors[color]}`}>
      {label}
      <button onClick={() => onRemove(label)} className="hover:text-red-600 ml-1">
        <X size={12} />
      </button>
    </span>
  )
}

function SkillTag({ skill, onRemove }) {
  return <Tag label={skill} onRemove={onRemove} color="blue" />
}

export default function Profile() {
  const { user, refreshUser } = useAuth()
  const [saving, setSaving] = useState(false)
  const [cvUploading, setCvUploading] = useState(false)
  const [message, setMessage] = useState(null)
  const [skills, setSkills] = useState(user?.skills || [])
  const [skillInput, setSkillInput] = useState('')
  const [roles, setRoles] = useState(user?.target_roles || [])
  const [roleInput, setRoleInput] = useState('')
  const fileInputRef = useRef()

  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      name: user?.name || '',
      phone: user?.phone || '',
      school: user?.school || '',
      education_level: user?.education_level || '',
      github_url: user?.github_url || '',
      linkedin_url: user?.linkedin_url || '',
      target_city: user?.target_city || '',
      target_salary: user?.target_salary || '',
    },
  })

  const onSubmit = async (data) => {
    setSaving(true)
    setMessage(null)
    try {
      await userApi.updateMe({ ...data, skills, target_roles: roles })
      await refreshUser()
      setMessage({ type: 'success', text: 'Profil mis à jour avec succès' })
    } catch {
      setMessage({ type: 'error', text: 'Erreur lors de la sauvegarde' })
    } finally {
      setSaving(false)
    }
  }

  const handleCvUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setCvUploading(true)
    setMessage(null)
    try {
      const res = await cvApi.upload(file)
      await refreshUser()
      setMessage({ type: 'success', text: `CV uploadé ! Compétences détectées : ${res.data.skills_detected?.join(', ') || 'aucune'}` })
      if (res.data.skills_detected?.length) {
        setSkills(prev => [...new Set([...prev, ...res.data.skills_detected])])
      }
    } catch {
      setMessage({ type: 'error', text: 'Erreur lors de l\'upload du CV' })
    } finally {
      setCvUploading(false)
    }
  }

  const addSkill = () => {
    const s = skillInput.trim().toLowerCase()
    if (s && !skills.includes(s)) {
      setSkills(prev => [...prev, s])
    }
    setSkillInput('')
  }

  const removeSkill = (skill) => setSkills(prev => prev.filter(s => s !== skill))

  const addRole = () => {
    const r = roleInput.trim()
    if (r && !roles.includes(r)) {
      setRoles(prev => [...prev, r])
    }
    setRoleInput('')
  }

  const removeRole = (role) => setRoles(prev => prev.filter(r => r !== role))

  return (
    <div className="p-8 max-w-3xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Mon profil</h1>
        <p className="text-gray-500 mt-1">Complétez votre profil pour améliorer le matching</p>
      </div>

      {message && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-lg mb-6 text-sm ${
          message.type === 'success' ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-red-50 border border-red-200 text-red-700'
        }`}>
          {message.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {message.text}
        </div>
      )}

      <div className="space-y-6">
        {/* CV Upload */}
        <div className="card">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Upload size={18} className="text-blue-600" />
            Curriculum Vitae
          </h2>
          <div
            className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleCvUpload} className="hidden" />
            {user?.cv_path ? (
              <div>
                <CheckCircle size={32} className="text-green-500 mx-auto mb-2" />
                <p className="text-gray-700 font-medium">CV uploadé</p>
                <p className="text-sm text-gray-500 mt-1">Cliquez pour remplacer</p>
              </div>
            ) : (
              <div>
                <Upload size={32} className="text-gray-400 mx-auto mb-2" />
                <p className="text-gray-700 font-medium">Glissez votre CV ici</p>
                <p className="text-sm text-gray-500 mt-1">Format PDF uniquement</p>
              </div>
            )}
            {cvUploading && <p className="text-blue-600 text-sm mt-2">Upload en cours...</p>}
          </div>
        </div>

        {/* Personal Info */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <User size={18} className="text-blue-600" />
              Informations personnelles
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nom complet</label>
                <input className="input-field" {...register('name', { required: true })} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Téléphone</label>
                <input className="input-field" placeholder="06 12 34 56 78" {...register('phone')} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <GraduationCap size={14} className="inline mr-1" />
                  École / Établissement
                </label>
                <input className="input-field" placeholder="Ex: ESIEA, Université Paris-Saclay..." {...register('school')} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <GraduationCap size={14} className="inline mr-1" />
                  Niveau d'études
                </label>
                <select className="input-field" {...register('education_level')}>
                  <option value="">Sélectionner...</option>
                  <option value="Bac+1">Bac+1</option>
                  <option value="Bac+2 (BTS / BUT)">Bac+2 (BTS / BUT)</option>
                  <option value="Bac+3 (Licence / Bachelor)">Bac+3 (Licence / Bachelor)</option>
                  <option value="Bac+4 (Master 1 / Ingénieur 3ème année)">Bac+4 (Master 1 / Ingénieur 3ème année)</option>
                  <option value="Bac+5 (Master 2 / Ingénieur)">Bac+5 (Master 2 / Ingénieur)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <MapPin size={14} className="inline mr-1" />
                  Ville cible
                </label>
                <input className="input-field" placeholder="Paris, Lyon..." {...register('target_city')} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Salaire souhaité (alternance)</label>
                <input className="input-field" placeholder="Ex: 900€/mois" {...register('target_salary')} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Github size={14} className="inline mr-1" />
                  GitHub
                </label>
                <input className="input-field" placeholder="https://github.com/..." {...register('github_url')} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Linkedin size={14} className="inline mr-1" />
                  LinkedIn
                </label>
                <input className="input-field" placeholder="https://linkedin.com/in/..." {...register('linkedin_url')} />
              </div>
            </div>
          </div>

          {/* Target Roles */}
          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-1 flex items-center gap-2">
              <Briefcase size={18} className="text-purple-600" />
              Postes / Domaines souhaités
            </h2>
            <p className="text-xs text-gray-400 mb-4">Utilisés pour cibler les offres d'alternance correspondantes</p>
            <div className="flex gap-2 mb-4">
              <input
                className="input-field flex-1"
                placeholder="Ex: Administrateur réseau, Analyste SOC, DevOps..."
                value={roleInput}
                onChange={(e) => setRoleInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addRole())}
              />
              <button type="button" onClick={addRole} className="btn-secondary px-4">
                Ajouter
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {roles.map((role) => (
                <Tag key={role} label={role} onRemove={removeRole} color="purple" />
              ))}
              {roles.length === 0 && (
                <p className="text-sm text-gray-400">Aucun poste souhaité. L'algorithme se basera sur vos compétences.</p>
              )}
            </div>
          </div>

          {/* Skills */}
          <div className="card">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Zap size={18} className="text-blue-600" />
              Compétences techniques
            </h2>
            <div className="flex gap-2 mb-4">
              <input
                className="input-field flex-1"
                placeholder="Python, Linux, Cybersécurité..."
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill())}
              />
              <button type="button" onClick={addSkill} className="btn-secondary px-4">
                Ajouter
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {skills.map((skill) => (
                <SkillTag key={skill} skill={skill} onRemove={removeSkill} />
              ))}
              {skills.length === 0 && (
                <p className="text-sm text-gray-400">Aucune compétence ajoutée. Uploadez votre CV pour les détecter automatiquement.</p>
              )}
            </div>
          </div>

          <button type="submit" disabled={saving} className="btn-primary w-full py-3">
            {saving ? 'Sauvegarde...' : 'Sauvegarder le profil'}
          </button>
        </form>
      </div>
    </div>
  )
}
