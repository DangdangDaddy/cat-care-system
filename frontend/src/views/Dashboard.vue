<template>
  <div class="dashboard">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>🐱 猫咪成长健康管理系统</h1>
          <div class="user-info">
            <span>欢迎，{{ userStore.username }}</span>
            <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
          </div>
        </div>
      </el-header>
      <el-main>
        <!-- 猫咪列表 -->
        <el-row :gutter="20">
          <el-col :span="8" v-for="cat in cats" :key="cat.id">
            <el-card class="cat-card" @click="$router.push(`/cats/${cat.id}`)" shadow="hover">
              <div class="cat-avatar">🐱</div>
              <h3>{{ cat.name }}</h3>
              <p>{{ cat.breed }}</p>
              <p>{{ cat.gender === 'male' ? '公' : '母' }} · {{ cat.neutered ? '已绝育' : '未绝育' }}</p>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="cat-card add-card" @click="showAddDialog = true" shadow="hover">
              <div class="add-icon">+</div>
              <p>添加猫咪</p>
            </el-card>
          </el-col>
        </el-row>

        <!-- 体重曲线图 -->
        <el-card class="chart-card" v-if="chartData.length > 0">
          <template #header>
            <h3>📊 体重曲线</h3>
          </template>
          <div ref="chartRef" style="height: 400px"></div>
        </el-card>
      </el-main>
    </el-container>

    <!-- 添加猫咪对话框 -->
    <el-dialog v-model="showAddDialog" title="添加猫咪" width="500px">
      <el-form :model="newCat" label-width="80px">
        <el-form-item label="名字">
          <el-input v-model="newCat.name" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="newCat.gender">
            <el-radio value="male">公</el-radio>
            <el-radio value="female">母</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="品种">
          <el-input v-model="newCat.breed" />
        </el-form-item>
        <el-form-item label="出生日期">
          <el-date-picker v-model="newCat.birth_date" type="date" />
        </el-form-item>
        <el-form-item label="绝育状态">
          <el-switch v-model="newCat.neutered" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddCat">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { useUserStore } from '../stores/user'
import { getCats, createCat } from '../api/cats'
import { getChartData } from '../api/weights'

const router = useRouter()
const userStore = useUserStore()
const cats = ref<any[]>([])
const chartData = ref<any[]>([])
const chartRef = ref()
const showAddDialog = ref(false)
const newCat = reactive({
  name: '',
  gender: 'male',
  breed: '',
  birth_date: '',
  neutered: false
})

const loadData = async () => {
  try {
    cats.value = await getCats(userStore.userId)
    chartData.value = await getChartData(userStore.userId)
    if (chartData.value.length > 0) {
      await nextTick()
      renderChart()
    }
  } catch (e) {
    ElMessage.error('加载数据失败')
  }
}

const renderChart = () => {
  const chart = echarts.init(chartRef.value)
  const series = chartData.value.map(cat => ({
    name: cat.cat_name,
    type: 'line',
    smooth: true,
    data: cat.data.map((d: any) => [d.date, d.weight])
  }))
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: chartData.value.map(c => c.cat_name) },
    xAxis: { type: 'time', name: '日期' },
    yAxis: { type: 'value', name: '体重(g)' },
    series
  })
}

const handleAddCat = async () => {
  if (!newCat.name || !newCat.breed || !newCat.birth_date) {
    ElMessage.warning('请填写完整信息')
    return
  }
  try {
    await createCat(userStore.userId, {
      ...newCat,
      birth_date: new Date(newCat.birth_date).toISOString().split('T')[0]
    })
    ElMessage.success('添加成功')
    showAddDialog.value = false
    loadData()
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

onMounted(loadData)
</script>

<style scoped>
.dashboard { min-height: 100vh; background: #f5f5f5; }
.el-header { background: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.header-content { display: flex; justify-content: space-between; align-items: center; }
.header-content h1 { font-size: 20px; margin: 0; }
.user-info { display: flex; align-items: center; gap: 10px; }
.cat-card { cursor: pointer; text-align: center; margin-bottom: 20px; }
.cat-avatar { font-size: 60px; }
.cat-card h3 { margin: 10px 0 5px; }
.cat-card p { margin: 5px 0; color: #666; }
.add-card { display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 200px; }
.add-icon { font-size: 40px; color: #999; }
.chart-card { margin-top: 20px; }
</style>
