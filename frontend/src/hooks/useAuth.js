import { useState, useEffect } from 'react'
import { onAuthStateChanged } from 'firebase/auth'
import { auth } from '../firebase/config'
import { createUserIfNotExists } from '../firebase/firestore'

export function useAuth() {
  const [user, setUser] = useState(undefined) // undefined = loading
  const [userData, setUserData] = useState(null)

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        const data = await createUserIfNotExists(firebaseUser)
        setUserData(data)
        setUser(firebaseUser)
      } else {
        setUser(null)
        setUserData(null)
      }
    })
    return unsub
  }, [])

  return { user, userData }
}
