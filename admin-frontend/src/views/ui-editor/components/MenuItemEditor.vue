<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import type { UIMenuItem, MenuItemForm } from '../types'

const props = defineProps<{
  visible: boolean
  mode: 'add' | 'edit'
  menuType: 'quick_entry' | 'tabbar'
  initialData: UIMenuItem | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'save', data: MenuItemForm): void
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const formRef = ref()
const form = ref<MenuItemForm>({
  menu_code: '',
  menu_type: 'quick_entry',
  title: '',
  subtitle: '',
  icon: '',
  icon_active: '',
  link_type: 'page',
  link_value: '',
  link_params: {},
  show_condition: {},
  badge_type: 'none',
  badge_value: '',
  sort_order: 0,
  is_visible: true
})

const rules = {
  menu_code: [{ required: true, message: '请输入菜单编码', trigger: 'blur' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }]
}

const linkTypeOptions = [
  { label: '页面', value: 'page' },
  { label: 'Tab切换', value: 'tab' },
  { label: 'WebView', value: 'webview' },
  { label: '其他小程序', value: 'miniprogram' },
  { label: '无跳转', value: 'none' }
]

const badgeTypeOptions = [
  { label: '无', value: 'none' },
  { label: '小红点', value: 'dot' },
  { label: '数字', value: 'number' },
  { label: '文字', value: 'text' }
]

const dialogTitle = computed(() => {
  const typeText = props.menuType === 'tabbar' ? 'TabBar项' : '快捷入口'
  return props.mode === 'add' ? `添加${typeText}` : `编辑${typeText}`
})

watch(() => props.visible, (val) => {
  if (val) {
    if (props.mode === 'edit' && props.initialData) {
      form.value = {
        menu_code: props.initialData.menu_code,
        menu_type: props.initialData.menu_type,
        title: props.initialData.title,
        subtitle: props.initialData.subtitle || '',
        icon: props.initialData.icon || '',
        icon_active: props.initialData.icon_active || '',
        link_type: props.initialData.link_type,
        link_value: props.initialData.link_value || '',
        link_params: props.initialData.link_params || {},
        show_condition: props.initialData.show_condition || {},
        badge_type: props.initialData.badge_type || 'none',
        badge_value: props.initialData.badge_value || '',
        sort_order: props.initialData.sort_order,
        is_visible: props.initialData.is_visible
      }
    } else {
      // 重置表单
      form.value = {
        menu_code: `${props.menuType}_${Date.now()}`,
        menu_type: props.menuType,
        title: '',
        subtitle: '',
        icon: '',
        icon_active: '',
        link_type: 'page',
        link_value: '',
        link_params: {},
        show_condition: {},
        badge_type: 'none',
        badge_value: '',
        sort_order: 0,
        is_visible: true
      }
    }
  }
})

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    emit('save', { ...form.value })
  } catch (err) {
    // 验证失败
  }
}

const handleClose = () => {
  dialogVisible.value = false
}
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="600px"
    @close="handleClose"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="菜单编码" prop="menu_code">
            <el-input v-model="form.menu_code" placeholder="唯一标识" :disabled="mode === 'edit'" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="标题" prop="title">
            <el-input v-model="form.title" placeholder="显示文字" maxlength="8" show-word-limit />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="图标URL">
            <el-input v-model="form.icon" placeholder="图标地址" />
          </el-form-item>
        </el-col>
        <el-col :span="12" v-if="menuType === 'tabbar'">
          <el-form-item label="选中图标">
            <el-input v-model="form.icon_active" placeholder="选中状态图标地址" />
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 图标预览 -->
      <el-form-item label="图标预览" v-if="form.icon">
        <div class="icon-preview">
          <div class="preview-item">
            <el-image :src="form.icon" fit="contain" />
            <span>默认</span>
          </div>
          <div class="preview-item" v-if="form.icon_active && menuType === 'tabbar'">
            <el-image :src="form.icon_active" fit="contain" />
            <span>选中</span>
          </div>
        </div>
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="跳转类型">
            <el-select v-model="form.link_type" placeholder="选择跳转类型" style="width: 100%">
              <el-option
                v-for="item in linkTypeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="跳转值" v-if="form.link_type !== 'none'">
            <el-input v-model="form.link_value" placeholder="页面路径/URL" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="角标类型">
            <el-select v-model="form.badge_type" placeholder="选择角标类型" style="width: 100%">
              <el-option
                v-for="item in badgeTypeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="角标值" v-if="form.badge_type === 'number' || form.badge_type === 'text'">
            <el-input v-model="form.badge_value" placeholder="角标显示内容" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="是否显示">
        <el-switch v-model="form.is_visible" active-text="显示" inactive-text="隐藏" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.icon-preview {
  display: flex;
  gap: 20px;
}

.preview-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.preview-item .el-image {
  width: 48px;
  height: 48px;
  border: 1px solid #eee;
  border-radius: 8px;
}

.preview-item span {
  font-size: 12px;
  color: #909399;
}
</style>
