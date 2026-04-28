<template>
  <div class="dashboard-container">
    <header class="dashboard-header">
      <h1>
        <el-icon><KoiFish /></el-icon>
        猫咪成长健康管理系统
      </h1>
      <div style="display: flex; align-items: center; gap: 16px;">
        <span style="color: #666;">欢迎，{{ userStore.username }}</span>
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
            猫咪相册
          </h2>
          
          <div class="album-container" v-if="allPhotos.length > 0">
            <div 
              class="photo-item" 
              v-for="(photo, index) in shuffledPhotos" 
              :key="index"
              @click="viewPhoto(photo)"
            >
              <img :src="photo.url" :alt="photo.catName" />
              <div class="photo-overlay">
                <span class="cat-name">{{ photo.catName }}</span>
              </div>
            </div>
          </div>
          
          <el-empty v-else description="暂无猫咪照片" />
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

    <!-- 照片预览对话框 -->
    <el-dialog v-model="showPhotoDialog" width="80%" :title="selectedPhoto?.catName">
      <img v-if="selectedPhoto" :src="selectedPhoto.url" style="width: 100%;" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { StarFilled, Plus, TrendCharts, SwitchButton, PictureFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { catApi, weightApi } from '../api'
import { useUserStore } from '../stores/user'

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
const selectedPhoto = ref<{ url: string; catName: string } | null>(null)

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

// 收集所有猫咪照片
const allPhotos = computed(() => {
  const photos: { url: string; catName: string; catId: number }[] = []
  cats.value.forEach(cat => {
    if (cat.avatar) {
      photos.push({
        url: cat.avatar,
        catName: cat.name,
        catId: cat.id
      })
    }
    if (cat.photos && Array.isArray(cat.photos)) {
      cat.photos.forEach((photo: string) => {
        photos.push({
          url: photo,
          catName: cat.name,
          catId: cat.id
        })
      })
    }
  })
  return photos
})

// 随机打乱照片
const shuffledPhotos = computed(() => {
  const photos = [...allPhotos.value]
  for (let i = photos.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[photos[i], photos[j]] = [photos[j], photos[i]]
  }
  return photos
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

// 查看照片
function viewPhoto(photo: { url: string; catName: string }) {
  selectedPhoto.value = photo
  showPhotoDialog.value = true
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
})
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.dashboard-header h1 {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 24px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.dashboard-content {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.main-tabs {
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 20px 0;
  font-size: 20px;
  color: #333;
}

.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.cat-card {
  background: linear-gradient(145deg, #f8f9ff, #ffffff);
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.cat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.2);
  border-color: #667eea;
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
  background: linear-gradient(135deg, #667eea, #764ba2);
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
  color: #333;
}

.cat-info p {
  margin: 4px 0 0;
  font-size: 14px;
  color: #666;
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
  color: #999;
}

.cat-details span:last-child {
  color: #333;
  font-weight: 500;
}

.vaccination-complete {
  color: #67c23a !important;
}

.vaccination-progress {
  color: #e6a23c !important;
}

.vaccination-none {
  color: #f56c6c !important;
}

.add-cat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  background: #fafafa;
  border: 1px dashed #dcdfe6;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #909399;
}

.add-cat-card:hover {
  border-color: #c0c4cc;
  color: #606266;
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
  background: #f8f9ff;
  border-radius: 12px;
}

/* 相册样式 */
.album-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.photo-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.photo-item:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
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
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
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
}
</style>