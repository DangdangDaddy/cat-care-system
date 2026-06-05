import { expect, test } from '@playwright/test'

test('cat detail feeding tab can create a feeding plan', async ({ page }) => {
  await page.goto('/login')

  await page.getByPlaceholder('用户名').fill('demo')
  await page.getByPlaceholder('密码').fill('123456')
  await page.getByRole('button', { name: '登录' }).click()

  await page.waitForURL('**/dashboard')
  await expect(page.getByRole('tab', { name: '我的猫咪' })).toBeVisible()

  await page.locator('.cat-card').first().click()
  await page.waitForURL(/\/cat\/\d+/)

  await page.getByRole('tab', { name: '饮食记录' }).click()
  await expect(page.getByRole('heading', { name: '当前喂养方案' })).toBeVisible()
  await expect(page.getByRole('button', { name: '新增方案' })).toBeVisible()

  await page.getByRole('button', { name: '新增方案' }).click()
  await page.getByPlaceholder('请输入方案名称').fill('UI自动化方案')
  await page.getByPlaceholder('请输入产品名').fill('测试主粮')
  await page.locator('.el-dialog').last().getByRole('button', { name: '保存' }).click()

  await expect(page.getByText('UI自动化方案').first()).toBeVisible()
})

test('feeding sub tabs expose sync controls when user has multiple cats', async ({ page }) => {
  await page.goto('/login')

  await page.getByPlaceholder('用户名').fill('demo')
  await page.getByPlaceholder('密码').fill('123456')
  await page.getByRole('button', { name: '登录' }).click()

  await page.waitForURL('**/dashboard')
  await expect(page.getByRole('tab', { name: '我的猫咪' })).toBeVisible()

  const catCards = page.locator('.cat-card')
  const catCount = await catCards.count()
  test.skip(catCount < 2, '需要至少两只猫才能验证饮食记录同步控件')

  await catCards.first().click()
  await page.waitForURL(/\/cat\/\d+/)

  await page.getByRole('tab', { name: '饮食记录' }).click()

  const expectSyncBlock = async (openButtonName: string) => {
    await page.getByRole('button', { name: openButtonName }).click()
    const dialog = page.locator('.el-dialog').last()
    await expect(dialog.getByText('同步到其他猫咪')).toBeVisible()
    await expect(dialog.locator('.health-sync-options .el-checkbox').first()).toBeVisible()
    await dialog.getByRole('button', { name: '取消' }).click()
  }

  await expectSyncBlock('新增方案')

  await page.getByRole('tab', { name: '每日喂食记录' }).click()
  await expectSyncBlock('添加记录')

  await page.getByRole('tab', { name: '换粮计划' }).click()
  await expectSyncBlock('新增换粮')

  await page.getByRole('tab', { name: '补剂疗程' }).click()
  await expectSyncBlock('新增疗程')
})
