<template>
  <div class="cat-detail-container">
    <div class="detail-layout" v-if="cat">
      <aside v-if="userCats.length > 0" class="cat-dock-panel">
        <div class="cat-dock-panel__top">
          <el-button class="cat-dock-back" @click="goBack" text>
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
        </div>
        <div ref="catDockWrapRef" class="cat-dock-wrap">
          <div
            class="cat-dock"
            @mousemove="handleCatDockMouseMove"
            @mouseleave="handleCatDockMouseLeave"
          >
            <button
              v-for="dockCat in userCats"
              :key="dockCat.id"
              type="button"
              class="cat-dock__item"
              :class="{
                'is-active': dockCat.id === currentCatId,
                'is-hovered': dockHoverCatId === dockCat.id
              }"
              :ref="(el) => setCatDockItemRef(el, dockCat.id)"
              :style="getCatDockItemStyle(dockCat.id)"
              @click="switchCat(dockCat.id)"
              @mouseenter="dockHoverCatId = dockCat.id"
              @mouseleave="dockHoverCatId = null"
            >
              <span class="cat-dock__avatar">
                <img v-if="dockCat.avatar" :src="dockCat.avatar" :alt="dockCat.name" />
                <span v-else>{{ getCatAvatarFallback(dockCat) }}</span>
              </span>
              <span class="cat-dock__name">{{ dockCat.name }}</span>
            </button>
          </div>
        </div>
      </aside>

      <main class="detail-content">
        <!-- 页签切换 -->
        <el-tabs v-model="activeTab" class="detail-tabs">
        <!-- 基本信息页签 -->
        <el-tab-pane label="基本信息" name="info">
          <div class="info-section">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="名字">{{ cat.name }}</el-descriptions-item>
              <el-descriptions-item label="性别">
                {{ cat.gender === 'female' ? '母猫' : '公猫' }}
              </el-descriptions-item>
              <el-descriptions-item label="品种">
                {{ cat.breed || '未知品种' }}
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

            <div class="basic-info-actions">
              <el-button @click="showAvatarDialog = true">
                更换头像
              </el-button>
              <el-button type="primary" @click="showEditDialog = true">
                <el-icon><Edit /></el-icon>
                编辑基础信息
              </el-button>
              <el-button type="danger" @click="handleDeleteCat">
                <el-icon><Delete /></el-icon>
                删除猫咪
              </el-button>
            </div>

            <div class="basic-health-preview" @dblclick="goHealthTab">
              <div class="basic-health-preview-header">
                <h3>健康摘要</h3>
                <el-button class="summary-link-button" text type="primary" @click="goHealthTab">
                  查看健康记录
                </el-button>
              </div>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="疫苗状态">
                  <el-tag :type="getVaccinationType(cat.vaccination_status)">
                    {{ cat.vaccination_status || '未设置' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="最近疫苗">
                  <span v-if="latestVaccinationRecord">
                    {{ latestVaccinationRecord.date }}
                    <span class="summary-inline-text">{{ latestVaccinationRecord.disease }}</span>
                  </span>
                  <span v-else class="text-muted">暂无记录</span>
                </el-descriptions-item>
                <el-descriptions-item label="体内驱虫">
                  <div v-if="internalDewormingReminder" class="health-summary-cell">
                    <span>{{ internalDewormingSourceDate || '暂无记录' }}</span>
                    <span class="summary-inline-text" v-if="latestInternalDewormingRecord">
                      {{ latestInternalDewormingRecord.disease }}
                    </span>
                    <el-tag :type="internalDewormingReminder.type" size="small">
                      {{ internalDewormingReminder.text }}
                    </el-tag>
                  </div>
                  <span v-else class="text-muted">暂无记录</span>
                </el-descriptions-item>
                <el-descriptions-item label="体外驱虫">
                  <div v-if="externalDewormingReminder" class="health-summary-cell">
                    <span>{{ externalDewormingSourceDate || '暂无记录' }}</span>
                    <span class="summary-inline-text" v-if="latestExternalDewormingRecord">
                      {{ latestExternalDewormingRecord.disease }}
                    </span>
                    <el-tag :type="externalDewormingReminder.type" size="small">
                      {{ externalDewormingReminder.text }}
                    </el-tag>
                  </div>
                  <span v-else class="text-muted">暂无记录</span>
                </el-descriptions-item>
              </el-descriptions>
            </div>

          </div>
        </el-tab-pane>

        <el-tab-pane label="健康记录" name="health">
          <div class="health-section">
            <div class="health-info-card">
              <div class="health-info-header">
                <h3><el-icon><FirstAidKit /></el-icon> 健康记录</h3>
                <div class="health-info-actions">
                  <el-button size="small" @click="openHealthSettingsDialog">
                    <el-icon><Edit /></el-icon>
                    健康设置
                  </el-button>
                  <el-button type="primary" size="small" @click="openAddHealthRecordDialog">
                    <el-icon><Plus /></el-icon>
                    添加记录
                  </el-button>
                </div>
              </div>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="疫苗状态">
                  <el-tag :type="getVaccinationType(cat.vaccination_status)">
                    {{ cat.vaccination_status || '未设置' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="最近疫苗">
                  <span v-if="latestVaccinationRecord">
                    {{ latestVaccinationRecord.date }}
                    <span class="summary-inline-text">{{ latestVaccinationRecord.disease }}</span>
                  </span>
                  <span v-else class="text-muted">暂无记录</span>
                </el-descriptions-item>
                <el-descriptions-item label="体内驱虫">
                  <div v-if="internalDewormingReminder" class="health-summary-cell">
                    <span>{{ internalDewormingSourceDate || '暂无记录' }}</span>
                    <span class="summary-inline-text" v-if="latestInternalDewormingRecord">
                      {{ latestInternalDewormingRecord.disease }}
                    </span>
                    <el-tag :type="internalDewormingReminder.type" size="small">
                      {{ internalDewormingReminder.text }}
                    </el-tag>
                  </div>
                  <span v-else class="text-muted">暂无记录</span>
                </el-descriptions-item>
                <el-descriptions-item label="体外驱虫">
                  <div v-if="externalDewormingReminder" class="health-summary-cell">
                    <span>{{ externalDewormingSourceDate || '暂无记录' }}</span>
                    <span class="summary-inline-text" v-if="latestExternalDewormingRecord">
                      {{ latestExternalDewormingRecord.disease }}
                    </span>
                    <el-tag :type="externalDewormingReminder.type" size="small">
                      {{ externalDewormingReminder.text }}
                    </el-tag>
                  </div>
                  <span v-else class="text-muted">暂无记录</span>
                </el-descriptions-item>
                <el-descriptions-item label="健康时间线" :span="2">
                  <div v-if="healthRecords.length > 0" class="health-record-list">
                    <div
                      v-for="record in healthRecords"
                      :key="record.id"
                      class="health-record-item"
                    >
                      <div class="health-record-main">
                        <div class="health-record-title-row">
                          <el-tag size="small" :type="getHealthRecordTagType(record.record_type)">
                            {{ getHealthRecordTypeLabel(record.record_type) }}
                          </el-tag>
                          <strong>{{ record.disease }}</strong>
                          <span class="health-record-date">{{ record.date }}</span>
                        </div>
                        <div v-if="record.treatment" class="health-record-detail">
                          处理：{{ record.treatment }}
                        </div>
                        <div v-if="record.notes" class="health-record-detail">
                          备注：{{ record.notes }}
                        </div>
                      </div>
                      <div class="health-record-actions">
                        <el-tag v-if="record.sync_group_id && (record.sync_group_size || 0) > 1" size="small" type="success">
                          已同步
                        </el-tag>
                        <el-button class="inline-action-button" size="small" text type="primary" @click="editHealthRecord(record)">
                          编辑
                        </el-button>
                        <el-button class="inline-action-button inline-action-button--danger" size="small" text type="danger" @click="deleteHealthRecord(record.id)">
                          删除
                        </el-button>
                      </div>
                    </div>
                  </div>
                  <el-empty v-else description="暂无健康记录" />
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-tab-pane>

        <!-- 体重记录页签 -->
        <el-tab-pane label="饮食记录" name="feeding">
          <CatFeedingTab :cat-id="currentCatId" :latest-weight="latestWeight" />
        </el-tab-pane>

        <!-- 体重记录页签 -->
        <el-tab-pane label="体重记录" name="weight">
          <div class="weight-section">
            <div class="weight-header">
              <h3>体重记录</h3>
              <div class="weight-actions">
                <el-button type="primary" @click="openAddWeightDialog">
                  <el-icon><Plus /></el-icon>
                  添加记录
                </el-button>
                <el-button @click="handleDownloadTemplate">
                  <el-icon><Download /></el-icon>
                  下载模板
                </el-button>
                <el-upload
                  :show-file-list="false"
                  :before-upload="beforeImportUpload"
                  :http-request="handleImportWeights"
                  accept=".xlsx,.xls"
                  class="inline-upload"
                >
                  <el-button type="success">
                    <el-icon><Upload /></el-icon>
                    导入数据
                  </el-button>
                </el-upload>
                <el-button type="warning" @click="handleExportWeights">
                  <el-icon><Download /></el-icon>
                  导出数据
                </el-button>
              </div>
            </div>

            <div class="weight-chart-card" v-if="weightRecords.length > 0">
              <div class="weight-chart-toolbar">
                <div class="weight-chart-toolbar__title">
                  <h4>体重趋势</h4>
                  <span>按时间范围查看变化曲线</span>
                </div>
                <div class="weight-chart-filters">
                  <el-radio-group v-model="weightChartFilterMode" size="small">
                    <el-radio-button label="all">全部</el-radio-button>
                    <el-radio-button label="1y">近一年</el-radio-button>
                    <el-radio-button label="6m">近半年</el-radio-button>
                    <el-radio-button label="custom">筛选日期</el-radio-button>
                  </el-radio-group>
                  <el-date-picker
                    v-if="weightChartFilterMode === 'custom'"
                    v-model="weightChartDateRange"
                    type="daterange"
                    start-placeholder="开始日期"
                    end-placeholder="截止日期"
                    range-separator="至"
                    value-format="YYYY-MM-DD"
                    class="weight-chart-date-picker"
                    clearable
                  />
                </div>
              </div>
              <div class="weight-chart" ref="weightChartRef"></div>
            </div>

            <el-table :data="paginatedWeightRecords" style="width: 100%" v-if="weightRecords.length > 0">
              <el-table-column prop="record_date" label="日期" width="180" />
              <el-table-column prop="weight" label="体重(g)" width="120" />
              <el-table-column prop="note" label="备注" />
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <div style="display: flex; gap: 8px;">
                    <el-button class="inline-action-button" type="primary" size="small" text @click="editWeightRecord(row)">
                      <el-icon><Edit /></el-icon>
                      编辑
                    </el-button>
                    <el-button class="inline-action-button inline-action-button--danger" type="danger" size="small" text @click="deleteWeightRecord(row.id)">
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>

            <div class="weight-pagination" v-if="weightRecords.length > 0">
              <div class="weight-pagination__meta">
                <div class="weight-pagination__summary">
                  共 {{ weightRecords.length }} 条
                </div>
                <div class="weight-pagination__size">
                  <el-select v-model="weightPageSize" size="small" class="weight-pagination__size-select">
                    <el-option
                      v-for="size in weightPageSizeOptions"
                      :key="size"
                      :label="String(size)"
                      :value="size"
                    />
                  </el-select>
                  <span class="weight-pagination__size-label">条/页</span>
                </div>
              </div>
              <el-pagination
                v-model:current-page="weightCurrentPage"
                background
                layout="prev, pager, next"
                :total="weightRecords.length"
                :page-size="weightPageSize"
              />
            </div>

            <el-empty v-else description="暂无体重记录" />
          </div>
        </el-tab-pane>

        <!-- 相册页签 -->
        <el-tab-pane label="相册" name="album">
          <div class="album-section">
            <div class="album-header">
              <h3>猫咪相册</h3>
              <div class="album-header-actions">
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
            </div>

            <div class="photo-grid" v-if="photos.length > 0">
              <div
                class="photo-item"
                v-for="photo in sortedPhotos"
                :key="photo.id"
                :class="{ 'is-dragging': draggingPhotoId === photo.id, 'manual-sort': photoSortMode === 'manual' }"
                :draggable="photoSortMode === 'manual'"
                @dragstart="handlePhotoDragStart(photo.id)"
                @dragend="handlePhotoDragEnd"
                @dragover.prevent
                @drop.prevent="handlePhotoDrop(photo)"
              >
                <img :src="photo.thumbnail || photo.url" @click="viewPhoto(photo)" />
                <div class="photo-overlay">
                  <span class="cat-name">
                    <el-icon v-if="photo.is_pinned"><StarFilled /></el-icon>
                    {{ formatPhotoCatNames(photo) }}
                  </span>
                </div>
                <div class="photo-actions">
                  <el-button
                    size="small"
                    circle
                    @click="togglePhotoPin(photo)"
                  >
                    <el-icon><StarFilled /></el-icon>
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    circle
                    @click="deletePhoto(photo)"
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
    </div>

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
          <el-select
            v-model="editForm.breed"
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
            v-if="editForm.breed === '其他'"
            v-model="editForm.breed_custom"
            placeholder="请输入品种名称"
            style="margin-top: 8px;"
          />
        </el-form-item>

        <el-form-item label="毛色" prop="color">
          <el-select
            v-model="editForm.color"
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
            v-if="editForm.color === '其他'"
            v-model="editForm.color_custom"
            placeholder="请输入毛色名称"
            style="margin-top: 8px;"
          />
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
        <el-button type="primary" :loading="saving" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showHealthSettingsDialog"
      title="健康设置"
      width="520px"
      :close-on-press-escape="false"
      @closed="resetHealthSettingsDialog"
    >
      <el-form :model="healthSettingsForm" label-width="110px">
        <el-form-item label="疫苗状态">
          <el-select v-model="healthSettingsForm.vaccination_status" placeholder="请选择" style="width: 100%">
            <el-option label="未接种" value="未接种" />
            <el-option label="接种中" value="接种中" />
            <el-option label="已完成基础免疫" value="已完成基础免疫" />
            <el-option label="定期接种中" value="定期接种中" />
          </el-select>
        </el-form-item>
        <el-form-item label="体内驱虫频率">
          <el-select v-model="healthSettingsForm.internal_deworming_interval_days" style="width: 100%">
            <el-option label="1个月一次" :value="30" />
            <el-option label="2个月一次" :value="60" />
            <el-option label="3个月一次" :value="90" />
            <el-option label="6个月一次" :value="180" />
          </el-select>
        </el-form-item>
        <el-form-item label="体外驱虫频率">
          <el-select v-model="healthSettingsForm.external_deworming_interval_days" style="width: 100%">
            <el-option label="1个月一次" :value="30" />
            <el-option label="2个月一次" :value="60" />
            <el-option label="3个月一次" :value="90" />
            <el-option label="6个月一次" :value="180" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showHealthSettingsDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingHealthSettings" @click="handleSaveHealthSettings">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showHealthRecordDialog"
      :title="healthRecordDialogTitle"
      width="520px"
      :close-on-press-escape="false"
      @closed="resetHealthRecordDialog"
    >
      <el-form :model="healthRecordForm" label-width="88px">
        <el-form-item label="记录类型">
          <el-select v-model="healthRecordForm.record_type" style="width: 100%">
            <el-option label="疫苗" value="vaccination" />
            <el-option label="体内驱虫" value="internal_deworming" />
            <el-option label="体外驱虫" value="external_deworming" />
            <el-option label="异常症状" value="abnormal_symptom" />
            <el-option label="生病" value="illness" />
            <el-option label="就医" value="visit" />
            <el-option label="复查" value="followup" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item :label="healthRecordTitleLabel">
          <el-input v-model="healthRecordForm.disease" :placeholder="healthRecordTitlePlaceholder" />
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="healthRecordForm.date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="处理记录">
          <el-input
            v-model="healthRecordForm.treatment"
            type="textarea"
            :rows="2"
            placeholder="如用药、检查、处置方案"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="healthRecordForm.notes"
            type="textarea"
            :rows="2"
            placeholder="可填写医院、复查提醒、费用等"
          />
        </el-form-item>
        <el-form-item v-if="syncTargetCats.length > 0" label="同步到其他猫咪">
          <div class="health-sync-block">
            <el-checkbox-group v-model="healthRecordForm.syncCatIds" class="health-sync-options">
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
        <el-form-item v-if="editingHealthRecordId && hasRealSyncGroup" label="同步修改">
          <div class="health-sync-block health-sync-switch-row">
            <el-switch v-model="healthRecordForm.syncUpdateGroup" />
            <span class="health-sync-tip">打开后，会把同组猫咪里的这条记录一起更新。</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showHealthRecordDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingHealthRecord" @click="handleSaveHealthRecord">
          {{ editingHealthRecordId ? '更新' : '添加' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加体重记录对话框 -->
    <el-dialog
      v-model="showWeightDialog"
      :title="weightDialogTitle"
      width="400px"
      @closed="resetWeightDialog"
    >
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
        <el-button type="primary" :loading="addingWeight" @click="handleAddWeight">
          {{ isEditingWeight ? '更新' : '添加' }}
        </el-button>
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

    <!-- 上传照片 -->
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
              <el-checkbox v-for="userCat in userCats" :key="userCat.id" :value="userCat.id">
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

    <PhotoPreviewDialog
      v-model="showPhotoPreview"
      :src="previewPhoto?.url || ''"
      :title="previewPhoto ? formatPhotoCatNames(previewPhoto) : ''"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, computed, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Delete, Plus, FirstAidKit, Download, Upload, StarFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { catApi, weightApi, photoApi, medicalHistoryApi } from '../api'
import PhotoPreviewDialog from '../components/PhotoPreviewDialog.vue'
import CatFeedingTab from '../components/CatFeedingTab.vue'
import { sortPhotos, type PhotoSortMode } from '../utils/photoOrder'

const router = useRouter()
const route = useRoute()

const cat = ref<any>(null)
const weightRecords = ref<any[]>([])
const healthRecords = ref<any[]>([])
const photos = ref<any[]>([])
const userCats = ref<any[]>([])
const DETAIL_TABS = ['info', 'health', 'feeding', 'weight', 'album'] as const
type DetailTab = typeof DETAIL_TABS[number]

const activeTab = ref<DetailTab>(normalizeDetailTab(route.query.tab))
const showEditDialog = ref(false)
const showHealthSettingsDialog = ref(false)
const showWeightDialog = ref(false)
const showHealthRecordDialog = ref(false)
const showAvatarDialog = ref(false)
const showPhotoUploadDialog = ref(false)
const showPhotoPreview = ref(false)
const previewPhoto = ref<any | null>(null)
const saving = ref(false)
const savingHealthSettings = ref(false)
const addingWeight = ref(false)
const savingHealthRecord = ref(false)
const uploadingPhoto = ref(false)
const weightChartRef = ref<HTMLElement>()
const editFormRef = ref()
const weightFormRef = ref()
const photoFileInputRef = ref<HTMLInputElement | null>(null)
const selectedPhotoFile = ref<File | null>(null)
const photoUploadQueue = ref<File[]>([])
const photoUploadQueueIndex = ref(0)
const photoUploadPreviewUrl = ref('')
const photoRecommendations = ref<any[]>([])
const editingHealthRecordId = ref<number | null>(null)
const syncedGroupRecords = ref<any[]>([])
const draggingPhotoId = ref<number | null>(null)
const photoSortMode = ref<PhotoSortMode>((localStorage.getItem('photoSortMode') as PhotoSortMode) || 'manual')
const weightCurrentPage = ref(1)
const weightPageSizeOptions = [10, 20, 50]
const weightPageSize = ref(weightPageSizeOptions[0])
const weightChartFilterMode = ref<'all' | '1y' | '6m' | 'custom'>('all')
const weightChartDateRange = ref<string[]>([])

let weightChart: echarts.ECharts | null = null
let weightChartResizeObserver: ResizeObserver | null = null

const currentCatId = computed(() => Number(route.params.id))
const catDockWrapRef = ref<HTMLElement | null>(null)
const catDockItemRefs = new Map<number, HTMLElement>()
const dockHoverCatId = ref<number | null>(null)
const dockPointer = ref<{ x: number; y: number } | null>(null)

const editForm = reactive({
  name: '',
  gender: 'male',
  breed: '',
  breed_custom: '',  // 自定义品种
  color: '',
  color_custom: '',  // 自定义毛色
  birth_date: '',
  neutered: false
})

const healthSettingsForm = reactive({
  vaccination_status: '',
  internal_deworming_interval_days: 90,
  external_deworming_interval_days: 180
})

// 品种选择变化处理
function handleBreedChange(value: string) {
  if (value !== '其他') {
    editForm.breed_custom = ''
  }
}

// 毛色选择变化处理
function handleColorChange(value: string) {
  if (value !== '其他') {
    editForm.color_custom = ''
  }
}

const weightForm = reactive({
  record_date: '',
  weight: 0,
  note: ''
})

const healthRecordForm = reactive({
  record_type: 'illness',
  disease: '',
  date: '',
  treatment: '',
  notes: '',
  sync_group_id: '',
  syncCatIds: [] as number[],
  syncUpdateGroup: true
})

const photoUploadForm = reactive({
  description: '',
  tagCatIds: [] as number[]
})

// 编辑的体重记录ID
const editingWeightId = ref<number | null>(null)
const isEditingWeight = computed(() => editingWeightId.value !== null)
const weightDialogTitle = computed(() => isEditingWeight.value ? '编辑体重记录' : '添加体重记录')
const healthRecordDialogTitle = computed(() => editingHealthRecordId.value ? '编辑健康记录' : '添加健康记录')
const maxImageUploadSizeMB = 20
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
const sortedPhotos = computed(() => sortPhotos(photos.value, photoSortMode.value))

watch(photoSortMode, (value) => {
  localStorage.setItem('photoSortMode', value)
})

watch(weightPageSize, () => {
  weightCurrentPage.value = 1
})

watch(weightRecords, () => {
  const maxPage = Math.max(1, Math.ceil(weightRecords.value.length / weightPageSize.value))
  if (weightCurrentPage.value > maxPage) {
    weightCurrentPage.value = maxPage
  }
  if (weightRecords.value.length === 0) {
    destroyWeightChart()
  }
})

watch(weightChartFilterMode, (mode) => {
  if (mode !== 'custom') {
    weightChartDateRange.value = []
  }
})

// 计算最新体重
const latestWeight = computed(() => {
  if (weightRecords.value.length === 0) return null
  return weightRecords.value[0].weight
})

const paginatedWeightRecords = computed(() => {
  const start = (weightCurrentPage.value - 1) * weightPageSize.value
  return weightRecords.value.slice(start, start + weightPageSize.value)
})

const filteredWeightRecords = computed(() => {
  if (weightRecords.value.length === 0) return []

  if (weightChartFilterMode.value === 'all') {
    return [...weightRecords.value]
  }

  if (weightChartFilterMode.value === 'custom') {
    if (weightChartDateRange.value.length !== 2) {
      return [...weightRecords.value]
    }
    const [start, end] = weightChartDateRange.value
    const startDate = parseLocalDate(start)
    const endDate = parseLocalDate(end)
    return weightRecords.value.filter((record) => {
      const recordDate = parseLocalDate(record.record_date)
      return recordDate >= startDate && recordDate <= endDate
    })
  }

  const monthCount = weightChartFilterMode.value === '1y' ? 12 : 6
  const startDate = new Date()
  startDate.setMonth(startDate.getMonth() - monthCount)
  return weightRecords.value.filter((record) => parseLocalDate(record.record_date) >= startDate)
})

watch([filteredWeightRecords, weightChartFilterMode, weightChartDateRange], () => {
  if (activeTab.value === 'weight') {
    renderWeightChart()
  }
})

const latestVaccinationRecord = computed(() => findLatestHealthRecord('vaccination'))
const latestInternalDewormingRecord = computed(() => findLatestHealthRecord('internal_deworming'))
const latestExternalDewormingRecord = computed(() => findLatestHealthRecord('external_deworming'))
const internalDewormingSourceDate = computed(() => {
  return latestInternalDewormingRecord.value?.date || cat.value?.deworming_date || ''
})
const externalDewormingSourceDate = computed(() => {
  return latestExternalDewormingRecord.value?.date || ''
})
const internalDewormingReminder = computed(() =>
  buildDewormingReminder(
    internalDewormingSourceDate.value,
    Number(cat.value?.internal_deworming_interval_days || healthSettingsForm.internal_deworming_interval_days || 90)
  )
)
const externalDewormingReminder = computed(() =>
  buildDewormingReminder(
    externalDewormingSourceDate.value,
    Number(cat.value?.external_deworming_interval_days || healthSettingsForm.external_deworming_interval_days || 180)
  )
)

const healthRecordTitleLabel = computed(() => {
  switch (healthRecordForm.record_type) {
    case 'vaccination':
      return '疫苗名称'
    case 'internal_deworming':
    case 'external_deworming':
      return '药品名称'
    case 'abnormal_symptom':
      return '异常症状'
    case 'illness':
      return '症状/疾病'
    case 'visit':
      return '就医事项'
    case 'followup':
      return '复查项目'
    default:
      return '记录标题'
  }
})

const healthRecordTitlePlaceholder = computed(() => {
  switch (healthRecordForm.record_type) {
    case 'vaccination':
      return '例如：三联疫苗加强针'
    case 'internal_deworming':
      return '例如：拜耳内驱'
    case 'external_deworming':
      return '例如：大宠爱外驱'
    case 'abnormal_symptom':
      return '例如：软便、打喷嚏、流口水'
    case 'illness':
      return '例如：软便、猫癣、感冒'
    case 'visit':
      return '例如：常规体检'
    case 'followup':
      return '例如：术后复查'
    default:
      return '请输入标题'
  }
})

const syncTargetCats = computed(() => {
  const currentCatId = Number(route.params.id)
  return userCats.value.filter((userCat) => userCat.id !== currentCatId)
})
const hasRealSyncGroup = computed(() => {
  return Boolean(healthRecordForm.sync_group_id) && syncedGroupRecords.value.length > 1
})

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

function parseLocalDate(dateStr: string): Date {
  return new Date(`${dateStr}T00:00:00`)
}

function normalizeDetailTab(tab: unknown): DetailTab {
  const tabValue = Array.isArray(tab) ? tab[0] : tab
  return DETAIL_TABS.includes(tabValue as DetailTab) ? (tabValue as DetailTab) : 'info'
}

function getCatAvatarFallback(targetCat: any): string {
  return targetCat?.gender === 'female' ? '🐱' : '😺'
}

function setCatDockItemRef(el: any, catId: number) {
  if (el instanceof HTMLElement) {
    catDockItemRefs.set(catId, el)
  } else {
    catDockItemRefs.delete(catId)
  }
}

async function centerSelectedCatDock() {
  await nextTick()
  const item = catDockItemRefs.get(currentCatId.value)
  if (!item) return
  item.scrollIntoView({ behavior: 'smooth', inline: 'nearest', block: 'center' })
}

function handleCatDockMouseMove(event: MouseEvent) {
  dockPointer.value = { x: event.clientX, y: event.clientY }
}

function handleCatDockMouseLeave() {
  dockPointer.value = null
  dockHoverCatId.value = null
}

function getCatDockItemStyle(catId: number) {
  const item = catDockItemRefs.get(catId)
  const isActive = catId === currentCatId.value

  let scale = isActive ? 1.1 : 1
  let dockInfluence = 0

  if (item && dockPointer.value) {
    const rect = item.getBoundingClientRect()
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    const distance = Math.hypot(dockPointer.value.x - centerX, dockPointer.value.y - centerY)
    dockInfluence = Math.max(0, 1 - distance / 190)
    scale += dockInfluence * 0.16
  }

  return {
    transform: `scale(${Math.min(scale, 1.24).toFixed(3)})`,
    zIndex: String(Math.round(scale * 100))
  }
}

function destroyWeightChart() {
  weightChartResizeObserver?.disconnect()
  weightChartResizeObserver = null
  window.removeEventListener('resize', handleWeightChartResize)

  if (weightChart) {
    weightChart.dispose()
    weightChart = null
  }
}

function buildDewormingReminder(dateStr: string, intervalDays: number) {
  if (!dateStr) return null

  const lastDate = parseLocalDate(dateStr)
  const dueDate = new Date(lastDate)
  dueDate.setDate(dueDate.getDate() + intervalDays)

  const today = parseLocalDate(new Date().toISOString().slice(0, 10))
  const diffDays = Math.floor((dueDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays < 0) {
    return { text: `超期未驱虫 ${Math.abs(diffDays)}天`, type: 'danger' as const }
  }
  if (diffDays === 0) {
    return { text: '今天应驱虫', type: 'warning' as const }
  }
  if (diffDays > 21) {
    return { text: '已驱虫', type: 'success' as const }
  }
  if (diffDays >= 14) {
    return { text: `${Math.floor(diffDays / 7)}周后应驱虫`, type: 'warning' as const }
  }
  return { text: `${diffDays}天后应驱虫`, type: 'warning' as const }
}

function getHealthRecordTypeLabel(type: string): string {
  switch (type) {
    case 'vaccination':
      return '疫苗'
    case 'internal_deworming':
      return '体内驱虫'
    case 'external_deworming':
      return '体外驱虫'
    case 'abnormal_symptom':
      return '异常症状'
    case 'illness':
      return '生病'
    case 'visit':
      return '就医'
    case 'followup':
      return '复查'
    default:
      return '其他'
  }
}

function getHealthRecordTagType(type: string): 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  switch (type) {
    case 'vaccination':
    case 'internal_deworming':
    case 'external_deworming':
      return 'success'
    case 'abnormal_symptom':
      return 'warning'
    case 'illness':
      return 'danger'
    case 'visit':
    case 'followup':
      return 'primary'
    default:
      return 'info'
  }
}

function normalizeHealthRecord(record: any) {
  return {
    ...record,
    record_type: record.record_type || 'illness',
    sync_group_id: record.sync_group_id || null,
    sync_group_size: typeof record.sync_group_size === 'number' ? record.sync_group_size : 0
  }
}

function findLatestHealthRecord(recordType: string) {
  return healthRecords.value.find((record) => record.record_type === recordType) || null
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
    editForm.breed_custom = ''  // 重置自定义品种
    editForm.color = res.color || ''
    editForm.color_custom = ''  // 重置自定义毛色
    editForm.birth_date = res.birth_date
    editForm.neutered = res.neutered

    healthSettingsForm.vaccination_status = res.vaccination_status || ''
    healthSettingsForm.internal_deworming_interval_days = res.internal_deworming_interval_days || 90
    healthSettingsForm.external_deworming_interval_days = res.external_deworming_interval_days || 180
  } catch (error) {
    ElMessage.error('加载猫咪详情失败')
    router.push('/dashboard')
  }
}

async function loadHealthRecords() {
  try {
    const catId = route.params.id as string
    const res = await medicalHistoryApi.getRecords(Number(catId))
    healthRecords.value = (res || [])
      .map((record: any) => normalizeHealthRecord(record))
      .sort((a: any, b: any) => new Date(b.date).getTime() - new Date(a.date).getTime())
  } catch (error) {
    ElMessage.error('加载健康记录失败')
  }
}

async function loadUserCats() {
  try {
    const userId = Number(localStorage.getItem('userId'))
    if (!userId) return
    const res = await catApi.getCats(userId)
    userCats.value = res
  } catch (error) {
    ElMessage.error('加载猫咪列表失败')
  }
}

async function loadPhotos() {
  try {
    const catId = route.params.id as string
    const res = await catApi.getPhotos(Number(catId))
    photos.value = res
  } catch (error) {
    ElMessage.error('加载相册失败')
  }
}

async function loadCurrentCatPageData() {
  await Promise.all([
    loadCatDetail(),
    loadWeightRecords(),
    loadHealthRecords(),
    loadUserCats(),
    loadPhotos()
  ])
  await centerSelectedCatDock()
}

async function loadWeightRecords() {
  try {
    const catId = route.params.id as string
    const res = await weightApi.getRecords(Number(catId))
    // 后端返回 date 字段，前端使用 record_date
    weightRecords.value = res.map((r: any) => ({
      ...r,
      record_date: r.date || r.record_date
    })).sort((a: any, b: any) =>
      new Date(b.record_date).getTime() - new Date(a.record_date).getTime()
    )
    weightCurrentPage.value = 1
    renderWeightChart()
  } catch (error) {
    ElMessage.error('加载体重记录失败')
  }
}

function renderWeightChart() {
  // 使用 nextTick 确保 DOM 已更新
  nextTick(() => {
    if (!weightChartRef.value) {
      return
    }

    weightChartResizeObserver?.disconnect()
    weightChartResizeObserver = null

    // 检查容器是否有有效尺寸
    const rect = weightChartRef.value.getBoundingClientRect()
    if (rect.width === 0 || rect.height === 0) {
      // 使用 ResizeObserver 等待容器变为可见
      weightChartResizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
            weightChartResizeObserver?.disconnect()
            weightChartResizeObserver = null
            // 容器现在有尺寸，渲染图表
            doRenderChart()
          }
        }
      })
      weightChartResizeObserver.observe(weightChartRef.value)
      return
    }

    doRenderChart()
  })
}

function doRenderChart() {
  if (!weightChartRef.value) return

  destroyWeightChart()
  weightChart = echarts.init(weightChartRef.value)

  const sortedRecords = [...filteredWeightRecords.value].sort((a, b) =>
    new Date(a.record_date).getTime() - new Date(b.record_date).getTime()
  )

  if (sortedRecords.length === 0) {
    weightChart.setOption({
      title: {
        text: '所选时间范围内暂无体重数据',
        left: 'center',
        top: 'middle',
        textStyle: {
          color: '#909399',
          fontSize: 14,
          fontWeight: 'normal'
        }
      },
      xAxis: {
        show: false,
        type: 'category',
        data: []
      },
      yAxis: {
        show: false,
        type: 'value'
      },
      series: []
    })
    window.addEventListener('resize', handleWeightChartResize)
    return
  }

  weightChart.setOption({
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

  window.addEventListener('resize', handleWeightChartResize)
}

function handleWeightChartResize() {
  weightChart?.resize()
}

async function handleSaveEdit() {
  try {
    saving.value = true
    const catId = route.params.id as string

    // 处理自定义品种和毛色
    const submitData = {
      ...editForm,
      breed: editForm.breed === '其他' ? editForm.breed_custom : editForm.breed,
      color: editForm.color === '其他' ? editForm.color_custom : editForm.color
    }
    // 移除临时字段
    delete (submitData as any).breed_custom
    delete (submitData as any).color_custom

    await catApi.updateCat(Number(catId), submitData)
    ElMessage.success('保存成功')
    showEditDialog.value = false
    loadCatDetail()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

function goHealthTab() {
  activeTab.value = 'health'
}

function switchCat(targetCatId: number) {
  if (targetCatId === currentCatId.value) return
  router.push({
    name: 'CatDetail',
    params: { id: targetCatId },
    query: {
      ...route.query,
      tab: activeTab.value
    }
  })
}

function openHealthSettingsDialog() {
  healthSettingsForm.vaccination_status = cat.value?.vaccination_status || ''
  healthSettingsForm.internal_deworming_interval_days = cat.value?.internal_deworming_interval_days || 90
  healthSettingsForm.external_deworming_interval_days = cat.value?.external_deworming_interval_days || 180
  showHealthSettingsDialog.value = true
}

function resetHealthSettingsDialog() {
  healthSettingsForm.vaccination_status = cat.value?.vaccination_status || ''
  healthSettingsForm.internal_deworming_interval_days = cat.value?.internal_deworming_interval_days || 90
  healthSettingsForm.external_deworming_interval_days = cat.value?.external_deworming_interval_days || 180
}

async function handleSaveHealthSettings() {
  try {
    savingHealthSettings.value = true
    const catId = route.params.id as string
    await catApi.updateCat(Number(catId), {
      vaccination_status: healthSettingsForm.vaccination_status,
      internal_deworming_interval_days: healthSettingsForm.internal_deworming_interval_days,
      external_deworming_interval_days: healthSettingsForm.external_deworming_interval_days
    })
    ElMessage.success('健康设置已保存')
    showHealthSettingsDialog.value = false
    await loadCatDetail()
  } catch (error) {
    ElMessage.error('保存健康设置失败')
  } finally {
    savingHealthSettings.value = false
  }
}

function openAddHealthRecordDialog() {
  resetHealthRecordDialog()
  healthRecordForm.date = new Date().toISOString().slice(0, 10)
  showHealthRecordDialog.value = true
}

async function editHealthRecord(record: any) {
  editingHealthRecordId.value = record.id
  healthRecordForm.record_type = record.record_type || 'illness'
  healthRecordForm.disease = record.disease || ''
  healthRecordForm.date = record.date || ''
  healthRecordForm.treatment = record.treatment || ''
  healthRecordForm.notes = record.notes || ''
  healthRecordForm.sync_group_id = record.sync_group_id || ''
  healthRecordForm.syncCatIds = []
  healthRecordForm.syncUpdateGroup = Boolean(record.sync_group_id && (record.sync_group_size || 0) > 1)
  syncedGroupRecords.value = []

  if (record.sync_group_id) {
    try {
      const groupRecords = (await medicalHistoryApi.getGroupRecords(record.sync_group_id) || [])
        .map((groupRecord: any) => normalizeHealthRecord(groupRecord))
      syncedGroupRecords.value = groupRecords
      healthRecordForm.syncCatIds = groupRecords
        .filter((groupRecord: any) => groupRecord.cat_id !== record.cat_id)
        .map((groupRecord: any) => groupRecord.cat_id)
      if (groupRecords.length <= 1) {
        healthRecordForm.syncUpdateGroup = false
      }
    } catch (error) {
      syncedGroupRecords.value = []
      healthRecordForm.syncUpdateGroup = false
    }
  }

  showHealthRecordDialog.value = true
}

function resetHealthRecordDialog() {
  editingHealthRecordId.value = null
  healthRecordForm.record_type = 'illness'
  healthRecordForm.disease = ''
  healthRecordForm.date = ''
  healthRecordForm.treatment = ''
  healthRecordForm.notes = ''
  healthRecordForm.sync_group_id = ''
  healthRecordForm.syncCatIds = []
  healthRecordForm.syncUpdateGroup = true
  syncedGroupRecords.value = []
}

async function handleSaveHealthRecord() {
  if (!healthRecordForm.disease.trim()) {
    ElMessage.error('请填写记录标题')
    return
  }
  if (!healthRecordForm.date) {
    ElMessage.error('请选择日期')
    return
  }

  try {
    savingHealthRecord.value = true
    const catId = Number(route.params.id)
    const desiredOtherCatIds = Array.from(new Set(healthRecordForm.syncCatIds.map(Number).filter(Boolean)))
    const desiredCatIds = Array.from(new Set([catId, ...desiredOtherCatIds]))
    const shouldSyncMultipleCats = desiredCatIds.length > 1
    const syncGroupId = shouldSyncMultipleCats
      ? (healthRecordForm.sync_group_id || (
          typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : ''
        ))
      : ''
    const payload = {
      record_type: healthRecordForm.record_type,
      sync_group_id: shouldSyncMultipleCats ? (syncGroupId || null) : null,
      disease: healthRecordForm.disease.trim(),
      date: healthRecordForm.date,
      treatment: healthRecordForm.treatment.trim() || null,
      notes: healthRecordForm.notes.trim() || null
    }

    if (editingHealthRecordId.value) {
      const existingGroupRecords = syncedGroupRecords.value.filter((groupRecord: any) => groupRecord.id !== editingHealthRecordId.value)
      const existingCatIdSet = new Set(existingGroupRecords.map((groupRecord: any) => Number(groupRecord.cat_id)))
      const desiredOtherCatIdSet = new Set(desiredOtherCatIds)

      await medicalHistoryApi.updateRecord(editingHealthRecordId.value, payload)

      const updatePromises: Promise<any>[] = []

      for (const groupRecord of existingGroupRecords) {
        const groupCatId = Number(groupRecord.cat_id)
        if (!desiredOtherCatIdSet.has(groupCatId)) {
          updatePromises.push(
            medicalHistoryApi.updateRecord(groupRecord.id, {
              sync_group_id: null
            })
          )
          continue
        }

        if (healthRecordForm.syncUpdateGroup && shouldSyncMultipleCats) {
          updatePromises.push(
            medicalHistoryApi.updateRecord(groupRecord.id, payload)
          )
        } else if (groupRecord.sync_group_id !== syncGroupId) {
          updatePromises.push(
            medicalHistoryApi.updateRecord(groupRecord.id, {
              sync_group_id: syncGroupId || null
            })
          )
        }
      }

      const newCatIds = desiredOtherCatIds.filter((targetCatId) => !existingCatIdSet.has(targetCatId))
      for (const targetCatId of newCatIds) {
        updatePromises.push(medicalHistoryApi.addRecord(targetCatId, payload))
      }

      if (updatePromises.length > 0) {
        await Promise.all(updatePromises)
      }
      ElMessage.success('健康记录已更新')
    } else {
      const targetCatIds = desiredCatIds
      if (targetCatIds.length > 1) {
        await medicalHistoryApi.addBatchRecords(catId, targetCatIds, payload)
      } else {
        await medicalHistoryApi.addRecord(catId, payload)
      }
      ElMessage.success('健康记录已添加')
    }

    showHealthRecordDialog.value = false
    await loadHealthRecords()
  } catch (error) {
    ElMessage.error(editingHealthRecordId.value ? '更新健康记录失败' : '添加健康记录失败')
  } finally {
    savingHealthRecord.value = false
  }
}

async function deleteHealthRecord(recordId: number) {
  try {
    await ElMessageBox.confirm('确定要删除这条健康记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await medicalHistoryApi.deleteRecord(recordId)
    ElMessage.success('删除成功')
    await loadHealthRecords()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除健康记录失败')
    }
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
  weightForm.record_date = record.date || record.record_date  // 兼容两种字段名
  weightForm.weight = record.weight
  weightForm.note = record.note || ''
  showWeightDialog.value = true
}

function openAddWeightDialog() {
  resetWeightDialog()
  showWeightDialog.value = true
}

function resetWeightDialog() {
  weightForm.record_date = ''
  weightForm.weight = 0
  weightForm.note = ''
  editingWeightId.value = null
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

    // 构建请求数据，确保字段名匹配后端
    const requestData = {
      date: weightForm.record_date,  // 后端期望 date 字段
      weight: weightForm.weight,
      note: weightForm.note
    }

    if (editingWeightId.value) {
      // 编辑模式
      await weightApi.updateRecord(editingWeightId.value, requestData)
      ElMessage.success('更新成功')
    } else {
      // 新增模式
      await weightApi.addRecord({
        cat_id: Number(catId),
        ...requestData
      })
      ElMessage.success('添加成功')
    }

    showWeightDialog.value = false
    loadWeightRecords()
  } catch (error) {
    ElMessage.error(editingWeightId.value ? '更新失败' : '添加失败')
  } finally {
    addingWeight.value = false
  }
}

function beforeAvatarUpload(file: File) {
  const isImage = file.type.startsWith('image/')
  const isWithinLimit = file.size / 1024 / 1024 < maxImageUploadSizeMB

  if (!isImage) {
    ElMessage.error('只能上传图片文件!')
    return false
  }
  if (!isWithinLimit) {
    ElMessage.error(`图片大小不能超过 ${maxImageUploadSizeMB}MB!`)
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

function formatPhotoCatNames(photo: any): string {
  if (!photo?.cats || photo.cats.length === 0) return '未标注'
  return photo.cats.map((taggedCat: any) => taggedCat.name).join(' / ')
}

function openPhotoUploadDialog() {
  resetPhotoUploadDialog()
  const currentCatId = Number(route.params.id)
  photoUploadForm.tagCatIds = [currentCatId]
  showPhotoUploadDialog.value = true
}

function triggerPhotoFileSelect() {
  photoFileInputRef.value?.click()
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

  const reordered = [...sortedPhotos.value]
  const fromIndex = reordered.findIndex((photo) => photo.id === draggingPhotoId.value)
  const toIndex = reordered.findIndex((photo) => photo.id === targetPhoto.id)
  if (fromIndex === -1 || toIndex === -1) return

  const [moved] = reordered.splice(fromIndex, 1)
  reordered.splice(toIndex, 0, moved)
  const newIndex = reordered.findIndex((photo) => photo.id === draggingPhotoId.value)
  if (newIndex === -1) return

  try {
    await photoApi.reorderPhoto({
      user_id: Number(localStorage.getItem('userId')),
      photo_id: draggingPhotoId.value,
      prev_photo_id: newIndex > 0 ? reordered[newIndex - 1].id : null,
      next_photo_id: newIndex < reordered.length - 1 ? reordered[newIndex + 1].id : null
    })
    await loadPhotos()
  } catch (error) {
    ElMessage.error('调整排序失败')
  } finally {
    draggingPhotoId.value = null
  }
}

async function togglePhotoPin(photo: any) {
  try {
    await photoApi.updatePhoto(photo.id, { is_pinned: !photo.is_pinned })
    await loadPhotos()
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
  photoUploadForm.tagCatIds = [Number(route.params.id)]

  await recommendPhotoTags(file)
}

async function handlePhotoFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (files.length === 0) return

  const validFiles = files.filter((file) => beforePhotoUpload(file))
  if (validFiles.length === 0) {
    input.value = ''
    return
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

async function recommendPhotoTags(file: File) {
  try {
    const userId = Number(localStorage.getItem('userId'))
    if (!userId) return
    const res = await photoApi.recommendTags(userId, file)
    photoRecommendations.value = res.recommendations || []
  } catch (error) {
    photoRecommendations.value = []
  }
}

async function uploadSelectedPhoto(options: { allowDuplicate?: boolean; allowSimilar?: boolean } = {}) {
  if (!selectedPhotoFile.value) {
    throw new Error('missing_file')
  }
  const formData = new FormData()
  formData.append('file', selectedPhotoFile.value)
  formData.append('description', photoUploadForm.description)
  formData.append('tag_cat_ids', JSON.stringify(photoUploadForm.tagCatIds))
  appendUploadDecisionFlags(formData, options)

  const catId = route.params.id as string
  await catApi.uploadPhoto(Number(catId), formData)
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
  await loadPhotos()
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

function viewPhoto(photo: any) {
  previewPhoto.value = photo
  showPhotoPreview.value = true
}

async function deletePhoto(photo: any) {
  try {
    const message = photo.cats?.length > 1
      ? '这是一张合照。继续后，只会从当前猫咪相册移除，其他猫咪相册仍会保留。'
      : '确定要删除这张照片吗？'

    await ElMessageBox.confirm(message, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const catId = route.params.id as string
    const res = await photoApi.deletePhoto(photo.id, Number(catId))
    ElMessage.success(res.message || '删除成功')
    loadPhotos()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// ==================== 导入导出功能 ====================

// 下载模板
async function handleDownloadTemplate() {
  try {
    const userId = localStorage.getItem('userId')
    if (!userId) {
      ElMessage.error('请先登录')
      return
    }

    const response = await weightApi.downloadTemplate(Number(userId))

    // 创建下载链接
    const blob = new Blob([response as any], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'weight_template.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('模板下载成功')
  } catch (error) {
    ElMessage.error('下载模板失败')
  }
}

// 导入前验证
function beforeImportUpload(file: File) {
  const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls')
  if (!isExcel) {
    ElMessage.error('请上传 Excel 文件 (.xlsx 或 .xls)')
    return false
  }
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  return true
}

// 导入体重数据
async function handleImportWeights(options: any) {
  try {
    const userId = localStorage.getItem('userId')
    if (!userId) {
      ElMessage.error('请先登录')
      return
    }

    const response = await weightApi.importWeights(Number(userId), options.file)

    ElMessage.success(response.message || '导入成功')

    // 如果有错误信息，显示详情
    if (response.errors && response.errors.length > 0) {
      ElMessageBox.alert(
        response.errors.join('\n') + (response.error_count > 10 ? `\n...还有 ${response.error_count - 10} 条错误` : ''),
        '导入警告',
        { type: 'warning' }
      )
    }

    // 刷新体重记录
    loadWeightRecords()
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || '导入失败'
    ElMessage.error(errorMsg)
  }
}

// 导出体重数据
async function handleExportWeights() {
  try {
    const userId = localStorage.getItem('userId')
    if (!userId) {
      ElMessage.error('请先登录')
      return
    }

    const catId = route.params.id as string

    const response = await weightApi.exportWeights(Number(userId), [Number(catId)])

    // 创建下载链接
    const blob = new Blob([response as any], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    link.download = `weight_export_${timestamp}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || '导出失败'
    ElMessage.error(errorMsg)
  }
}

function goBack() {
  router.push('/dashboard')
}

// 监听 tab 切换，当切换到体重记录页签时重新渲染图表
watch(() => route.query.tab, (tab) => {
  const normalizedTab = normalizeDetailTab(tab)
  if (normalizedTab !== activeTab.value) {
    activeTab.value = normalizedTab
  }
})

watch(() => route.params.id, (newId, oldId) => {
  if (newId !== oldId) {
    loadCurrentCatPageData()
  }
})

watch(activeTab, (newTab) => {
  if (route.query.tab !== newTab) {
    router.replace({
      query: {
        ...route.query,
        tab: newTab
      }
    })
  }

  if (newTab === 'weight') {
    // 使用 setTimeout 确保 DOM 已完全渲染
    setTimeout(() => {
      renderWeightChart()
    }, 100)
  }
})

onMounted(() => {
  loadCurrentCatPageData()
})

onBeforeUnmount(() => {
  destroyWeightChart()
})
</script>

<style scoped>
.cat-detail-container {
  --cat-orange-400: #f5a24f;
  --cat-orange-500: #ef8e36;
  --cat-orange-600: #dc7420;
  --cat-brown-700: #8f5831;
  --cat-ink: #5f4634;
  --dock-width: 108px;
  --dock-gap: 14px;
  --dock-side-offset: 20px;
  --dock-top-offset: 24px;
  --dock-bottom-offset: 24px;
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 12% 18%, rgba(255, 219, 164, 0.65) 0, rgba(255, 219, 164, 0.2) 16%, transparent 34%),
    radial-gradient(circle at 88% 14%, rgba(255, 187, 120, 0.28) 0, rgba(255, 187, 120, 0.14) 18%, transparent 38%),
    radial-gradient(circle at 78% 84%, rgba(255, 210, 155, 0.36) 0, rgba(255, 210, 155, 0.1) 18%, transparent 32%),
    linear-gradient(180deg, #fff7ec 0%, #ffe9ca 52%, #ffdcb5 100%);
  padding: 24px 20px 32px;
}

.cat-detail-container::before,
.cat-detail-container::after {
  position: absolute;
  pointer-events: none;
  opacity: 0.28;
  font-size: 116px;
  line-height: 1;
}

.cat-detail-container::before {
  content: '🐾';
  top: 88px;
  right: 42px;
  transform: rotate(-15deg);
}

.cat-detail-container::after {
  content: '🐾';
  left: 28px;
  bottom: 36px;
  transform: rotate(18deg) scale(0.88);
}

.detail-layout {
  display: block;
  padding-left: calc(var(--dock-width) + var(--dock-gap));
}

.cat-dock-panel {
  position: fixed;
  left: var(--dock-side-offset);
  top: var(--dock-top-offset);
  bottom: var(--dock-bottom-offset);
  width: var(--dock-width);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  padding: 10px 8px 12px;
  background: linear-gradient(180deg, rgba(255, 252, 245, 0.96), rgba(255, 244, 226, 0.95));
  border: 1px solid rgba(248, 196, 128, 0.45);
  border-radius: 24px;
  box-shadow: 0 16px 28px rgba(208, 141, 66, 0.12);
}

.cat-dock-panel__top {
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
}

.cat-dock-back {
  min-width: 0;
  padding: 6px 10px !important;
  border-radius: 999px;
  color: var(--cat-ink) !important;
  background: rgba(255, 249, 240, 0.9);
  border: 1px solid rgba(245, 185, 110, 0.38);
  box-shadow: 0 8px 16px rgba(217, 144, 63, 0.08);
}

.cat-dock-wrap {
  position: relative;
  z-index: 1;
  width: 100%;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: visible;
  padding: 2px 0;
  scrollbar-width: none;
}

.cat-dock-wrap::-webkit-scrollbar {
  display: none;
}

.cat-dock {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.cat-dock__item {
  position: relative;
  appearance: none;
  border: 0;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 8px 6px;
  border-radius: 18px;
  cursor: pointer;
  transition: transform 0.14s ease-out, opacity 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
  transform-origin: center center;
}

.cat-dock__item.is-active {
  background: transparent;
  box-shadow: none;
}

.cat-dock__item:hover {
  opacity: 1;
}

.cat-dock__item:not(.is-active) {
  opacity: 0.88;
}

.cat-dock__avatar {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  padding: 4px;
  box-sizing: border-box;
  background: linear-gradient(145deg, #fff9f0, #ffd9ac);
  border: 2px solid rgba(255, 252, 248, 0.96);
  box-shadow: 0 12px 22px rgba(230, 159, 85, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.cat-dock__avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  display: block;
  border-radius: 50%;
}

.cat-dock__name {
  max-width: 100%;
  opacity: 0;
  overflow: visible;
  font-size: 12px;
  color: var(--cat-brown-700);
  white-space: nowrap;
  text-align: center;
  transform: none;
  transition: color 0.2s ease, opacity 0.2s ease;
}

.cat-dock__item.is-active .cat-dock__avatar {
  border-color: rgba(255, 170, 75, 0.95);
  box-shadow: 0 16px 32px rgba(239, 142, 54, 0.28);
}

.cat-dock__item.is-active .cat-dock__name {
  opacity: 1;
  color: var(--cat-orange-600);
  font-weight: 600;
}

.cat-dock__item.is-hovered .cat-dock__name {
  opacity: 1;
}

.detail-content {
  position: relative;
  background: linear-gradient(180deg, rgba(255, 253, 248, 0.96), rgba(255, 247, 232, 0.98));
  border: 1px solid rgba(248, 196, 128, 0.5);
  border-radius: 30px;
  padding: 22px 20px;
  box-shadow: 0 24px 55px rgba(200, 132, 59, 0.15);
  backdrop-filter: blur(10px);
}

.detail-content::before {
  content: '';
  position: absolute;
  inset: 12px;
  border-radius: 22px;
  border: 1px dashed rgba(242, 168, 84, 0.28);
  pointer-events: none;
}

.detail-tabs {
  margin-bottom: 14px;
}

.detail-tabs :deep(.el-tabs__header) {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.detail-tabs :deep(.el-tabs__nav-wrap) {
  display: flex;
  justify-content: center;
  padding: 0 14px;
}

.detail-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.detail-tabs :deep(.el-tabs__nav-scroll) {
  display: flex;
  justify-content: center;
  width: fit-content;
  max-width: 100%;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 232, 199, 0.78);
  border: 1px solid rgba(247, 188, 104, 0.45);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

.detail-tabs :deep(.el-tabs__nav) {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  padding: 0;
}

.detail-tabs :deep(.el-tabs__item) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 88px;
  height: 36px;
  padding: 0 20px !important;
  box-sizing: border-box;
  text-align: center;
  border-radius: 999px;
  color: rgba(111, 73, 39, 0.78);
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  transition: color 0.2s ease, background 0.2s ease, transform 0.2s ease;
}

.detail-tabs :deep(.el-tabs__item:first-child),
.detail-tabs :deep(.el-tabs__item:last-child) {
  padding-left: 20px !important;
  padding-right: 20px !important;
}

.detail-tabs :deep(.el-tabs__item:hover) {
  color: var(--cat-orange-600);
}

.detail-tabs :deep(.el-tabs__item.is-active) {
  color: #fff;
  background: linear-gradient(135deg, var(--cat-orange-400), var(--cat-orange-600));
  box-shadow: 0 10px 18px rgba(239, 142, 54, 0.28);
  transform: translateY(-1px);
}

.detail-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.detail-content :deep(.el-button--primary) {
  border-color: transparent;
  background: linear-gradient(135deg, var(--cat-orange-400), var(--cat-orange-600));
  box-shadow: 0 10px 18px rgba(239, 142, 54, 0.22);
}

.detail-content :deep(.el-button--primary:hover) {
  filter: brightness(1.03);
}

.detail-content :deep(.el-button--default) {
  border-color: rgba(245, 185, 110, 0.5);
  color: var(--cat-ink);
  background: rgba(255, 249, 240, 0.95);
}

.detail-content :deep(.el-button.is-text) {
  color: var(--cat-orange-600);
}

.summary-link-button {
  color: #fff !important;
  background: linear-gradient(135deg, var(--cat-orange-400), var(--cat-orange-600));
  border: none;
  box-shadow: 0 10px 18px rgba(239, 142, 54, 0.2);
}

.summary-link-button:hover {
  filter: brightness(1.03);
}

.inline-action-button {
  color: #fff !important;
  background: linear-gradient(135deg, var(--cat-orange-400), var(--cat-orange-600));
  border: none;
  box-shadow: 0 8px 14px rgba(239, 142, 54, 0.18);
}

.inline-action-button--danger {
  background: linear-gradient(135deg, #ef8f7b, #d85b40);
  box-shadow: 0 8px 14px rgba(216, 91, 64, 0.16);
}

.inline-action-button:hover {
  filter: brightness(1.03);
}

.info-section {
  max-width: 800px;
  margin: 0 auto;
}

.health-section {
  max-width: 800px;
  margin: 0 auto;
}

.health-info-card {
  margin-top: 18px;
  padding: 16px 18px;
  background: linear-gradient(180deg, rgba(255, 249, 239, 0.96), rgba(255, 242, 221, 0.94));
  border: 1px solid rgba(246, 186, 110, 0.45);
  border-radius: 22px;
  box-shadow: 0 14px 26px rgba(214, 151, 76, 0.11);
}

.health-info-card h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  color: var(--cat-orange-600);
}

.health-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.health-info-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.health-sync-block {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  width: 100%;
}

.health-sync-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
}

.health-sync-switch-row {
  gap: 10px;
}

.basic-info-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 14px;
}

.basic-health-preview {
  margin-top: 18px;
  padding: 16px 18px;
  background: linear-gradient(180deg, rgba(255, 249, 239, 0.96), rgba(255, 242, 221, 0.94));
  border: 1px solid rgba(246, 186, 110, 0.45);
  border-radius: 22px;
  box-shadow: 0 14px 26px rgba(214, 151, 76, 0.11);
  cursor: pointer;
}

.basic-health-preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.basic-health-preview-header h3 {
  margin: 0;
  color: var(--cat-orange-600);
  font-size: 18px;
}

.health-summary-cell {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.summary-inline-text {
  color: rgba(95, 70, 52, 0.72);
  font-size: 13px;
}

.health-record-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.health-record-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid rgba(242, 188, 116, 0.42);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 253, 249, 0.96), rgba(255, 244, 226, 0.9));
  box-shadow: 0 10px 20px rgba(222, 162, 87, 0.08);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.health-record-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 28px rgba(222, 162, 87, 0.14);
}

.health-record-main {
  flex: 1;
  min-width: 0;
}

.health-record-title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.health-record-date {
  color: rgba(138, 106, 80, 0.75);
  font-size: 13px;
}

.health-record-detail {
  margin-top: 6px;
  color: rgba(95, 70, 52, 0.82);
  line-height: 1.6;
  white-space: pre-wrap;
}

.health-record-actions {
  display: flex;
  flex-shrink: 0;
  align-items: flex-start;
  gap: 4px;
}

.text-muted {
  color: rgba(138, 106, 80, 0.7);
}

.health-sync-tip {
  color: rgba(138, 106, 80, 0.78);
  font-size: 13px;
  line-height: 1.5;
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
  gap: 12px;
}

.weight-header h3 {
  margin: 0;
  color: var(--cat-orange-600);
}

.weight-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.inline-upload {
  display: inline-block;
}

.weight-chart-card {
  margin-bottom: 24px;
  padding: 18px 20px 8px;
  border: 1px solid rgba(246, 186, 110, 0.42);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 249, 239, 0.98) 0%, rgba(255, 255, 255, 0.96) 100%);
  box-shadow: 0 16px 28px rgba(214, 151, 76, 0.1);
}

.weight-chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 8px;
}

.weight-chart-toolbar__title h4 {
  margin: 0 0 4px;
  font-size: 16px;
  color: var(--cat-orange-600);
}

.weight-chart-toolbar__title span {
  font-size: 13px;
  color: rgba(138, 106, 80, 0.72);
}

.weight-chart-filters {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  flex-wrap: wrap;
}

.weight-chart-date-picker {
  width: 180px;
}

.weight-chart {
  height: 300px;
}

.weight-pagination {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.weight-pagination__meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.weight-pagination__summary {
  color: rgba(138, 106, 80, 0.72);
  font-size: 13px;
}

.weight-pagination__size {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(138, 106, 80, 0.72);
  font-size: 13px;
}

.weight-pagination__size-select {
  width: 88px;
}

.weight-pagination__size-label {
  white-space: nowrap;
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
  gap: 12px;
}

.album-header h3 {
  margin: 0;
  color: var(--cat-orange-600);
}

.album-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.photo-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 18px;
  overflow: hidden;
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

.photo-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
}

.photo-overlay {
  position: absolute;
  bottom: 8px;
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
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.photo-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.photo-item:hover .photo-actions {
  opacity: 1;
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

.avatar-uploader {
  display: flex;
  justify-content: center;
}

.avatar-uploader-icon {
  font-size: 48px;
  color: #c68e58;
  width: 150px;
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed rgba(239, 142, 54, 0.45);
  border-radius: 16px;
  background: rgba(255, 246, 232, 0.92);
}

.avatar-preview {
  width: 150px;
  height: 150px;
  object-fit: cover;
  border-radius: 16px;
}

.detail-content :deep(.el-descriptions) {
  --el-descriptions-table-border: rgba(244, 196, 127, 0.36);
}

.detail-content :deep(.el-descriptions__body) {
  border-radius: 18px;
  overflow: hidden;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.detail-content :deep(.el-descriptions__label.el-descriptions__cell.is-bordered-label) {
  background: rgba(255, 237, 210, 0.9);
  color: var(--cat-brown-700);
  font-weight: 600;
}

.detail-content :deep(.el-descriptions__content.el-descriptions__cell.is-bordered-content) {
  background: rgba(255, 252, 247, 0.92);
  color: var(--cat-ink);
}

.detail-content :deep(.el-tag--success) {
  background: #eff9e7;
  border-color: #b6dd9a;
  color: #5e9f2d;
}

.detail-content :deep(.el-tag--warning) {
  background: #fff2dd;
  border-color: #f3c57c;
  color: #c97916;
}

.detail-content :deep(.el-tag--danger) {
  background: #fff0ea;
  border-color: #efb29d;
  color: #d16339;
}

.detail-content :deep(.el-tag--info) {
  background: #fff6e8;
  border-color: #efd4a7;
  color: #99714e;
}

@media (max-width: 768px) {
  .cat-detail-container {
    padding: 16px 14px 24px;
  }

  .detail-layout {
    display: grid;
    grid-template-columns: 1fr;
    padding-left: 0;
  }

  .cat-dock-panel {
    position: static;
    left: auto;
    top: auto;
    bottom: auto;
    width: auto;
    padding: 10px 12px;
    border-radius: 22px;
  }

  .cat-dock-panel__top {
    justify-content: flex-start;
  }

  .cat-dock-wrap {
    width: 100%;
    flex: initial;
    min-height: auto;
    overflow-x: auto;
    overflow-y: visible;
    padding: 0;
  }

  .cat-dock {
    flex-direction: row;
    align-items: flex-end;
    gap: 8px;
    min-width: max-content;
  }

  .cat-dock__item {
    flex-direction: column;
    justify-content: center;
    width: auto;
    min-width: 74px;
    padding: 8px 8px 10px;
    border-radius: 20px;
    transform-origin: center bottom;
  }

  .cat-dock__name {
    max-width: 100%;
    opacity: 1;
    overflow: visible;
    transform: none;
  }

  .detail-content {
    padding: 22px 16px;
    border-radius: 24px;
  }

  .detail-tabs :deep(.el-tabs__nav-scroll) {
    width: 100%;
    overflow-x: auto;
    justify-content: flex-start;
  }

  .detail-tabs :deep(.el-tabs__nav) {
    min-width: max-content;
  }

  .basic-info-actions,
  .health-info-header,
  .basic-health-preview-header,
  .album-header,
  .album-header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .weight-header,
  .weight-chart-toolbar,
  .weight-pagination {
    flex-direction: column;
    align-items: stretch;
  }

  .health-record-item {
    flex-direction: column;
  }

  .health-record-actions {
    align-items: center;
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  .weight-pagination__meta {
    justify-content: flex-end;
  }

  .weight-chart-filters {
    justify-content: flex-start;
  }

  .weight-chart-date-picker {
    width: 100%;
  }
}
</style>
