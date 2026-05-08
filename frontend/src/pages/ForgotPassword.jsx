import { useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'
import { KeyRound, Mail, ArrowRight, RefreshCw, Eye, EyeOff } from 'lucide-react'

export default function ForgotPassword() {
  const navigate = useNavigate()
  const [step, setStep] = useState('email') // 'email' | 'otp'
  const [email, setEmail] = useState('')
  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [newPassword, setNewPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [resent, setResent] = useState(false)
  const inputs = useRef([])

  const handleSendCode = async (e) => {
    e.preventDefault()
    if (!email) return
    setLoading(true)
    setError('')
    try {
      await authApi.forgotPassword(email)
      setStep('otp')
    } catch {
      setError('Erreur lors de l\'envoi du code')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (i, val) => {
    if (!/^\d*$/.test(val)) return
    const next = [...code]
    next[i] = val.slice(-1)
    setCode(next)
    if (val && i < 5) inputs.current[i + 1]?.focus()
  }

  const handleKeyDown = (i, e) => {
    if (e.key === 'Backspace' && !code[i] && i > 0) inputs.current[i - 1]?.focus()
  }

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (pasted.length === 6) {
      setCode(pasted.split(''))
      inputs.current[5]?.focus()
    }
  }

  const handleReset = async (e) => {
    e.preventDefault()
    const fullCode = code.join('')
    if (fullCode.length < 6) return setError('Entre les 6 chiffres du code')
    if (newPassword.length < 8) return setError('Mot de passe trop court (8 caractères minimum)')
    setLoading(true)
    setError('')
    try {
      await authApi.resetPassword(email, fullCode, newPassword)
      navigate('/login', { state: { message: 'Mot de passe réinitialisé. Connecte-toi.' } })
    } catch (err) {
      setError(err.response?.data?.detail || 'Code invalide ou expiré')
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    try {
      await authApi.forgotPassword(email)
      setResent(true)
      setTimeout(() => setResent(false), 4000)
    } catch {}
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <KeyRound size={24} className="text-blue-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            {step === 'email' ? 'Mot de passe oublié' : 'Nouveau mot de passe'}
          </h1>
          <p className="text-gray-500 mt-1 text-sm">
            {step === 'email'
              ? 'Entre ton email pour recevoir un code de réinitialisation'
              : `Code envoyé à ${email}`}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}

        {step === 'email' ? (
          <form onSubmit={handleSendCode} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="email"
                  className="input-field pl-9"
                  placeholder="ton@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full py-3 flex items-center justify-center gap-2">
              {loading ? 'Envoi...' : 'Envoyer le code'}
              {!loading && <ArrowRight size={16} />}
            </button>
          </form>
        ) : (
          <form onSubmit={handleReset} className="space-y-6">
            {/* OTP */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3 text-center">Code reçu par email</label>
              <div className="flex justify-center gap-3" onPaste={handlePaste}>
                {code.map((digit, i) => (
                  <input
                    key={i}
                    ref={(el) => (inputs.current[i] = el)}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleChange(i, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(i, e)}
                    className="w-11 h-13 text-center text-xl font-bold border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition-colors"
                  />
                ))}
              </div>
              <button
                type="button"
                onClick={handleResend}
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-blue-600 mx-auto mt-2 transition-colors"
              >
                <RefreshCw size={11} />
                {resent ? 'Code renvoyé !' : 'Renvoyer le code'}
              </button>
            </div>

            {/* Nouveau mot de passe */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nouveau mot de passe</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="input-field pr-10"
                  placeholder="Minimum 8 caractères"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-3 flex items-center justify-center gap-2">
              {loading ? 'Réinitialisation...' : 'Réinitialiser le mot de passe'}
              {!loading && <ArrowRight size={16} />}
            </button>
          </form>
        )}

        <p className="text-center text-sm text-gray-600 mt-6">
          <Link to="/login" className="text-blue-600 hover:underline font-medium">
            ← Retour à la connexion
          </Link>
        </p>
      </div>
    </div>
  )
}
