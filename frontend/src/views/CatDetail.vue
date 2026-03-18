<template>
  <div class="cat-detail-container">
    <header class="cat-detail-header">
      <span class="back-btn" @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </span>
      <h1>{{ cat?.name || '猫咪详情' }}</h1>
    </header>

    <main class="cat-detail-content" v-if="cat">
      <div class="cat-profile">
        <div class="cat-profile-header">
          <div class="cat-profile-avatar">
            <img v-if="cat.avatar" :src="cat.avatar" :alt="cat.name" />
            <span v-else>{{ cat.gender === 'female' ? '🐱' : '😺' }}</span>
          </div>
          <h2>{{ cat.name }}</h2>
          <p>{{ cat.breed }}</p>
        </div>
        
        <div class="cat-profile-info">
          <p>
            <span class="label">性别</span>
            <span class="value">{{ cat.gender === 'female' ? '母猫' : '公猫' }}</span>
          </p>
          <p>
            <span class="label">生日</span>
            <span class="value">{{ cat.birth_date }}</span>
          </p>
          <p>
            <span class="label">年龄</span>
            <span class="value">{{ age }}</span>
          </p>
          <p>
            <span class="label">绝育状态</span>
            <span class="value">{{ cat.neutered ? '已绝育' : '未绝育' }}</span>
          </p>
          <p>
            <span class="label">最新体重</span>
            <span class="value">{{ latestWeight ? `${latestWeight}g` : '暂无记录' }}</span>
          </p>
        </div>

        <div style="margin-top: 24px; display: flex; gap: 12px;">
          <el-button type="primary" @click="showEditDialog = true">
            <el-icon><Edit /></el-icon>
            编辑信息
          </el-button>
          <el-button type="danger" @click="handleDelete">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
      </div>

      <div class="weight-section">
        <div class="weight-header">
          <h3>体重记录</h3>
          <el-button type="primary" @click="showWeightDialog = true">
            <el-icon><Plus /></el-icon>
            添加记录
          </el-button>
        </div>
        
        <div class="weight-chart" ref="chartRef"></div>
        
        <el-table :data="weights" style="width: 100%" max-height="300">
          <el-table-column prop="date" label="日期" />
          <el-table-column prop="weight" label="体重 (克)">
            <template #default="{ row }">
              {{ row.weight }}g
            </template>
          </el-table-column>
        </el-table>
      </div>
    </main>

    <!-- 编辑猫咪对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑猫咪信息" width="500px">
      <el-form :model="editForm" :rules="catRules" ref="editFormRef" label-width="80px">
        <el-form-item label="名字" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入猫咪名字" />
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
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingEdit" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 添加体重记录对话框 -->
    <el-dialog v-model="showWeightDialog" title="添加体重记录" width="400px">
      <el-form :model="weightForm" :rules="weightRules" ref="weightFormRef" label-width="80px">
        <el-form-item label="日期" prop="date">
          <el-date-picker 
            v-model="weightForm.date" 
            type="date" 
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="体重" prop="weight">
          <el-input-number 
            v-model="weightForm.weight" 
            :min="0" 
            :max="20000" 
            :step="50"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showWeightDialog = false">取消</el-button>
        <el-button type="primary" :loading="addingWeight" @click="handleAddWeight">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Delete, Plus } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { catApi, weightApi } from '../api'

const route = useRoute()
const router = useRouter()

const catId = computed(() => Number(route.params.id))
const cat = ref<any>(null)
const weights = ref<any[]>([])
const chartRef = ref<HTMLElement>()

const showEditDialog = ref(false)
const showWeightDialog = ref(false)
const editFormRef = ref()
const weightFormRef = ref()
const savingEdit = ref(false)
const addingWeight = ref(false)

const editForm = reactive({
  name: '',
  gender: 'male',
  breed: '',
  birth_date: '',
  neutered: false
})

const weightForm = reactive({
  date: new Date().toISOString().split('T')[0],
  weight: 3000
})

const catRules = {
  name: [{ required: true, message: '请输入猫咪名字', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  breed: [{ required: true, message: '请选择品种', trigger: 'change' }],
  birth_date: [{ required: true, message: '请选择生日', trigger: 'change' }]
}

const weightRules = {
  date: [{ required: true, message: '请选择日期', trigger: 'change' }],
  weight: [{ required: true, message: '请输入体重', trigger: 'blur' }]
}

const age = computed(() => {
  if (!cat.value?.birth_date) return '未知'
  const birth = new Date(cat.value.birth_date)
  const now = new Date()
  const months = (now.getFullYear() - birth.getFullYear()) * 12 + (now.getMonth() - birth.getMonth())
  if (months < 1) return '小于1个月'
  if (months < 12) return `${months}个月`
  const years = Math.floor(months / 12)
  const remainMonths = months % 12
  return remainMonths > 0 ? `${years}岁${remainMonths}个月` : `${years}岁`
})

const latestWeight = computed(() => {
  if (weights.value.length === 0) return null
  return weights.value[weights.value.length - 1]?.weight
})

async function loadCat() {
  try {
    const res = await catApi.getCat(catId.value)
    cat.value = res
    if (cat.value) {
      editForm.name = cat.value.name
      editForm.gender = cat.value.gender
      editForm.breed = cat.value.breed
      editForm.birth_date = cat.value.birth_date
      editForm.neutered = cat.value.neutered
    }
  } catch (error) {
    ElMessage.error('加载猫咪信息失败')
  }
}

async function loadWeights() {
  try {
    const res = await weightApi.getWeights(catId.value)
    weights.value = res
    renderChart()
  } catch (error) {
    ElMessage.error('加载体重记录失败')
  }
}

function renderChart() {
  if (!chartRef.value || weights.value.length === 0) return
  
  const chart = echarts.init(chartRef.value)
  
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        return `${params[0].axisValue}<br/>体重: ${params[0].value}g`
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
      data: weights.value.map(w => w.date),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '体重 (克)',
      axisLabel: {
        formatter: '{value}g'
      }
    },
    series: [{
      name: '体重',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { width: 3, color: '#667eea' },
      itemStyle: { color: '#667eea' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(102, 126, 234, 0.3)' },
          { offset: 1, color: 'rgba(102, 126, 234, 0.05)' }
        ])
      },
      data: weights.value.map(w => w.weight)
    }]
  })
  
  window.addEventListener('resize', () => chart.resize())
}

async function handleSaveEdit() {
  await editFormRef.value.validate()
  savingEdit.value = true
  
  try {
    await catApi.updateCat(catId.value, editForm)
    ElMessage.success('保存成功！')
    showEditDialog.value = false
    await loadCat()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    savingEdit.value = false
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定要删除这只猫咪吗？删除后无法恢复。', '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await catApi.deleteCat(catId.value)
    ElMessage.success('删除成功！')
    router.push('/dashboard')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

async function handleAddWeight() {
  await weightFormRef.value.validate()
  addingWeight.value = true
  
  try {
    await weightApi.addWeight(catId.value, weightForm)
    ElMessage.success('添加成功！')
    showWeightDialog.value = false
    weightForm.date = new Date().toISOString().split('T')[0]
    await loadWeights()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  } finally {
    addingWeight.value = false
  }
}

onMounted(() => {
  loadCat()
  loadWeights()
})

watch(catId, () => {
  loadCat()
  loadWeights()
})
</script>

<style scoped>
.cat-profile-avatar {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  margin: 0 auto 16px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.cat-profile-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cat-profile-avatar span {
  filter: grayscale(0);
}
</style>
