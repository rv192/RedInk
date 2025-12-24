<template>
  <!-- 主题输入组合框 -->
  <div class="composer-container">
    <!-- 输入区域 -->
    <div class="composer-input-wrapper">
      <div class="search-icon-static">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M21 21L16.65 16.65M19 11C19 15.4183 15.4183 19 11 19C6.58172 19 3 15.4183 3 11C3 6.58172 6.58172 3 11 3C15.4183 3 19 6.58172 19 11Z" stroke="#999" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <textarea
        ref="textareaRef"
        :value="modelValue"
        @input="handleInput"
        class="composer-textarea"
        placeholder="输入主题，例如：秋季显白美甲..."
        @keydown.enter.prevent="handleEnter"
        :disabled="loading"
        rows="1"
      ></textarea>
    </div>

    <!-- 已上传图片预览 -->
    <div v-if="uploadedImages.length > 0" class="uploaded-images-preview">
      <div
        v-for="(img, idx) in uploadedImages"
        :key="idx"
        class="uploaded-image-item"
      >
        <img :src="img.preview" :alt="`图片 ${idx + 1}`" />
        <button class="remove-image-btn" @click="removeImage(idx)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
      <div class="upload-hint">
        这些图片将用于生成封面和内容参考
      </div>
    </div>

    <!-- URL 输入区域（仅当 firecrawlEnabled 时显示） -->
    <div v-if="firecrawlEnabled && showUrlInput" class="url-input-section">
      <div class="url-input-header">
        <div class="url-input-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="2" y1="12" x2="22" y2="12"></line>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
          </svg>
          <span>网页引用</span>
        </div>
        <button class="url-close-btn" @click="closeUrlInput" title="关闭">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="url-input-wrapper">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="url-link-icon">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
        </svg>
        <input
          type="url"
          v-model="urlInput"
          class="url-input"
          placeholder="粘贴网页链接，如：https://example.com/article"
          :disabled="loading || scrapeStatus === 'loading'"
          @input="handleUrlInput"
          @blur="handleUrlBlur"
        />
        <button
          v-if="urlInput && scrapeStatus !== 'loading'"
          class="url-clear-btn"
          @click="clearUrl"
          title="清除"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
        <div v-if="scrapeStatus === 'loading'" class="url-loading">
          <span class="spinner-xs"></span>
        </div>
      </div>

      <!-- 抓取结果展示 -->
      <div v-if="scrapeStatus === 'success' && scrapeResult" class="scrape-result">
        <div class="scrape-result-header">
          <div class="scrape-result-status success">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span>抓取成功</span>
          </div>
        </div>
        <div class="scrape-result-card">
          <div class="scrape-result-title">📄 {{ scrapeResult.data?.title || '未知标题' }}</div>
          <div class="scrape-result-meta">
            📊 共 {{ scrapeResult.data?.word_count?.toLocaleString() }} 字
          </div>
          <div class="scrape-result-preview">
            {{ getContentPreview(scrapeResult.data?.content) }}
          </div>
          <button
            class="scrape-detail-btn"
            @click="showContentDetail = !showContentDetail"
          >
            {{ showContentDetail ? '收起详情' : '👁 查看详情' }}
          </button>
        </div>

        <!-- 展开的详情 -->
        <div v-if="showContentDetail" class="scrape-detail-content">
          <div class="scrape-detail-text">
            {{ getContentDetail(scrapeResult.data?.content) }}
          </div>
          <div class="scrape-detail-note">
            （显示前 500 字，完整内容将用于生成大纲）
          </div>
        </div>
      </div>

      <!-- 抓取失败 -->
      <div v-if="scrapeStatus === 'error'" class="scrape-result">
        <div class="scrape-result-header">
          <div class="scrape-result-status error">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="15" y1="9" x2="9" y2="15"></line>
              <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
            <span>抓取失败</span>
          </div>
        </div>
        <div class="scrape-error-card">
          <div class="scrape-error-msg">{{ scrapeError }}</div>
          <div class="scrape-error-actions">
            <button class="btn-text" @click="retryScrape">🔄 重试</button>
            <button class="btn-text" @click="clearUrl">继续生成（不使用网页内容）</button>
          </div>
        </div>
      </div>

      <!-- 提示信息 -->
      <div v-if="scrapeStatus === 'idle' && urlInput" class="url-hint">
        💡 输入完成后会自动抓取网页内容作为创作参考
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="composer-toolbar">
      <div class="toolbar-left">
        <label class="tool-btn" :class="{ 'active': uploadedImages.length > 0 }" title="上传参考图">
          <input
            type="file"
            accept="image/*"
            multiple
            @change="handleImageUpload"
            :disabled="loading"
            style="display: none;"
          />
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <circle cx="8.5" cy="8.5" r="1.5"></circle>
            <polyline points="21 15 16 10 5 21"></polyline>
          </svg>
          <span v-if="uploadedImages.length > 0" class="badge-count">{{ uploadedImages.length }}</span>
        </label>

        <!-- 网页引用按钮（仅当 firecrawlEnabled 时显示） -->
        <button
          v-if="firecrawlEnabled"
          class="tool-btn"
          :class="{ 'active': showUrlInput || scrapeStatus === 'success' }"
          @click="toggleUrlInput"
          title="添加网页引用"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="2" y1="12" x2="22" y2="12"></line>
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
          </svg>
          <span v-if="scrapeStatus === 'success'" class="badge-check">✓</span>
        </button>
      </div>
      <div class="toolbar-right">
        <button
          class="btn btn-primary generate-btn"
          @click="$emit('generate')"
          :disabled="!modelValue.trim() || loading"
        >
          <span v-if="loading" class="spinner-sm"></span>
          <span v-else>生成大纲</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted, watch } from 'vue'
import { scrapeUrl, type ScrapeResult } from '../../api'

/**
 * 主题输入组合框组件
 *
 * 功能：
 * - 主题文本输入（自动调整高度）
 * - 参考图片上传（最多5张）
 * - 网页 URL 引用（需启用 Firecrawl）
 * - 生成按钮
 */

// 定义上传的图片类型
interface UploadedImage {
  file: File
  preview: string
}

// 定义 Props
const props = defineProps<{
  modelValue: string
  loading: boolean
  firecrawlEnabled: boolean
}>()

// 定义 Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'generate'): void
  (e: 'imagesChange', images: File[]): void
  (e: 'urlContentChange', content: ScrapeResult | null): void
}>()

// 输入框引用
const textareaRef = ref<HTMLTextAreaElement | null>(null)

// 已上传的图片
const uploadedImages = ref<UploadedImage[]>([])

// URL 输入相关状态
const showUrlInput = ref(false)
const urlInput = ref('')
const scrapeStatus = ref<'idle' | 'loading' | 'success' | 'error'>('idle')
const scrapeResult = ref<ScrapeResult | null>(null)
const scrapeError = ref('')
const showContentDetail = ref(false)

// 防抖定时器
let scrapeDebounceTimer: ReturnType<typeof setTimeout> | null = null

/**
 * 处理输入变化
 */
function handleInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
  adjustHeight()
}

/**
 * 处理回车键
 */
function handleEnter(e: KeyboardEvent) {
  if (e.shiftKey) return // 允许 Shift+Enter 换行
  emit('generate')
}

/**
 * 自动调整输入框高度
 */
function adjustHeight() {
  const el = textareaRef.value
  if (!el) return

  el.style.height = 'auto'
  const newHeight = Math.max(64, Math.min(el.scrollHeight, 200))
  el.style.height = newHeight + 'px'
}

/**
 * 处理图片上传
 */
function handleImageUpload(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files) return

  const files = Array.from(target.files)
  files.forEach((file) => {
    // 限制最多 5 张图片
    if (uploadedImages.value.length >= 5) {
      return
    }
    // 创建预览 URL
    const preview = URL.createObjectURL(file)
    uploadedImages.value.push({ file, preview })
  })

  // 通知父组件
  emitImagesChange()

  // 清空 input，允许重复选择同一文件
  target.value = ''
}

/**
 * 移除图片
 */
function removeImage(index: number) {
  const img = uploadedImages.value[index]
  // 释放预览 URL
  URL.revokeObjectURL(img.preview)
  uploadedImages.value.splice(index, 1)

  // 通知父组件
  emitImagesChange()
}

/**
 * 通知父组件图片变化
 */
function emitImagesChange() {
  const files = uploadedImages.value.map(img => img.file)
  emit('imagesChange', files)
}

/**
 * 清理所有预览 URL
 */
function clearPreviews() {
  uploadedImages.value.forEach(img => URL.revokeObjectURL(img.preview))
  uploadedImages.value = []
}

// ==================== URL 输入相关方法 ====================

/**
 * 切换 URL 输入区域显示
 */
function toggleUrlInput() {
  showUrlInput.value = !showUrlInput.value
}

/**
 * 关闭 URL 输入区域
 */
function closeUrlInput() {
  showUrlInput.value = false
  // 如果有成功抓取的内容，保留状态
}

/**
 * 处理 URL 输入变化（防抖）
 */
function handleUrlInput() {
  // 清除之前的定时器
  if (scrapeDebounceTimer) {
    clearTimeout(scrapeDebounceTimer)
  }

  // 重置状态
  if (!urlInput.value.trim()) {
    scrapeStatus.value = 'idle'
    scrapeResult.value = null
    emit('urlContentChange', null)
    return
  }

  // 设置新的防抖定时器
  scrapeDebounceTimer = setTimeout(() => {
    doScrape()
  }, 1500)
}

/**
 * URL 输入框失焦时立即抓取
 */
function handleUrlBlur() {
  if (urlInput.value.trim() && scrapeStatus.value === 'idle') {
    // 取消防抖，立即抓取
    if (scrapeDebounceTimer) {
      clearTimeout(scrapeDebounceTimer)
    }
    doScrape()
  }
}

/**
 * 执行抓取
 */
async function doScrape() {
  const url = urlInput.value.trim()
  if (!url) return

  // 简单的 URL 格式验证
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    scrapeStatus.value = 'error'
    scrapeError.value = '请输入有效的网页链接（以 http:// 或 https:// 开头）'
    return
  }

  scrapeStatus.value = 'loading'
  scrapeError.value = ''

  try {
    const result = await scrapeUrl(url)
    
    if (result.success && result.data) {
      scrapeStatus.value = 'success'
      scrapeResult.value = result
      emit('urlContentChange', result)
    } else {
      scrapeStatus.value = 'error'
      scrapeError.value = result.error || '抓取失败，请检查链接是否正确'
      emit('urlContentChange', null)
    }
  } catch (error: any) {
    scrapeStatus.value = 'error'
    scrapeError.value = error.response?.data?.error || error.message || '网络错误，请稍后重试'
    emit('urlContentChange', null)
  }
}

/**
 * 重试抓取
 */
function retryScrape() {
  doScrape()
}

/**
 * 清除 URL
 */
function clearUrl() {
  urlInput.value = ''
  scrapeStatus.value = 'idle'
  scrapeResult.value = null
  scrapeError.value = ''
  showContentDetail.value = false
  emit('urlContentChange', null)
}

/**
 * 获取内容预览（前 100 字）
 */
function getContentPreview(content?: string): string {
  if (!content) return ''
  const preview = content.substring(0, 100).replace(/\n/g, ' ')
  return preview + (content.length > 100 ? '...' : '')
}

/**
 * 获取内容详情（前 500 字）
 */
function getContentDetail(content?: string): string {
  if (!content) return ''
  return content.substring(0, 500)
}

/**
 * 清理 URL 相关状态
 */
function clearUrlState() {
  clearUrl()
  showUrlInput.value = false
}

// 组件卸载时清理
onUnmounted(() => {
  clearPreviews()
  if (scrapeDebounceTimer) {
    clearTimeout(scrapeDebounceTimer)
  }
})

// 暴露方法给父组件
defineExpose({
  clearPreviews,
  clearUrlState
})
</script>

<style scoped>
/* 组合框容器 */
.composer-container {
  background: white;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

/* 输入区域 */
.composer-input-wrapper {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.search-icon-static {
  flex-shrink: 0;
  padding-top: 8px;
  color: #999;
}

.composer-textarea {
  flex: 1;
  border: none;
  outline: none;
  font-size: 16px;
  line-height: 1.6;
  resize: none;
  min-height: 44px;
  max-height: 200px;
  padding: 8px 0;
  font-family: inherit;
  color: var(--text-main, #1a1a1a);
}

.composer-textarea::placeholder {
  color: #999;
}

.composer-textarea:disabled {
  background: transparent;
  color: #999;
}

/* 已上传图片预览 */
.uploaded-images-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 12px;
  align-items: center;
}

.uploaded-image-item {
  position: relative;
  width: 60px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.uploaded-image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-image-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
}

.uploaded-image-item:hover .remove-image-btn {
  opacity: 1;
}

.remove-image-btn:hover {
  background: var(--primary, #ff2442);
}

.upload-hint {
  flex: 1;
  font-size: 12px;
  color: var(--text-sub, #666);
  text-align: right;
}

/* URL 输入区域 */
.url-input-section {
  margin-top: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.url-input-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.url-input-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #334155;
}

.url-close-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.url-close-btn:hover {
  background: #e2e8f0;
  color: #64748b;
}

.url-input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 12px;
  transition: border-color 0.2s;
}

.url-input-wrapper:focus-within {
  border-color: var(--primary, #ff2442);
}

.url-link-icon {
  flex-shrink: 0;
  color: #94a3b8;
}

.url-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  color: var(--text-main, #1a1a1a);
}

.url-input::placeholder {
  color: #94a3b8;
}

.url-clear-btn {
  width: 20px;
  height: 20px;
  border: none;
  background: #f1f5f9;
  cursor: pointer;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.url-clear-btn:hover {
  background: #e2e8f0;
  color: #334155;
}

.url-loading {
  display: flex;
  align-items: center;
}

.spinner-xs {
  width: 14px;
  height: 14px;
  border: 2px solid #e2e8f0;
  border-top-color: var(--primary, #ff2442);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.url-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
}

/* 抓取结果 */
.scrape-result {
  margin-top: 12px;
}

.scrape-result-header {
  margin-bottom: 8px;
}

.scrape-result-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 4px;
}

.scrape-result-status.success {
  background: #dcfce7;
  color: #16a34a;
}

.scrape-result-status.error {
  background: #fee2e2;
  color: #dc2626;
}

.scrape-result-card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #e2e8f0;
}

.scrape-result-title {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 4px;
  line-height: 1.4;
}

.scrape-result-meta {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}

.scrape-result-preview {
  font-size: 13px;
  color: #475569;
  line-height: 1.5;
  margin-bottom: 8px;
}

.scrape-detail-btn {
  background: none;
  border: none;
  color: var(--primary, #ff2442);
  font-size: 13px;
  cursor: pointer;
  padding: 0;
}

.scrape-detail-btn:hover {
  text-decoration: underline;
}

.scrape-detail-content {
  margin-top: 12px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.scrape-detail-text {
  font-size: 13px;
  color: #475569;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.scrape-detail-note {
  margin-top: 8px;
  font-size: 11px;
  color: #94a3b8;
  font-style: italic;
}

.scrape-error-card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #fecaca;
}

.scrape-error-msg {
  font-size: 13px;
  color: #dc2626;
  margin-bottom: 12px;
}

.scrape-error-actions {
  display: flex;
  gap: 16px;
}

.btn-text {
  background: none;
  border: none;
  color: #64748b;
  font-size: 13px;
  cursor: pointer;
  padding: 0;
}

.btn-text:hover {
  color: var(--primary, #ff2442);
}

/* 工具栏 */
.composer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.toolbar-left {
  display: flex;
  gap: 8px;
}

.tool-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #f5f5f5;
  border: none;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: #eee;
  color: var(--primary, #ff2442);
}

.tool-btn.active {
  background: rgba(255, 36, 66, 0.1);
  color: var(--primary, #ff2442);
}

.badge-count {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  background: var(--primary, #ff2442);
  color: white;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.badge-check {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  background: #16a34a;
  color: white;
  border-radius: 9px;
  font-size: 10px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 生成按钮 */
.generate-btn {
  padding: 10px 24px;
  font-size: 15px;
  border-radius: 100px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 加载动画 */
.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
