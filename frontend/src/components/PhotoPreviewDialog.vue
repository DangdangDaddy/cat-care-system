<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="min(92vw, 1100px)"
    top="4vh"
    destroy-on-close
    class="photo-preview-dialog"
    @closed="handleClosed"
  >
    <div class="photo-preview-shell">
      <div class="photo-preview-toolbar">
        <span class="photo-preview-zoom">{{ zoomLabel }}</span>
        <div class="photo-preview-actions">
          <el-button size="small" :disabled="zoomRatio <= minZoomRatio" @click="zoomOut">
            缩小
          </el-button>
          <el-button size="small" @click="resetZoom">
            适应窗口
          </el-button>
          <el-button size="small" :disabled="zoomRatio >= maxZoomRatio" @click="zoomIn">
            放大
          </el-button>
        </div>
      </div>

      <div ref="viewportRef" class="photo-preview-viewport">
        <img
          v-if="src"
          :src="src"
          :alt="title || '照片预览'"
          class="photo-preview-image"
          :style="imageStyle"
          @load="handleImageLoad"
        />
        <el-empty v-else description="暂无图片" />
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    src?: string
    title?: string
  }>(),
  {
    src: '',
    title: ''
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value)
})

const viewportRef = ref<HTMLElement | null>(null)
const naturalWidth = ref(0)
const naturalHeight = ref(0)
const fitScale = ref(1)
const zoomRatio = ref(1)

const minZoomRatio = 0.5
const maxZoomRatio = 3
const zoomStep = 0.25

const zoomLabel = computed(() => `${Math.round(zoomRatio.value * 100)}%`)

const imageStyle = computed(() => {
  if (!naturalWidth.value || !naturalHeight.value) {
    return {}
  }

  const width = naturalWidth.value * fitScale.value * zoomRatio.value
  const height = naturalHeight.value * fitScale.value * zoomRatio.value

  return {
    width: `${width}px`,
    height: `${height}px`
  }
})

function updateFitScale() {
  if (!viewportRef.value || !naturalWidth.value || !naturalHeight.value) {
    return
  }

  const { clientWidth, clientHeight } = viewportRef.value
  if (!clientWidth || !clientHeight) {
    return
  }

  fitScale.value = Math.min(
    clientWidth / naturalWidth.value,
    clientHeight / naturalHeight.value,
    1
  )
}

function handleImageLoad(event: Event) {
  const image = event.target as HTMLImageElement | null
  if (!image) {
    return
  }

  naturalWidth.value = image.naturalWidth
  naturalHeight.value = image.naturalHeight
  nextTick(() => {
    updateFitScale()
  })
}

function zoomIn() {
  zoomRatio.value = Math.min(maxZoomRatio, Number((zoomRatio.value + zoomStep).toFixed(2)))
}

function zoomOut() {
  zoomRatio.value = Math.max(minZoomRatio, Number((zoomRatio.value - zoomStep).toFixed(2)))
}

function resetZoom() {
  zoomRatio.value = 1
  nextTick(() => {
    updateFitScale()
  })
}

function resetState() {
  naturalWidth.value = 0
  naturalHeight.value = 0
  fitScale.value = 1
  zoomRatio.value = 1
}

function handleClosed() {
  resetState()
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      zoomRatio.value = 1
      nextTick(() => {
        updateFitScale()
      })
    }
  }
)

watch(
  () => props.src,
  () => {
    resetState()
  }
)

function handleResize() {
  updateFitScale()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.photo-preview-dialog {
  --photo-preview-orange-400: #f5a24f;
  --photo-preview-orange-500: #ef8e36;
  --photo-preview-orange-600: #dc7420;
  --photo-preview-ink: #5f4634;
  --photo-preview-line: rgba(246, 186, 110, 0.4);
}

.photo-preview-dialog :deep(.el-dialog) {
  overflow: hidden;
  margin-bottom: 4vh;
  border: 1px solid var(--photo-preview-line);
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(255, 252, 246, 0.98), rgba(255, 244, 227, 0.96));
  box-shadow: 0 24px 55px rgba(200, 132, 59, 0.18);
  backdrop-filter: blur(14px);
}

.photo-preview-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 20px 24px 14px;
  border-bottom: 1px solid rgba(244, 197, 129, 0.45);
  background: linear-gradient(135deg, rgba(255, 251, 244, 0.96), rgba(255, 241, 218, 0.94));
}

.photo-preview-dialog :deep(.el-dialog__title) {
  font-size: 20px;
  font-weight: 700;
  color: var(--photo-preview-orange-600);
}

.photo-preview-dialog :deep(.el-dialog__headerbtn) {
  top: 18px;
  right: 20px;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: rgba(255, 246, 232, 0.9);
  border: 1px solid rgba(246, 186, 110, 0.32);
  transition: transform 0.2s ease, background 0.2s ease;
}

.photo-preview-dialog :deep(.el-dialog__headerbtn:hover) {
  transform: translateY(-1px);
  background: rgba(255, 237, 210, 0.96);
}

.photo-preview-dialog :deep(.el-dialog__close) {
  color: rgba(143, 88, 49, 0.76);
}

.photo-preview-dialog :deep(.el-dialog__body) {
  padding: 16px 18px 18px;
}

.photo-preview-shell {
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: var(--photo-preview-ink);
}

.photo-preview-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 0 4px;
}

.photo-preview-zoom {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 230, 196, 0.86);
  border: 1px solid rgba(246, 186, 110, 0.38);
  color: var(--photo-preview-orange-600);
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.photo-preview-actions {
  display: flex;
  gap: 8px;
}

.photo-preview-actions :deep(.el-button) {
  border-color: rgba(245, 185, 110, 0.5);
  color: var(--photo-preview-ink);
  background: rgba(255, 249, 240, 0.95);
  box-shadow: 0 8px 14px rgba(239, 142, 54, 0.1);
}

.photo-preview-actions :deep(.el-button:hover) {
  color: var(--photo-preview-orange-600);
  border-color: rgba(239, 142, 54, 0.45);
  background: rgba(255, 240, 217, 0.95);
}

.photo-preview-actions :deep(.el-button:disabled) {
  opacity: 0.55;
  box-shadow: none;
}

.photo-preview-viewport {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  max-height: calc(88vh - 130px);
  min-height: min(60vh, 540px);
  padding: 14px;
  border-radius: 22px;
  border: 1px solid rgba(245, 189, 116, 0.34);
  background:
    radial-gradient(circle at top left, rgba(255, 221, 173, 0.34), transparent 30%),
    linear-gradient(180deg, rgba(255, 248, 236, 0.98), rgba(255, 241, 220, 0.94));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.photo-preview-image {
  display: block;
  max-width: none;
  flex: 0 0 auto;
  border-radius: 18px;
  border: 1px solid rgba(255, 245, 232, 0.92);
  box-shadow: 0 16px 30px rgba(178, 116, 47, 0.18);
}

@media (max-width: 768px) {
  .photo-preview-dialog :deep(.el-dialog) {
    width: calc(100vw - 24px) !important;
  }

  .photo-preview-toolbar {
    align-items: stretch;
  }

  .photo-preview-actions {
    width: 100%;
  }

  .photo-preview-actions :deep(.el-button) {
    flex: 1;
  }

  .photo-preview-viewport {
    min-height: 48vh;
    max-height: calc(86vh - 150px);
  }
}
</style>
