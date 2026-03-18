# 迭代2 并行开发任务分配

## 项目信息
- 代码目录：`/Users/jianghaoqi/.openclaw/workspace/cat-care-system`
- 需求文档：`~/Documents/猫咪项目需求/需求文档-迭代2-正式版.md`
- 目标版本：v0.2.0
- 开发时间：1天（并行开发）

---

## Agent 1：后端开发任务

### 数据库模型更新
1. **cats 表新增字段**：
   - breed (VARCHAR 50) - 品种
   - coat_color (VARCHAR 50) - 毛色
   - vaccination_status (VARCHAR 20) - 疫苗接种状态
   - last_internal_deworming (DATE) - 最近体内驱虫
   - last_external_deworming (DATE) - 最近体外驱虫

2. **新建 medical_history 表**：
   - id, cat_id, disease, date, treatment, notes, created_at

3. **新建 photos 表**：
   - id, cat_id, album_id, url, thumbnail, description, created_at

4. **新建 albums 表**：
   - id, cat_id, name, cover_photo_id, created_at

### API 接口开发
- PUT /api/cats/{id} - 更新猫咪信息（含新字段）
- GET/POST /api/cats/{id}/medical-history - 病史记录
- GET/POST /api/cats/{id}/photos - 照片管理
- DELETE /api/cats/{id}/photos/{photo_id} - 删除照片
- GET/POST /api/cats/{id}/albums - 相册管理
- PUT /api/weights/{id} - 修改体重记录
- DELETE /api/weights/{id} - 删除体重记录

### 数据迁移
- 创建 Alembic 迁移脚本
- 保留现有数据

---

## Agent 2：前端开发任务

### 添加猫咪弹窗优化
1. **品种下拉框**（15种）：
   - 英国短毛猫、美国短毛猫、中华田园猫、布偶猫、缅因猫、暹罗猫、波斯猫、俄罗斯蓝猫、加菲猫、斯芬克斯猫、挪威森林猫、金吉拉、孟加拉豹猫、苏格兰折耳猫、其他

2. **毛色下拉框**（14种）：
   - 纯白色、纯黑色、纯灰色/蓝色、橘色/橘猫、奶牛色、三花色、玳瑁色、虎斑/狸花、银渐层、金渐层、蓝金渐层、重点色、烟色、其他

3. **新增字段**：
   - 疫苗接种情况（下拉：未接种/第1针/第2针/已完成）
   - 最近体内驱虫日期
   - 最近体外驱虫日期
   - 病史记录（多行文本，支持多条）

### 详情页优化
1. **左侧信息展示**：显示新品种、毛色、疫苗、驱虫信息
2. **体重记录**：添加编辑/删除按钮
3. **相册页签**：上传/展示/删除照片

### 主页优化
- 相册页签：随机展示所有猫咪照片

### 品种展示智能匹配
```javascript
// 展示规则示例
formatBreedDisplay(breed, coatColor) {
  const breedMap = {
    '英国短毛猫': '英短',
    '美国短毛猫': '美短',
    '中华田园猫': '中华田园'
  }
  const coatMap = {
    '纯灰色/蓝色': '蓝猫',
    '橘色/橘猫': '橘猫',
    '虎斑/狸花': '狸花猫'
  }
  return `${breedMap[breed] || breed}${coatMap[coatColor] || coatColor}`
}
```

---

## Agent 3：测试任务

### 后端 API 测试
1. 测试所有新增 API 接口
2. 测试数据库迁移是否正确
3. 测试数据验证

### 前端功能测试
1. 测试添加猫咪弹窗所有新字段
2. 测试详情页信息展示
3. 测试体重记录编辑/删除
4. 测试相册上传/展示/删除

### 集成测试
1. 前后端联调
2. 端到端流程测试

---

## 协作规则

1. **文件冲突避免**：
   - Agent 1 只修改 backend/ 目录
   - Agent 2 只修改 frontend/ 目录
   - Agent 3 最后进行测试

2. **提交规范**：
   - 每个 agent 完成任务后提交代码
   - 提交信息格式：`[agent-N] 功能描述`

3. **沟通方式**：
   - 遇到问题在 docs/iteration2-issues.md 记录
   - 由虾虾协调解决

---

_创建时间：2026-03-19 04:32_
_创建者：虾虾 🦐_
