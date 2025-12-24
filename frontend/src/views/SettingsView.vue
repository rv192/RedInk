<template>
  <div class="container">
    <div class="page-header">
      <h1 class="page-title">系统设置</h1>
      <p class="page-subtitle">配置文本生成和图片生成的 API 服务</p>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>加载配置中...</p>
    </div>

    <div v-else class="settings-container">
      <!-- 文本生成配置 -->
      <div class="card">
        <div class="section-header">
          <div>
            <h2 class="section-title">文本生成配置</h2>
            <p class="section-desc">用于生成小红书图文大纲</p>
          </div>
          <button class="btn btn-small" @click="openAddTextModal">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            添加
          </button>
        </div>

        <!-- 服务商列表表格 -->
        <ProviderTable
          :providers="textConfig.providers"
          :activeProvider="textConfig.active_provider"
          @activate="activateTextProvider"
          @edit="openEditTextModal"
          @delete="deleteTextProvider"
          @test="testTextProviderInList"
        />
      </div>

      <!-- 图片生成配置 -->
      <div class="card">
        <div class="section-header">
          <div>
            <h2 class="section-title">图片生成配置</h2>
            <p class="section-desc">用于生成小红书配图</p>
          </div>
          <button class="btn btn-small" @click="openAddImageModal">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            添加
          </button>
        </div>

        <!-- 服务商列表表格 -->
        <ProviderTable
          :providers="imageConfig.providers"
          :activeProvider="imageConfig.active_provider"
          @activate="activateImageProvider"
          @edit="openEditImageModal"
          @delete="deleteImageProvider"
          @test="testImageProviderInList"
        />
      </div>

      <!-- Firecrawl 配置（可选） -->
      <div class="card">
        <div class="section-header">
          <div>
            <h2 class="section-title">Firecrawl 配置（可选）</h2>
            <p class="section-desc">用于抓取网页内容，将 URL 转换为 LLM 可读格式</p>
          </div>
        </div>

        <div class="firecrawl-form">
          <!-- 启用开关 -->
          <div class="form-row">
            <label class="toggle-label">
              <input
                type="checkbox"
                v-model="firecrawlConfig.enabled"
                @change="saveFirecrawlConfig"
              />
              <span>启用 Firecrawl</span>
            </label>
          </div>

          <template v-if="firecrawlConfig.enabled">
            <!-- Base URL -->
            <div class="form-row">
              <label class="form-label">Base URL（本地部署必填，云端版本可留空）</label>
              <input
                type="text"
                class="form-input"
                v-model="firecrawlConfig.base_url"
                placeholder="https://api.firecrawl.dev 或 http://localhost:3002"
                @blur="saveFirecrawlConfig"
              />
            </div>

            <!-- API Key -->
            <div class="form-row">
              <label class="form-label">API Key（可选，部分本地部署无需 token）</label>
              <input
                type="password"
                class="form-input"
                v-model="firecrawlConfig.api_key"
                :placeholder="firecrawlConfig._has_api_key ? '•••••••• (已配置)' : '留空则不使用 API Key'"
                @blur="saveFirecrawlConfig"
              />
            </div>

            <!-- 测试连接按钮 -->
            <div class="form-row">
              <button
                class="btn btn-small"
                :disabled="testingFirecrawl"
                @click="testFirecrawlConnection"
              >
                {{ testingFirecrawl ? '测试中...' : '测试连接' }}
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 文本服务商弹窗 -->
    <ProviderModal
      :visible="showTextModal"
      :isEditing="!!editingTextProvider"
      :formData="textForm"
      :testing="testingText"
      :typeOptions="textTypeOptions"
      providerCategory="text"
      @close="closeTextModal"
      @save="saveTextProvider"
      @test="testTextConnection"
      @update:formData="updateTextForm"
    />

    <!-- 图片服务商弹窗 -->
    <ImageProviderModal
      :visible="showImageModal"
      :isEditing="!!editingImageProvider"
      :formData="imageForm"
      :testing="testingImage"
      :typeOptions="imageTypeOptions"
      @close="closeImageModal"
      @save="saveImageProvider"
      @test="testImageConnection"
      @update:formData="updateImageForm"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import ProviderTable from '../components/settings/ProviderTable.vue'
import ProviderModal from '../components/settings/ProviderModal.vue'
import ImageProviderModal from '../components/settings/ImageProviderModal.vue'
import {
  useProviderForm,
  textTypeOptions,
  imageTypeOptions
} from '../composables/useProviderForm'

/**
 * 系统设置页面
 *
 * 功能：
 * - 管理文本生成服务商配置
 * - 管理图片生成服务商配置
 * - 管理 Firecrawl 配置
 * - 测试 API 连接
 */

// 使用 composable 管理表单状态和逻辑
const {
  // 状态
  loading,
  testingText,
  testingImage,
  testingFirecrawl,

  // 配置数据
  textConfig,
  imageConfig,
  firecrawlConfig,

  // 文本服务商弹窗
  showTextModal,
  editingTextProvider,
  textForm,

  // 图片服务商弹窗
  showImageModal,
  editingImageProvider,
  imageForm,

  // 方法
  loadConfig,

  // 文本服务商方法
  activateTextProvider,
  openAddTextModal,
  openEditTextModal,
  closeTextModal,
  saveTextProvider,
  deleteTextProvider,
  testTextConnection,
  testTextProviderInList,
  updateTextForm,

  // 图片服务商方法
  activateImageProvider,
  openAddImageModal,
  openEditImageModal,
  closeImageModal,
  saveImageProvider,
  deleteImageProvider,
  testImageConnection,
  testImageProviderInList,
  updateImageForm,

  // Firecrawl 方法
  saveFirecrawlConfig,
  testFirecrawlConnection
} = useProviderForm()

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.settings-container {
  max-width: 900px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
  color: #1a1a1a;
}

.section-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
}

/* 按钮样式 */
.btn-small {
  padding: 6px 12px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #666;
}

/* Firecrawl 表单样式 */
.firecrawl-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-input {
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #007aff;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
}

.toggle-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}
</style>

