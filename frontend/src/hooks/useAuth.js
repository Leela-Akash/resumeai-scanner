import { useState, useEffect } from 'react'
import { onAuthStateChanged } from 'firebase/auth'
import { auth } from '../firebase/config'

// The backend creates the user's Firestore profile on their first scan,
// so the browser only needs the Firebase auth state here.
export function useAuth() {
  const [user, setUser] = useState(undefined) // undefined = loading

  useEffect(() => onAuthStateChanged(auth, (firebaseUser) => setUser(firebaseUser ?? null)), [])

  return { user }
}
