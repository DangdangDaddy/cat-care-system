export type PhotoSortMode = 'manual' | 'captured_at' | 'created_at'

export interface PhotoLike {
  id: number
  created_at?: string
  captured_at?: string | null
  sort_order?: number | null
  is_pinned?: boolean | null
}

function getTimeValue(value?: string | null): number {
  if (!value) return 0
  const time = new Date(value).getTime()
  return Number.isNaN(time) ? 0 : time
}

export function sortPhotos<T extends PhotoLike>(photos: T[], mode: PhotoSortMode): T[] {
  const sorted = [...photos]
  sorted.sort((left, right) => {
    const leftPinned = left.is_pinned ? 1 : 0
    const rightPinned = right.is_pinned ? 1 : 0
    if (leftPinned !== rightPinned) return rightPinned - leftPinned

    if (mode === 'captured_at') {
      const timeDelta = getTimeValue(right.captured_at || right.created_at) - getTimeValue(left.captured_at || left.created_at)
      if (timeDelta !== 0) return timeDelta
    } else if (mode === 'created_at') {
      const timeDelta = getTimeValue(right.created_at) - getTimeValue(left.created_at)
      if (timeDelta !== 0) return timeDelta
    } else {
      const orderLeft = left.sort_order ?? Number.POSITIVE_INFINITY
      const orderRight = right.sort_order ?? Number.POSITIVE_INFINITY
      if (orderLeft !== orderRight) return orderLeft - orderRight
    }

    const fallback = getTimeValue(right.created_at) - getTimeValue(left.created_at)
    if (fallback !== 0) return fallback
    return right.id - left.id
  })
  return sorted
}

export function buildReorderPayload<T extends PhotoLike>(photos: T[], draggedPhotoId: number, targetPhotoId: number) {
  const orderedIds = photos.map((photo) => photo.id)
  const fromIndex = orderedIds.indexOf(draggedPhotoId)
  const toIndex = orderedIds.indexOf(targetPhotoId)
  if (fromIndex === -1 || toIndex === -1 || fromIndex === toIndex) {
    return null
  }

  const nextOrder = [...orderedIds]
  const [movedId] = nextOrder.splice(fromIndex, 1)
  nextOrder.splice(toIndex, 0, movedId)

  const newIndex = nextOrder.indexOf(draggedPhotoId)
  return {
    prev_photo_id: newIndex > 0 ? nextOrder[newIndex - 1] : null,
    next_photo_id: newIndex < nextOrder.length - 1 ? nextOrder[newIndex + 1] : null
  }
}
