<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <h1>
        <el-icon><KoiFish /></el-icon>
        猫咪成长健康管理系统
      </h1>
      <div style="display: flex; align-items: center; gap: 16px;">
        <span class="dashboard-welcome">欢迎，{{ userStore.username }}</span>
        <el-button type="danger" text @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          退出
        </el-button>
      </div>
    </header>

    <main class="dashboard-content">
      <!-- 页签切换 -->
      <el-tabs v-model="activeTab" class="main-tabs">
        <!-- 我的猫咪页签 -->
        <el-tab-pane label="我的猫咪" name="cats">
          <h2 class="section-title">
            <el-icon><StarFilled /></el-icon>
            我的猫咪
          </h2>

          <div class="cat-grid">
            <div
              v-for="cat in cats"
              :key="cat.id"
              class="cat-card"
              @click="goToCatDetail(cat.id)"
            >
              <div class="cat-card-header">
                <div class="cat-avatar">
                  <img v-if="cat.avatar" :src="cat.avatar" :alt="cat.name" />
                  <span v-else>{{ cat.gender === 'female' ? '🐱' : '😺' }}</span>
                </div>
                <div class="cat-info">
                  <h3>{{ cat.name }}</h3>
                  <p>{{ getBreedDisplay(cat.breed, cat.color) }}</p>
                </div>
              </div>
              <div class="cat-details">
                <p>
                  <span>性别：</span>
                  <span>{{ cat.gender === 'female' ? '母猫' : '公猫' }}</span>
                </p>
                <p>
                  <span>生日：</span>
                  <span>{{ cat.birth_date }}</span>
                </p>
                <p>
                  <span>绝育：</span>
                  <span>{{ cat.neutered ? '已绝育' : '未绝育' }}</span>
                </p>
                <p v-if="cat.deworming_date">
                  <span>驱虫：</span>
                  <span>{{ formatDeworming(cat.deworming_date) }}</span>
                </p>
                <p v-if="cat.vaccination_status">
                  <span>疫苗：</span>
                  <span :class="getVaccinationClass(cat.vaccination_status)">
                    {{ cat.vaccination_status }}
                  </span>
                </p>
              </div>
            </div>

            <div class="add-cat-card" @click="showAddDialog = true">
              <el-icon class="icon"><Plus /></el-icon>
              <span>添加猫咪</span>
            </div>
          </div>

          <div class="chart-section">
            <h2 class="section-title">
              <el-icon><TrendCharts /></el-icon>
              体重趋势
            </h2>
            <div class="chart-container" ref="chartRef"></div>
          </div>
        </el-tab-pane>

        <!-- 相册页签 -->
        <el-tab-pane label="相册" name="album">
          <h2 class="section-title">
            <el-icon><PictureFilled /></el-icon>
 ？」           猫咪相册
          </h2>

          <div class="album-toolbar">
            <el-select v-model="photoSortMode" size="small" style="width: 140px">
              <el-option label="手动排序" value="manual" />
              <el-option label="拍摄时间" value="captured_at" />
              <el-option label="上传时间" value="created_at" />
            </el-select>
            <el-button type="primary" @click="openPhotoUploadDialog">
              <el-icon><Plus /></el-icon>
              上传照片
            </el-button>
          </div>

          <div class="album-container" v-if="dashboardPhotos.length > 0">
            <div
              class="photo-item"
              v-for="photo in sortedDashboardPhotos"
              :key="photo.id"
              :class="{ 'is-dragging': draggingPhotoId === photo.id, 'manual-sort': photoSortMode === 'manual' }"
              :draggable="photoSortMode === 'manual'"
              @dragstart="handlePhotoDragStart(photo.id)"
              @dragend="handlePhotoDragEnd"
              @dragover.prevent
              @drop.prevent="handlePhotoDrop(photo)"
              @click="viewPhoto(photo)"
            >
              <img :src="photo.thumbnail || photo.url" :alt="formatPhotoCatNames(photo)" />
              <div class="photo-overlay">
                <span class="cat-name">
                  <el-icon v-if="photo.is_pinned"><StarFilled /></el-icon>
                  {{ formatPhotoCatNames(photo) }}
                </span>
                <div class="photo-overlay-actions">
                  <el-button size="small" @click.stop="togglePhotoPin(photo)">
                    {{ photo.is_pinned ? '取消置顶' : '置顶' }}
                  </el-button>
                  <el-button size="small" @click.stop="openPhotoEditDialog(photo)">编辑</el-button>
                  <el-button size="small" type="danger" @click.stop="deletePhoto(photo)">删除</el-button>
                </div>
              </div>
            </div>
          </div>

          <el-empty v-else description="暂无已标注照片" />
        </el-tab-pane>
      </el-tabs>
    </main>

    <!-- 添加猫咪对话框 -->
    <el-dialog v-model="showAddDialog" title="添加猫咪" width="600px">
      <el-form :model="catForm" :rules="catRules" ref="catFormRef" label-width="100px">
        <el-form-item label="名字" prop="name">
          <el-input v-model="catForm.name" placeholder="请输入猫咪名字" />
        </el-form-item>

        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="catForm.gender">
            <el-radio label="male">公猫</el-radio>
            <el-radio label="female">母猫</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="品种" prop="breed">
          <el-select
            v-model="catForm.breed"
            placeholder="请选择品种"
            style="width: 100%"
            @change="handleBreedChange"
          >
            <el-option label="英国短毛猫" value="英国短毛猫" />
            <el-option label="美国短毛猫" value="美国短毛猫" />
            <el-option label="布偶猫" value="布偶猫" />
            <el-option label="缅因猫" value="缅因猫" />
            <el-option label="波斯猫" value="波斯猫" />
            <el-option label="加菲猫（异国短毛猫）" value="加菲猫" />
            <el-option label="孟加拉豹猫" value="孟加拉豹猫" />
            <el-option label="斯芬克斯猫（无毛猫）" value="斯芬克斯猫" />
            <el-option label="挪威森林猫" value="挪威森林猫" />
            <el-option label="德文卷毛猫" value="德文卷毛猫" />
            <el-option label="俄罗斯蓝猫" value="俄罗斯蓝猫" />
            <el-option label="阿比西尼亚猫" value="阿比西尼亚猫" />
            <el-option label="苏格兰折耳猫" value="苏格兰折耳猫" />
            <el-option label="曼基康猫（矮脚猫）" value="曼基康猫" />
            <el-option label="拿破仑猫（矮脚长毛猫）" value="拿破仑猫" />
            <el-option label="西伯利亚猫" value="西伯利亚猫" />
            <el-option label="索马里猫" value="索马里猫" />
            <el-option label="暹罗猫" value="暹罗猫" />
            <el-option label="金吉拉猫" value="金吉拉猫" />
            <el-option label="中国狸花猫" value="中国狸花猫" />
            <el-option label="中华田园猫" value="中华田园猫" />
            <el-option label="其他（支持手工录入）" value="其他" />
          </el-select>
          <el-input
            v-if="catForm.breed === '其他'"
            v-model="catForm.breed_custom"
            placeholder="请输入品种名称"
            style="margin-top: 8px;"
          />
        </el-form-item>

        <el-form-item label="毛色" prop="color">
          <el-select
            v-model="catForm.color"
            placeholder="请选择毛色"
            style="width: 100%"
            @change="handleColorChange"
          >
            <el-option label="白色" value="白色" />
            <el-option label="黑色" value="黑色" />
            <el-option label="蓝色" value="蓝色" />
            <el-option label="红色" value="红色" />
            <el-option label="奶油色" value="奶油色" />
            <el-option label="巧克力色" value="巧克力色" />
            <el-option label="银渐层" value="银渐层" />
            <el-option label="金渐层" value="金渐层" />
            <el-option label="蓝金渐层" value="蓝金渐层" />
            <el-option label="蓝银渐层" value="蓝银渐层" />
            <el-option label="银虎斑" value="银虎斑" />
            <el-option label="金虎斑" value="金虎斑" />
            <el-option label="棕虎斑" value="棕虎斑" />
            <el-option label="蓝虎斑" value="蓝虎斑" />
            <el-option label="红虎斑" value="红虎斑" />
            <el-option label="海豹重点色" value="海豹重点色" />
            <el-option label="蓝重点色" value="蓝重点色" />
            <el-option label="巧克力重点色" value="巧克力重点色" />
            <el-option label="火焰重点色" value="火焰重点色" />
            <el-option label="玳瑁色" value="玳瑁色" />
            <el-option label="三花色" value="三花色" />
            <el-option label="双色" value="双色" />
            <el-option label="烟色" value="烟色" />
            <el-option label="纯色" value="纯色" />
            <el-option label="其他（支持手工录入）" value="其他" />
          </el-select>
          <el-input
            v-if="catForm.color === '其他'"
            v-model="catForm.color_custom"
            placeholder="请输入毛色名称"
            style="margin-top: 8px;"
          />
        </el-form-item>

        <el-form-item label="生日" prop="birth_date">
          <el-date-picker
            v-model="catForm.birth_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="是否绝育">
          <el-switch v-model="catForm.neutered" />
        </el-form-item>

        <el-divider content-position="left">健康信息</el-divider>

        <el-form-item label="疫苗接种">
          <el-select v-model="catForm.vaccination_status" placeholder="请选择疫苗接种情况" style="width: 100%">
            <el-option label="未接种" value="未接种" />
            <el-option label="接种中" value="接种中" />
            <el-option label="已完成基础免疫" value="已完成基础免疫" />
            <el-option label="定期接种中" value="定期接种中" />
          </el-select>
        </el-form-item>

        <el-form-item label="驱虫日期">
          <el-date-picker
            v-model="catForm.deworming_date"
            type="date"
            placeholder="选择最近驱虫日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="病史记录">
          <el-input
            v-model="catForm.medical_history"
            type="textarea"
            :rows="3"
            placeholder="请输入猫咪病史记录（如有）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="addingCat" @click="handleAddCat">确定</el-button>
      </template>
    </el-dialog>

    <PhotoPreviewDialog
      v-model="showPhotoDialog"
      :src="selectedPhoto?.url || ''"
      :title="selectedPhoto ? formatPhotoCatNames(selectedPhoto) : ''"
    />

    <el-dialog
      v-model="showPhotoUploadDialog"
      :title="photoUploadDialogTitle"
      width="520px"
      @closed="resetPhotoUploadDialog"
    >
      <div class="photo-upload-panel">
        <input
          ref="photoFileInputRef"
          type="file"
          accept="image/*"
          multiple
          style="display: none"
          @change="handlePhotoFileChange"
        />

        <div class="photo-upload-file-row">
          <el-button @click="triggerPhotoFileSelect">选择照片</el-button>
          <span class="photo-upload-file-name">
            {{ currentPhotoUploadFile?.name || '尚未选择文件' }}
          </span>
        </div>

        <div v-if="photoUploadQueue.length > 1" class="photo-upload-queue-status">
          已选择 {{ photoUploadQueue.length }} 张，当前第 {{ photoUploadQueueIndex + 1 }} 张
        </div>

        <img v-if="photoUploadPreviewUrl" :src="photoUploadPreviewUrl" class="photo-upload-preview" />

        <el-form label-width="88px">
          <el-form-item v-if="photoRecommendations.length > 0" label="推荐标签">
            <div class="photo-recommendations">
              <span
                v-for="item in photoRecommendations"
                :key="item.cat_id"
                class="photo-recommendation-item"
              >
                {{ item.cat_name }} {{ Math.round(item.confidence * 100) }}%
              </span>
            </div>
          </el-form-item>
          <el-form-item label="照片说明">
            <el-input v-model="photoUploadForm.description" placeholder="可选备注" />
          </el-form-item>
          <el-form-item label="照片里的猫">
            <el-checkbox-group v-model="photoUploadForm.tagCatIds">
              <el-checkbox v-for="userCat in cats" :key="userCat.id" :value="userCat.id">
                {{ userCat.name }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showPhotoUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploadingPhoto" @click="submitPhotoUpload">
          {{ photoUploadSubmitText }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showPhotoEditDialog"
      title="编辑照片"
      width="520px"
      @closed="resetPhotoEditDialog"
    >
      <div class="photo-upload-panel">
        <img v-if="photoEditForm.url" :src="photoEditForm.url" class="photo-upload-preview" />
        <el-form label-width="88px">
          <el-form-item label="照片说明">
            <el-input v-model="photoEditForm.description" placeholder="可选备注" />
          </el-form-item>
          <el-form-item label="照片里的猫">
            <el-checkbox-group v-model="photoEditForm.tagCatIds">
              <el-checkbox v-for="userCat in cats" :key="userCat.id" :value="userCat.id">
                {{ userCat.name }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showPhotoEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingPhotoEdit" @click="submitPhotoEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { StarFilled, Plus, TrendCharts, SwitchButton, PictureFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { catApi, weightApi, photoApi } from '../api'
import { useUserStore } from '../stores/user'
import { sortPhotos, type PhotoSortMode } from '../utils/photoOrder'
import PhotoPreviewDialog from '../components/PhotoPreviewDialog.vue'

// 自定义图标
const KoiFish = {
  template: `<svg viewBox="0 0 1024 1024"><path fill="currentColor" d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z"/><path fill="currentColor" d="M512 256c-141.4 0-256 114.6-256 256s114.6 256 256 256 256-114.6 256-256-114.6-256-256-256zm0 428c-95.2 0-172-76.8-172-172s76.8-172 172-172 172 76.8 172 172-76.8 172-172 172z"/><circle fill="currentColor" cx="512" cy="512" r="64"/></svg>`
}

const router = useRouter()
const userStore = useUserStore()

const cats = ref<any[]>([])
const chartRef = ref<HTMLElement>()
const showAddDialog = ref(false)
const catFormRef = ref()
const addingCat = ref(false)
const activeTab = ref('cats')
const showPhotoDialog = ref(false)
const showPhotoUploadDialog = ref(false)
const showPhotoEditDialog = ref(false)
const selectedPhoto = ref<any | null>(null)
const dashboardPhotos = ref<any[]>([])
const uploadingPhoto = ref(false)
const savingPhotoEdit = ref(false)
const draggingPhotoId = ref<number | null>(null)
const photoFileInputRef = ref<HTMLInputElement | null>(null)
const selectedPhotoFile = ref<File | null>(null)
const photoUploadQueue = ref<File[]>([])
const photoUploadQueueIndex = ref(0)
const photoUploadPreviewUrl = ref('')
const photoRecommendations = ref<any[]>([])
const editingPhotoId = ref<number | null>(null)
const photoSortMode = ref<PhotoSortMode>((localStorage.getItem('photoSortMode') as PhotoSortMode) || 'manual')

// 猫咪表单
const catForm = reactive({
  name: '',
  gender: 'male',
  breed: '',
  breed_custom: '',  // 自定义品种
  color: '',
  color_custom: '',  // 自定义毛色
  birth_date: '',
  neutered: false,
  vaccination_status: '',
  deworming_date: '',
  medical_history: ''
})

const photoUploadForm = reactive({
  description: '',
  tagCatIds: [] as number[]
})

const photoEditForm = reactive({
  url: '',
  description: '',
  tagCatIds: [] as number[]
})

// 品种选择变化处理
function handleBreedChange(value: string) {
  if (value !== '其他') {
    catForm.breed_custom = ''
  }
}

// 毛色选择变化处理
function handleColorChange(value: string) {
  if (value !== '其他') {
    catForm.color_custom = ''
  }
}

const catRules = {
  name: [{ required: true, message: '请输入猫咪名字', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  breed: [{ required: true, message: '请选择品种', trigger: 'change' }],
  birth_date: [{ required: true, message: '请选择生日', trigger: 'change' }]
}

const sortedDashboardPhotos = computed(() => sortPhotos(dashboardPhotos.value, photoSortMode.value))

const currentPhotoUploadFile = computed(() => photoUploadQueue.value[photoUploadQueueIndex.value] ?? null)

const photoUploadDialogTitle = computed(() => {
  if (photoUploadQueue.value.length > 1) {
    return `上传照片（${photoUploadQueueIndex.value + 1}/${photoUploadQueue.value.length}）`
  }
  return '上传照片'
})

const photoUploadSubmitText = computed(() => {
  if (photoUploadQueue.value.length > 1) {
    return photoUploadQueueIndex.value < photoUploadQueue.value.length - 1 ? '上传并下一张' : '完成上传'
  }
  return '上传照片'
})

watch(photoSortMode, (value) => {
  localStorage.setItem('photoSortMode', value)
})

// 品种和毛色展示（空格分隔）
function getBreedDisplay(breed: string, color: string | undefined): string {
  if (!breed) return '未知品种'

  // 如果有毛色，显示 品种 毛色（空格分隔）
  if (color && color !== '其他') {
    return `${breed} ${color}`
  }

  // 如果没有毛色或毛色是"其他"，只显示品种
  return breed
}

// 格式化驱虫日期
function formatDeworming(dateStr: string): string {
  if (!dateStr) return '未记录'

  const dewormDate = new Date(dateStr)
  const today = new Date()
  const diffDays = Math.floor((today.getTime() - dewormDate.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays < 0) {
    return '未记录'
  } else if (diffDays === 0) {
    return '今天'
  } else if (diffDays < 30) {
    return `${diffDays}天前`
  } else if (diffDays < 90) {
    return `${Math.floor(diffDays / 30)}个月前`
  } else {
    return `${Math.floor(diffDays / 30)}个月前 ⚠️`
  }
}

// 疫苗状态样式
function getVaccinationClass(status: string): string {
  switch (status) {
    case '已完成基础免疫':
    case '定期接种中':
      return 'vaccination-complete'
    case '接种中':
      return 'vaccination-progress'
    default:
      return 'vaccination-none'
  }
}

function formatPhotoCatNames(photo: any): string {
  if (!photo?.cats || photo.cats.length === 0) return '未标注'
  return photo.cats.map((cat: any) => cat.name).join(' / ')
}

// 查看照片
function viewPhoto(photo: any) {
  selectedPhoto.value = photo
  showPhotoDialog.value = true
}

function openPhotoUploadDialog() {
  resetPhotoUploadDialog()
  showPhotoUploadDialog.value = true
}

function triggerPhotoFileSelect() {
  photoFileInputRef.value?.click()
}

function buildPhotoFormData(file: File, description: string, tagCatIds: number[]) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('description', description)
  formData.append('tag_cat_ids', JSON.stringify(tagCatIds))
  return formData
}

function appendUploadDecisionFlags(formData: FormData, options: { allowDuplicate?: boolean; allowSimilar?: boolean }) {
  if (options.allowDuplicate) {
    formData.append('allow_duplicate', 'true')
  }
  if (options.allowSimilar) {
    formData.append('allow_similar', 'true')
  }
}

function getDuplicatePhotoMessage(photo: any) {
  const names = formatPhotoCatNames(photo)
  return names ? `检测到一张相同照片，已存在于「${names}」。要继续上传吗？` : '检测到一张相同照片，已存在。要继续上传吗？'
}

function getSimilarPhotoMessage(photo: any) {
  const names = formatPhotoCatNames(photo)
  const confidenceText = typeof photo?.confidence === 'number'
    ? `（相似度约 ${Math.round(photo.confidence * 100)}%）`
    : ''
  return names
    ? `这张照片和「${names}」相册中的一张照片非常像${confidenceText}。要继续上传吗？`
    : `这张照片和现有照片非常像${confidenceText}。要继续上传吗？`
}

function handlePhotoDragStart(photoId: number) {
  if (photoSortMode.value !== 'manual') return
  draggingPhotoId.value = photoId
}

function handlePhotoDragEnd() {
  draggingPhotoId.value = null
}

async function handlePhotoDrop(targetPhoto: any) {
  if (photoSortMode.value !== 'manual') return
  if (!draggingPhotoId.value || draggingPhotoId.value === targetPhoto.id) {
    draggingPhotoId.value = null
    return
  }

  const reordered = [...sortedDashboardPhotos.value]
  const fromIndex = reordered.findIndex((photo) => photo.id === draggingPhotoId.value)
  const toIndex = reordered.findIndex((photo) => photo.id === targetPhoto.id)
  if (fromIndex === -1 || toIndex === -1) return

  const [moved] = reordered.splice(fromIndex, 1)
  reordered.splice(toIndex, 0, moved)

  const newIndex = reordered.findIndex((photo) => photo.id === draggingPhotoId.value)
  if (newIndex === -1) return
  const payload = {
    prev_photo_id: newIndex > 0 ? reordered[newIndex - 1].id : null,
    next_photo_id: newIndex < reordered.length - 1 ? reordered[newIndex + 1].id : null
  }

  try {
    await photoApi.reorderPhoto({
      user_id: Number(localStorage.getItem('userId')),
      photo_id: draggingPhotoId.value,
      ...payload
    })
    await loadDashboardPhotos()
  } catch (error) {
    ElMessage.error('调整排序失败')
  } finally {
    draggingPhotoId.value = null
  }
}

async function togglePhotoPin(photo: any) {
  try {
    await photoApi.updatePhoto(photo.id, { is_pinned: !photo.is_pinned })
    await loadDashboardPhotos()
  } catch (error) {
    ElMessage.error('置顶设置失败')
  }
}

async function preparePhotoUploadStep(file: File) {
  if (photoUploadPreviewUrl.value) {
    URL.revokeObjectURL(photoUploadPreviewUrl.value)
  }

  selectedPhotoFile.value = file
  photoUploadPreviewUrl.value = URL.createObjectURL(file)
  photoRecommendations.value = []
  photoUploadForm.description = ''
  photoUploadForm.tagCatIds = []

  await recommendPhotoTags(file)
}

async function handlePhotoFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (files.length === 0) return

  const validFiles = files.filter((file) => file.type.startsWith('image/'))
  if (validFiles.length === 0) {
    ElMessage.error('只能上传图片文件')
    input.value = ''
    return
  }

  if (validFiles.length !== files.length) {
    ElMessage.warning('已自动跳过非图片文件')
  }

  photoUploadQueue.value = validFiles
  photoUploadQueueIndex.value = 0
  input.value = ''

  await preparePhotoUploadStep(validFiles[0])
}

function resetPhotoUploadDialog() {
  if (photoUploadPreviewUrl.value) {
    URL.revokeObjectURL(photoUploadPreviewUrl.value)
  }
  photoUploadPreviewUrl.value = ''
  selectedPhotoFile.value = null
  photoUploadQueue.value = []
  photoUploadQueueIndex.value = 0
  photoUploadForm.description = ''
  photoUploadForm.tagCatIds = []
  photoRecommendations.value = []
}

function resetPhotoEditDialog() {
  editingPhotoId.value = null
  photoEditForm.url = ''
  photoEditForm.description = ''
  photoEditForm.tagCatIds = []
}

async function recommendPhotoTags(file: File) {
  try {
    const userId = Number(localStorage.getItem('userId'))
    if (!userId) return
    const res = await photoApi.recommendTags(userId, file)
    photoRecommendations.value = res.recommendations || []
    if (photoUploadForm.tagCatIds.length === 0 && photoRecommendations.value.length > 0) {
      photoUploadForm.tagCatIds = photoRecommendations.value.slice(0, 2).map((item: any) => item.cat_id)
    }
  } catch (error) {
    photoRecommendations.value = []
  }
}

async function uploadSelectedPhoto(options: { allowDuplicate?: boolean; allowSimilar?: boolean } = {}) {
  if (!selectedPhotoFile.value) {
    throw new Error('missing_file')
  }
  const primaryCatId = photoUploadForm.tagCatIds[0]
  const formData = buildPhotoFormData(selectedPhotoFile.value, photoUploadForm.description, photoUploadForm.tagCatIds)
  appendUploadDecisionFlags(formData, options)
  await catApi.uploadPhoto(primaryCatId, formData)
}

async function advancePhotoUploadQueue(message: string) {
  const totalFiles = photoUploadQueue.value.length || 1
  const hasNext = photoUploadQueueIndex.value < photoUploadQueue.value.length - 1

  if (hasNext) {
    photoUploadQueueIndex.value += 1
    await preparePhotoUploadStep(photoUploadQueue.value[photoUploadQueueIndex.value])
    ElMessage.success(totalFiles > 1 ? `${message}，请继续处理第 ${photoUploadQueueIndex.value + 1}/${totalFiles} 张` : message)
    return
  }

  ElMessage.success(totalFiles > 1 ? `已完成 ${totalFiles} 张照片处理` : message)
  showPhotoUploadDialog.value = false
  await loadDashboardPhotos()
}

async function submitPhotoUpload() {
  if (!selectedPhotoFile.value) {
    ElMessage.error('请先选择照片')
    return
  }
  if (photoUploadForm.tagCatIds.length === 0) {
    ElMessage.error('请至少标注一只猫咪')
    return
  }

  uploadingPhoto.value = true
  try {
    await uploadSelectedPhoto()
    await advancePhotoUploadQueue('照片上传成功')
  } catch (error: any) {
    const conflictDetail = error?.response?.data?.detail
    if (error?.response?.status === 409 && conflictDetail?.code === 'duplicate_photo') {
      try {
        await ElMessageBox.confirm(getDuplicatePhotoMessage(conflictDetail.duplicate_photo), '检测到重复照片', {
          confirmButtonText: '继续上传',
          cancelButtonText: '跳过这张',
          type: 'warning'
        })
        await uploadSelectedPhoto({ allowDuplicate: true, allowSimilar: true })
        await advancePhotoUploadQueue('重复照片已继续上传')
      } catch (confirmError: any) {
        if (confirmError === 'cancel') {
          await advancePhotoUploadQueue('已跳过重复照片')
        } else if (confirmError !== 'close') {
          ElMessage.error('上传失败')
        }
      }
    } else if (error?.response?.status === 409 && conflictDetail?.code === 'similar_photo') {
      try {
        await ElMessageBox.confirm(getSimilarPhotoMessage(conflictDetail.similar_photo), '检测到相似照片', {
          confirmButtonText: '继续上传',
          cancelButtonText: '跳过这张',
          type: 'warning'
        })
        await uploadSelectedPhoto({ allowSimilar: true })
        await advancePhotoUploadQueue('相似照片已继续上传')
      } catch (confirmError: any) {
        if (confirmError === 'cancel') {
          await advancePhotoUploadQueue('已跳过相似照片')
        } else if (confirmError !== 'close') {
          ElMessage.error('上传失败')
        }
      }
    } else {
      ElMessage.error('上传失败')
    }
  } finally {
    uploadingPhoto.value = false
  }
}

function openPhotoEditDialog(photo: any) {
  editingPhotoId.value = photo.id
  photoEditForm.url = photo.thumbnail || photo.url
  photoEditForm.description = photo.description || ''
  photoEditForm.tagCatIds = (photo.cats || []).map((cat: any) => cat.id)
  showPhotoEditDialog.value = true
}

async function submitPhotoEdit() {
  try {
    if (!editingPhotoId.value) return
    if (photoEditForm.tagCatIds.length === 0) {
      ElMessage.error('请至少保留一只猫咪标注')
      return
    }

    savingPhotoEdit.value = true
    await photoApi.updatePhoto(editingPhotoId.value, {
      description: photoEditForm.description,
      tag_cat_ids: photoEditForm.tagCatIds
    })
    ElMessage.success('保存成功')
    showPhotoEditDialog.value = false
    await loadDashboardPhotos()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    savingPhotoEdit.value = false
  }
}

async function deletePhoto(photo: any) {
  try {
    await ElMessageBox.confirm('确定要删除这张照片吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await photoApi.deletePhoto(photo.id)
    ElMessage.success('删除成功')
    await loadDashboardPhotos()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function loadCats() {
  try {
    const userId = Number(localStorage.getItem('userId'))
    if (!userId) {
      ElMessage.error('请重新登录')
      router.push('/login')
      return
    }
    const res = await catApi.getCats(userId)
    cats.value = res
  } catch (error) {
    ElMessage.error('加载猫咪列表失败')
  }
}

async function loadDashboardPhotos() {
  try {
    const userId = Number(localStorage.getItem('userId'))
    if (!userId) return
    const res = await photoApi.getAllPhotos(userId)
    dashboardPhotos.value = res
  } catch (error) {
    ElMessage.error('加载相册失败')
  }
}

async function loadChart() {
  try {
    const userId = Number(localStorage.getItem('userId'))
    if (!userId) return
    const res = await weightApi.getChartData(userId)

    // 使用 nextTick 确保 DOM 已渲染
    await nextTick()

    if (!chartRef.value) {
      console.log('Chart container not ready')
      return
    }

    const existingChart = echarts.getInstanceByDom(chartRef.value)
    if (existingChart) {
      existingChart.dispose()
    }

    const chart = echarts.init(chartRef.value)

    const validData = res.filter((item: any) => item.data && item.data.length > 0)

    if (validData.length === 0) {
      chart.setOption({
        title: {
          text: '暂无体重数据',
          left: 'center',
          top: 'center',
          textStyle: { color: '#999', fontSize: 16 }
        }
      })
      return
    }

    const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe']

    const series = validData.map((item: any, index: number) => ({
      name: item.cat_name,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { width: 3 },
      itemStyle: { color: colors[index % colors.length] },
      data: item.data.map((d: any) => [d.date, d.weight])
    }))

    chart.setOption({
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let result = params[0].axisValue + '<br/>'
          params.forEach((item: any) => {
            result += `${item.marker}${item.seriesName}: ${item.value[1]}g<br/>`
          })
          return result
        }
      },
      legend: {
        data: validData.map((item: any) => item.cat_name),
        bottom: 0
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'time',
        boundaryGap: false
      },
      yAxis: {
        type: 'value',
        name: '体重(g)',
        axisLine: { show: true }
      },
      series
    })

    const handleResize = () => chart.resize()
    window.addEventListener('resize', handleResize)
  } catch (error) {
    console.error('加载图表失败:', error)
    ElMessage.error('加载图表失败')
  }
}

async function handleAddCat() {
  try {
    await catFormRef.value.validate()
    addingCat.value = true
    const userId = Number(localStorage.getItem('userId'))

    // 处理自定义品种和毛色
    const submitData = {
      ...catForm,
      user_id: userId,
      breed: catForm.breed === '其他' ? catForm.breed_custom : catForm.breed,
      color: catForm.color === '其他' ? catForm.color_custom : catForm.color
    }
    // 移除临时字段
    delete (submitData as any).breed_custom
    delete (submitData as any).color_custom

    await catApi.addCat(submitData)

    ElMessage.success('添加成功')
    showAddDialog.value = false

    // 重置表单
    catForm.name = ''
    catForm.gender = 'male'
    catForm.breed = ''
    catForm.breed_custom = ''
    catForm.color = ''
    catForm.color_custom = ''
    catForm.birth_date = ''
    catForm.neutered = false
    catForm.vaccination_status = ''
    catForm.deworming_date = ''
    catForm.medical_history = ''

    loadCats()
    loadChart()
  } catch (error) {
    ElMessage.error('添加失败')
  } finally {
    addingCat.value = false
  }
}

function goToCatDetail(catId: number) {
  router.push(`/cat/${catId}`)
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

// 监听 tab 切换，当切换到猫咪页签时重新渲染图表
watch(activeTab, (newTab) => {
  if (newTab === 'cats') {
    loadChart()
  }
})

onMounted(() => {
  loadCats()
  loadChart()
  loadDashboardPhotos()
})
</script>

<style scoped>
.dashboard-container {
  --cat-orange-400: #f5a24f;
  --cat-orange-500: #ef8e36;
  --cat-orange-600: #dc7420;
  --cat-brown-700: #8f5831;
  --cat-ink: #5f4634;
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 24px 20px 32px;
  background:
    radial-gradient(circle at 14% 18%, rgba(255, 219, 164, 0.64) 0, rgba(255, 219, 164, 0.18) 16%, transparent 34%),
    radial-gradient(circle at 88% 12%, rgba(255, 187, 120, 0.24) 0, rgba(255, 187, 120, 0.12) 18%, transparent 36%),
    radial-gradient(circle at 76% 84%, rgba(255, 210, 155, 0.3) 0, rgba(255, 210, 155, 0.08) 18%, transparent 32%),
    linear-gradient(180deg, #fff7ec 0%, #ffe9ca 52%, #ffdcb5 100%);
}

.dashboard-container::before,
.dashboard-container::after {
  position: absolute;
  pointer-events: none;
  opacity: 0.24;
  font-size: 120px;
  line-height: 1;
}

.dashboard-container::before {
  content: '🐾';
  top: 92px;
  right: 34px;
  transform: rotate(-16deg);
}

.dashboard-container::after {
  content: '🐾';
  left: 20px;
  bottom: 28px;
  transform: rotate(15deg) scale(0.9);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(135deg, rgba(255, 250, 241, 0.98), rgba(255, 239, 212, 0.96));
  border: 1px solid rgba(255, 197, 123, 0.45);
  border-radius: 26px;
  box-shadow: 0 18px 40px rgba(217, 144, 63, 0.16);
  margin-bottom: 24px;
  backdrop-filter: blur(12px);
}

.dashboard-header h1 {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 24px;
  color: var(--cat-orange-600);
}

.dashboard-welcome {
  color: rgba(95, 70, 52, 0.82);
}

.dashboard-header :deep(.el-button--text) {
  color: var(--cat-orange-600);
}

.dashboard-content {
  position: relative;
  background: linear-gradient(180deg, rgba(255, 253, 248, 0.96), rgba(255, 247, 232, 0.98));
  border: 1px solid rgba(248, 196, 128, 0.5);
  border-radius: 30px;
  padding: 28px 24px;
  box-shadow: 0 24px 55px rgba(200, 132, 59, 0.15);
  backdrop-filter: blur(10px);
}

.dashboard-content::before {
  content: '';
  position: absolute;
  inset: 14px;
  border-radius: 22px;
  border: 1px dashed rgba(242, 168, 84, 0.28);
  pointer-events: none;
}

.main-tabs {
  margin-bottom: 20px;
}

.main-tabs :deep(.el-tabs__header) {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.main-tabs :deep(.el-tabs__nav-wrap) {
  display: flex;
  justify-content: center;
  padding: 0 14px;
}

.main-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.main-tabs :deep(.el-tabs__nav-scroll) {
  display: flex;
  justify-content: center;
  width: fit-content;
  max-width: 100%;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 232, 199, 0.78);
  border: 1px solid rgba(247, 188, 104, 0.45);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

.main-tabs :deep(.el-tabs__nav) {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  padding: 0;
}

.main-tabs :deep(.el-tabs__item) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 96px;
  height: 40px;
  padding: 0 24px !important;
  box-sizing: border-box;
  text-align: center;
  border-radius: 999px;
  color: rgba(111, 73, 39, 0.78);
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  transition: color 0.2s ease, background 0.2s ease, transform 0.2s ease;
}

.main-tabs :deep(.el-tabs__item:first-child),
.main-tabs :deep(.el-tabs__item:last-child) {
  padding-left: 24px !important;
  padding-right: 24px !important;
}

.main-tabs :deep(.el-tabs__item:hover) {
  color: var(--cat-orange-600);
}

.main-tabs :deep(.el-tabs__item.is-active) {
  color: #fff;
  background: linear-gradient(135deg, var(--cat-orange-400), var(--cat-orange-600));
  box-shadow: 0 10px 18px rgba(239, 142, 54, 0.28);
  transform: translateY(-1px);
}

.main-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.dashboard-content :deep(.el-button--primary) {
  border-color: transparent;
  background: linear-gradient(135deg, var(--cat-orange-400), var(--cat-orange-600));
  box-shadow: 0 10px 18px rgba(239, 142, 54, 0.22);
}

.dashboard-content :deep(.el-button--default),
.dashboard-content :deep(.el-select .el-input__wrapper) {
  border-color: rgba(245, 185, 110, 0.5);
  color: var(--cat-ink);
  background: rgba(255, 249, 240, 0.95);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 20px 0;
  font-size: 20px;
  color: var(--cat-orange-600);
}

.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.cat-card {
  background: linear-gradient(145deg, rgba(255, 251, 245, 0.98), rgba(255, 241, 220, 0.94));
  border-radius: 18px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(246, 186, 110, 0.36);
  box-shadow: 0 14px 26px rgba(214, 151, 76, 0.08);
}

.cat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 18px 34px rgba(214, 151, 76, 0.16);
  border-color: rgba(239, 142, 54, 0.55);
}

.cat-card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.cat-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 35% 30%, rgba(255, 255, 255, 0.72), transparent 28%),
    linear-gradient(145deg, #ffca7c, #ef8e36);
  border: 4px solid rgba(255, 251, 245, 0.92);
  box-shadow: 0 14px 26px rgba(235, 149, 56, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  overflow: hidden;
}

.cat-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cat-info h3 {
  margin: 0;
  font-size: 18px;
  color: var(--cat-orange-600);
}

.cat-info p {
  margin: 4px 0 0;
  font-size: 14px;
  color: rgba(95, 70, 52, 0.72);
}

.cat-details {
  font-size: 14px;
}

.cat-details p {
  margin: 8px 0;
  display: flex;
  justify-content: space-between;
}

.cat-details span:first-child {
  color: rgba(138, 106, 80, 0.72);
}

.cat-details span:last-child {
  color: var(--cat-ink);
  font-weight: 500;
}

.vaccination-complete {
  color: #5e9f2d !important;
}

.vaccination-progress {
  color: #c97916 !important;
}

.vaccination-none {
  color: #d16339 !important;
}

.add-cat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  background: rgba(255, 249, 240, 0.95);
  border: 2px dashed rgba(239, 142, 54, 0.35);
  border-radius: 18px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(138, 106, 80, 0.72);
}

.add-cat-card:hover {
  border-color: rgba(239, 142, 54, 0.6);
  background: rgba(255, 242, 221, 0.92);
}

.add-cat-card .icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.chart-section {
  margin-top: 32px;
}

.chart-container {
  height: 350px;
  background: linear-gradient(180deg, rgba(255, 249, 239, 0.98), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(246, 186, 110, 0.42);
  border-radius: 22px;
  box-shadow: 0 16px 28px rgba(214, 151, 76, 0.1);
}

.album-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.album-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-bottom: 16px;
  gap: 12px;
}

.photo-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 18px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid rgba(246, 186, 110, 0.3);
  box-shadow: 0 14px 26px rgba(214, 151, 76, 0.12);
  transition: all 0.3s ease;
}

.photo-item.manual-sort {
  cursor: grab;
}

.photo-item.is-dragging {
  opacity: 0.65;
}

.photo-item:hover {
  transform: scale(1.03);
  box-shadow: 0 18px 34px rgba(214, 151, 76, 0.16);
}

.photo-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  background: linear-gradient(transparent, rgba(62, 35, 15, 0.74));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.photo-item:hover .photo-overlay {
  opacity: 1;
}

.cat-name {
  color: white;
  font-size: 14px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.photo-overlay-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.photo-upload-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.photo-upload-file-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.photo-upload-file-name {
  color: rgba(95, 70, 52, 0.82);
  font-size: 14px;
  word-break: break-all;
}

.photo-upload-queue-status {
  color: rgba(138, 106, 80, 0.72);
  font-size: 13px;
}

.photo-upload-preview {
  width: 100%;
  height: auto;
  max-height: 260px;
  object-fit: contain;
  object-position: center;
  display: block;
  background: #fff7ea;
  border-radius: 16px;
}

.photo-recommendations {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.photo-recommendation-item {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 228, 194, 0.96);
  color: var(--cat-orange-600);
  font-size: 12px;
}

.dashboard-content :deep(.el-empty__description p) {
  color: rgba(138, 106, 80, 0.72);
}
</style>
