import { useState, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { authApi } from '../services/api'
import { Mail, ArrowRight, RefreshCw } from 'lucide-react'

export default function VerifyEmail() {
  const navigate = useNavigate()
  const location = useLocation()
  const email = location.state?.email || ''

  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [resent, setResent] = useState(false)
  const inputs = useRef([])

  const handleChange = (i, val) => {
    if (!/^\d*$/.test(val)) return
    const next = [...code]
    next[i] = val.slice(-1)
    setCode(next)
    if (val && i < 5) inputs.current[i + 1]?.focus()
  }

  const handleKeyDown = (i, e) => {
    if (e.key === 'Backspace' && !code[i] && i > 0) {
      inputs.current[i - 1]?.focus()
    }
  }

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (pasted.length === 6) {
      setCode(pasted.split(''))
      inputs.current[5]?.focus()
    }
  }

  const handleVerify = async () => {
    const fullCode = code.join('')
    if (fullCode.length < 6) return setError('Entre les 6 chiffres du code')
    setLoading(true)
    setError('')
    try {
      await authApi.verifyEmail(email, fullCode)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Code invalide ou expiré')
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    try {
      await authApi.resendOtp(email)
      setResent(true)
      setTimeout(() => setResent(false), 4000)
    } catch {}
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 w-full max-w-md text-center">
        <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <Mail size={28} className="text-blue-600" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">Vérifie ton email</h1>
        <p className="text-gray-500 text-sm mb-1">Code envoyé à</p>
        <p className="font-medium text-gray-800 mb-8">{email}</p>

        {/* OTP inputs */}
        <div className="flex justify-center gap-3 mb-6" onPaste={handlePaste}>
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
              className="w-12 h-14 text-center text-2xl font-bold border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none transition-colors"
            />
          ))}
        </div>

        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}

        <button
          onClick={handleVerify}
          disabled={loading || code.join('').length < 6}
          className="btn-primary w-full flex items-center justify-center gap-2 mb-4"
        >
          {loading ? 'Vérification...' : 'Vérifier'}
          {!loading && <ArrowRight size={16} />}
        </button>

        <button
          onClick={handleResend}
          className="text-sm text-gray-500 hover:text-blue-600 flex items-center justify-center gap-1 mx-auto transition-colors"
        >
          <RefreshCw size={13} />
          {resent ? 'Code renvoyé !' : 'Renvoyer le code'}
        </button>
      </div>
    </div>
  )
}
