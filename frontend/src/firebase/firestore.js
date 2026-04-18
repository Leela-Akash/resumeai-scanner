import {
  collection, addDoc, getDocs, doc,
  getDoc, setDoc, updateDoc, query,
  where, orderBy, serverTimestamp, increment
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
      scansLimit: 3,
      createdAt: serverTimestamp(),
    })
  }
  return (await getDoc(ref)).data()
}

export async function getUser(uid) {
  const snap = await getDoc(doc(db, 'users', uid))
  return snap.exists() ? snap.data() : null
}

export async function saveScan(uid, result) {
  const docRef = await addDoc(collection(db, 'scans'), {
    userId: uid,
    jobTitle: result.job_title,
    ats_score: result.ats_score,
    matched_keywords: result.matched_keywords,
    missing_keywords: result.missing_keywords,
    weak_bullets: result.weak_bullets,
    improved_bullets: result.improved_bullets,
    overall_feedback: result.overall_feedback,
    hire_probability: result.hire_probability,
    createdAt: serverTimestamp(),
  })
  await updateDoc(doc(db, 'users', uid), { scansUsed: increment(1) })
  return docRef.id
}

export async function getUserScans(uid) {
  const q = query(
    collection(db, 'scans'),
    where('userId', '==', uid),
    orderBy('createdAt', 'desc')
  )
  const snap = await getDocs(q)
  return snap.docs.map(d => ({ id: d.id, ...d.data() }))
}
