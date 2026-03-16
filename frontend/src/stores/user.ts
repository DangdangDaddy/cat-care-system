import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userId = ref(Number(localStorage.getItem('userId')) || null)
  const username = ref(localStorage.getItem('username') || '')

  const isLoggedIn = computed(() => !!token.value)

  function setUser(newToken: string, newUserId: number, newUsername: string) {
    token.value = newToken
    userId.value = newUserId
    username.value = newUsername
    localStorage.setItem('token', newToken)
    localStorage.setItem('userId', String(newUserId))
    localStorage.setItem('username', newUsername)
  }

  function logout() {
    token.value = ''
    userId.value = null
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('userId')
    localStorage.removeItem('username')
  }

  return {
    token,
    userId,
    username,
    isLoggedIn,
    setUser,
    logout
  }
})
