import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '@/services/api'
import type { User } from '@/types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (username: string, password: string) => {
        try {
          const response = await api.post(
            '/auth/token',
            new URLSearchParams({
              username,
              password,
            }),
            {
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
              },
            }
          )

          const { access_token } = response.data

          // Set token in API client
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

          // Get user info
          const userResponse = await api.get('/auth/me')

          set({
            token: access_token,
            user: userResponse.data,
            isAuthenticated: true,
          })
        } catch (error) {
          set({
            token: null,
            user: null,
            isAuthenticated: false,
          })
          throw error
        }
      },

      logout: () => {
        delete api.defaults.headers.common['Authorization']
        set({
          token: null,
          user: null,
          isAuthenticated: false,
        })
      },

      checkAuth: async () => {
        const { token } = get()
        if (!token) {
          set({ isAuthenticated: false })
          return
        }

        try {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`
          const response = await api.get('/auth/me')
          set({
            user: response.data,
            isAuthenticated: true,
          })
        } catch (_error) {
          get().logout()
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
)
