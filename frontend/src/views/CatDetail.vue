<template>
  <div class="cat-detail-container">
    <header class="detail-header">
      <el-button @click="goBack" text>
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h1>{{ cat?.name || '猫咪详情' }}</h1>
      <div style="width: 60px"></div>
    </header>

    <main class="detail-content" v-if="cat">
      <!-- 页签切换 -->
      <el-tabs v-model="activeTab" class="detail-tabs">
        <!-- 基本信息页签 -->
        <el-tab-pane label="基本信息" name="info">
          <div class="info-section">
            <div class="cat-avatar-section">
              <div class="cat-avatar-large">
                <img v-if="cat.avatar" :src="cat.avatar" :alt="cat.name" />
                <span v-else>{{ cat.gender === 'female' ? '🐱' : '😺' }}</span>
              </div>
              <el-button type="primary" size="small" @click="showAvatarDialog = true">
                更换头像
              </el-button>
            </div>

            <el-descriptions :column="2" border>
              <el-descriptions-item label="名字">{{ cat.name }}</el-descriptions-item>
              <el-descriptions-item label="性别">
                {{ cat.gender === 'female' ? '母猫' : '公猫' }}
              </el-descriptions-item>
              <el-descriptions-item label="品种">
                {{ getBreedDisplay(cat.breed, cat.color) }}
              </el-descriptions-item>
              <el-descriptions-item label="毛色">
                {{ cat.color || '未设置' }}
              </el-descriptions-item>
              <el-descriptions-item label="生日">{{ cat.birth_date }}</el-descriptions-item>
              <el-descriptions-item label="年龄">
                {{ calculateAge(cat.birth_date) }}
              </el-descriptions-item>
              <el-descriptions-item label="绝育状态">
                <el-tag :type="cat.neutered ? 'success' : 'info'">
                  {{ cat.neutered ? '已绝育' : '未绝育' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="当前体重">
                {{ latestWeight ? latestWeight + 'g' : '暂无记录' }}
              </el-descriptions-item>
            </el-descriptions>

            <!-- 健康信息卡片 -->
            <div class="health-info-card">
              <h3><el-icon><FirstAidKit /></el-icon> 健康信息</h3>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="疫苗接种">
                  <el-tag :type="getVaccinationType(cat.vaccination_status)">
                    {{ cat.vaccination_status || '未设置' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="驱虫日期">
                  <span v-if="cat.deworming_date">
                    {{ cat.deworming_date }}
                    <el-tag 
                      v-if="isDewormingDue(cat.deworming_date)" 
                      type="warning" 
                      size="small"
                    >
                      需驱虫
                    </el-tag>
                    <el-tag v-else type="success" size="small">
                      已驱虫
                    </el-tag>
                  </span>
                  <span v-else class="text-muted">未设置</span>
                </el-descriptions-item>
                <el-descriptions-item label="病史记录" :span="2">
                  <div class="medical-history">
                    {{ cat.medical_history || '暂无病史记录' }}
                  </div>
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <div class="action-buttons">
              <el-button type="primary" @click="showEditDialog = true">
                <el-icon><Edit /></el-icon>
                编辑信息
              </el-button>
              <el-button type="danger" @click="handleDeleteCat">
                <el-icon><Delete /></el-icon>
                删除猫咪
              </el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- 体重记录页签 -->
        <el-tab-pane label="体重记录" name="weight">
          <div class="weight-section">
            <div class="weight-header">
              <h3>体重记录</h3>
              <el-button type="primary" @click="showWeightDialog = true">
                <el-icon><Plus /></el-icon>
                添加记录
              </el-button>
            </div>

            <div class="weight-chart" ref="weightChartRef"></div>

            <el-table :data="weightRecords" style="width: 100%" v-if="weightRecords.length > 0">
              <el-table-column prop="record_date" label="日期" width="180" />
              <el-table-column prop="weight" label="体重(g)" width="120" />
              <el-table-column prop="note" label="备注" />
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button type="primary" size="small" text @click="editWeightRecord(row)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-button type="danger" size="small" text @click="deleteWeightRecord(row.id)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <el-empty v-else description="暂无体重记录" />
          </div>
        </el-tab-pane>

        <!-- 相册页签 -->
        <el-tab-pane label="相册" name="album">
          <div class="album-section">
            <div class="album-header">
              <h3>猫咪相册</h3>
              <el-upload
                :show-file-list="false"
                :before-upload="beforePhotoUpload"
                :http-request="handlePhotoUpload"
                accept="image/*"
              >
                <el-button type="primary">
                  <el-icon><Plus /></el-icon>
                  上传照片
                </el-button>
              </el-upload>
            </div>

            <div class="photo-grid" v-if="photos.length > 0">
              <div 
                class="photo-item" 
                v-for="(photo, index) in photos" 
                :key="index"
              >
                <img :src="photo.url" @click="viewPhoto(photo)" />
                <div class="photo-actions">
                  <el-button 
                    type="danger" 
                    size="small" 
                    circle
                    @click="deletePhoto(index)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>

            <el-empty v-else description="暂无照片" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </main>

    <!-- 编辑信息对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑猫咪信息" width="600px">
      <el-form :model="editForm" ref="editFormRef" label-width="100px">
        <el-form-item label="名字" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="editForm.gender">
            <el-radio label="male">公猫</el-radio>
            <el-radio label="female">母猫</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="品种" prop="breed">
          <el-select v-model="editForm.breed" placeholder="请选择品种" style="width: 100%">
            <el-option label="英短蓝猫" value="英短蓝猫" />
            <el-option label="英短金渐层" value="英短金渐层" />
            <el-option label="英短银渐层" value="英短银渐层" />
            <el-option label="美短虎斑" value="美短虎斑" />
            <el-option label="美短起司猫" value="美短起司猫" />
            <el-option label="橘猫" value="橘猫" />
            <el-option label="布偶猫" value="布偶猫" />
            <el-option label="暹罗猫" value="暹罗猫" />
            <el-option label="缅因猫" value="缅因猫" />
            <el-option label="波斯猫" value="波斯猫" />
            <el-option label="折耳猫" value="折耳猫" />
            <el-option label="加菲猫" value="加菲猫" />
            <el-option label="无毛猫（斯芬克斯）" value="无毛猫" />
            <el-option label="田园猫（狸花猫）" value="田园猫" />
            <el-option label="其他品种" value="其他" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="毛色" prop="color">
          <el-select v-model="editForm.color" placeholder="请选择毛色" style="width: 100%">
            <el-option label="白色" value="白色" />
            <el-option label="黑色" value="黑色" />
            <el-option label="灰色/蓝灰色" value="灰色" />
            <el-option label="橘色/黄色" value="橘色" />
            <el-option label="虎斑纹" value="虎斑纹" />
            <el-option label="三花（白+黑+橘）" value="三花" />
            <el-option label="玳瑁色" value="玳瑁色" />
            <el-option label="奶牛猫（黑白）" value="奶牛猫" />
            <el-option label="重点色（暹罗色）" value="重点色" />
            <el-option label="金渐层" value="金渐层" />
            <el-option label="银渐层" value="银渐层" />
            <el-option label="奶油色" value="奶油色" />
            <el-option label="巧克力色/棕色" value="巧克力色" />
            <el-option label="其他颜色" value="其他" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="生日" prop="birth_date">
          <el-date-picker 
            v-model="editForm.birth_date" 
            type="date" 
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        
        <el-form-item label="是否绝育">
          <el-switch v-model="editForm.neutered" />
        </el-form-item>

        <el-divider content-position="left">健康信息</el-divider>

        <el-form-item label="疫苗接种">
          <el-select v-model="editForm.vaccination_status" placeholder="请选择" style="width: 100%">
            <el-option label="未接种" value="未接种" />
            <el-option label="接种中" value="接种中" />
            <el-option label="已完成基础免疫" value="已完成基础免疫" />
            <el-option label="定期接种中" value="定期接种中" />
          </el-select>
        </el-form-item>

        <el-form-item label="驱虫日期">
          <el-date-picker 
            v-model="editForm.deworming_date" 
            type="date" 
            placeholder="选择最近驱虫日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="病史记录">
          <el-input 
            v-model="editForm.medical_history" 
            type="textarea" 
            :rows="3"
            placeholder="请输入猫咪病史记录"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加体重记录对话框 -->
    <el-dialog v-model="showWeightDialog" title="添加体重记录" width="400px">
      <el-form :model="weightForm" ref="weightFormRef" label-width="80px">
        <el-form-item label="日期" prop="record_date">
          <el-date-picker 
            v-model="weightForm.record_date" 
            type="date" 
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="体重(g)" prop="weight">
          <el-input-number v-model="weightForm.weight" :min="0" :max="20000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="weightForm.note" placeholder="可选备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showWeightDialog = false">取消</el-button>
        <el-button type="primary" :loading="addingWeight" @click="handleAddWeight">确定</el-button>
      </template>
    </el-dialog>

    <!-- 更换头像对话框 -->
    <el-dialog v-model="showAvatarDialog" title="更换头像" width="400px">
      <el-upload
        class="avatar-uploader"
        :show-file-list="false"
        :before-upload="beforeAvatarUpload"
        :http-request="handleAvatarUpload"
        accept="image/*"
      >
        <img v-if="cat?.avatar" :src="cat.avatar" class="avatar-preview" />
        <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
      </el-upload>
    </el-dialog>

    <!-- 照片预览对话框 -->
    <el-dialog v-model="showPhotoPreview" width="80%">
      <img :src="previewPhoto?.url" style="width: 100%;" v-if="previewPhoto" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Delete, Plus, FirstAidKit } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { catApi, weightApi } from '../api'

const router = useRouter()
const route = useRoute()

const cat = ref<any>(null)
const weightRecords = ref<any[]>([])
const photos = ref<{ url: string }[]>([])
const activeTab = ref('info')
const showEditDialog = ref(false)
const showWeightDialog = ref(false)
const showAvatarDialog = ref(false)
const showPhotoPreview = ref(false)
const previewPhoto = ref<{ url: string } | null>(null)
const saving = ref(false)
const addingWeight = ref(false)
const weightChartRef = ref<HTMLElement>()
const editFormRef = ref()
const weightFormRef = ref()

const editForm = reactive({
  name: '',
  gender: 'male',
  breed: '',
  color: '',
  birth_date: '',
  neutered: false,
  vaccination_status: '',
  deworming_date: '',
  medical_history: ''
})

const weightForm = reactive({
  record_date: '',
  weight: 0,
  note: ''
})

// 编辑的体重记录ID
const editingWeightId = ref<number | null>(null)

// 计算最新体重
const latestWeight = computed(() => {
  if (weightRecords.value.length === 0) return null
  return weightRecords.value[0].weight
})

// 品种智能匹配展示
function getBreedDisplay(breed: string, color: string | undefined): string {
  if (!breed) return '未知品种'
  
  const breedColorMap: Record<string, Record<string, string>> = {
    '英短蓝猫': { '灰色': '英短蓝猫', '默认': '英短蓝猫' },
    '英短金渐层': { '金渐层': '英短金渐层', '默认': '英短金渐层' },
    '英短银渐层': { '银渐层': '英短银渐层', '默认': '英短银渐层' },
    '美短虎斑': { '虎斑纹': '美短虎斑', '默认': '美短虎斑' },
    '美短起司猫': { '奶牛猫': '美短起司', '默认': '美短起司猫' },
    '橘猫': { '橘色': '橘猫', '默认': '橘猫' },
    '布偶猫': { '重点色': '布偶猫', '奶油色': '布偶猫', '默认': '布偶猫' },
    '暹罗猫': { '重点色': '暹罗猫', '默认': '暹罗猫' },
    '田园猫': {
      '橘色': '橘猫（田园）',
      '虎斑纹': '狸花猫',
      '三花': '三花猫',
      '玳瑁色': '玳瑁猫',
      '奶牛猫': '奶牛猫',
      '默认': '田园猫'
    }
  }
  
  if (breedColorMap[breed] && color && breedColorMap[breed][color]) {
    return breedColorMap[breed][color]
  }
  
  if (color && color !== '其他') {
    return `${breed}（${color}）`
  }
  
  return breed
}

// 疫苗状态标签类型
function getVaccinationType(status: string): string {
  switch (status) {
    case '已完成基础免疫':
    case '定期接种中':
      return 'success'
    case '接种中':
      return 'warning'
    default:
      return 'info'
  }
}

// 计算年龄
function calculateAge(birthDate: string): string {
  if (!birthDate) return '未知'
  const birth = new Date(birthDate)
  const now = new Date()
  const months = (now.getFullYear() - birth.getFullYear()) * 12 + (now.getMonth() - birth.getMonth())
  if (months < 1) return '不到1个月'
  if (months < 12) return `${months}个月`
  const years = Math.floor(months / 12)
  const remainingMonths = months % 12
  if (remainingMonths === 0) return `${years}岁`
  return `${years}岁${remainingMonths}个月`
}

// 检查是否需要驱虫（超过3个月）
function isDewormingDue(date: string): boolean {
  if (!date) return true
  const lastDeworming = new Date(date)
  const now = new Date()
  const diffTime = now.getTime() - lastDeworming.getTime()
  const diffDays = diffTime / (1000 * 60 * 60 * 24)
  return diffDays > 90 // 超过90天需要驱虫
}

async function loadCatDetail() {
  try {
    const catId = route.params.id as string
    const res = await catApi.getCat(Number(catId))
    cat.value = res
    
    // 初始化编辑表单
    editForm.name = res.name
    editForm.gender = res.gender
    editForm.breed = res.breed || ''
    editForm.color = res.color || ''
    editForm.birth_date = res.birth_date
    editForm.neutered = res.neutered
    editForm.vaccination_status = res.vaccination_status || ''
    editForm.deworming_date = res.deworming_date || ''
    editForm.medical_history = res.medical_history || ''
    
    // 加载相册
    if (res.photos) {
      photos.value = res.photos.map((url: string) => ({ url }))
    }
  } catch (error) {
    ElMessage.error('加载猫咪详情失败')
    router.push('/dashboard')
  }
}

async function loadWeightRecords() {
  try {
    const catId = route.params.id as string
    const res = await weightApi.getRecords(Number(catId))
    weightRecords.value = res.sort((a: any, b: any) => 
      new Date(b.record_date).getTime() - new Date(a.record_date).getTime()
    )
    renderWeightChart()
  } catch (error) {
    ElMessage.error('加载体重记录失败')
  }
}

function renderWeightChart() {
  if (!weightChartRef.value || weightRecords.value.length === 0) return
  
  const existingChart = echarts.getInstanceByDom(weightChartRef.value)
  if (existingChart) {
    existingChart.dispose()
  }
  
  const chart = echarts.init(weightChartRef.value)
  const sortedRecords = [...weightRecords.value].sort((a, b) => 
    new Date(a.record_date).getTime() - new Date(b.record_date).getTime()
  )
  
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        return `${data.axisValue}<br/>体重: ${data.value}g`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: sortedRecords.map((r: any) => r.record_date)
    },
    yAxis: {
      type: 'value',
      name: '体重(g)'
    },
    series: [{
      type: 'line',
      smooth: true,
      data: sortedRecords.map((r: any) => r.weight),
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
          { offset: 1, color: 'rgba(102, 126, 234, 0.05)' }
        ])
      },
      lineStyle: { color: '#667eea', width: 3 },
      itemStyle: { color: '#667eea' }
    }]
  })
}

async function handleSaveEdit() {
  try {
    saving.value = true
    const catId = route.params.id as string
    await catApi.updateCat(Number(catId), editForm)
    ElMessage.success('保存成功')
    showEditDialog.value = false
    loadCatDetail()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDeleteCat() {
  try {
    await ElMessageBox.confirm('确定要删除这只猫咪吗？此操作不可恢复。', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const catId = route.params.id as string
    await catApi.deleteCat(Number(catId))
    ElMessage.success('删除成功')
    router.push('/dashboard')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 编辑体重记录
function editWeightRecord(record: any) {
  editingWeightId.value = record.id
  weightForm.record_date = record.record_date
  weightForm.weight = record.weight
  weightForm.note = record.note || ''
  showWeightDialog.value = true
}

// 删除体重记录
async function deleteWeightRecord(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除这条体重记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await weightApi.deleteRecord(id)
    ElMessage.success('删除成功')
    loadWeightRecords()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function handleAddWeight() {
  try {
    addingWeight.value = true
    const catId = route.params.id as string
    
    if (editingWeightId.value) {
      // 编辑模式
      await weightApi.updateRecord(editingWeightId.value, weightForm)
      ElMessage.success('更新成功')
    } else {
      // 新增模式
      await weightApi.addRecord({
        cat_id: Number(catId),
        ...weightForm
      })
      ElMessage.success('添加成功')
    }
    
    showWeightDialog.value = false
    // 重置表单
    weightForm.record_date = ''
    weightForm.weight = 0
    weightForm.note = ''
    editingWeightId.value = null
    
    loadWeightRecords()
  } catch (error) {
    ElMessage.error(editingWeightId.value ? '更新失败' : '添加失败')
  } finally {
    addingWeight.value = false
  }
}

function beforeAvatarUpload(file: File) {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5
  
  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB!')
    return false
  }
  return true
}

async function handleAvatarUpload(options: any) {
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    const catId = route.params.id as string
    await catApi.uploadAvatar(Number(catId), formData)
    ElMessage.success('头像更新成功')
    showAvatarDialog.value = false
    loadCatDetail()
  } catch (error) {
    ElMessage.error('上传失败')
  }
}

function beforePhotoUpload(file: File) {
  return beforeAvatarUpload(file)
}

async function handlePhotoUpload(options: any) {
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    const catId = route.params.id as string
    const res = await catApi.uploadPhoto(Number(catId), formData)
    photos.value.push({ url: res.url })
    ElMessage.success('照片上传成功')
  } catch (error) {
    ElMessage.error('上传失败')
  }
}

function viewPhoto(photo: { url: string }) {
  previewPhoto.value = photo
  showPhotoPreview.value = true
}

async function deletePhoto(index: number) {
  try {
    await ElMessageBox.confirm('确定要删除这张照片吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    photos.value.splice(index, 1)
    // 更新到后端
    const catId = route.params.id as string
    await catApi.updatePhotos(Number(catId), photos.value.map(p => p.url))
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function goBack() {
  router.push('/dashboard')
}

onMounted(() => {
  loadCatDetail()
  loadWeightRecords()
})
</script>

<style scoped>
.cat-detail-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.detail-header h1 {
  margin: 0;
  font-size: 24px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.detail-content {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.detail-tabs {
  margin-bottom: 20px;
}

.info-section {
  max-width: 800px;
  margin: 0 auto;
}

.cat-avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.cat-avatar-large {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  margin-bottom: 12px;
  overflow: hidden;
}

.cat-avatar-large img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.health-info-card {
  margin-top: 24px;
  padding: 20px;
  background: #f8f9ff;
  border-radius: 12px;
}

.health-info-card h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  color: #667eea;
}

.medical-history {
  white-space: pre-wrap;
  word-break: break-word;
}

.text-muted {
  color: #999;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  justify-content: center;
}

.weight-section {
  max-width: 900px;
  margin: 0 auto;
}

.weight-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.weight-header h3 {
  margin: 0;
}

.weight-chart {
  height: 300px;
  margin-bottom: 24px;
}

.album-section {
  max-width: 900px;
  margin: 0 auto;
}

.album-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.album-header h3 {
  margin: 0;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.photo-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.photo-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
}

.photo-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.photo-item:hover .photo-actions {
  opacity: 1;
}

.avatar-uploader {
  display: flex;
  justify-content: center;
}

.avatar-uploader-icon {
  font-size: 48px;
  color: #8c939d;
  width: 150px;
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
}

.avatar-preview {
  width: 150px;
  height: 150px;
  object-fit: cover;
  border-radius: 8px;
}
</style>