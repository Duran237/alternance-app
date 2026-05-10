import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuth } from '../contexts/AuthContext'
import { Briefcase, AlertCircle } from 'lucide-react'

export default function Register() {
  const { register: signup } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register, handleSubmit, watch, formState: { errors } } = useForm()

  const onSubmit = async ({ name, email, password }) => {
    setError('')
    setLoading(true)
    try {
      await signup(name, email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la création du compte')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Briefcase size={24} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Créer un compte</h1>
          <p className="text-gray-500 mt-1">Trouvez votre alternance plus rapidement</p>
        </div>

        {error && (
          <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nom complet</label>
            <input
              type="text"
              className="input-field"
              placeholder="Jean Dupont"
              {...register('name', { required: 'Nom requis', minLength: { value: 2, message: 'Minimum 2 caractères' } })}
            />
            {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              className="input-field"
              placeholder="vous@email.com"
              {...register('email', { required: 'Email requis' })}
            />
            {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mot de passe</label>
            <input
              type="password"
              className="input-field"
              placeholder="Minimum 8 caractères"
              {...register('password', { required: 'Requis', minLength: { value: 8, message: 'Minimum 8 caractères' } })}
            />
            {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full py-3">
            {loading ? 'Création...' : 'Créer mon compte'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-600 mt-6">
          Déjà un compte ?{' '}
          <Link to="/login" className="text-blue-600 hover:underline font-medium">
            Se connecter
          </Link>
        </p>
      </div>
    </div>
  )
}
