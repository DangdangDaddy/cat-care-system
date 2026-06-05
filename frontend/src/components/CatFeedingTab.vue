<template>
  <div class="feeding-tab">
    <div class="feeding-summary-grid">
      <el-card class="feeding-summary-card" shadow="hover">
        <div class="summary-label">当前主粮</div>
        <div class="summary-value">
          {{ overview?.active_plan?.product_name || '未设置' }}
        </div>
        <div class="summary-subtext">
          {{ overview?.active_plan?.food_type || '可新增当前喂养方案' }}
        </div>
      </el-card>

      <el-card class="feeding-summary-card" shadow="hover">
        <div class="summary-label">换粮状态</div>
        <div class="summary-value">
          {{ getTransitionStatusLabel(overview?.active_transition_plan?.status) }}
        </div>
        <div class="summary-subtext">
          {{ getActiveTransitionStepText(overview?.active_transition_plan) }}
        </div>
      </el-card>

      <el-card class="feeding-summary-card" shadow="hover">
        <div class="summary-label">今日摄入概览</div>
        <div class="summary-value">
          {{ overview?.daily_summary?.main_food_count || 0 }} 次主粮
        </div>
        <div class="summary-subtext">
          罐头 {{ overview?.daily_summary?.canned_food_count || 0 }} / 零食 {{ overview?.daily_summary?.treat_count || 0 }} / 补剂 {{ overview?.daily_summary?.supplement_count || 0 }}
        </div>
      </el-card>

      <el-card class="feeding-summary-card" shadow="hover">
        <div class="summary-label">最近异常</div>
        <div class="summary-value">
          {{ latestReactionLabel }}
        </div>
        <div class="summary-subtext">
          最近体重 {{ latestWeight ? `${latestWeight}g` : '暂无记录' }}
        </div>
      </el-card>
    </div>

    <el-card class="feeding-section-card feeding-pane-card" shadow="never">
      <el-tabs v-model="activeSubTab" class="feeding-subtabs">
        <el-tab-pane label="喂养方案" name="plans">
          <div class="section-header">
            <div>
              <h3>当前喂养方案</h3>
              <p>记录这只猫理论上应该怎么吃。</p>
            </div>
            <el-button type="primary" @click="openPlanDialog()">
              新增方案
            </el-button>
          </div>

          <div v-if="plans.length > 0" class="stack-list">
            <div
              v-for="plan in plans"
              :key="plan.id"
              class="stack-item"
              :class="{ 'is-active': plan.is_active }"
            >
              <div class="stack-item-main">
                <div class="stack-item-title-row">
                  <strong>{{ plan.name }}</strong>
                  <el-tag size="small" :type="plan.is_active ? 'success' : 'info'">
                    {{ plan.is_active ? '当前生效' : '历史方案' }}
                  </el-tag>
                </div>
                <div class="stack-item-meta">
                  {{ plan.brand || '未填品牌' }} / {{ plan.product_name }} / {{ plan.food_type }}
                </div>
                <div class="stack-item-meta">
                  {{ plan.start_date }}<span v-if="plan.end_date"> 至 {{ plan.end_date }}</span>
                  <span v-if="plan.daily_amount"> · {{ plan.daily_amount }}{{ plan.amount_unit || '' }}</span>
                  <span v-if="plan.feeding_frequency"> · {{ plan.feeding_frequency }}</span>
                </div>
                <div v-if="plan.notes" class="stack-item-notes">
                  {{ plan.notes }}
                </div>
              </div>
              <div class="stack-item-actions">
                <el-button size="small" type="primary" class="action-button" @click="openPlanDialog(plan)">编辑</el-button>
                <el-button size="small" type="danger" class="action-button action-button--danger" @click="removePlan(plan.id)">删除</el-button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无喂养方案" />
        </el-tab-pane>

        <el-tab-pane label="每日喂食记录" name="records">
          <div class="section-header">
            <div>
              <h3>每日喂食记录</h3>
              <p>记录每天实际吃了什么，以及吃后的反应。</p>
            </div>
            <div class="section-header-actions">
              <el-select v-model="recordFilterType" clearable placeholder="筛选类型" style="width: 150px">
                <el-option label="主粮" value="main_food" />
                <el-option label="罐头" value="canned_food" />
                <el-option label="零食" value="treat" />
                <el-option label="补剂" value="supplement" />
                <el-option label="羊奶粉/营养液" value="nutrition" />
              </el-select>
              <el-button type="primary" @click="openRecordDialog()">
                添加记录
              </el-button>
            </div>
          </div>

          <el-table v-if="filteredRecords.length > 0" :data="filteredRecords" style="width: 100%">
            <el-table-column prop="recorded_at" label="时间" min-width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.recorded_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="record_type" label="类型" width="110">
              <template #default="{ row }">
                <el-tag size="small">{{ getRecordTypeLabel(row.record_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="item_name" label="名称" min-width="180" />
            <el-table-column label="摄入" min-width="140">
              <template #default="{ row }">
                {{ formatAmount(row.amount, row.amount_unit) }}
              </template>
            </el-table-column>
            <el-table-column prop="consumed_status" label="食用情况" width="120">
              <template #default="{ row }">
                {{ getConsumedStatusLabel(row.consumed_status) }}
              </template>
            </el-table-column>
            <el-table-column prop="reaction" label="异常反馈" width="120">
              <template #default="{ row }">
                <span :class="{ 'reaction-danger': row.reaction && row.reaction !== 'none' }">
                  {{ getReactionLabel(row.reaction) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="156" fixed="right">
              <template #default="{ row }">
                <div class="table-action-group">
                  <el-button size="small" type="primary" class="action-button" @click="openRecordDialog(row)">编辑</el-button>
                  <el-button size="small" type="danger" class="action-button action-button--danger" @click="removeRecord(row.id)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无喂食记录" />
        </el-tab-pane>

        <el-tab-pane label="换粮计划" name="transitions">
          <div class="section-header">
            <div>
              <h3>换粮计划</h3>
              <p>支持 7 日/10 日/更慢的渐进换粮节奏。</p>
            </div>
            <el-button type="primary" @click="openTransitionDialog()">
              新增换粮
            </el-button>
          </div>

          <div v-if="transitions.length > 0" class="stack-list">
            <div v-for="transition in transitions" :key="transition.id" class="stack-item">
              <div class="stack-item-main">
                <div class="stack-item-title-row">
                  <strong>{{ transition.name }}</strong>
                  <el-tag size="small" :type="getTransitionTagType(transition.status)">
                    {{ getTransitionStatusLabel(transition.status) }}
                  </el-tag>
                </div>
                <div class="stack-item-meta">
                  {{ transition.old_food_name }} → {{ transition.new_food_name }}
                </div>
                <div class="stack-item-meta">
                  {{ transition.start_date }} · {{ transition.planned_days }} 天
                  <span v-if="transition.reason"> · {{ transition.reason }}</span>
                </div>
                <div class="transition-steps">
                  <el-tag
                    v-for="step in transition.steps"
                    :key="step.id"
                    size="small"
                    effect="plain"
                  >
                    D{{ step.day_index }} {{ step.old_food_ratio }}/{{ step.new_food_ratio }}
                  </el-tag>
                </div>
                <div v-if="transition.stop_reason || transition.observation_notes" class="stack-item-notes">
                  {{ transition.stop_reason || transition.observation_notes }}
                </div>
              </div>
              <div class="stack-item-actions">
                <el-button size="small" type="primary" class="action-button" @click="openTransitionDialog(transition)">编辑</el-button>
                <el-button size="small" type="danger" class="action-button action-button--danger" @click="removeTransition(transition.id)">删除</el-button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无换粮计划" />
        </el-tab-pane>

        <el-tab-pane label="补剂疗程" name="supplements">
          <div class="section-header">
            <div>
              <h3>补剂与保健品疗程</h3>
              <p>把补血肝精、赖氨酸、化毛片等长期记录下来。</p>
            </div>
            <el-button type="primary" @click="openSupplementDialog()">
              新增疗程
            </el-button>
          </div>

          <div v-if="supplements.length > 0" class="stack-list">
            <div v-for="course in supplements" :key="course.id" class="stack-item">
              <div class="stack-item-main">
                <div class="stack-item-title-row">
                  <strong>{{ course.product_name }}</strong>
                  <el-tag size="small" :type="course.is_active ? 'success' : 'info'">
                    {{ course.is_active ? '进行中' : '已结束' }}
                  </el-tag>
                </div>
                <div class="stack-item-meta">
                  {{ course.category || '未分类' }}<span v-if="course.purpose"> · {{ course.purpose }}</span>
                </div>
                <div class="stack-item-meta">
                  {{ course.start_date }}<span v-if="course.end_date"> 至 {{ course.end_date }}</span>
                  <span v-if="course.frequency"> · {{ course.frequency }}</span>
                  <span v-if="course.dosage"> · {{ course.dosage }}{{ course.dosage_unit || '' }}</span>
                </div>
                <div v-if="course.risk_notes || course.response" class="stack-item-notes">
                  {{ course.response || course.risk_notes }}
                </div>
              </div>
              <div class="stack-item-actions">
                <el-button size="small" type="primary" class="action-button" @click="openSupplementDialog(course)">编辑</el-button>
                <el-button size="small" type="danger" class="action-button action-button--danger" @click="removeSupplement(course.id)">删除</el-button>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无补剂疗程" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="showPlanDialog" :title="editingPlanId ? '编辑喂养方案' : '新增喂养方案'" width="560px" class="feeding-dialog">
      <div class="dialog-form-scroll">
      <el-form :model="planForm" label-width="110px">
        <el-form-item label="方案名称"><el-input v-model="planForm.name" placeholder="请输入方案名称" /></el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="planForm.start_date" type="date" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="主粮类型">
          <el-select v-model="planForm.food_type" style="width: 100%">
            <el-option label="干粮" value="dry_food" />
            <el-option label="湿粮" value="wet_food" />
            <el-option label="混喂" value="mixed" />
            <el-option label="冻干" value="freeze_dried" />
            <el-option label="处方粮" value="prescription" />
          </el-select>
        </el-form-item>
        <el-form-item label="品牌"><el-input v-model="planForm.brand" placeholder="请输入品牌" /></el-form-item>
        <el-form-item label="产品名"><el-input v-model="planForm.product_name" placeholder="请输入产品名" /></el-form-item>
        <el-form-item label="生命阶段">
          <el-select v-model="planForm.life_stage" style="width: 100%">
            <el-option label="幼猫" value="kitten" />
            <el-option label="成猫" value="adult" />
            <el-option label="老年" value="senior" />
            <el-option label="全阶段" value="all_life_stages" />
            <el-option label="处方" value="prescription" />
          </el-select>
        </el-form-item>
        <el-form-item label="完整均衡">
          <el-select v-model="planForm.complete_balance_status" style="width: 100%">
            <el-option label="是" value="yes" />
            <el-option label="否" value="no" />
            <el-option label="待确认" value="pending" />
          </el-select>
        </el-form-item>
        <el-form-item label="每日计划量">
          <div class="inline-form-row">
            <el-input-number v-model="planForm.daily_amount" :min="0" style="width: 100%" />
            <el-select v-model="planForm.amount_unit" style="width: 120px">
              <el-option label="g" value="g" />
              <el-option label="罐" value="can" />
              <el-option label="袋" value="bag" />
              <el-option label="ml" value="ml" />
            </el-select>
          </div>
        </el-form-item>
        <el-form-item label="喂食频次"><el-input v-model="planForm.feeding_frequency" placeholder="例如：每日 2 次" /></el-form-item>
        <el-form-item label="饮水辅助"><el-input v-model="planForm.hydration_strategy" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="planForm.notes" type="textarea" :rows="3" /></el-form-item>
        <el-form-item v-if="syncTargetCats.length > 0" label="同步到其他猫咪">
          <div class="health-sync-block">
            <el-checkbox-group v-model="planForm.syncCatIds" class="health-sync-options">
              <el-checkbox
                v-for="userCat in syncTargetCats"
                :key="userCat.id"
                :value="userCat.id"
              >
                {{ userCat.name }}
              </el-checkbox>
            </el-checkbox-group>
            <div class="health-sync-tip">
              当前猫咪会自动包含在内，这里只需要补选其他猫咪。取消勾选后，保存时会解除对应猫咪的同步。
            </div>
          </div>
        </el-form-item>
        <el-form-item v-if="editingPlanId && hasRealPlanSyncGroup" label="同步修改">
          <div class="health-sync-block health-sync-switch-row">
            <el-switch v-model="planForm.syncUpdateGroup" />
            <span class="health-sync-tip">打开后，会把同组猫咪里的喂养方案一起更新。</span>
          </div>
        </el-form-item>
        <el-form-item label="设为当前"><el-switch v-model="planForm.is_active" /></el-form-item>
      </el-form>
      </div>
      <template #footer>
        <el-button @click="showPlanDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingPlan" @click="submitPlan">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showRecordDialog" :title="editingRecordId ? '编辑喂食记录' : '添加喂食记录'" width="560px" class="feeding-dialog">
      <div class="dialog-form-scroll">
      <el-form :model="recordForm" label-width="110px">
        <el-form-item label="记录时间">
          <el-date-picker
            v-model="recordForm.recorded_at"
            type="datetime"
            style="width: 100%"
            value-format="YYYY-MM-DDTHH:mm:ss"
          />
        </el-form-item>
        <el-form-item label="记录类型">
          <el-select v-model="recordForm.record_type" style="width: 100%">
            <el-option label="主粮" value="main_food" />
            <el-option label="罐头" value="canned_food" />
            <el-option label="零食" value="treat" />
            <el-option label="补剂" value="supplement" />
            <el-option label="羊奶粉/营养液" value="nutrition" />
            <el-option label="喂药伴食" value="medication_food" />
          </el-select>
        </el-form-item>
        <el-form-item label="品牌"><el-input v-model="recordForm.brand" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="recordForm.item_name" /></el-form-item>
        <el-form-item label="口味/规格"><el-input v-model="recordForm.flavor" /></el-form-item>
        <el-form-item label="摄入量">
          <div class="inline-form-row">
            <el-input-number v-model="recordForm.amount" :min="0" style="width: 100%" />
            <el-select v-model="recordForm.amount_unit" style="width: 120px">
              <el-option label="g" value="g" />
              <el-option label="颗" value="piece" />
              <el-option label="条" value="strip" />
              <el-option label="勺" value="scoop" />
              <el-option label="ml" value="ml" />
              <el-option label="罐" value="can" />
            </el-select>
          </div>
        </el-form-item>
        <el-form-item label="食用情况">
          <el-select v-model="recordForm.consumed_status" style="width: 100%">
            <el-option label="吃完" value="finished" />
            <el-option label="吃了一半" value="half" />
            <el-option label="只闻不吃" value="sniff_only" />
            <el-option label="拒食" value="refused" />
          </el-select>
        </el-form-item>
        <el-form-item label="异常反馈">
          <el-select v-model="recordForm.reaction" style="width: 100%">
            <el-option label="无" value="none" />
            <el-option label="软便" value="soft_stool" />
            <el-option label="呕吐" value="vomiting" />
            <el-option label="胀气" value="bloating" />
            <el-option label="食欲下降" value="low_appetite" />
            <el-option label="拒食" value="refused" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联方案">
          <el-select v-model="recordForm.plan_id" clearable style="width: 100%">
            <el-option v-for="plan in plans" :key="plan.id" :label="plan.name" :value="plan.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联换粮">
          <el-select v-model="recordForm.transition_plan_id" clearable style="width: 100%">
            <el-option v-for="transition in transitions" :key="transition.id" :label="transition.name" :value="transition.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="recordForm.notes" type="textarea" :rows="3" /></el-form-item>
        <el-form-item v-if="syncTargetCats.length > 0" label="同步到其他猫咪">
          <div class="health-sync-block">
            <el-checkbox-group v-model="recordForm.syncCatIds" class="health-sync-options">
              <el-checkbox
                v-for="userCat in syncTargetCats"
                :key="userCat.id"
                :value="userCat.id"
              >
                {{ userCat.name }}
              </el-checkbox>
            </el-checkbox-group>
            <div class="health-sync-tip">
              当前猫咪会自动包含在内，这里只需要补选其他猫咪。取消勾选后，保存时会解除对应猫咪的同步。
            </div>
          </div>
        </el-form-item>
        <el-form-item v-if="editingRecordId && hasRealRecordSyncGroup" label="同步修改">
          <div class="health-sync-block health-sync-switch-row">
            <el-switch v-model="recordForm.syncUpdateGroup" />
            <span class="health-sync-tip">打开后，会把同组猫咪里的喂食记录一起更新。</span>
          </div>
        </el-form-item>
      </el-form>
      </div>
      <template #footer>
        <el-button @click="showRecordDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingRecord" @click="submitRecord">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showTransitionDialog" :title="editingTransitionId ? '编辑换粮计划' : '新增换粮计划'" width="620px" class="feeding-dialog">
      <div class="dialog-form-scroll">
      <el-form :model="transitionForm" label-width="110px">
        <el-form-item label="计划名称"><el-input v-model="transitionForm.name" /></el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="transitionForm.start_date" type="date" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="计划天数">
          <el-input-number v-model="transitionForm.planned_days" :min="3" :max="30" style="width: 100%" />
        </el-form-item>
        <el-form-item label="旧粮"><el-input v-model="transitionForm.old_food_name" /></el-form-item>
        <el-form-item label="新粮"><el-input v-model="transitionForm.new_food_name" /></el-form-item>
        <el-form-item label="原因"><el-input v-model="transitionForm.reason" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="transitionForm.status" style="width: 100%">
            <el-option label="未开始" value="planned" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已中止" value="stopped" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划步骤">
          <div class="transition-step-editor">
            <div v-for="(step, index) in transitionForm.steps" :key="index" class="transition-step-row">
              <span>D{{ step.day_index }}</span>
              <el-input-number v-model="step.old_food_ratio" :min="0" :max="100" />
              <span>/</span>
              <el-input-number v-model="step.new_food_ratio" :min="0" :max="100" />
            </div>
            <el-button text type="primary" @click="resetTransitionSteps">重置默认步骤</el-button>
          </div>
        </el-form-item>
        <el-form-item label="观察备注"><el-input v-model="transitionForm.observation_notes" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="中止原因"><el-input v-model="transitionForm.stop_reason" type="textarea" :rows="2" /></el-form-item>
        <el-form-item v-if="syncTargetCats.length > 0" label="同步到其他猫咪">
          <div class="health-sync-block">
            <el-checkbox-group v-model="transitionForm.syncCatIds" class="health-sync-options">
              <el-checkbox
                v-for="userCat in syncTargetCats"
                :key="userCat.id"
                :value="userCat.id"
              >
                {{ userCat.name }}
              </el-checkbox>
            </el-checkbox-group>
            <div class="health-sync-tip">
              当前猫咪会自动包含在内，这里只需要补选其他猫咪。取消勾选后，保存时会解除对应猫咪的同步。
            </div>
          </div>
        </el-form-item>
        <el-form-item v-if="editingTransitionId && hasRealTransitionSyncGroup" label="同步修改">
          <div class="health-sync-block health-sync-switch-row">
            <el-switch v-model="transitionForm.syncUpdateGroup" />
            <span class="health-sync-tip">打开后，会把同组猫咪里的换粮计划一起更新。</span>
          </div>
        </el-form-item>
      </el-form>
      </div>
      <template #footer>
        <el-button @click="showTransitionDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingTransition" @click="submitTransition">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showSupplementDialog" :title="editingSupplementId ? '编辑补剂疗程' : '新增补剂疗程'" width="560px" class="feeding-dialog">
      <div class="dialog-form-scroll">
      <el-form :model="supplementForm" label-width="110px">
        <el-form-item label="产品名称"><el-input v-model="supplementForm.product_name" /></el-form-item>
        <el-form-item label="类别"><el-input v-model="supplementForm.category" /></el-form-item>
        <el-form-item label="用途"><el-input v-model="supplementForm.purpose" /></el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="supplementForm.start_date" type="date" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="supplementForm.end_date" type="date" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="频次"><el-input v-model="supplementForm.frequency" /></el-form-item>
        <el-form-item label="单次剂量">
          <div class="inline-form-row">
            <el-input-number v-model="supplementForm.dosage" :min="0" style="width: 100%" />
            <el-select v-model="supplementForm.dosage_unit" style="width: 120px">
              <el-option label="ml" value="ml" />
              <el-option label="勺" value="scoop" />
              <el-option label="粒" value="pill" />
              <el-option label="条" value="strip" />
              <el-option label="包" value="pack" />
            </el-select>
          </div>
        </el-form-item>
        <el-form-item label="喂食方式"><el-input v-model="supplementForm.feeding_method" /></el-form-item>
        <el-form-item label="来源"><el-input v-model="supplementForm.source" placeholder="如医生建议/自主补充" /></el-form-item>
        <el-form-item label="反应记录"><el-input v-model="supplementForm.response" /></el-form-item>
        <el-form-item label="风险备注"><el-input v-model="supplementForm.risk_notes" type="textarea" :rows="3" /></el-form-item>
        <el-form-item v-if="syncTargetCats.length > 0" label="同步到其他猫咪">
          <div class="health-sync-block">
            <el-checkbox-group v-model="supplementForm.syncCatIds" class="health-sync-options">
              <el-checkbox
                v-for="userCat in syncTargetCats"
                :key="userCat.id"
                :value="userCat.id"
              >
                {{ userCat.name }}
              </el-checkbox>
            </el-checkbox-group>
            <div class="health-sync-tip">
              当前猫咪会自动包含在内，这里只需要补选其他猫咪。取消勾选后，保存时会解除对应猫咪的同步。
            </div>
          </div>
        </el-form-item>
        <el-form-item v-if="editingSupplementId && hasRealSupplementSyncGroup" label="同步修改">
          <div class="health-sync-block health-sync-switch-row">
            <el-switch v-model="supplementForm.syncUpdateGroup" />
            <span class="health-sync-tip">打开后，会把同组猫咪里的补剂疗程一起更新。</span>
          </div>
        </el-form-item>
        <el-form-item label="进行中"><el-switch v-model="supplementForm.is_active" /></el-form-item>
      </el-form>
      </div>
      <template #footer>
        <el-button @click="showSupplementDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingSupplement" @click="submitSupplement">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { catApi, feedingApi } from '../api'

const props = defineProps<{
  catId: number
  latestWeight?: number | null
}>()

const overview = ref<any | null>(null)
const plans = ref<any[]>([])
const records = ref<any[]>([])
const transitions = ref<any[]>([])
const supplements = ref<any[]>([])
const userCats = ref<any[]>([])
const activeSubTab = ref('plans')
const recordFilterType = ref('')

const showPlanDialog = ref(false)
const showRecordDialog = ref(false)
const showTransitionDialog = ref(false)
const showSupplementDialog = ref(false)

const savingPlan = ref(false)
const savingRecord = ref(false)
const savingTransition = ref(false)
const savingSupplement = ref(false)

const editingPlanId = ref<number | null>(null)
const editingRecordId = ref<number | null>(null)
const editingTransitionId = ref<number | null>(null)
const editingSupplementId = ref<number | null>(null)
const syncedGroupPlans = ref<any[]>([])
const syncedGroupRecords = ref<any[]>([])
const syncedGroupTransitions = ref<any[]>([])
const syncedGroupSupplements = ref<any[]>([])

const planForm = reactive({
  name: '',
  start_date: '',
  food_type: 'mixed',
  brand: '',
  product_name: '',
  life_stage: 'adult',
  complete_balance_status: 'pending',
  daily_amount: null as number | null,
  amount_unit: 'g',
  feeding_frequency: '',
  hydration_strategy: '',
  notes: '',
  sync_group_id: '',
  syncCatIds: [] as number[],
  syncUpdateGroup: true,
  is_active: true
})

const recordForm = reactive({
  recorded_at: '',
  record_type: 'main_food',
  brand: '',
  item_name: '',
  flavor: '',
  amount: null as number | null,
  amount_unit: 'g',
  consumed_status: 'finished',
  reaction: 'none',
  sync_group_id: '',
  syncCatIds: [] as number[],
  syncUpdateGroup: true,
  plan_id: null as number | null,
  transition_plan_id: null as number | null,
  notes: ''
})

const transitionForm = reactive({
  name: '',
  start_date: '',
  planned_days: 7,
  old_food_name: '',
  new_food_name: '',
  reason: '',
  status: 'planned',
  observation_notes: '',
  stop_reason: '',
  sync_group_id: '',
  syncCatIds: [] as number[],
  syncUpdateGroup: true,
  steps: [] as Array<{ day_index: number; old_food_ratio: number; new_food_ratio: number }>
})

const supplementForm = reactive({
  product_name: '',
  category: '',
  purpose: '',
  start_date: '',
  end_date: '',
  frequency: '',
  dosage: null as number | null,
  dosage_unit: 'ml',
  feeding_method: '',
  source: '',
  response: '',
  risk_notes: '',
  sync_group_id: '',
  syncCatIds: [] as number[],
  syncUpdateGroup: true,
  is_active: true
})

const filteredRecords = computed(() => {
  if (!recordFilterType.value) {
    return records.value
  }
  return records.value.filter((record) => record.record_type === recordFilterType.value)
})

const latestReactionLabel = computed(() => {
  const reaction = overview.value?.recent_reactions?.[0]?.reaction
  return getReactionLabel(reaction)
})

const syncTargetCats = computed(() => {
  return userCats.value.filter((userCat) => Number(userCat.id) !== Number(props.catId))
})

const hasRealPlanSyncGroup = computed(() => Boolean(planForm.sync_group_id) && syncedGroupPlans.value.length > 1)
const hasRealRecordSyncGroup = computed(() => Boolean(recordForm.sync_group_id) && syncedGroupRecords.value.length > 1)
const hasRealTransitionSyncGroup = computed(() => Boolean(transitionForm.sync_group_id) && syncedGroupTransitions.value.length > 1)
const hasRealSupplementSyncGroup = computed(() => Boolean(supplementForm.sync_group_id) && syncedGroupSupplements.value.length > 1)

watch(
  () => props.catId,
  async () => {
    await loadAll()
  }
)

watch(
  () => transitionForm.planned_days,
  (value) => {
    if (!editingTransitionId.value) {
      transitionForm.steps = buildDefaultSteps(value)
    }
  }
)

onMounted(async () => {
  await loadAll()
})

async function loadUserCats() {
  try {
    const userId = Number(localStorage.getItem('userId'))
    if (!userId) return
    const res = await catApi.getCats(userId)
    userCats.value = res || []
  } catch (error) {
    ElMessage.error('加载猫咪列表失败')
  }
}

async function loadAll() {
  if (!props.catId) return
  try {
    const [overviewRes, planRes, recordRes, transitionRes, supplementRes] = await Promise.all([
      feedingApi.getOverview(props.catId),
      feedingApi.getPlans(props.catId),
      feedingApi.getRecords(props.catId),
      feedingApi.getTransitions(props.catId),
      feedingApi.getSupplements(props.catId)
    ])
    await loadUserCats()
    overview.value = overviewRes
    plans.value = planRes || []
    records.value = recordRes || []
    transitions.value = transitionRes || []
    supplements.value = supplementRes || []
  } catch (error) {
    ElMessage.error('加载饮食记录失败')
  }
}

function generateSyncGroupId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `feeding-sync-${Date.now()}`
}

function buildDefaultSteps(days: number) {
  if (days <= 7) {
    return [
      { day_index: 1, old_food_ratio: 75, new_food_ratio: 25 },
      { day_index: 3, old_food_ratio: 50, new_food_ratio: 50 },
      { day_index: 5, old_food_ratio: 25, new_food_ratio: 75 },
      { day_index: days, old_food_ratio: 0, new_food_ratio: 100 }
    ]
  }
  if (days <= 10) {
    return [
      { day_index: 1, old_food_ratio: 80, new_food_ratio: 20 },
      { day_index: 3, old_food_ratio: 60, new_food_ratio: 40 },
      { day_index: 6, old_food_ratio: 40, new_food_ratio: 60 },
      { day_index: 8, old_food_ratio: 20, new_food_ratio: 80 },
      { day_index: days, old_food_ratio: 0, new_food_ratio: 100 }
    ]
  }
  return [
    { day_index: 1, old_food_ratio: 90, new_food_ratio: 10 },
    { day_index: 4, old_food_ratio: 75, new_food_ratio: 25 },
    { day_index: 7, old_food_ratio: 60, new_food_ratio: 40 },
    { day_index: 10, old_food_ratio: 40, new_food_ratio: 60 },
    { day_index: 13, old_food_ratio: 20, new_food_ratio: 80 },
    { day_index: days, old_food_ratio: 0, new_food_ratio: 100 }
  ].filter((step) => step.day_index <= days)
}

function getRecordTypeLabel(type: string) {
  const labels: Record<string, string> = {
    main_food: '主粮',
    canned_food: '罐头',
    treat: '零食',
    supplement: '补剂',
    nutrition: '营养液',
    medication_food: '喂药伴食'
  }
  return labels[type] || '其他'
}

function getConsumedStatusLabel(status: string) {
  const labels: Record<string, string> = {
    finished: '吃完',
    half: '吃了一半',
    sniff_only: '只闻不吃',
    refused: '拒食'
  }
  return labels[status] || '未记录'
}

function getReactionLabel(reaction?: string) {
  const labels: Record<string, string> = {
    none: '无异常',
    soft_stool: '软便',
    vomiting: '呕吐',
    bloating: '胀气',
    low_appetite: '食欲下降',
    refused: '拒食'
  }
  return labels[reaction || 'none'] || reaction || '无异常'
}

function getTransitionStatusLabel(status?: string) {
  const labels: Record<string, string> = {
    planned: '未开始',
    in_progress: '进行中',
    completed: '已完成',
    stopped: '已中止'
  }
  return labels[status || 'planned'] || '未开始'
}

function getTransitionTagType(status?: string) {
  if (status === 'completed') return 'success'
  if (status === 'stopped') return 'danger'
  if (status === 'in_progress') return 'warning'
  return 'info'
}

function getActiveTransitionStepText(transition?: any) {
  if (!transition) return '当前没有进行中的换粮计划'
  return `${transition.old_food_name} → ${transition.new_food_name}`
}

function formatAmount(amount?: number, unit?: string) {
  if (amount === null || amount === undefined) return '未填写'
  return `${amount}${unit || ''}`
}

function formatDateTime(value: string) {
  if (!value) return ''
  return value.replace('T', ' ').slice(0, 16)
}

async function openPlanDialog(plan?: any) {
  syncedGroupPlans.value = []
  if (plan) {
    editingPlanId.value = plan.id
    Object.assign(planForm, {
      name: plan.name,
      start_date: plan.start_date,
      food_type: plan.food_type,
      brand: plan.brand || '',
      product_name: plan.product_name,
      life_stage: plan.life_stage || 'adult',
      complete_balance_status: plan.complete_balance_status || 'pending',
      daily_amount: plan.daily_amount,
      amount_unit: plan.amount_unit || 'g',
      feeding_frequency: plan.feeding_frequency || '',
      hydration_strategy: plan.hydration_strategy || '',
      notes: plan.notes || '',
      sync_group_id: plan.sync_group_id || '',
      syncCatIds: [],
      syncUpdateGroup: Boolean(plan.sync_group_id && (plan.sync_group_size || 0) > 1),
      is_active: Boolean(plan.is_active)
    })
    if (plan.sync_group_id) {
      const groupPlans = await feedingApi.getGroupPlans(plan.sync_group_id)
      syncedGroupPlans.value = groupPlans || []
      planForm.syncCatIds = syncedGroupPlans.value
        .filter((groupPlan: any) => Number(groupPlan.cat_id) !== Number(props.catId))
        .map((groupPlan: any) => Number(groupPlan.cat_id))
      if (syncedGroupPlans.value.length <= 1) {
        planForm.syncUpdateGroup = false
      }
    }
  } else {
    editingPlanId.value = null
    Object.assign(planForm, {
      name: '',
      start_date: new Date().toISOString().slice(0, 10),
      food_type: 'mixed',
      brand: '',
      product_name: '',
      life_stage: 'adult',
      complete_balance_status: 'pending',
      daily_amount: null,
      amount_unit: 'g',
      feeding_frequency: '',
      hydration_strategy: '',
      notes: '',
      sync_group_id: '',
      syncCatIds: [],
      syncUpdateGroup: true,
      is_active: true
    })
  }
  showPlanDialog.value = true
}

async function submitPlan() {
  if (!planForm.name.trim() || !planForm.start_date || !planForm.product_name.trim()) {
    ElMessage.error('请完整填写方案名称、开始日期和产品名')
    return
  }

  try {
    savingPlan.value = true
    const currentCatId = Number(props.catId)
    const desiredOtherCatIds = Array.from(new Set(planForm.syncCatIds.map(Number).filter(Boolean)))
    const desiredCatIds = Array.from(new Set([currentCatId, ...desiredOtherCatIds]))
    const shouldSyncMultipleCats = desiredCatIds.length > 1
    const syncGroupId = shouldSyncMultipleCats ? (planForm.sync_group_id || generateSyncGroupId()) : ''
    const payload = {
      name: planForm.name.trim(),
      start_date: planForm.start_date,
      food_type: planForm.food_type,
      brand: planForm.brand.trim() || null,
      product_name: planForm.product_name.trim(),
      life_stage: planForm.life_stage,
      complete_balance_status: planForm.complete_balance_status,
      daily_amount: planForm.daily_amount,
      amount_unit: planForm.amount_unit,
      feeding_frequency: planForm.feeding_frequency.trim() || null,
      hydration_strategy: planForm.hydration_strategy.trim() || null,
      notes: planForm.notes.trim() || null,
      sync_group_id: shouldSyncMultipleCats ? syncGroupId : null,
      is_active: planForm.is_active
    }

    if (editingPlanId.value) {
      const existingGroupPlans = syncedGroupPlans.value.filter((groupPlan: any) => groupPlan.id !== editingPlanId.value)
      const existingCatIdSet = new Set(existingGroupPlans.map((groupPlan: any) => Number(groupPlan.cat_id)))
      const desiredOtherCatIdSet = new Set(desiredOtherCatIds)
      await feedingApi.updatePlan(editingPlanId.value, payload)

      const updatePromises: Promise<any>[] = []
      for (const groupPlan of existingGroupPlans) {
        const groupCatId = Number(groupPlan.cat_id)
        if (!desiredOtherCatIdSet.has(groupCatId)) {
          updatePromises.push(feedingApi.updatePlan(groupPlan.id, { sync_group_id: null }))
          continue
        }
        if (planForm.syncUpdateGroup && shouldSyncMultipleCats) {
          updatePromises.push(feedingApi.updatePlan(groupPlan.id, payload))
        } else if (groupPlan.sync_group_id !== syncGroupId) {
          updatePromises.push(feedingApi.updatePlan(groupPlan.id, { sync_group_id: syncGroupId || null }))
        }
      }

      const newCatIds = desiredOtherCatIds.filter((targetCatId) => !existingCatIdSet.has(targetCatId))
      for (const targetCatId of newCatIds) {
        updatePromises.push(feedingApi.createPlan(targetCatId, payload))
      }

      if (updatePromises.length > 0) {
        await Promise.all(updatePromises)
      }
      ElMessage.success('喂养方案已更新')
    } else {
      if (desiredCatIds.length > 1) {
        await feedingApi.createBatchPlans(currentCatId, desiredCatIds, payload)
      } else {
        await feedingApi.createPlan(currentCatId, payload)
      }
      ElMessage.success('喂养方案已添加')
    }

    showPlanDialog.value = false
    await loadAll()
  } catch (error) {
    ElMessage.error(editingPlanId.value ? '更新喂养方案失败' : '添加喂养方案失败')
  } finally {
    savingPlan.value = false
  }
}

async function removePlan(planId: number) {
  try {
    await ElMessageBox.confirm('确定删除这条喂养方案吗？', '提示', { type: 'warning' })
    await feedingApi.deletePlan(planId)
    ElMessage.success('删除成功')
    await loadAll()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除喂养方案失败')
    }
  }
}

async function openRecordDialog(record?: any) {
  syncedGroupRecords.value = []
  if (record) {
    editingRecordId.value = record.id
    Object.assign(recordForm, {
      recorded_at: normalizeDateTime(record.recorded_at),
      record_type: record.record_type,
      brand: record.brand || '',
      item_name: record.item_name,
      flavor: record.flavor || '',
      amount: record.amount,
      amount_unit: record.amount_unit || 'g',
      consumed_status: record.consumed_status || 'finished',
      reaction: record.reaction || 'none',
      sync_group_id: record.sync_group_id || '',
      syncCatIds: [],
      syncUpdateGroup: Boolean(record.sync_group_id && (record.sync_group_size || 0) > 1),
      plan_id: record.plan_id || null,
      transition_plan_id: record.transition_plan_id || null,
      notes: record.notes || ''
    })
    if (record.sync_group_id) {
      const groupRecords = await feedingApi.getGroupRecords(record.sync_group_id)
      syncedGroupRecords.value = groupRecords || []
      recordForm.syncCatIds = syncedGroupRecords.value
        .filter((groupRecord: any) => Number(groupRecord.cat_id) !== Number(props.catId))
        .map((groupRecord: any) => Number(groupRecord.cat_id))
      if (syncedGroupRecords.value.length <= 1) {
        recordForm.syncUpdateGroup = false
      }
    }
  } else {
    editingRecordId.value = null
    Object.assign(recordForm, {
      recorded_at: normalizeDateTime(new Date().toISOString()),
      record_type: 'main_food',
      brand: '',
      item_name: '',
      flavor: '',
      amount: null,
      amount_unit: 'g',
      consumed_status: 'finished',
      reaction: 'none',
      sync_group_id: '',
      syncCatIds: [],
      syncUpdateGroup: true,
      plan_id: null,
      transition_plan_id: null,
      notes: ''
    })
  }
  showRecordDialog.value = true
}

function normalizeDateTime(value: string) {
  if (!value) return ''
  return value.slice(0, 19)
}

async function submitRecord() {
  if (!recordForm.recorded_at || !recordForm.item_name.trim()) {
    ElMessage.error('请填写记录时间和名称')
    return
  }
  try {
    savingRecord.value = true
    const currentCatId = Number(props.catId)
    const desiredOtherCatIds = Array.from(new Set(recordForm.syncCatIds.map(Number).filter(Boolean)))
    const desiredCatIds = Array.from(new Set([currentCatId, ...desiredOtherCatIds]))
    const shouldSyncMultipleCats = desiredCatIds.length > 1
    const syncGroupId = shouldSyncMultipleCats ? (recordForm.sync_group_id || generateSyncGroupId()) : ''
    const payload = {
      recorded_at: recordForm.recorded_at,
      record_type: recordForm.record_type,
      brand: recordForm.brand.trim() || null,
      item_name: recordForm.item_name.trim(),
      flavor: recordForm.flavor.trim() || null,
      amount: recordForm.amount,
      amount_unit: recordForm.amount_unit,
      consumed_status: recordForm.consumed_status,
      reaction: recordForm.reaction,
      sync_group_id: shouldSyncMultipleCats ? syncGroupId : null,
      plan_id: recordForm.plan_id,
      transition_plan_id: recordForm.transition_plan_id,
      notes: recordForm.notes.trim() || null
    }
    if (editingRecordId.value) {
      const existingGroupRecords = syncedGroupRecords.value.filter((groupRecord: any) => groupRecord.id !== editingRecordId.value)
      const existingCatIdSet = new Set(existingGroupRecords.map((groupRecord: any) => Number(groupRecord.cat_id)))
      const desiredOtherCatIdSet = new Set(desiredOtherCatIds)
      await feedingApi.updateRecord(editingRecordId.value, payload)

      const updatePromises: Promise<any>[] = []
      for (const groupRecord of existingGroupRecords) {
        const groupCatId = Number(groupRecord.cat_id)
        if (!desiredOtherCatIdSet.has(groupCatId)) {
          updatePromises.push(feedingApi.updateRecord(groupRecord.id, { sync_group_id: null }))
          continue
        }
        if (recordForm.syncUpdateGroup && shouldSyncMultipleCats) {
          updatePromises.push(feedingApi.updateRecord(groupRecord.id, payload))
        } else if (groupRecord.sync_group_id !== syncGroupId) {
          updatePromises.push(feedingApi.updateRecord(groupRecord.id, { sync_group_id: syncGroupId || null }))
        }
      }

      const newCatIds = desiredOtherCatIds.filter((targetCatId) => !existingCatIdSet.has(targetCatId))
      for (const targetCatId of newCatIds) {
        updatePromises.push(feedingApi.createRecord(targetCatId, payload))
      }
      if (updatePromises.length > 0) {
        await Promise.all(updatePromises)
      }
      ElMessage.success('喂食记录已更新')
    } else {
      if (desiredCatIds.length > 1) {
        await feedingApi.createBatchRecords(currentCatId, desiredCatIds, payload)
      } else {
        await feedingApi.createRecord(currentCatId, payload)
      }
      ElMessage.success('喂食记录已添加')
    }
    showRecordDialog.value = false
    await loadAll()
  } catch (error) {
    ElMessage.error(editingRecordId.value ? '更新喂食记录失败' : '添加喂食记录失败')
  } finally {
    savingRecord.value = false
  }
}

async function removeRecord(recordId: number) {
  try {
    await ElMessageBox.confirm('确定删除这条喂食记录吗？', '提示', { type: 'warning' })
    await feedingApi.deleteRecord(recordId)
    ElMessage.success('删除成功')
    await loadAll()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除喂食记录失败')
    }
  }
}

async function openTransitionDialog(transition?: any) {
  syncedGroupTransitions.value = []
  if (transition) {
    editingTransitionId.value = transition.id
    Object.assign(transitionForm, {
      name: transition.name,
      start_date: transition.start_date,
      planned_days: transition.planned_days,
      old_food_name: transition.old_food_name,
      new_food_name: transition.new_food_name,
      reason: transition.reason || '',
      status: transition.status || 'planned',
      observation_notes: transition.observation_notes || '',
      stop_reason: transition.stop_reason || '',
      sync_group_id: transition.sync_group_id || '',
      syncCatIds: [],
      syncUpdateGroup: Boolean(transition.sync_group_id && (transition.sync_group_size || 0) > 1),
      steps: (transition.steps || []).map((step: any) => ({
        day_index: step.day_index,
        old_food_ratio: step.old_food_ratio,
        new_food_ratio: step.new_food_ratio
      }))
    })
    if (transition.sync_group_id) {
      const groupTransitions = await feedingApi.getGroupTransitions(transition.sync_group_id)
      syncedGroupTransitions.value = groupTransitions || []
      transitionForm.syncCatIds = syncedGroupTransitions.value
        .filter((groupTransition: any) => Number(groupTransition.cat_id) !== Number(props.catId))
        .map((groupTransition: any) => Number(groupTransition.cat_id))
      if (syncedGroupTransitions.value.length <= 1) {
        transitionForm.syncUpdateGroup = false
      }
    }
  } else {
    editingTransitionId.value = null
    Object.assign(transitionForm, {
      name: '',
      start_date: new Date().toISOString().slice(0, 10),
      planned_days: 7,
      old_food_name: '',
      new_food_name: '',
      reason: '',
      status: 'planned',
      observation_notes: '',
      stop_reason: '',
      sync_group_id: '',
      syncCatIds: [],
      syncUpdateGroup: true,
      steps: buildDefaultSteps(7)
    })
  }
  showTransitionDialog.value = true
}

function resetTransitionSteps() {
  transitionForm.steps = buildDefaultSteps(transitionForm.planned_days)
}

async function submitTransition() {
  if (!transitionForm.name.trim() || !transitionForm.old_food_name.trim() || !transitionForm.new_food_name.trim()) {
    ElMessage.error('请填写计划名称、旧粮和新粮')
    return
  }
  try {
    savingTransition.value = true
    const currentCatId = Number(props.catId)
    const desiredOtherCatIds = Array.from(new Set(transitionForm.syncCatIds.map(Number).filter(Boolean)))
    const desiredCatIds = Array.from(new Set([currentCatId, ...desiredOtherCatIds]))
    const shouldSyncMultipleCats = desiredCatIds.length > 1
    const syncGroupId = shouldSyncMultipleCats ? (transitionForm.sync_group_id || generateSyncGroupId()) : ''
    const payload = {
      name: transitionForm.name.trim(),
      start_date: transitionForm.start_date,
      planned_days: transitionForm.planned_days,
      old_food_name: transitionForm.old_food_name.trim(),
      new_food_name: transitionForm.new_food_name.trim(),
      reason: transitionForm.reason.trim() || null,
      status: transitionForm.status,
      end_date: null,
      stop_reason: transitionForm.stop_reason.trim() || null,
      observation_notes: transitionForm.observation_notes.trim() || null,
      sync_group_id: shouldSyncMultipleCats ? syncGroupId : null,
      steps: transitionForm.steps
    }
    if (editingTransitionId.value) {
      const existingGroupTransitions = syncedGroupTransitions.value.filter((groupTransition: any) => groupTransition.id !== editingTransitionId.value)
      const existingCatIdSet = new Set(existingGroupTransitions.map((groupTransition: any) => Number(groupTransition.cat_id)))
      const desiredOtherCatIdSet = new Set(desiredOtherCatIds)
      await feedingApi.updateTransition(editingTransitionId.value, payload)

      const updatePromises: Promise<any>[] = []
      for (const groupTransition of existingGroupTransitions) {
        const groupCatId = Number(groupTransition.cat_id)
        if (!desiredOtherCatIdSet.has(groupCatId)) {
          updatePromises.push(feedingApi.updateTransition(groupTransition.id, { sync_group_id: null }))
          continue
        }
        if (transitionForm.syncUpdateGroup && shouldSyncMultipleCats) {
          updatePromises.push(feedingApi.updateTransition(groupTransition.id, payload))
        } else if (groupTransition.sync_group_id !== syncGroupId) {
          updatePromises.push(feedingApi.updateTransition(groupTransition.id, { sync_group_id: syncGroupId || null }))
        }
      }

      const newCatIds = desiredOtherCatIds.filter((targetCatId) => !existingCatIdSet.has(targetCatId))
      for (const targetCatId of newCatIds) {
        updatePromises.push(feedingApi.createTransition(targetCatId, payload))
      }
      if (updatePromises.length > 0) {
        await Promise.all(updatePromises)
      }
      ElMessage.success('换粮计划已更新')
    } else {
      if (desiredCatIds.length > 1) {
        await feedingApi.createBatchTransitions(currentCatId, desiredCatIds, payload)
      } else {
        await feedingApi.createTransition(currentCatId, payload)
      }
      ElMessage.success('换粮计划已添加')
    }
    showTransitionDialog.value = false
    await loadAll()
  } catch (error) {
    ElMessage.error(editingTransitionId.value ? '更新换粮计划失败' : '添加换粮计划失败')
  } finally {
    savingTransition.value = false
  }
}

async function removeTransition(transitionId: number) {
  try {
    await ElMessageBox.confirm('确定删除这条换粮计划吗？', '提示', { type: 'warning' })
    await feedingApi.deleteTransition(transitionId)
    ElMessage.success('删除成功')
    await loadAll()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除换粮计划失败')
    }
  }
}

async function openSupplementDialog(course?: any) {
  syncedGroupSupplements.value = []
  if (course) {
    editingSupplementId.value = course.id
    Object.assign(supplementForm, {
      product_name: course.product_name,
      category: course.category || '',
      purpose: course.purpose || '',
      start_date: course.start_date,
      end_date: course.end_date || '',
      frequency: course.frequency || '',
      dosage: course.dosage,
      dosage_unit: course.dosage_unit || 'ml',
      feeding_method: course.feeding_method || '',
      source: course.source || '',
      response: course.response || '',
      risk_notes: course.risk_notes || '',
      sync_group_id: course.sync_group_id || '',
      syncCatIds: [],
      syncUpdateGroup: Boolean(course.sync_group_id && (course.sync_group_size || 0) > 1),
      is_active: Boolean(course.is_active)
    })
    if (course.sync_group_id) {
      const groupSupplements = await feedingApi.getGroupSupplements(course.sync_group_id)
      syncedGroupSupplements.value = groupSupplements || []
      supplementForm.syncCatIds = syncedGroupSupplements.value
        .filter((groupCourse: any) => Number(groupCourse.cat_id) !== Number(props.catId))
        .map((groupCourse: any) => Number(groupCourse.cat_id))
      if (syncedGroupSupplements.value.length <= 1) {
        supplementForm.syncUpdateGroup = false
      }
    }
  } else {
    editingSupplementId.value = null
    Object.assign(supplementForm, {
      product_name: '',
      category: '',
      purpose: '',
      start_date: new Date().toISOString().slice(0, 10),
      end_date: '',
      frequency: '',
      dosage: null,
      dosage_unit: 'ml',
      feeding_method: '',
      source: '',
      response: '',
      risk_notes: '',
      sync_group_id: '',
      syncCatIds: [],
      syncUpdateGroup: true,
      is_active: true
    })
  }
  showSupplementDialog.value = true
}

async function submitSupplement() {
  if (!supplementForm.product_name.trim() || !supplementForm.start_date) {
    ElMessage.error('请填写产品名称和开始日期')
    return
  }
  try {
    savingSupplement.value = true
    const currentCatId = Number(props.catId)
    const desiredOtherCatIds = Array.from(new Set(supplementForm.syncCatIds.map(Number).filter(Boolean)))
    const desiredCatIds = Array.from(new Set([currentCatId, ...desiredOtherCatIds]))
    const shouldSyncMultipleCats = desiredCatIds.length > 1
    const syncGroupId = shouldSyncMultipleCats ? (supplementForm.sync_group_id || generateSyncGroupId()) : ''
    const payload = {
      product_name: supplementForm.product_name.trim(),
      category: supplementForm.category.trim() || null,
      purpose: supplementForm.purpose.trim() || null,
      start_date: supplementForm.start_date,
      end_date: supplementForm.end_date || null,
      frequency: supplementForm.frequency.trim() || null,
      dosage: supplementForm.dosage,
      dosage_unit: supplementForm.dosage_unit,
      feeding_method: supplementForm.feeding_method.trim() || null,
      source: supplementForm.source.trim() || null,
      response: supplementForm.response.trim() || null,
      risk_notes: supplementForm.risk_notes.trim() || null,
      sync_group_id: shouldSyncMultipleCats ? syncGroupId : null,
      is_active: supplementForm.is_active
    }
    if (editingSupplementId.value) {
      const existingGroupSupplements = syncedGroupSupplements.value.filter((groupCourse: any) => groupCourse.id !== editingSupplementId.value)
      const existingCatIdSet = new Set(existingGroupSupplements.map((groupCourse: any) => Number(groupCourse.cat_id)))
      const desiredOtherCatIdSet = new Set(desiredOtherCatIds)
      await feedingApi.updateSupplement(editingSupplementId.value, payload)

      const updatePromises: Promise<any>[] = []
      for (const groupCourse of existingGroupSupplements) {
        const groupCatId = Number(groupCourse.cat_id)
        if (!desiredOtherCatIdSet.has(groupCatId)) {
          updatePromises.push(feedingApi.updateSupplement(groupCourse.id, { sync_group_id: null }))
          continue
        }
        if (supplementForm.syncUpdateGroup && shouldSyncMultipleCats) {
          updatePromises.push(feedingApi.updateSupplement(groupCourse.id, payload))
        } else if (groupCourse.sync_group_id !== syncGroupId) {
          updatePromises.push(feedingApi.updateSupplement(groupCourse.id, { sync_group_id: syncGroupId || null }))
        }
      }

      const newCatIds = desiredOtherCatIds.filter((targetCatId) => !existingCatIdSet.has(targetCatId))
      for (const targetCatId of newCatIds) {
        updatePromises.push(feedingApi.createSupplement(targetCatId, payload))
      }
      if (updatePromises.length > 0) {
        await Promise.all(updatePromises)
      }
      ElMessage.success('补剂疗程已更新')
    } else {
      if (desiredCatIds.length > 1) {
        await feedingApi.createBatchSupplements(currentCatId, desiredCatIds, payload)
      } else {
        await feedingApi.createSupplement(currentCatId, payload)
      }
      ElMessage.success('补剂疗程已添加')
    }
    showSupplementDialog.value = false
    await loadAll()
  } catch (error) {
    ElMessage.error(editingSupplementId.value ? '更新补剂疗程失败' : '添加补剂疗程失败')
  } finally {
    savingSupplement.value = false
  }
}

async function removeSupplement(courseId: number) {
  try {
    await ElMessageBox.confirm('确定删除这条补剂疗程吗？', '提示', { type: 'warning' })
    await feedingApi.deleteSupplement(courseId)
    ElMessage.success('删除成功')
    await loadAll()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除补剂疗程失败')
    }
  }
}
</script>

<style scoped>
.feeding-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.feeding-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.feeding-summary-card {
  border-radius: 18px;
}

.summary-label {
  color: #7a6f67;
  font-size: 13px;
}

.summary-value {
  margin-top: 8px;
  color: #2f2724;
  font-size: 22px;
  font-weight: 700;
}

.summary-subtext {
  margin-top: 8px;
  color: #8a7f78;
  font-size: 13px;
  line-height: 1.5;
}

.feeding-layout {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.feeding-section-card {
  border-radius: 20px;
}

.feeding-pane-card {
  padding-top: 4px;
}

.feeding-subtabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.feeding-subtabs :deep(.el-tabs__nav-wrap::after) {
  background: rgba(214, 192, 174, 0.55);
}

.feeding-subtabs :deep(.el-tabs__item) {
  height: 40px;
  padding: 0 18px;
  color: #7f746c;
  font-weight: 600;
}

.feeding-subtabs :deep(.el-tabs__item.is-active) {
  color: #9e6437;
}

.feeding-subtabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(90deg, #ce9368, #b36a3c);
  border-radius: 999px;
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.section-header h3 {
  margin: 0;
  color: #2f2724;
  font-size: 20px;
}

.section-header p {
  margin: 6px 0 0;
  color: #8a7f78;
  font-size: 13px;
}

.section-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stack-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stack-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  border: 1px solid #ebe5df;
  border-radius: 16px;
  background: #fffdfa;
}

.stack-item.is-active {
  border-color: #d6b79b;
  box-shadow: 0 8px 18px rgba(184, 142, 101, 0.12);
}

.stack-item-main {
  min-width: 0;
  flex: 1;
}

.stack-item-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stack-item-meta {
  margin-top: 6px;
  color: #6b625c;
  font-size: 13px;
  line-height: 1.5;
}

.stack-item-notes {
  margin-top: 8px;
  color: #4d433e;
  font-size: 13px;
  line-height: 1.6;
}

.stack-item-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.table-action-group {
  display: flex;
  gap: 8px;
}

.action-button {
  --el-button-text-color: #ffffff;
  --el-button-hover-text-color: #ffffff;
  --el-button-active-text-color: #ffffff;
  font-weight: 600;
}

.action-button--danger {
  --el-button-bg-color: #d55f5f;
  --el-button-border-color: #d55f5f;
  --el-button-hover-bg-color: #bf4f4f;
  --el-button-hover-border-color: #bf4f4f;
  --el-button-active-bg-color: #a94343;
  --el-button-active-border-color: #a94343;
}

.transition-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.reaction-danger {
  color: #d03050;
  font-weight: 600;
}

.inline-form-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 120px;
  gap: 12px;
  width: 100%;
}

.transition-step-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.transition-step-row {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr) 24px minmax(0, 1fr);
  gap: 8px;
  align-items: center;
}

.health-sync-block {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #eadfd6;
  border-radius: 14px;
  background: #fffaf6;
}

.health-sync-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
}

.health-sync-tip {
  margin-top: 10px;
  color: #85776e;
  font-size: 12px;
  line-height: 1.5;
}

.health-sync-switch-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dialog-form-scroll {
  max-height: min(68vh, 620px);
  overflow-y: auto;
  padding-right: 6px;
}

.feeding-dialog :deep(.el-dialog) {
  margin-top: 6vh;
}

.feeding-dialog :deep(.el-dialog__body) {
  padding-top: 8px;
  padding-bottom: 8px;
}

@media (max-width: 1024px) {
  .feeding-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .feeding-summary-grid {
    grid-template-columns: 1fr;
  }

  .section-header,
  .stack-item {
    flex-direction: column;
  }

  .feeding-subtabs :deep(.el-tabs__nav) {
    flex-wrap: wrap;
  }

  .section-header-actions,
  .stack-item-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .inline-form-row {
    grid-template-columns: 1fr;
  }
}
</style>
