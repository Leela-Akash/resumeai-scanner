import {
  collection, getDocs, doc,
  getDoc, setDoc, query,
  where, orderBy, limit, serverTimestamp
} from 'firebase/firestore'
import { db } from './config'

export async function createUserIfNotExists(user) {
  const ref = doc(db, 'users', user.uid)
  const snap = await getDoc(ref)
  if (!snap.exists()) {
    await setDoc(ref, {
      email: user.email,
      name: user.displayName,
      photoURL: user.photoURL,
      plan: 'free',
      scansUsed: 0,
      createdAt: serverTimestamp(),
    })
  }
  return (await getDoc(ref)).data()
}

export async function getUser(uid) {
  const snap = await getDoc(doc(db, 'users', uid))
  return snap.exists() ? snap.data() : null
}

export async function getUserScans(uid) {
  const q = query(
    collection(db, 'scans'),
    where('userId', '==', uid),
    orderBy('createdAt', 'desc'),
    limit(50)
  )
  const snap = await getDocs(q)
  return snap.docs.map(d => ({ id: d.id, ...d.data() }))
}
