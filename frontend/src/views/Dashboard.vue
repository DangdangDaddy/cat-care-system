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
              <p>{{ cat.breed }}</p>
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
    </main>

    <!-- 添加猫咪对话框 -->
    <el-dialog v-model="showAddDialog" title="添加猫咪" width="500px">
      <el-form :model="catForm" :rules="catRules" ref="catFormRef" label-width="80px">
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
          <el-select v-model="catForm.breed" placeholder="请选择品种" style="width: 100%">
            <el-option label="英短蓝猫" value="英短蓝猫" />
            <el-option label="美短" value="美短" />
            <el-option label="橘猫" value="橘猫" />
            <el-option label="布偶猫" value="布偶猫" />
            <el-option label="暹罗猫" value="暹罗猫" />
            <el-option label="田园猫" value="田园猫" />
            <el-option label="其他" value="其他" />
          </el-select>
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
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="addingCat" @click="handleAddCat">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { StarFilled, Plus, TrendCharts, SwitchButton } from '@element-plus/icons-vue'
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

const catForm = reactive({
  name: '',
  gender: 'male',
  breed: '',
  birth_date: '',
  neutered: false
})

const catRules = {
  name: [{ required: true, message: '请输入猫咪名字', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  breed: [{ required: true, message: '请选择品种', trigger: 'change' }],
  birth_date: [{ required: true, message: '请选择生日', trigger: 'change' }]
}

async function loadCats() {
  try {
    // 直接从 localStorage 读取 userId，避免 userStore 初始化问题
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
    
    if (!chartRef.value) return
    
    // 销毁之前的实例（如果存在）
    const existingChart = echarts.getInstanceByDom(chartRef.value)
    if (existingChart) {
      existingChart.dispose()
    }
    
    const chart = echarts.init(chartRef.value)
    
    // 过滤掉没有数据的猫咪
    const validData = res.filter((item: any) => item.data && item.data.length > 0)
    
    // 如果没有数据，显示提示
    if (validData.length === 0) {
      chart.setOption({
        title: {
          text: '暂无体重数据',
          left: 'center',
          top: 'center',
          textStyle: {
            color: '#999',
            fontSize: 16
          }
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
        axisLabel: {
          formatter: '{MM}-{dd}'
        }
      },
      yAxis: {
        type: 'value',
        name: '体重 (克)',
        axisLabel: {
          formatter: '{value}g'
        }
      },
      series
    })
    
    const resizeHandler = () => chart.resize()
    window.addEventListener('resize', resizeHandler)
    
    // 保存 resize handler 以便卸载时移除
    ;(chart as any)._resizeHandler = resizeHandler
  } catch (error) {
    console.error('加载图表失败', error)
  }
}

async function handleAddCat() {
  await catFormRef.value.validate()
  addingCat.value = true
  
  try {
    const userId = Number(localStorage.getItem('userId'))
    if (!userId) {
      ElMessage.error('请重新登录')
      return
    }
    await catApi.createCat(userId, catForm)
    ElMessage.success('添加成功！')
    showAddDialog.value = false
    catFormRef.value.resetFields()
    await loadCats()
    await loadChart()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  } finally {
    addingCat.value = false
  }
}

function goToCatDetail(catId: number) {
  router.push(`/cat/${catId}`)
}

function handleLogout() {
  userStore.logout()
  window.location.href = '/login'
}

onMounted(() => {
  loadCats()
  loadChart()
})

onUnmounted(() => {
  // 清理 ECharts 实例
  if (chartRef.value) {
    const chart = echarts.getInstanceByDom(chartRef.value)
    if (chart) {
      if ((chart as any)._resizeHandler) {
        window.removeEventListener('resize', (chart as any)._resizeHandler)
      }
      chart.dispose()
    }
  }
})
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.dashboard-header {
  background: rgba(255, 255, 255, 0.95);
  padding: 20px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.dashboard-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
  display: flex;
  align-items: center;
  gap: 10px;
}

.dashboard-content {
  padding: 30px 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-title {
  color: white;
  font-size: 20px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.cat-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.cat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.cat-card-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;
}

.cat-avatar {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
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
  margin: 5px 0 0;
  color: #666;
  font-size: 14px;
}

.cat-details {
  border-top: 1px solid #eee;
  padding-top: 15px;
}

.cat-details p {
  margin: 8px 0;
  font-size: 14px;
  color: #666;
}

.cat-details span:first-child {
  color: #999;
}

.add-cat-card {
  background: rgba(255, 255, 255, 0.9);
  border: 2px dashed rgba(255, 255, 255, 0.5);
  border-radius: 16px;
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 200px;
}

.add-cat-card:hover {
  background: white;
  border-color: #667eea;
}

.add-cat-card .icon {
  font-size: 40px;
  color: #667eea;
  margin-bottom: 10px;
}

.add-cat-card span {
  color: #666;
  font-size: 16px;
}

.chart-section {
  background: white;
  border-radius: 16px;
  padding: 25px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.chart-section .section-title {
  color: #333;
  margin-bottom: 20px;
}

.chart-container {
  width: 100%;
  height: 350px;
  min-height: 350px;
}
</style>
