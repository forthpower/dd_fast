// 后台管理系统 JavaScript - 模型管理版本

// 清理所有现有通知 - 已禁用
function clearAllToasts() {
    // 通知功能已完全禁用
}

// 显示进度条
function showProgressBar(total) {
    // 移除已存在的进度条
    const existingBar = document.getElementById('sync-progress-bar');
    if (existingBar) {
        existingBar.remove();
    }
    
    const progressBar = document.createElement('div');
    progressBar.id = 'sync-progress-bar';
    progressBar.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 350px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        padding: 16px;
        z-index: 10000;
        font-family: "Microsoft YaHei", Arial, sans-serif;
        animation: slideInUp 0.3s ease-out;
    `;
    
    progressBar.innerHTML = `
        <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 14px; font-weight: 500; color: #374151;">🔄 正在同步模型</span>
            <span id="progress-text" style="font-size: 13px; color: #6b7280;">0/${total}</span>
        </div>
        <div style="background: #e5e7eb; border-radius: 4px; height: 8px; overflow: hidden;">
            <div id="progress-fill" style="background: linear-gradient(90deg, #0d9488, #14b8a6); height: 100%; width: 0%; transition: width 0.3s ease;"></div>
        </div>
        <div id="current-model" style="margin-top: 8px; font-size: 12px; color: #9ca3af; min-height: 18px;"></div>
    `;
    
    document.body.appendChild(progressBar);
    return progressBar;
}

// 更新进度条
function updateProgressBar(current, total, modelName) {
    const progressText = document.getElementById('progress-text');
    const progressFill = document.getElementById('progress-fill');
    const currentModel = document.getElementById('current-model');
    
    if (progressText) {
        progressText.textContent = `${current}/${total}`;
    }
    
    if (progressFill) {
        const percentage = (current / total) * 100;
        progressFill.style.width = `${percentage}%`;
    }
    
    if (currentModel && modelName) {
        currentModel.textContent = `当前: ${modelName}`;
    }
}

// 移除进度条
function removeProgressBar(success = true, message = '') {
    const progressBar = document.getElementById('sync-progress-bar');
    if (progressBar) {
        if (success) {
            // 成功时显示完成状态
            progressBar.style.background = '#f0fdf4';
            progressBar.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 20px;">✅</span>
                    <span style="font-size: 14px; color: #15803d; font-weight: 500;">${message || '同步完成！'}</span>
                </div>
            `;
        } else {
            // 失败时显示错误状态
            progressBar.style.background = '#fef2f2';
            progressBar.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 20px;">❌</span>
                    <span style="font-size: 14px; color: #dc2626; font-weight: 500;">${message || '同步失败！'}</span>
                </div>
            `;
        }
        
        // 2秒后移除
        setTimeout(() => {
            if (progressBar.parentNode) {
                progressBar.remove();
            }
        }, 2000);
    }
}

class AdminSystem {
    constructor() {
        this.models = []; // 存储所有模型
        this.currentModel = null; // 当前编辑的模型
        this.currentView = 'model-list'; // 当前视图：model-list 或 field-config
        this.modelIdToChipEl = new Map();
        this.parentMenus = []; // 存储父菜单列表
        this.init();
    }
    
    async init() {
        this.bindEvents();
        await this.loadModels();
        this.loadParentMenus();
        this.renderLeftModelMenu();
        this.showModelList();
    }
    
    bindEvents() {
        // 事件绑定
    }
    
    loadParentMenus() {
        // 从已有模型中提取所有不重复的父菜单
        const parentSet = new Set();
        this.models.forEach(model => {
            if (model.parent && model.parent.label && model.parent.name) {
                const key = `${model.parent.label}|||${model.parent.name}`;
                parentSet.add(key);
            }
        });
        
        this.parentMenus = Array.from(parentSet).map(key => {
            const [label, name] = key.split('|||');
            return { label, name };
        });
    }
    
    
    async loadModels() {
        try {
            const response = await fetch('/api/models');
            if (response.ok) {
                const data = await response.json();
                // 新的API返回格式: {success: true, models: [...]}
                if (data.success && Array.isArray(data.models)) {
                    this.models = data.models;
                } else if (Array.isArray(data)) {
                    // 兼容旧格式，直接返回数组
                    this.models = data;
                } else {
                    this.models = [];
                }
            } else {
                this.models = [];
            }
        } catch (error) {
            console.error('加载模型失败:', error);
            this.models = [];
        }
    }
    
    showModelList() {
        this.currentView = 'model-list';
        this.currentModel = null;
        document.getElementById('current-page').textContent = '模型列表';
        
        // 显示模型列表表格
        document.getElementById('model-list-view').style.display = 'block';
        document.getElementById('field-config-view').style.display = 'none';
        
        this.updateModelTable();
        this.renderLeftModelMenu();
        this.updateMenuActive('model-list');
    }
    
    showFieldManager() {
        this.currentView = 'field-config';
        
        // 更新面包屑显示 parent / model
        this.updateBreadcrumb();
        
        // 显示字段配置区域
        document.getElementById('model-list-view').style.display = 'none';
        document.getElementById('field-config-view').style.display = 'block';
        
        this.updateMenuActive('field-config');
        this.renderLeftModelMenu();
        this.updateConfigSections();
    }
    
    updateBreadcrumb() {
        const currentPageEl = document.getElementById('current-page');
        if (!this.currentModel) {
            if (currentPageEl) currentPageEl.textContent = '模型列表';
            return;
        }
        
        // 面包屑格式：parent / model
        let breadcrumbText = '';
        
        // 如果有父菜单，显示父菜单
        if (this.currentModel.parent && this.currentModel.parent.name) {
            breadcrumbText = this.currentModel.parent.name + ' / ';
        }
        
        // 添加模型label
        breadcrumbText += this.currentModel.label || this.currentModel.name || '未命名模型';
        
        if (currentPageEl) {
            currentPageEl.textContent = breadcrumbText;
        }
    }
    
    updateMenuActive(viewType) {
        // 更新菜单选中状态
        document.querySelectorAll('.submenu-item').forEach(item => {
            item.classList.remove('active');
        });
        
        if (viewType === 'model-list') {
            document.querySelector('.submenu-item').classList.add('active');
        } else {
            document.querySelectorAll('.submenu-item')[1].classList.add('active');
        }
    }
    
    updateModelTable() {
        const tbody = document.getElementById('model-table-body');
        tbody.innerHTML = '';
        
        if (this.models.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; color: #9ca3af; padding: 40px;">
                        No Data
                    </td>
                </tr>
            `;
            return;
        }
        
        this.models.forEach(model => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${model.name}</td>
                <td>${model.label}</td>
                <td>${model.fields.length}</td>
                <td>${model.primary_key}</td>
                <td>${model.createdAt}</td>
                <td>
                    <span style="color: #14b8a6; font-weight: 500;">${model.status}</span>
                </td>
                <td>
                    <button class="btn btn-primary btn-small" onclick="adminSystem.editModel(${model.id})" style="margin-right: 8px;">编辑</button>
                    <button class="btn btn-secondary btn-small" onclick="adminSystem.viewModel(${model.id})" style="margin-right: 8px;">查看</button>
                    <button class="btn btn-danger btn-small" onclick="adminSystem.deleteModel(${model.id})">删除</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }
    
    editModel(modelId) {
        const model = this.models.find(m => m.id === modelId);
        if (!model) return;
        
        this.currentModel = model;
        this.showFieldManager();
        this.updateBreadcrumb();
    }
    
    viewModel(modelId) {
        const model = this.models.find(m => m.id === modelId);
        if (!model) return;
        
        // 显示模型详情
        alert(`查看模型: ${model.label}\n字段数量: ${model.fields.length}\n主键: ${model.primary_key}`);
    }
    
    async deleteModel(modelId) {
        const model = this.models.find(m => m.id === modelId);
        if (!model) return;
        
        if (confirm(`确认删除模型 "${model.label}"？`)) {
            try {
                const response = await fetch(`/api/models/${modelId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    this.models = this.models.filter(m => m.id !== modelId);
                    this.loadParentMenus();
                    this.renderLeftModelMenu();
                    this.updateModelTable();
                    this.renderLeftModelMenu();
                    this.showSuccessMessage(`模型 "${model.label}" 已删除！`);
                } else {
                    throw new Error('删除失败');
                }
            } catch (error) {
                console.error('删除模型失败:', error);
                alert('删除模型失败，请重试');
            }
        }
    }
    
    addNewModel(autoShowFieldManager = true) {
        const newModel = {
            id: Date.now(),
            name: '',
            label: '',
            primary_key: '',
            entry: 'list',
            parent: '',
            action: [],
            fields: [],
            base_props: {},
            custom_actions: [],
            createdAt: new Date().toISOString().split('T')[0],
            status: 'active'
        };
        
        // 添加到模型列表
        this.models.push(newModel);
        this.currentModel = newModel;
        
        // 更新左侧显示
        this.renderLeftModelMenu();
        
        if (autoShowFieldManager) {
            this.showFieldManager();
            this.updateBreadcrumb();
        }
    }
    
    updateConfigSections() {
        if (!this.currentModel) return;
        
        const sections = document.querySelectorAll('.config-section');
        
        // 基础配置状态
        const basicConfig = sections[0];
        if (this.currentModel.name || this.currentModel.label || this.currentModel.primary_key) {
            basicConfig.classList.add('has-content');
            basicConfig.querySelector('.config-subtitle').textContent = `${this.currentModel.name || '未设置'} - ${this.currentModel.label || '未设置'}`;
        } else {
            basicConfig.classList.remove('has-content');
            basicConfig.querySelector('.config-subtitle').textContent = '点击配置模型名称、标签、主键等基础信息';
        }
        
        // 渲染字段卡片
        this.renderFieldCards();
    }
    
    renderFieldCards() {
        // 字段管理已集成到预览区域，这里只需要更新预览
        this.updatePreview();
    }
    
    updatePreview() {
        if (!this.currentModel) return;
        
        // 检查是否有各种动作
        const hasCreateAction = this.currentModel.action?.some(a => a.name === 'create');
        const hasEditAction = this.currentModel.action?.some(a => a.name === 'edit');
        const hasFormAction = hasCreateAction || hasEditAction;
        
        // 更新预览标签的显示状态
        const formTab = document.querySelector('.preview-tab:nth-child(2)');
        const editTab = document.querySelector('.preview-tab:nth-child(3)');
        const detailTab = document.querySelector('.preview-tab:nth-child(4)');
        
        // 表单页预览（create）
        if (formTab) {
            if (hasCreateAction) {
                formTab.style.display = 'block';
            } else {
                formTab.style.display = 'none';
                if (formTab.classList.contains('active')) {
                    document.querySelector('.preview-tab:nth-child(1)').click();
                }
            }
        }
        
        // 编辑页预览（edit）
        if (editTab) {
            if (hasEditAction) {
                editTab.style.display = 'block';
            } else {
                editTab.style.display = 'none';
                if (editTab.classList.contains('active')) {
                    document.querySelector('.preview-tab:nth-child(1)').click();
                }
            }
        }
        
        // 详情页预览（始终显示）
        if (detailTab) {
            detailTab.style.display = 'block';
        }
        
        this.renderListPreview();
        this.renderFormPreview();
        this.renderEditPreview();
        this.renderDetailPreview();
    }
    
    renderListPreview() {
        const previewList = document.getElementById('preview-list');
        if (!previewList) return;
        
        const allFields = this.currentModel.fields || [];
        const columnList = this.currentModel.base_props?.column_list || [];
        
        // 根据 column_list 筛选要显示的字段
        const fields = columnList.length > 0 
            ? allFields.filter(f => columnList.includes(f.name))
            : allFields;
        
        if (fields.length === 0) {
            previewList.innerHTML = `
                <div class="preview-empty">
                    <div class="preview-empty-icon">📋</div>
                    <div>暂无列表字段</div>
                    <div style="font-size: 12px; margin-top: 8px;">请在高级属性配置中设置 column_list</div>
                </div>
            `;
            return;
        }
        
        previewList.innerHTML = `
            <div style="overflow-x: auto;">
                <table class="preview-table field-horizontal-table">
                <thead>
                    <tr>
                            <th style="width: 120px; position: sticky; left: 0; background: #f8fafc; z-index: 1;"></th>
                            ${fields.map((field, index) => `
                                <th style="min-width: 150px;">
                                    ${field.label}
                                </th>
                            `).join('')}
                    </tr>
                </thead>
                <tbody>
                    <tr>
                            <td style="font-weight: 500; background: #f8fafc; position: sticky; left: 0; z-index: 1;">字段名称</td>
                            ${fields.map(field => `
                                <td><code style="background: #f3f4f6; padding: 2px 6px; border-radius: 3px; font-size: 12px;">${field.name}</code></td>
                            `).join('')}
                    </tr>
                    <tr>
                            <td style="font-weight: 500; background: #f8fafc; position: sticky; left: 0; z-index: 1;">字段类型</td>
                            ${fields.map(field => `
                                <td>
                                    <span style="background: #e0f2f1; color: #14b8a6; padding: 2px 8px; border-radius: 4px; font-size: 12px;">
                                        ${field.type}
                                    </span>
                        </td>
                            `).join('')}
                    </tr>
                </tbody>
            </table>
            </div>
        `;
    }
    
    renderFormPreview() {
        const previewForm = document.getElementById('preview-form');
        if (!previewForm) return;
        
        const fields = this.currentModel.fields || [];
        const formColumns = this.currentModel.base_props?.form_columns || fields.map(f => f.name);
        const hasCreateAction = this.currentModel.action?.some(a => a.name === 'create');
        const hasEditAction = this.currentModel.action?.some(a => a.name === 'edit');
        
        // 只有在配置了 create 或 edit 动作时才显示表单预览
        if (fields.length === 0 || (!hasCreateAction && !hasEditAction)) {
            previewForm.innerHTML = `
                <div class="preview-empty">
                    <div class="preview-empty-icon">📝</div>
                    <div>暂无字段或未配置表单动作</div>
                    <div style="font-size: 12px; margin-top: 8px;">添加字段并配置 create 或 edit 动作后将显示预览</div>
                </div>
            `;
            return;
        }
        
        // 获取应该显示的字段
        const displayFields = fields.filter(f => formColumns.includes(f.name));
        
        const createTemplate = this.currentModel.action?.find(a => a.name === 'create')?.template || '';
        const editTemplate = this.currentModel.action?.find(a => a.name === 'edit')?.template || '';
        
        previewForm.innerHTML = `
            <div style="margin-bottom: 12px;">
                <h4 style="margin: 0; font-size: 14px; color: #374151;">表单页效果预览 ${createTemplate || editTemplate ? '(' + (createTemplate || editTemplate) + ')' : ''}</h4>
            </div>
            <div class="preview-form">
                ${displayFields.map(f => `
                    <div class="preview-form-group">
                        <label class="preview-form-label">${f.label}${f.required ? ' *' : ''}</label>
                        <input type="text" class="preview-form-input" placeholder="${f.placeholder || '请输入' + f.label}" value="${f.default || ''}" readonly>
                    </div>
                `).join('')}
                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <div class="preview-actions">
                        <button class="preview-action-btn">取消</button>
                        <button class="preview-action-btn primary">提交</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderEditPreview() {
        const previewEdit = document.getElementById('preview-edit');
        if (!previewEdit) return;
        
        const fields = this.currentModel.fields || [];
        const editFormColumns = this.currentModel.base_props?.edit_form_columns || this.currentModel.base_props?.form_columns || fields.map(f => f.name);
        const hasEditAction = this.currentModel.action?.some(a => a.name === 'edit');
        
        if (fields.length === 0 || !hasEditAction) {
            previewEdit.innerHTML = `
                <div class="preview-empty">
                    <div class="preview-empty-icon">✏️</div>
                    <div>暂无字段或未配置编辑动作</div>
                    <div style="font-size: 12px; margin-top: 8px;">添加字段并配置 edit 动作后将显示预览</div>
                </div>
            `;
            return;
        }
        
        const displayFields = fields.filter(f => editFormColumns.includes(f.name));
        const editTemplate = this.currentModel.action?.find(a => a.name === 'edit')?.template || '';
        
        previewEdit.innerHTML = `
            <div style="margin-bottom: 12px;">
                <h4 style="margin: 0; font-size: 14px; color: #374151;">编辑页效果预览 ${editTemplate ? '(' + editTemplate + ')' : ''}</h4>
            </div>
            <div class="preview-form">
                ${displayFields.map(f => `
                    <div class="preview-form-group">
                        <label class="preview-form-label">${f.label}${f.required ? ' *' : ''}</label>
                        <input type="text" class="preview-form-input" placeholder="${f.placeholder || '请输入' + f.label}" value="${this.getFieldSampleValue(f)}" readonly>
                    </div>
                `).join('')}
                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <div class="preview-actions">
                        <button class="preview-action-btn">取消</button>
                        <button class="preview-action-btn primary">更新</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderDetailPreview() {
        const previewDetail = document.getElementById('preview-detail');
        if (!previewDetail) return;
        
        const fields = this.currentModel.fields || [];
        const detailColumns = this.currentModel.base_props?.column_details_list || fields.map(f => f.name);
        
        if (fields.length === 0) {
            previewDetail.innerHTML = `
                <div class="preview-empty">
                    <div class="preview-empty-icon">📄</div>
                    <div>暂无字段</div>
                    <div style="font-size: 12px; margin-top: 8px;">添加字段后将显示预览</div>
                </div>
            `;
            return;
        }
        
        const displayFields = fields.filter(f => detailColumns.includes(f.name));
        
        previewDetail.innerHTML = `
            <div style="margin-bottom: 12px;">
                <h4 style="margin: 0; font-size: 14px; color: #374151;">详情页效果预览</h4>
            </div>
            <div class="preview-form">
                ${displayFields.map(f => `
                    <div class="preview-form-group">
                        <label class="preview-form-label">${f.label}</label>
                        <div class="preview-form-input" style="background: #f9fafb; border-color: #e5e7eb;">${this.getFieldSampleValue(f)}</div>
                    </div>
                `).join('')}
                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <div class="preview-actions">
                        ${this.currentModel.action?.some(a => a.name === 'edit') ? '<button class="preview-action-btn primary">编辑</button>' : ''}
                        <button class="preview-action-btn">返回</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    getFieldSampleValue(field) {
        // 根据字段类型返回示例值
        const sampleValues = {
            'String': 'sample text',
            'Integer': '123',
            'Float': '12.34',
            'DateTime': '2024-01-01 12:00:00',
            'Boolean': 'true',
            'Select': '选项1',
            'Image': '🖼️',
            'File': '📄 file.pdf'
        };
        return sampleValues[field.type] || field.label;
    }
    
    openBasicConfig() {
        if (!this.currentModel) {
            this.addNewModel(false);
        }
        
        const modal = document.getElementById('config-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        modalTitle.textContent = '基础配置';
        modalBody.innerHTML = `
            <form id="basic-config-form">
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">模型名称 *</label>
                        <input type="text" class="form-input" id="model-name" value="${this.currentModel.name}" placeholder="例如: user">
            </div>
                    <div class="form-group">
                        <label class="form-label">显示标签 *</label>
                        <input type="text" class="form-input" id="model-label" value="${this.currentModel.label}" placeholder="例如: 用户管理">
            </div>
        </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">主键字段</label>
                        <input type="text" class="form-input" id="primary-key" value="${this.currentModel.primary_key}" placeholder="例如: user_id">
            </div>
                    <div class="form-group">
                        <label class="form-label">入口类型</label>
                        <select class="form-input" id="entry-type">
                            <option value="list" ${this.currentModel.entry === 'list' ? 'selected' : ''}>列表页 (list)</option>
                            <option value="add" ${this.currentModel.entry === 'add' ? 'selected' : ''}>添加页 (add)</option>
                        </select>
            </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">父级菜单</label>
                    <select class="form-input" id="parent-select" onchange="onParentSelectChange()">
                        <option value="">无父菜单（一级菜单）</option>
                        ${this.parentMenus.map(p => {
                            const selected = this.currentModel.parent && this.currentModel.parent.name === p.name ? 'selected' : '';
                            return `<option value="${p.name}" ${selected}>${p.name} (${p.label})</option>`;
                        }).join('')}
                        <option value="__custom__">➕ 自定义父菜单...</option>
                    </select>
                    
                    <div id="custom-parent-inputs" style="display: none; margin-top: 8px;">
                        <input type="text" class="form-input" id="parent-label" placeholder="父菜单标识（如：system）" style="margin-bottom: 8px;">
                        <input type="text" class="form-input" id="parent-name" placeholder="父菜单名称（如：系统管理）">
                    </div>
        </div>

                <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
                    <button type="button" class="btn btn-primary" onclick="saveBasicConfig()">保存</button>
                </div>
            </form>
        `;
        
        modal.style.display = 'flex';
        
        // 如果当前模型有自定义的父菜单（不在列表中），显示自定义输入框
        setTimeout(() => {
            const currentParent = this.currentModel.parent;
            if (currentParent && currentParent.name) {
                const existsInList = this.parentMenus.some(p => p.name === currentParent.name);
                if (!existsInList) {
                    // 自定义父菜单
                    document.getElementById('parent-select').value = '__custom__';
                    document.getElementById('custom-parent-inputs').style.display = 'block';
                    document.getElementById('parent-label').value = currentParent.label || '';
                    document.getElementById('parent-name').value = currentParent.name || '';
                }
            }
        }, 0);
    }
    
    openFieldConfig() {
        if (!this.currentModel) {
            this.addNewModel(false);
        }
        
        const modal = document.getElementById('config-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        modalTitle.textContent = '字段配置';
        modalBody.innerHTML = `
            <div>
                <div style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <h4 style="margin: 0; color: #374151;">字段列表</h4>
                        <button type="button" class="btn btn-primary" id="add-field-btn">
                            <span>➕</span>
                            <span>添加字段</span>
                        </button>
                    </div>
                    
                    <div id="fields-list" style="border: 1px solid #e5e7eb; border-radius: 6px; max-height: 300px; overflow-y: auto;">
                        ${this.currentModel.fields.length === 0 ? 
                            '<div style="text-align: center; padding: 40px; color: #9ca3af;">暂无字段，点击"添加字段"开始配置</div>' :
                            this.currentModel.fields.map(field => this.renderFieldItem(field)).join('')
                        }
            </div>
        </div>

                <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
                    <button type="button" class="btn btn-primary" onclick="saveFieldConfig()">保存</button>
                </div>
            </div>
        `;
        
        modal.style.display = 'flex';
        
        // 绑定添加字段按钮事件（使用 setTimeout 确保 DOM 已渲染）
        setTimeout(() => {
            const addFieldBtn = document.getElementById('add-field-btn');
            if (addFieldBtn) {
                addFieldBtn.onclick = function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    addField();
                };
            }
        }, 0);
    }
    
    renderFieldItem(field) {
        // 检查是否有常量引用标记
        const hasConstants = field._has_constants || field._constants_used;
        const constantRefs = field._constant_refs || field._constants_used || [];
        
        // 检查是否有解析问题
        const hasParsingIssues = field._has_parsing_issues;
        
        // 确定样式
        let fieldStyle = 'padding: 12px 8px; border-bottom: 1px solid #f3f4f6; display: flex; justify-content: space-between; align-items: center;';
        if (hasConstants) {
            fieldStyle += 'background: #fef3c7; border-left: 3px solid #f59e0b;';
        } else if (hasParsingIssues) {
            fieldStyle += 'background: #fee2e2; border-left: 3px solid #ef4444;';
        }
        
        // 构建警告标签
        let warningTags = '';
        if (hasConstants) {
            warningTags += '<span style="background: #f59e0b; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: normal;">常量引用</span>';
        }
        if (hasParsingIssues) {
            warningTags += '<span style="background: #ef4444; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: normal; margin-left: 4px;">⚠️ 解析问题</span>';
        }
        
        // 构建详细信息
        let detailInfo = '';
        if (hasConstants) {
            detailInfo += `<div style="font-size: 11px; color: #92400e; margin-top: 4px;">🔗 常量: ${constantRefs.join(', ')}</div>`;
        }
        if (hasParsingIssues) {
            detailInfo += `<div style="font-size: 11px; color: #dc2626; margin-top: 4px;">⚠️ 字段包含无法解析的内容，已跳过有问题的部分</div>`;
        }
        
        return `
            <div class="field-item" style="${fieldStyle}">
                <div style="flex: 1;">
                    <div style="font-weight: 500; color: #374151; display: flex; align-items: center; gap: 8px;">
                        ${field.name}
                        ${warningTags}
                    </div>
                    <div style="font-size: 12px; color: #6b7280;">${field.type} - ${field.label}</div>
                    ${detailInfo}
                </div>
                <div style="display: flex; gap: 8px;">
                    <button type="button" class="btn btn-secondary btn-small" onclick="editField(${field.id})">编辑</button>
                    <button type="button" class="btn btn-danger btn-small" onclick="removeField(${field.id})">删除</button>
                </div>
            </div>
        `;
    }
    
    openActionConfig() {
        if (!this.currentModel) {
            this.addNewModel(false);
        }
        
        const modal = document.getElementById('config-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        const getActionTemplate = (actionName) => {
            const action = this.currentModel.action?.find(a => a.name === actionName);
            return action?.template || '';
        };
        
        modalTitle.textContent = '动作配置';
        modalBody.innerHTML = `
            <form id="action-config-form">
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 16px 0; color: #374151;">基础动作</h4>
                    
                    <!-- 两列网格布局 -->
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                    <!-- List 动作 -->
                        <div style="padding: 12px 8px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fafbfc;">
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 500; margin-bottom: 8px;">
                            <input type="checkbox" id="action-list" ${this.hasAction('list') ? 'checked' : ''}>
                            📋 列表查看 (list)
                        </label>
                            <select class="form-input" id="template-list" style="margin-left: 20px;">
                            <option value="tablebase" ${getActionTemplate('list') === 'tablebase' ? 'selected' : ''}>tablebase - 基础列表模版</option>
                            <option value="batch_table" ${getActionTemplate('list') === 'batch_table' ? 'selected' : ''}>batch_table - 带批量操作的列表</option>
                        </select>
                            <small style="display: block; margin-left: 20px; margin-top: 4px; color: #6b7280; font-size: 12px;">显示数据列表，支持查询、排序、分页</small>
                    </div>
                    
                    <!-- Create 动作 -->
                        <div style="padding: 12px 8px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fafbfc;">
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 500; margin-bottom: 8px;">
                            <input type="checkbox" id="action-create" ${this.hasAction('create') ? 'checked' : ''}>
                            ➕ 创建 (create)
                        </label>
                            <select class="form-input" id="template-create" style="margin-left: 20px;">
                            <option value="formbase" ${getActionTemplate('create') === 'formbase' ? 'selected' : ''}>formbase - 基础添加表单模版</option>
                        </select>
                            <small style="display: block; margin-left: 20px; margin-top: 4px; color: #6b7280; font-size: 12px;">添加新数据的表单页面</small>
                    </div>
                    
                    <!-- Edit 动作 -->
                        <div style="padding: 12px 8px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fafbfc;">
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 500; margin-bottom: 8px;">
                            <input type="checkbox" id="action-edit" ${this.hasAction('edit') ? 'checked' : ''}>
                            ✏️ 编辑 (edit)
                        </label>
                            <select class="form-input" id="template-edit" style="margin-left: 20px;">
                            <option value="editbase" ${getActionTemplate('edit') === 'editbase' ? 'selected' : ''}>editbase - 基础编辑表单模版</option>
                            <option value="edit_single" ${getActionTemplate('edit') === 'edit_single' ? 'selected' : ''}>edit_single - 单独编辑模版（与添加表单不同）</option>
                        </select>
                            <small style="display: block; margin-left: 20px; margin-top: 4px; color: #6b7280; font-size: 12px;">编辑已有数据，edit_single用于添加和编辑表单完全不同的场景</small>
                    </div>
                    
                    <!-- Delete 动作 -->
                        <div style="padding: 12px 8px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fafbfc;">
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 500; margin-bottom: 8px;">
                            <input type="checkbox" id="action-delete" ${this.hasAction('delete') ? 'checked' : ''}>
                            🗑️ 删除 (delete)
                        </label>
                            <select class="form-input" id="template-delete" style="margin-left: 20px;">
                            <option value="button" ${getActionTemplate('delete') === 'button' ? 'selected' : ''}>button - 删除按钮模版</option>
                        </select>
                            <small style="display: block; margin-left: 20px; margin-top: 4px; color: #6b7280; font-size: 12px;">删除数据功能</small>
                    </div>
                    
                    <!-- Export 动作 -->
                        <div style="padding: 12px 8px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fafbfc;">
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 500; margin-bottom: 8px;">
                            <input type="checkbox" id="action-export" ${this.hasAction('export') ? 'checked' : ''}>
                            📥 导出 (export)
                        </label>
                            <select class="form-input" id="template-export" style="margin-left: 20px;">
                            <option value="exportbase" ${getActionTemplate('export') === 'exportbase' ? 'selected' : ''}>exportbase - 基础导出模版</option>
                        </select>
                            <small style="display: block; margin-left: 20px; margin-top: 4px; color: #6b7280; font-size: 12px;">导出数据到文件（CSV等）</small>
                    </div>
                    
                    <!-- Ajax 动作 -->
                        <div style="padding: 12px 8px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fafbfc;">
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 500; margin-bottom: 8px;">
                            <input type="checkbox" id="action-ajax" ${this.hasAction('ajax') ? 'checked' : ''}>
                            ⚡ Ajax表单 (ajax)
                        </label>
                            <select class="form-input" id="template-ajax" style="margin-left: 20px;">
                            <option value="ajaxbase" ${getActionTemplate('ajax') === 'ajaxbase' ? 'selected' : ''}>ajaxbase - 基础ajax表单模版</option>
                            <option value="filterform" ${getActionTemplate('ajax') === 'filterform' ? 'selected' : ''}>filterform - 带查询的ajax表单</option>
                        </select>
                            <small style="display: block; margin-left: 20px; margin-top: 4px; color: #6b7280; font-size: 12px;">Ajax表单提交，filterform支持查询后渲染第一条数据</small>
                    </div>
                    
                    <!-- Chart 动作 -->
                        <div style="padding: 12px 8px; border: 1px solid #e5e7eb; border-radius: 6px; background: #fafbfc;">
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 500; margin-bottom: 8px;">
                            <input type="checkbox" id="action-chart" ${this.hasAction('chart') ? 'checked' : ''}>
                            📊 图表 (chart)
                        </label>
                            <select class="form-input" id="template-chart" style="margin-left: 20px;">
                            <option value="chartbase" ${getActionTemplate('chart') === 'chartbase' ? 'selected' : ''}>chartbase - 图表模版</option>
                        </select>
                            <small style="display: block; margin-left: 20px; margin-top: 4px; color: #6b7280; font-size: 12px;">数据可视化图表展示</small>
                        </div>
            </div>
        </div>

                <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
                    <button type="button" class="btn btn-primary" onclick="saveActionConfig()">保存</button>
            </div>
            </form>
        `;
        
        modal.style.display = 'flex';
    }
    
    hasAction(actionName) {
        return this.currentModel.action.some(action => action.name === actionName);
    }
    
    openBasePropsConfig() {
        if (!this.currentModel) {
            this.addNewModel(false);
        }
        
        const modal = document.getElementById('config-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        const baseProps = this.currentModel.base_props || {};
        const fieldNames = this.currentModel.fields.map(f => f.name);
        
        // 如果没有字段，提示用户先添加字段
        if (fieldNames.length === 0) {
            alert('请先添加字段！');
            return;
        }
        
        // 生成可折叠的多选框HTML的辅助函数
        const generateFieldMultiSelect = (id, selectedFields, description, hint = '') => {
            const selected = selectedFields || [];
            const selectedCount = selected.length;
            const selectedText = selectedCount > 0 ? ` (已选 ${selectedCount} 个)` : ' (未选择)';
            
            return `
                <div class="form-group collapsible-field-group" style="margin-bottom: 0;">
                    <div class="field-select-header" onclick="toggleFieldSelector('${id}')" style="
                        display: flex; 
                        justify-content: space-between; 
                        align-items: center; 
                        padding: 10px 8px; 
                        background: #f8fafc; 
                        border: 1px solid #e5e7eb; 
                        border-radius: 6px; 
                        cursor: pointer;
                        transition: all 0.3s;
                    ">
                        <div>
                            <span style="font-weight: 500; color: #374151; font-size: 13px;">${description}</span>
                            <span style="color: #14b8a6; font-size: 12px; margin-left: 8px;">${selectedText}</span>
                    </div>
                        <span class="toggle-icon" style="color: #6b7280; transition: transform 0.3s;">▼</span>
                    </div>
                    ${hint ? `<small style="color: #6b7280; font-size: 12px; display: block; margin-top: 4px;">${hint}</small>` : ''}
                    <div id="${id}-selector" class="field-selector-content" style="display: none; margin-top: 8px;">
                        <div style="border: 1px solid #d1d5db; border-radius: 6px; padding: 8px; background: white; max-height: 200px; overflow-y: auto;">
                            ${fieldNames.map(fieldName => `
                                <label style="display: flex; align-items: center; gap: 6px; padding: 4px 0; cursor: pointer; font-size: 13px;">
                                    <input type="checkbox" 
                                        class="field-checkbox" 
                                        data-select-id="${id}" 
                                        value="${fieldName}" 
                                        ${selected.includes(fieldName) ? 'checked' : ''}
                                        onchange="updateFieldCount('${id}')"
                                        style="cursor: pointer;">
                                    <span style="color: #374151;">${fieldName}</span>
                                </label>
                            `).join('')}
                    </div>
                        <div style="margin-top: 8px; display: flex; gap: 8px;">
                            <button type="button" class="btn btn-secondary btn-small" onclick="toggleAllFields('${id}', true)">全选</button>
                            <button type="button" class="btn btn-secondary btn-small" onclick="toggleAllFields('${id}', false)">全不选</button>
                    </div>
                    </div>
                    </div>
            `;
        };
        
        // 生成可折叠的过滤器配置HTML
        const generateFilterConfig = (id, filterType, filterData, description, hint = '') => {
            const selectedCount = Object.keys(filterData || {}).length;
            const selectedText = selectedCount > 0 ? ` (已配置 ${selectedCount} 个字段)` : ' (未配置)';
            
            return `
                <div class="form-group collapsible-field-group" style="margin-bottom: 12px;">
                    <div class="field-select-header" onclick="toggleFieldSelector('${id}')" style="
                        display: flex; 
                        justify-content: space-between; 
                        align-items: center; 
                        padding: 10px 8px; 
                        background: #f8fafc; 
                        border: 1px solid #e5e7eb; 
                        border-radius: 6px; 
                        cursor: pointer;
                        transition: all 0.3s;
                    ">
                        <div>
                            <span style="font-weight: 500; color: #374151; font-size: 13px;">${description}</span>
                            <span style="color: #14b8a6; font-size: 12px; margin-left: 8px;">${selectedText}</span>
                    </div>
                        <span class="toggle-icon" style="color: #6b7280; transition: transform 0.3s;">▼</span>
                </div>
                    ${hint ? `<small style="color: #6b7280; font-size: 12px; display: block; margin-top: 4px;">${hint}</small>` : ''}
                    <div id="${id}-selector" class="field-selector-content" style="display: none; margin-top: 8px;">
                        <div id="${id}-container" style="border: 1px solid #d1d5db; border-radius: 6px; padding: 8px; background: white; max-height: 300px; overflow-y: auto;">
                            ${fieldNames.map(fieldName => {
                                const filters = filterData?.[fieldName] || [];
                                return `
                                    <div style="padding: 4px 0; border-bottom: 1px solid #f3f4f6;">
                                        <label style="display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 4px;">
                                            <input type="checkbox" 
                                                class="filter-field-checkbox" 
                                                data-filter-type="${filterType}" 
                                                value="${fieldName}" 
                                                ${filters.length > 0 ? 'checked' : ''}
                                                onchange="toggleFilterField(this)"
                                                style="cursor: pointer;">
                                            ${fieldName}
                                        </label>
                                        <div class="filter-operators" style="margin-left: 24px; display: ${filters.length > 0 ? 'flex' : 'none'}; gap: 8px; flex-wrap: wrap;">
                                            ${['$eq', '$like', '$gt', '$lt', '$gte', '$lte', '$in'].map(op => `
                                                <label style="font-size: 12px; cursor: pointer; color: #6b7280;">
                                                    <input type="checkbox" 
                                                        class="filter-operator-checkbox" 
                                                        data-field="${fieldName}" 
                                                        data-filter-type="${filterType}" 
                                                        value="${op}" 
                                                        ${filters.includes(op) ? 'checked' : ''}
                                                        style="cursor: pointer;">
                                                    ${op}
                                                </label>
                                            `).join('')}
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                </div>
            `;
        };
        
        // 获取action配置，用于条件显示
        const actions = this.currentModel.action || [];
        const hasAction = (actionName) => actions.some(a => a.name === actionName);
        const hasActionWithTemplate = (actionName, templateName) => actions.some(a => a.name === actionName && a.template === templateName);
        
        // 根据action配置决定显示哪些字段配置
        const showColumnList = hasAction('list');
        const showFormColumns = hasAction('create');
        const showEditFormColumns = hasActionWithTemplate('edit', 'edit_single');
        const showAjaxFormColumns = hasActionWithTemplate('ajax', 'ajaxbase');
        const showFilterFormColumns = hasActionWithTemplate('ajax', 'filterform');
        const showFormFilters = hasActionWithTemplate('ajax', 'filterform'); // form_filters 只在 filterform 模板时显示
        const showExportList = hasAction('export');
        
        modalTitle.textContent = 'Base Props 配置';
        modalBody.innerHTML = `
            <form id="baseprops-config-form">
                ${!showColumnList && !showFormColumns && !showEditFormColumns && !showAjaxFormColumns && !showFilterFormColumns && !showExportList ? `
                    <div style="padding: 20px; text-align: center; color: #6b7280; background: #f8fafc; border: 1px dashed #d1d5db; border-radius: 8px; margin-bottom: 20px;">
                        <div style="font-size: 14px; margin-bottom: 8px;">💡 提示</div>
                        <div style="font-size: 13px;">请先在"动作配置"中选择相应的操作（list、create、edit、export、ajax等），然后回到这里配置对应的字段。</div>
                    </div>
                ` : ''}
                
                <!-- 1. 字段配置 -->
                <div style="margin-bottom: 16px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                    <div onclick="toggleBasePropSection('fields')" style="cursor: pointer; padding: 12px 16px; background: linear-gradient(to bottom, #f8fafc, #f1f5f9); display: flex; justify-content: space-between; align-items: center; user-select: none;">
                        <div>
                            <h4 style="margin: 0; color: #374151; font-size: 14px; font-weight: 600;">1. 字段配置</h4>
                            <p style="margin: 0; color: #6b7280; font-size: 11px;">字段均为 fields 中配置的字段，按需使用</p>
                    </div>
                        <span id="bp-fields-toggle" style="font-size: 18px; color: #9ca3af; transition: transform 0.3s;">▼</span>
                </div>
                    <div id="bp-fields-content" style="display: none; padding: 16px; background: white;">
                    
                    ${!showColumnList && !showFormColumns && !showEditFormColumns && !showAjaxFormColumns && !showFilterFormColumns && !showExportList ? `
                        <div style="padding: 16px; text-align: center; color: #9ca3af; background: #fafafa; border: 1px solid #f3f4f6; border-radius: 6px; font-size: 13px;">
                            暂无可配置的字段列表项（根据已选择的 action 操作显示）
                        </div>
                    ` : ''}
                    
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                        ${showColumnList ? generateFieldMultiSelect('bp-column-list', baseProps.column_list || fieldNames, '列表页展示字段 (column_list)', '列表页要显示的字段') : ''}
                        
                        ${showFormColumns ? generateFieldMultiSelect('bp-form-columns', baseProps.form_columns || fieldNames, '添加编辑字段 (form_columns)', '与 create & edit 基础模版搭配使用') : ''}
                        
                        ${showEditFormColumns ? generateFieldMultiSelect('bp-edit-form-columns', baseProps.edit_form_columns || [], '单独编辑字段 (edit_form_columns)', '搭配 edit_single 模板使用') : ''}
                        
                        ${generateFieldMultiSelect('bp-column-details', baseProps.column_details_list || [], '详情页字段 (column_details_list)', '详情页展示字段')}
                        
                        ${showAjaxFormColumns ? generateFieldMultiSelect('bp-ajax-form-columns', baseProps.ajax_form_columns || [], 'Ajax表单字段 (ajax_form_columns)', '配置 ajax form 表单字段') : ''}
                        
                        ${showFilterFormColumns ? generateFieldMultiSelect('bp-filter-form-columns', baseProps.filter_form_columns || [], '查询表单字段 (filter_form_columns)', '搭配 filterform 模板使用') : ''}
                        
                        ${generateFieldMultiSelect('bp-column-editable', baseProps.column_editable_list || [], '行内编辑字段 (column_editable_list)', '支持在列表页直接编辑的字段')}
                        
                        ${generateFieldMultiSelect('bp-column-sortable', baseProps.column_sortable_list || [], '可排序字段 (column_sortable_list)', '列表页排序字段')}
                        
                        ${showExportList ? generateFieldMultiSelect('bp-export-list', baseProps.export_list || [], '导出字段 (export_list)', '指定导出文件的字段') : ''}
                        </div>
                    
                    ${showColumnList ? generateFilterConfig('bp-column-filters', 'column', baseProps.column_filters || {}, '可搜索字段 (column_filters)', '优先级为 base_props 中 filter 配置，支持操作符: $eq, $like, $gt, $lt, $gte, $lte, $in') : ''}
                    
                    ${showFormFilters ? generateFilterConfig('bp-form-filters', 'form', baseProps.form_filters || {}, '表单搜索字段 (form_filters)', '搭配 filterform 使用') : ''}
                        </div>
                    </div>
                    
                <!-- 2. 跳转配置 -->
                ${(hasAction('create') || hasAction('edit')) ? `
                    <div style="margin-bottom: 16px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                        <div onclick="toggleBasePropSection('jump')" style="cursor: pointer; padding: 12px 16px; background: linear-gradient(to bottom, #f8fafc, #f1f5f9); display: flex; justify-content: space-between; align-items: center; user-select: none;">
                            <div>
                                <h4 style="margin: 0; color: #374151; font-size: 14px; font-weight: 600;">2. 跳转配置</h4>
                                <p style="margin: 0; color: #6b7280; font-size: 11px;">配置表单提交后的跳转行为</p>
                    </div>
                            <span id="bp-jump-toggle" style="font-size: 18px; color: #9ca3af; transition: transform 0.3s;">▼</span>
                        </div>
                        <div id="bp-jump-content" style="display: none; padding: 16px; background: white;">
                    
                        <div class="form-grid">
                            ${hasAction('create') ? `
                    <div class="form-group">
                                    <label class="form-label">创建后跳转 (submit_jump)</label>
                                    <select class="form-input" id="bp-submit-jump">
                                        <option value="">默认（跳转到list）</option>
                                        <option value="detail" ${baseProps.custom_style?.submit_jump === 'detail' ? 'selected' : ''}>detail - 跳转到详情页</option>
                                    </select>
                                    <small style="color: #6b7280; font-size: 11px;">创建表单提交后跳转到detail，默认跳转list</small>
                    </div>
                            ` : ''}
                            ${hasAction('edit') ? `
                    <div class="form-group">
                        <label class="form-label">编辑后跳转 (submit_jump_edit)</label>
                        <select class="form-input" id="bp-submit-jump-edit">
                            <option value="">默认（停留在编辑页）</option>
                            <option value="list" ${baseProps.submit_jump_edit === 'list' ? 'selected' : ''}>list - 跳转到列表页</option>
                        </select>
                                    <small style="color: #6b7280; font-size: 11px;">编辑保存后跳转位置</small>
                    </div>
                            ` : ''}
                        </div>
                        </div>
                    </div>
                ` : ''}
                
                <!-- 3. 样式配置 -->
                <div style="margin-bottom: 16px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                    <div onclick="toggleBasePropSection('style')" style="cursor: pointer; padding: 12px 16px; background: linear-gradient(to bottom, #f8fafc, #f1f5f9); display: flex; justify-content: space-between; align-items: center; user-select: none;">
                        <div>
                            <h4 style="margin: 0; color: #374151; font-size: 14px; font-weight: 600;">3. 样式配置 (custom_style)</h4>
                            <p style="margin: 0; color: #6b7280; font-size: 11px;">页面展示样式和交互行为配置</p>
                    </div>
                        <span id="bp-style-toggle" style="font-size: 18px; color: #9ca3af; transition: transform 0.3s;">▼</span>
                </div>
                    <div id="bp-style-content" style="display: none; padding: 16px; background: white;">
                
                    <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">详情样式 (detail_style)</label>
                        <select class="form-input" id="bp-detail-style">
                                <option value="none">none - 不需要detail</option>
                                <option value="dropdown" ${baseProps.custom_style?.detail_style === 'dropdown' ? 'selected' : ''}>dropdown - 下拉式detail</option>
                            <option value="process" ${baseProps.custom_style?.detail_style === 'process' ? 'selected' : ''}>process - 流程图样式</option>
                        </select>
                            <small style="color: #6b7280; font-size: 11px;">process需配合process_details_list使用</small>
                    </div>
                    <div class="form-group">
                        <label class="form-label">表单提交样式 (form_submit_style)</label>
                        <select class="form-input" id="bp-form-submit-style">
                            <option value="">默认（显示提交按钮）</option>
                            <option value="none" ${baseProps.custom_style?.form_submit_style === 'none' ? 'selected' : ''}>none - 不显示提交按钮</option>
                        </select>
                            <small style="color: #6b7280; font-size: 11px;">form页是否展示提交按钮</small>
                        </div>
                    </div>
                    
                    <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">字段展示方式 (field_style)</label>
                        <select class="form-input" id="bp-field-style">
                                <option value="">默认（左右展示）</option>
                                <option value="top" ${baseProps.custom_style?.field_style === 'top' ? 'selected' : ''}>top - 上下展示</option>
                        </select>
                            <small style="color: #6b7280; font-size: 11px;">默认不写正常左右展示，top为上下展示</small>
                    </div>
                    <div class="form-group">
                            <label class="form-label">行内编辑样式 (editable_list_style)</label>
                            <select class="form-input" id="bp-editable-list-style">
                                <option value="">默认（单元格内编辑）</option>
                                <option value="alert" ${baseProps.custom_style?.editable_list_style === 'alert' ? 'selected' : ''}>alert - 弹出编辑框</option>
                        </select>
                            <small style="color: #6b7280; font-size: 11px;">行内编辑的样式类型</small>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">提交验证</label>
                        <div style="display: flex; flex-direction: column; gap: 6px;">
                            <label style="display: flex; align-items: center; gap: 6px; font-size: 13px;">
                                <input type="checkbox" id="bp-submit-alert" ${baseProps.custom_style?.submit_alert ? 'checked' : ''}>
                                提交不完整时弹出提示 (submit_alert)
                            </label>
                        </div>
                    </div>
                    
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">详情label宽度 (detail_label_width)</label>
                            <input type="number" class="form-input" id="bp-detail-label-width" value="${baseProps.custom_style?.detail_label_width || ''}" placeholder="40">
                            <small style="color: #6b7280; font-size: 11px;">单位px，下拉类型(dropdown)的detail中字段key的宽度</small>
                        </div>
                        <div class="form-group">
                            <label class="form-label">表单label宽度 (form_label_width)</label>
                            <input type="number" class="form-input" id="bp-form-label-width" value="${baseProps.custom_style?.form_label_width || ''}" placeholder="50">
                            <small style="color: #6b7280; font-size: 11px;">单位px，form页配置label的宽度</small>
                        </div>
                    </div>
                    
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">操作列宽度 (operation_width)</label>
                            <input type="number" class="form-input" id="bp-operation-width" value="${baseProps.custom_style?.operation_width || ''}" placeholder="300">
                            <small style="color: #6b7280; font-size: 11px;">单位px，列表页operation宽度配置</small>
                        </div>
                        <div class="form-group">
                            <label class="form-label">表格高度 (table_height)</label>
                            <input type="number" class="form-input" id="bp-table-height" value="${baseProps.custom_style?.table_height || ''}" placeholder="700">
                            <small style="color: #6b7280; font-size: 11px;">单位px，固定表头</small>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">固定列数 (table_column_fixed)</label>
                        <input type="number" class="form-input" id="bp-table-column-fixed" value="${baseProps.custom_style?.table_column_fixed || ''}" placeholder="1">
                        <small style="color: #6b7280; font-size: 11px;">固定第几列数据</small>
                    </div>
                    </div>
                </div>
                
                <!-- 4. 其他配置 -->
                <div style="margin-bottom: 16px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                    <div onclick="toggleBasePropSection('other')" style="cursor: pointer; padding: 12px 16px; background: linear-gradient(to bottom, #f8fafc, #f1f5f9); display: flex; justify-content: space-between; align-items: center; user-select: none;">
                        <div>
                            <h4 style="margin: 0; color: #374151; font-size: 14px; font-weight: 600;">4. 其他配置</h4>
                            <p style="margin: 0; color: #6b7280; font-size: 11px;">通用页面配置</p>
                        </div>
                        <span id="bp-other-toggle" style="font-size: 18px; color: #9ca3af; transition: transform 0.3s;">▼</span>
                    </div>
                    <div id="bp-other-content" style="display: none; padding: 16px; background: white;">
                    
                    <div class="form-grid">
                        <div class="form-group">
                            <label class="form-label">页面大小 (page_size)</label>
                            <input type="number" class="form-input" id="bp-page-size" value="${baseProps.page_size || 10}" placeholder="10">
                        </div>
                        <div class="form-group">
                            <label class="form-label">导出条数 (import_size)</label>
                            <input type="number" class="form-input" id="bp-import-size" value="${baseProps.import_size || 3000}" placeholder="3000">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">说明文本 (explain)</label>
                        <input type="text" class="form-input" id="bp-explain" value="${baseProps.explain || ''}" placeholder="模型解释说明">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">超时配置 (timeout)</label>
                        <textarea class="form-input" id="bp-timeout" rows="2" placeholder='{"list": 120, "create": 120}'>${baseProps.timeout ? JSON.stringify(baseProps.timeout, null, 2) : ''}</textarea>
                        <small style="color: #6b7280; font-size: 11px;">单位：秒，默认20秒，最大120秒。格式: {"list": 120}</small>
                    </div>
                    
                    <div style="padding: 12px; background: #f8fafc; border-radius: 6px; border: 1px solid #e5e7eb; margin-top: 16px;">
                        <h5 style="margin: 0 0 8px 0; color: #374151; font-size: 14px;">前端搜索配置 (filter_style)</h5>
                        <p style="margin: 0 0 12px 0; color: #6b7280; font-size: 11px;">启用前端搜索，关闭后端搜索。只针对当前页面假搜索，不实现假分页</p>
                        
                        <div class="form-grid">
                            <div class="form-group">
                                <label class="form-label">搜索类型 (filter_type)</label>
                                <select class="form-input" id="bp-filter-type">
                                    <option value="">默认（后端搜索）</option>
                                    <option value="front" ${baseProps.filter_style?.filter_type === 'front' ? 'selected' : ''}>front - 前端筛选页面数据</option>
                                    <option value="backend" ${baseProps.filter_style?.filter_type === 'backend' ? 'selected' : ''}>backend - 后端接口查询</option>
                                </select>
                                <small style="color: #6b7280; font-size: 11px;">front筛选页面数据，backend后端接口查询</small>
                            </div>
                            <div class="form-group">
                                <label class="form-label">全局搜索框 (filter_all)</label>
                                <div style="display: flex; align-items: center; gap: 8px; height: 38px;">
                                    <label style="display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer;">
                                        <input type="checkbox" id="bp-filter-all" ${baseProps.filter_style?.filter_all ? 'checked' : ''}>
                                        <span>展示全局搜索框</span>
                                    </label>
                                </div>
                                <small style="color: #6b7280; font-size: 11px;">是否展示全局搜索框（匹配model所有字段）</small>
                            </div>
                        </div>
                    </div>
                    
                    <div style="padding: 12px; background: #f8fafc; border-radius: 6px; border: 1px solid #e5e7eb; margin-top: 12px;">
                        <h5 style="margin: 0 0 8px 0; color: #374151; font-size: 14px;">编辑提交设置 (submit_style)</h5>
                        <p style="margin: 0 0 12px 0; color: #6b7280; font-size: 11px;">配置表单提交的样式和提示</p>
                        
                        <div class="form-grid">
                            <div class="form-group">
                                <label class="form-label">提交类型 (type)</label>
                                <select class="form-input" id="bp-submit-type">
                                    <option value="">默认</option>
                                    <option value="alert" ${baseProps.submit_style?.type === 'alert' ? 'selected' : ''}>alert - 弹出提示</option>
                                </select>
                                <small style="color: #6b7280; font-size: 11px;">提交类型，alert为弹出式提交</small>
                            </div>
                            <div class="form-group">
                                <label class="form-label">提示文案 (alert_content)</label>
                                <input type="text" class="form-input" id="bp-alert-content" value="${baseProps.submit_style?.alert_content || ''}" placeholder="whether to execute the current configuration？">
                                <small style="color: #6b7280; font-size: 11px;">提交时的提示文案</small>
                            </div>
                        </div>
                    </div>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
                    <button type="button" class="btn btn-primary" onclick="saveBasePropsConfig()">保存</button>
                </div>
            </form>
        `;
        
        modal.style.display = 'flex';
    }
    
    openCustomActionsConfig() {
        if (!this.currentModel) {
            this.addNewModel(false);
        }
        
        const modal = document.getElementById('config-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        const customActions = this.currentModel.custom_actions || [];
        
        modalTitle.textContent = 'Custom Actions 配置';
        modalBody.innerHTML = `
            <form id="customactions-config-form">
                <div style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <h4 style="margin: 0; color: #374151;">自定义动作列表</h4>
                        <button type="button" class="btn btn-primary btn-small" onclick="addCustomAction()">
                            <span>➕</span>
                            <span>添加动作</span>
                        </button>
                    </div>
                    
                    <div id="custom-actions-list" style="border: 1px solid #e5e7eb; border-radius: 6px; max-height: 400px; overflow-y: auto;">
                        ${customActions.length === 0 ? 
                            '<div style="text-align: center; padding: 40px; color: #9ca3af;">暂无自定义动作，点击"添加动作"开始配置</div>' :
                            customActions.map((action, idx) => this.renderCustomActionItem(action, idx)).join('')
                        }
                    </div>
                </div>
                
                <div style="padding: 16px; background: #f8fafc; border-radius: 6px; border: 1px solid #e5e7eb;">
                    <h5 style="margin: 0 0 8px 0; font-size: 14px; color: #374151;">自定义动作类型说明</h5>
                    <ul style="margin: 0; padding-left: 20px; font-size: 12px; color: #6b7280; line-height: 1.6;">
                        <li><strong>ajax</strong>: Ajax请求动作</li>
                        <li><strong>jump</strong>: 跳转动作（内部/外部/下载）</li>
                        <li><strong>alert</strong>: 弹框确认动作</li>
                        <li><strong>form</strong>: 二次弹窗表单</li>
                        <li><strong>qcr_code</strong>: 二维码生成</li>
                    </ul>
                </div>
                
                <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
                    <button type="button" class="btn btn-primary" onclick="saveCustomActionsConfig()">保存</button>
                </div>
            </form>
        `;
        
        modal.style.display = 'flex';
    }
    
    renderCustomActionItem(action, index) {
        return `
            <div class="custom-action-item" data-index="${index}" style="padding: 12px; border-bottom: 1px solid #f3f4f6; display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1;">
                    <div style="font-weight: 500; color: #374151;">${action.action_name || '未命名'}</div>
                    <div style="font-size: 12px; color: #6b7280;">
                        ${action.label || '无标签'} - ${action.action || '无类型'} 
                        ${action.location ? `(${action.location})` : ''}
                    </div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button type="button" class="btn btn-secondary btn-small" onclick="editCustomAction(${index})">编辑</button>
                    <button type="button" class="btn btn-danger btn-small" onclick="removeCustomAction(${index})">删除</button>
                </div>
            </div>
        `;
    }
    
    async generateAndCopy() {
        if (!this.currentModel) {
            alert('请先创建或选择一个模型！');
            return;
        }
        
        try {
            // 构建完整配置 - 按照Century Games规范
            // 清理字段：移除前端使用的id属性
            const cleanFields = this.currentModel.fields.map(field => {
                const { id, ...cleanField } = field;
                return cleanField;
            });
            
            const config = {
                name: this.currentModel.name || 'model_name',
                label: this.currentModel.label || 'label',
                primary_key: this.currentModel.primary_key || '',
                entry: this.currentModel.entry || 'list',
                parent: this.currentModel.parent || '',
                action: this.currentModel.action,
                fields: cleanFields,
                base_props: this.currentModel.base_props,
                custom_actions: this.currentModel.custom_actions
            };
            
            // 发送到后端处理
            const response = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP 错误: ${response.status}`);
            }
            
            const result = await response.json();
            
            // 格式化JSON
            const formattedJson = this.formatJSON(result);
            
            // 直接复制到剪贴板
            await this.copyToClipboard(formattedJson);
            
            // 显示成功提示
            this.showSuccessMessage('配置已复制到剪贴板！');
            
            // 重新加载模型列表以更新左侧菜单
            await this.loadModels();
            this.renderLeftModelMenu();
            
        } catch (error) {
            console.error('生成配置失败:', error);
            alert('生成配置失败，请检查后端是否正常运行');
        }
    }
    
    formatJSON(obj) {
        const indent = '    '; // 4 spaces
        let result = 'schema = {\n';
        
        // 顶层字段顺序
        const topLevelOrder = ['name', 'label', 'primary_key', 'entry', 'parent', 'action', 'fields', 'base_props', 'custom_actions'];
        
        // Fields 内字段顺序
        const fieldOrder = ['name', 'label', 'type', 'placeholder', 'explain', 'default', 'coerce', 'choices', 'copy_rule', 'tooltip', 'show_rule', 'method', 'style', 'config'];
        
        // Base props 字段顺序
        const basePropsOrder = [
            'form_columns', 'column_list', 'column_details_list', 'column_filters',
            'edit_form_columns', 'column_editable_list', 'column_sortable_list',
            'ajax_form_columns', 'filter_form_columns', 'form_filters',
            'export_list', 'page_size', 'import_size',
            'submit_jump', 'submit_jump_edit',
            'detail_style', 'form_submit_style', 'field_style', 'editable_list_style',
            'submit_alert', 'detail_label_width', 'form_label_width',
            'operation_width', 'table_height', 'table_column_fixed',
            'explain', 'timeout', 'filter_style', 'submit_style', 'custom_style'
        ];
        
        topLevelOrder.forEach((key, idx) => {
            if (!(key in obj)) return;
            
            const value = obj[key];
            
            if (key === 'action') {
                // Action 数组紧凑格式
                result += `${indent}"action": [`;
                value.forEach((action, i) => {
                    if (i === 0) {
                        result += `{"name": "${action.name}", "template": "${action.template}"}`;
                    } else {
                        result += `,\n${indent}           {"name": "${action.name}", "template": "${action.template}"}`;
                    }
                });
                result += '],\n';
            } else if (key === 'fields') {
                // Fields 数组格式化
                result += `${indent}"fields": [\n`;
                value.forEach((field, i) => {
                    result += `${indent}${indent}{\n`;
                    
                    // 按特定顺序排列字段属性
                    fieldOrder.forEach(prop => {
                        if (!(prop in field)) return;
                        const val = field[prop];
                        result += `${indent}${indent}${indent}"${prop}": ${this.formatValue(val, 3)},\n`;
                    });
                    
                    // 处理不在预定义顺序中的其他字段
                    Object.keys(field).forEach(prop => {
                        if (fieldOrder.includes(prop)) return;
                        const val = field[prop];
                        result += `${indent}${indent}${indent}"${prop}": ${this.formatValue(val, 3)},\n`;
                    });
                    
                    result += `${indent}${indent}}${i < value.length - 1 ? ',' : ','}\n`;
                });
                result += `${indent}],\n`;
            } else if (key === 'base_props') {
                // Base props 格式化
                result += `${indent}"base_props": {\n`;
                
                basePropsOrder.forEach(prop => {
                    if (!(prop in value)) return;
                    
                    const val = value[prop];
                    
                    // 特殊处理带注释的字段
                    if (prop === 'form_submit_style') {
                        result += `${indent}${indent}"${prop}": ${this.formatValue(val, 2)},  # form 页是否展示提交按钮\n`;
                    } else if (prop === 'timeout' && typeof val === 'object') {
                        // Timeout 紧凑格式
                        result += `${indent}${indent}"${prop}": {\n`;
                        Object.keys(val).forEach((key, idx, arr) => {
                            result += `${indent}${indent}${indent}"${key}": ${val[key]}`;
                            result += idx < arr.length - 1 ? ',\n' : '\n';
                        });
                        result += `${indent}${indent}},\n`;
                    } else if (prop === 'submit_style' && val.type) {
                        result += `${indent}${indent}"${prop}": {\n`;
                        result += `${indent}${indent}${indent}'type': '${val.type}',  # 提交类型. alert(弹出)\n`;
                        if (val.alert_content) {
                            result += `${indent}${indent}${indent}'alert_content': "${val.alert_content}",  # 提交时提示文案\n`;
                        }
                        result += `${indent}${indent}},\n`;
                    } else if (prop === 'custom_style') {
                        result += `${indent}${indent}"${prop}": ${this.formatValue(val, 2)}\n`;
                    } else {
                        result += `${indent}${indent}"${prop}": ${this.formatValue(val, 2)},\n`;
                    }
                });
                
                result += `\n${indent}},\n`;
            } else if (key === 'custom_actions') {
                // Custom actions 格式化
                result += `${indent}# 自定义action\n`;
                result += `${indent}"custom_actions": [\n`;
                value.forEach((action, i) => {
                    result += `${indent}${indent}{\n`;
                    
                    const actionOrder = ['action_name', 'label', 'action', 'params', 'location', 'icon', 'config', 'jump'];
                    actionOrder.forEach(prop => {
                        if (!(prop in action)) return;
                        const val = action[prop];
                        result += `${indent}${indent}${indent}"${prop}": ${this.formatValue(val, 3)},\n`;
                    });
                    
                    result += `${indent}${indent}}${i < value.length - 1 ? ',' : ','}\n`;
                });
                result += `${indent}]\n`;
            } else {
                // 普通字段
                result += `${indent}"${key}": ${this.formatValue(value, 1)},\n`;
            }
        });
        
        result += '}\n';
        return result;
    }
    
    formatValue(value, indentLevel) {
        const indent = '    '.repeat(indentLevel);
        
        if (value === null) return 'None';
        if (value === true) return 'True';
        if (value === false) return 'False';
        if (typeof value === 'string') {
            // 处理特殊字符串（如 "关闭"）
            if (value === '关闭') return '"关闭"';
            return `"${value}"`;
        }
        if (typeof value === 'number') return value;
        
        if (Array.isArray(value)) {
            if (value.length === 0) return '[]';
            
            // 检查是否是简单数组（字符串或数字）
            if (value.every(v => typeof v === 'string' || typeof v === 'number')) {
                // 短数组在一行，长数组换行
                // 使用单引号格式化字符串（符合 Python 风格）
                if (JSON.stringify(value).length < 60) {
                    return '[' + value.map(v => typeof v === 'string' ? `'${v}'` : v).join(', ') + ']';
                } else {
                    return '[\n' + indent + '    ' + 
                        value.map(v => typeof v === 'string' ? `'${v}'` : v).join(',\n' + indent + '    ') + 
                        '\n' + indent + ']';
                }
            }
            
            // 元组数组（choices）
            if (value.length > 0 && Array.isArray(value[0])) {
                return '[' + value.map(v => '(' + v.map(x => typeof x === 'string' ? `'${x}'` : x).join(', ') + ')').join(', ') + ']';
            }
            
            // 复杂数组
            return '[\n' + value.map(v => indent + '    ' + this.formatValue(v, indentLevel + 1)).join(',\n') + '\n' + indent + ']';
        }
        
        if (typeof value === 'object') {
            const keys = Object.keys(value);
            if (keys.length === 0) return '{}';
            
            // 检查是否是 copy_rule 的特殊格式 {"开启"} 或空对象 {}
            if (keys.length === 1 && keys[0] === 'status' && value.status === '开启') {
                return '{"开启"}';
            }
            
            // 紧凑对象格式（单行，如 column_filters 中的值）
            if (keys.length <= 3 && keys.every(k => typeof value[k] !== 'object' || Array.isArray(value[k]))) {
                const isSimple = keys.every(k => {
                    const v = value[k];
                    return typeof v === 'string' || typeof v === 'number' || 
                           (Array.isArray(v) && v.length <= 2);
                });
                
                if (isSimple) {
                    const items = keys.map(k => `"${k}": ${this.formatValue(value[k], indentLevel + 1)}`).join(', ');
                    return `{${items}}`;
                }
            }
            
            // 多行对象格式
            let result = '{\n';
            keys.forEach((key, idx, arr) => {
                result += `${indent}${indent}"${key}": ${this.formatValue(value[key], indentLevel + 1)}`;
                result += idx < arr.length - 1 ? ',\n' : '\n';
            });
            result += `${indent}}`;
            return result;
        }
        
        return JSON.stringify(value);
    }
    
    async copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
        } else {
            // fallback
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
        }
    }
    
    showSuccessMessage(message) {
        // 通知功能已完全禁用
    }
    
    closeModal() {
        document.getElementById('config-modal').style.display = 'none';
    }
    
    saveBasicConfig() {
        const name = document.getElementById('model-name').value.trim();
        const label = document.getElementById('model-label').value.trim();
        const primaryKey = document.getElementById('primary-key').value.trim();
        const entry = document.getElementById('entry-type').value;
        
        if (!name || !label) {
            alert('请填写必填项（模型名称、显示标签）');
            return;
        }
        
        this.currentModel.name = name;
        this.currentModel.label = label;
        this.currentModel.primary_key = primaryKey;
        this.currentModel.entry = entry;
        
        // 处理父菜单
        const parentSelect = document.getElementById('parent-select').value;
        
        if (parentSelect === '__custom__') {
            // 自定义父菜单
            const parentLabel = document.getElementById('parent-label').value.trim();
            const parentName = document.getElementById('parent-name').value.trim();
            
            if (parentLabel && parentName) {
                this.currentModel.parent = {
                    label: parentLabel,
                    name: parentName
                };
                
                // 添加到父菜单列表（如果不存在）
                const exists = this.parentMenus.some(p => p.name === parentName);
                if (!exists) {
                    this.parentMenus.push({ label: parentLabel, name: parentName });
                }
            } else {
                this.currentModel.parent = '';
            }
        } else if (parentSelect) {
            // 选择已有父菜单
            const selectedParent = this.parentMenus.find(p => p.name === parentSelect);
            if (selectedParent) {
                this.currentModel.parent = {
                    label: selectedParent.label,
                    name: selectedParent.name
                };
            } else {
                this.currentModel.parent = '';
            }
        } else {
            // 无父菜单
            this.currentModel.parent = '';
        }
        
        this.loadParentMenus();
        this.renderLeftModelMenu();
        this.renderLeftModelMenu();
        this.updateConfigSections();
        this.updatePreview();
        this.updateBreadcrumb();
        this.closeModal();
        this.showSuccessMessage('基础配置已保存！');
    }
    
    saveFieldConfig() {
        this.updateConfigSections();
        this.updatePreview();
        this.closeModal();
        this.showSuccessMessage('字段配置已保存！');
    }
    
    saveActionConfig() {
        const actions = [];
        const actionDefs = [
            { id: 'action-list', name: 'list', templateId: 'template-list' },
            { id: 'action-create', name: 'create', templateId: 'template-create' },
            { id: 'action-edit', name: 'edit', templateId: 'template-edit' },
            { id: 'action-delete', name: 'delete', templateId: 'template-delete' },
            { id: 'action-export', name: 'export', templateId: 'template-export' },
            { id: 'action-ajax', name: 'ajax', templateId: 'template-ajax' },
            { id: 'action-chart', name: 'chart', templateId: 'template-chart' }
        ];
        
        actionDefs.forEach(actionDef => {
            const checkbox = document.getElementById(actionDef.id);
            if (checkbox && checkbox.checked) {
                const templateSelect = document.getElementById(actionDef.templateId);
                const template = templateSelect ? templateSelect.value : '';
                actions.push({
                    name: actionDef.name,
                    template: template
                });
            }
        });
        
        this.currentModel.action = actions;
        this.updateConfigSections();
        this.updatePreview();
        this.closeModal();
        this.showSuccessMessage('动作配置已保存！');
    }
    
    saveModel() {
        if (!this.currentModel) return;
        
        // 如果是新模型，添加到模型列表
        const existingIndex = this.models.findIndex(m => m.id === this.currentModel.id);
        if (existingIndex === -1) {
            this.models.push(this.currentModel);
        } else {
            this.models[existingIndex] = this.currentModel;
        }
        
        this.updateModelTable();
        this.renderLeftModelMenu();
        this.showSuccessMessage('模型保存成功！');
    }

    renderLeftModelMenu() {
        this.renderModelTree();
    }
    
    updateActiveModel() {
        // 重置所有模型的激活状态
        document.querySelectorAll('.model-item').forEach(item => {
            item.style.background = '';
            item.classList.remove('active');
        });
        
        // 激活当前选中的模型
        if (this.currentModel) {
            const activeItem = document.querySelector(`[data-model-id="${this.currentModel.id}"]`);
            if (activeItem) {
                activeItem.style.background = 'rgb(110, 182, 172)';
                activeItem.classList.add('active');
            }
        }
    }
    
    renderModelTree() {
        const container = document.getElementById('model-tree-list');
        if (!container) return;
        container.innerHTML = '';
        
        // 获取所有父菜单（从parentMenus和models中合并）
        const modelParents = [...new Set(this.models
            .filter(m => m.parent && m.parent.name)
            .map(m => m.parent)
            .map(p => JSON.stringify(p))
        )].map(p => JSON.parse(p));
        
        // 合并parentMenus和modelParents，去重
        const allParents = [...this.parentMenus];
        modelParents.forEach(modelParent => {
            const exists = allParents.some(p => p.name === modelParent.name);
            if (!exists) {
                allParents.push(modelParent);
            }
        });
        
        const parentMenus = allParents;
        
        // 渲染父菜单及其子模型
        parentMenus.forEach(parent => {
            const parentItem = this.createParentMenuItem(parent);
            container.appendChild(parentItem);
            
            // 添加该父菜单下的子模型
            const childModels = this.models.filter(m => 
                m.parent && m.parent.name === parent.name
            );
            
            const subContainer = document.createElement('div');
            subContainer.id = `parent-models-${parent.name}`;
            subContainer.style.display = 'block';
            subContainer.style.background = 'rgb(225, 241, 239)';
            
            childModels.forEach(model => {
                const modelItem = this.createModelMenuItem(model, true);
                subContainer.appendChild(modelItem);
            });
            
            container.appendChild(subContainer);
        });
        
        // 渲染没有父菜单的模型
        const topLevelModels = this.models.filter(m => !m.parent || !m.parent.name);
        topLevelModels.forEach(model => {
            const item = this.createModelMenuItem(model);
            container.appendChild(item);
        });
        
        // 更新激活状态
        this.updateActiveModel();
    }
    
    createParentMenuItem(parent) {
        const parentItem = document.createElement('div');
        parentItem.className = 'submenu-item parent-menu';
        parentItem.style.cssText = 'position: relative;';
        parentItem.setAttribute('data-parent-name', parent.name);
        
        parentItem.innerHTML = `
            <div style="display: flex; align-items: center; width: 100%; gap: 8px;">
                <div class="menu-icon parent-arrow" style="cursor: pointer;">▼</div>
                <div class="menu-text" style="flex: 1; cursor: pointer;">${parent.name}</div>
                <div class="parent-menu-actions" style="opacity: 0; transition: opacity 0.2s; display: flex; gap: 4px;">
                    <span class="parent-edit-btn" style="cursor: pointer; font-size: 14px;" title="编辑">✏️</span>
                    <span class="parent-delete-btn" style="cursor: pointer; font-size: 14px; color: #ef4444;" title="删除">🗑️</span>
                </div>
            </div>
        `;
        
        // 点击整个父菜单区域展开/折叠（除了编辑和删除按钮）
        parentItem.addEventListener('click', (e) => {
            // 如果点击的是编辑或删除按钮，不触发展开/折叠
            if (e.target.closest('.parent-edit-btn') || e.target.closest('.parent-delete-btn')) {
                return;
            }
                toggleParentSubmenu(parent.name);
            });
        
        // 设置整个父菜单为可点击样式
        parentItem.style.cursor = 'pointer';
        
        // 点击编辑
        const editBtn = parentItem.querySelectorAll('.parent-menu-actions span')[0];
        if (editBtn) {
            editBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = this.parentMenus.findIndex(p => p.name === parent.name);
                if (index >= 0) editParentMenuInline(index);
            });
        }
        
        // 点击删除
        const deleteBtn = parentItem.querySelectorAll('.parent-menu-actions span')[1];
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = this.parentMenus.findIndex(p => p.name === parent.name);
                if (index >= 0) removeParentMenu(index);
            });
        }
        
        // 悬停显示操作按钮和改变背景色
        parentItem.addEventListener('mouseenter', () => {
            parentItem.style.background = 'rgb(110, 182, 172)';
            const actions = parentItem.querySelector('.parent-menu-actions');
            if (actions) actions.style.opacity = '1';
        });
        
        parentItem.addEventListener('mouseleave', () => {
            parentItem.style.background = 'rgb(194, 219, 216)';
            const actions = parentItem.querySelector('.parent-menu-actions');
            if (actions) actions.style.opacity = '0';
        });
        
        // 支持拖拽放入
        parentItem.addEventListener('dragover', (e) => {
            e.preventDefault();
            parentItem.style.background = 'rgba(20, 184, 166, 0.2)';
        });
        
        parentItem.addEventListener('dragleave', (e) => {
            parentItem.style.background = 'rgb(194, 219, 216)';
        });
        
        parentItem.addEventListener('drop', (e) => {
            e.preventDefault();
            parentItem.style.background = 'rgb(194, 219, 216)';
            
            const modelId = e.dataTransfer.getData('modelId');
            if (modelId) {
                this.assignModelToParent(modelId, parent);
            }
        });
        
        return parentItem;
    }
    
    createModelMenuItem(model, isChild = false) {
        const item = document.createElement('div');
        item.className = isChild ? 'submenu-item model-item child-model' : 'submenu-item model-item';
        item.style.position = 'relative';
        item.setAttribute('draggable', 'true');
        item.setAttribute('data-model-id', model.id);
        
        // 检查模型是否有常量引用
        const hasConstants = model._constants_used && model._constants_used.length > 0;
        const constantsCount = hasConstants ? model._constants_used.length : 0;
        
        // 检查模型是否有解析问题
        const hasParsingIssues = model._has_parsing_issues || model._has_field_issues || model._has_schema_issues || model._has_action_issues;
        
        // 构建警告标签
        let warningTags = '';
        if (hasConstants) {
            warningTags += `<span style="background: #f59e0b; color: white; padding: 1px 4px; border-radius: 2px; font-size: 9px;">常量${constantsCount}</span>`;
        }
        if (hasParsingIssues) {
            warningTags += `<span style="background: #ef4444; color: white; padding: 1px 4px; border-radius: 2px; font-size: 9px; margin-left: 2px;">⚠️</span>`;
        }
        
        item.innerHTML = `
            <div class="menu-icon">📄</div>
            <div class="menu-text" style="display: flex; align-items: center; gap: 6px;">
                ${model.label || model.name || '(未命名)'}
                ${warningTags}
            </div>
            <div class="model-menu-delete" style="
                opacity: 0;
                transition: opacity 0.2s;
                cursor: pointer;
                padding: 4px;
                color: #ef4444;
                font-size: 16px;
            " title="删除此模型">🗑️</div>
        `;
        
        // 点击模型名切换（不隐藏左侧列表）
        item.addEventListener('click', (e) => {
            if (e.target.classList.contains('model-menu-delete') || 
                e.target.closest('.model-menu-delete')) {
                return;
            }
            this.currentModel = model;
            this.showFieldManager();
            this.updateBreadcrumb();
            this.updateActiveModel();
            // 保持父菜单展开
            if (model.parent && model.parent.name) {
                const subContainer = document.getElementById(`parent-models-${model.parent.name}`);
                const parentItem = document.querySelector(`[data-parent-name="${model.parent.name}"]`);
                const arrow = parentItem?.querySelector('.parent-arrow');
                if (subContainer) subContainer.style.display = 'block';
                if (arrow) arrow.textContent = '▼';
            }
        });
        
        // 拖拽事件
        item.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('modelId', model.id);
            item.style.opacity = '0.5';
        });
        
        item.addEventListener('dragend', (e) => {
            item.style.opacity = '1';
        });
        
        // 悬停时显示删除按钮和改变背景色
        item.addEventListener('mouseenter', () => {
            // 只有在不是激活状态时才改变背景色
            if (!item.classList.contains('active')) {
                item.style.background = 'rgb(110, 182, 172)';
            }
            const deleteBtn = item.querySelector('.model-menu-delete');
            if (deleteBtn) deleteBtn.style.opacity = '1';
        });
        
        item.addEventListener('mouseleave', () => {
            // 只有在不是激活状态时才恢复背景色
            if (!item.classList.contains('active')) {
                item.style.background = '';
            }
            const deleteBtn = item.querySelector('.model-menu-delete');
            if (deleteBtn) deleteBtn.style.opacity = '0';
        });
        
        // 删除按钮点击事件
        const deleteBtn = item.querySelector('.model-menu-delete');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.currentModel = model;
                deleteCurrentModel();
            });
        }
        
        return item;
    }
    
    
    assignModelToParent(modelId, parent) {
        const model = this.models.find(m => m.id == modelId);
        if (!model) return;
        
        model.parent = {
            label: parent.label,
            name: parent.name
        };
        
        // 更新界面
        this.renderLeftModelMenu();
        
        // 如果是当前模型，更新面包屑
        if (this.currentModel && this.currentModel.id == modelId) {
            this.updateBreadcrumb();
        }
        
        this.showSuccessMessage(`模型 "${model.label}" 已移动到 "${parent.name}" 下`);
    }
    
    openParentMenuModal(editIndex = null) {
        const modal = document.getElementById('config-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');
        
        const isEdit = editIndex !== null;
        const parent = isEdit ? this.parentMenus[editIndex] : null;
        
        modalTitle.textContent = isEdit ? '编辑父菜单' : '添加父菜单';
        modalBody.innerHTML = `
            <form id="parent-menu-form">
                <div class="form-group">
                    <label class="form-label">父菜单标识 (label) *</label>
                    <input type="text" class="form-input" id="parent-label" 
                           value="${parent ? parent.label : ''}" 
                           placeholder="例如: system">
                    <small style="color: #6b7280; font-size: 12px;">英文标识，用于配置</small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">父菜单名称 (name) *</label>
                    <input type="text" class="form-input" id="parent-name" 
                           value="${parent ? parent.name : ''}" 
                           placeholder="例如: 系统管理">
                    <small style="color: #6b7280; font-size: 12px;">显示在菜单上的名称（中文）</small>
                </div>
                
                <div style="padding: 12px; background: #f0fdf4; border: 1px solid #22c55e; border-radius: 6px; margin-top: 16px;">
                    <p style="margin: 0; color: #166534; font-size: 12px; line-height: 1.6;">
                        ✅ ${isEdit ? '修改后，使用此父菜单的所有模型将自动更新' : '添加后，在模型的基础配置中可以选择此父菜单'}
                    </p>
                </div>
                
                <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
                    <button type="button" class="btn btn-primary" onclick="adminSystem.saveParentMenu(${editIndex})">${isEdit ? '保存修改' : '添加'}</button>
                </div>
            </form>
        `;
        
        modal.style.display = 'flex';
    }
    
    saveParentMenu(editIndex = null) {
        const label = document.getElementById('parent-label').value.trim();
        const name = document.getElementById('parent-name').value.trim();
        
        if (!label || !name) {
            alert('请填写完整的父菜单信息！');
            return;
        }
        
        const isEdit = editIndex !== null;
        
        if (isEdit) {
            // 编辑模式
            const oldParent = this.parentMenus[editIndex];
            this.parentMenus[editIndex] = { label, name };
            
            // 更新使用此父菜单的所有模型
            this.models.forEach(model => {
                if (model.parent && model.parent.name === oldParent.name) {
                    model.parent = { label, name };
                }
            });
            
            this.closeModal();
            this.renderLeftModelMenu();
            this.showSuccessMessage(`父菜单 "${name}" 已更新！`);
        } else {
            // 添加模式
            // 检查是否已存在
            const exists = this.parentMenus.some(p => p.name === name);
            if (exists) {
                alert('该父菜单名称已存在！');
                return;
            }
            
            // 添加到列表
            this.parentMenus.push({ label, name });
            this.closeModal();
            this.renderLeftModelMenu();
            this.showSuccessMessage(`父菜单 "${name}" 已添加！`);
        }
    }


}

// 全局函数
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}

function toggleSubmenu(element) {
    const submenu = element.nextElementSibling;
    const arrow = element.querySelector('.menu-arrow');
    
    if (submenu && submenu.classList.contains('submenu')) {
        submenu.classList.toggle('show');
        element.classList.toggle('expanded');
    }
}

function showModelList() {
    adminSystem.showModelList();
}

function showFieldManager() {
    adminSystem.showFieldManager();
}

function openBasicConfig() {
    adminSystem.openBasicConfig();
}

function openNewModelBaseConfig() {
    // 新建模型并显示基础配置弹窗
    adminSystem.addNewModel(false);
    adminSystem.openBasicConfig();
}

function deleteCurrentModel() {
    if (!adminSystem.currentModel) {
        alert('当前没有选中的模型！');
        return;
    }
    
    const modelName = adminSystem.currentModel.label || adminSystem.currentModel.name;
    const modelId = adminSystem.currentModel.id;
    
    // 确认删除
    if (!confirm(`确定要删除模型 "${modelName}" 吗？\n\n此操作不可恢复！`)) {
        return;
    }
    
    // 二次确认
    if (!confirm(`最后确认：真的要删除模型 "${modelName}" 及其所有配置吗？`)) {
        return;
    }
    
    // 从列表中移除
    adminSystem.models = adminSystem.models.filter(m => m.id !== modelId);
    
    // 如果模型已保存到数据库，也需要删除
    if (modelId && !isNaN(modelId) && modelId < Date.now() - 1000000000) {
        // 调用后端删除接口
        fetch(`/api/models/${modelId}`, {
            method: 'DELETE'
        }).then(response => {
            if (response.ok) {
                console.log('模型已从数据库删除');
            }
        }).catch(error => {
            console.error('删除数据库记录失败:', error);
        });
    }
    
    // 清空当前模型
    adminSystem.currentModel = null;
    
    // 更新父菜单列表
    adminSystem.loadParentMenus();
    adminSystem.renderLeftModelMenu();
    
    // 更新界面
    adminSystem.renderLeftModelMenu();
    adminSystem.showModelList();
    
    // 显示成功消息
    adminSystem.showSuccessMessage(`模型 "${modelName}" 已删除！`);
}

function toggleParentSubmenu(parentName) {
    const subContainer = document.getElementById(`parent-models-${parentName}`);
    const parentItem = document.querySelector(`[data-parent-name="${parentName}"]`);
    const arrow = parentItem?.querySelector('.menu-icon');
    
    if (subContainer) {
        if (subContainer.style.display === 'none') {
            subContainer.style.display = 'block';
            if (arrow) arrow.textContent = '▼';
        } else {
            subContainer.style.display = 'none';
            if (arrow) arrow.textContent = '▶';
        }
    }
}

function openParentMenuModal(editIndex = null) {
    adminSystem.openParentMenuModal(editIndex);
}

function addParentMenuQuick() {
    adminSystem.openParentMenuModal();
}

function editParentMenuInline(index) {
    adminSystem.openParentMenuModal(index);
}

function removeParentMenu(index) {
    const parent = adminSystem.parentMenus[index];
    
    // 检查是否有模型在使用
    const usingModels = adminSystem.models.filter(m => 
        m.parent && m.parent.name === parent.name
    );
    
    if (usingModels.length > 0) {
        const modelNames = usingModels.map(m => m.label || m.name).join('、');
        if (!confirm(`以下模型正在使用此父菜单：\n${modelNames}\n\n删除后这些模型将移到一级菜单。\n\n确认删除吗？`)) {
            return;
        }
        
        // 清除这些模型的父菜单
        usingModels.forEach(model => {
            model.parent = '';
        });
    }
    
    adminSystem.parentMenus.splice(index, 1);
    adminSystem.renderLeftModelMenu();
    adminSystem.renderLeftModelMenu();
    adminSystem.showSuccessMessage(`父菜单 "${parent.name}" 已删除！`);
}

async function autoSyncSchemas() {
    // 收集所有有源文件路径的模型
    const modelsToSync = adminSystem.models.filter(m => m.source_file);
    
    if (modelsToSync.length === 0) {
        alert('没有可同步的模型！\n\n只有通过"批量导入(文件夹)"功能导入的模型才能自动同步。');
        return;
    }
    
    // 显示进度条
    showProgressBar(modelsToSync.length);
    
    try {
        let successCount = 0;
        let failedCount = 0;
        
        // 逐个同步模型以显示进度
        for (let i = 0; i < modelsToSync.length; i++) {
            const model = modelsToSync[i];
            
            // 更新进度条
            updateProgressBar(i, modelsToSync.length, model.label || model.name);
            
            // 清理字段：移除前端使用的id属性
            const cleanFields = (model.fields || []).map(field => {
                const { id, ...cleanField } = field;
                return cleanField;
            });
            
            // 构建 schema 对象
            const schemaObj = {
                name: model.name || 'model_name',
                label: model.label || 'label',
                primary_key: model.primary_key || '',
                entry: model.entry || 'list',
                parent: model.parent || '',
                action: model.action || [],
                fields: cleanFields,
                base_props: model.base_props || {},
                custom_actions: model.custom_actions || []
            };
            
            const schemaContent = adminSystem.formatJSON(schemaObj);
            
            const syncData = [{
                file_path: model.source_file,
                schema_content: schemaContent,
                model_name: model.name
            }];
            
            // 远程同步配置（后端从数据库读取）
            const remoteSyncConfig = {
                enabled: i === modelsToSync.length - 1  // 只在最后一个模型时执行远程同步
            };
            
            try {
                const response = await fetch('/api/auto_sync', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        sync_data: syncData,
                        remote_sync: remoteSyncConfig
                    })
                });
                
                if (response.ok) {
                    successCount++;
                } else {
                    failedCount++;
                }
            } catch (err) {
                console.error(`同步模型 ${model.name} 失败:`, err);
                failedCount++;
            }
            
            // 小延迟以显示进度动画
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        // 更新最终进度
        updateProgressBar(modelsToSync.length, modelsToSync.length, '完成');
        
        // 构建完成消息
        let message = `同步完成！成功: ${successCount} 个`;
        if (failedCount > 0) {
            message += `，失败: ${failedCount} 个`;
        }
        
        // 显示完成状态
        removeProgressBar(true, message);
        
    } catch (error) {
        console.error('自动同步失败:', error);
        removeProgressBar(false, '同步失败: ' + error.message);
    }
}

function openImportModelDialog() {
    // 打开导入模型对话框
    const modal = document.getElementById('config-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    
    modalTitle.textContent = '从文件导入模型 & 仓库管理';
    modalBody.innerHTML = `
        <div style="margin-bottom: 20px;">
            <div style="background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 6px; padding: 16px; margin-bottom: 20px;">
                <h4 style="margin: 0 0 8px 0; color: #0369a1; font-size: 14px;">📋 支持的导入方式</h4>
                <ul style="margin: 0; padding-left: 20px; color: #0c4a6e; font-size: 13px; line-height: 1.8;">
                    <li><strong>单文件导入</strong> - 支持 Python Model、SQL DDL、JSON Schema</li>
                    <li><strong>批量导入 (文件夹)</strong> - 批量导入文件夹中的所有 .py schema 文件，自动识别父菜单</li>
                </ul>
            </div>
            
            <!-- 导入方式选择 -->
            <div class="form-group">
                <label class="form-label">导入方式</label>
                <select class="form-input" id="import-mode" onchange="toggleImportMode()">
                    <option value="folder" selected>批量导入 (文件夹)</option>
                    <option value="single">单文件导入</option>
                </select>
            </div>
            
            <!-- 单文件导入 -->
            <div id="single-file-import" style="display: none;">
            <div class="form-group">
                <label class="form-label">选择文件类型</label>
                <select class="form-input" id="import-file-type">
                    <option value="auto">自动识别</option>
                    <option value="python">Python Model (SQLAlchemy/Django)</option>
                    <option value="sql">SQL DDL (CREATE TABLE)</option>
                    <option value="json">JSON Schema</option>
                </select>
            </div>
            
            <div class="form-group">
                <label class="form-label">上传文件或粘贴内容</label>
                <input type="file" class="form-input" id="import-file-input" accept=".py,.sql,.json,.txt" style="margin-bottom: 12px;">
                <small style="display: block; color: #6b7280; font-size: 12px; margin-bottom: 8px;">或直接粘贴模型定义到下方文本框：</small>
                <textarea class="form-input" id="import-content" rows="15" placeholder="粘贴您的模型定义...

示例 1 - Python SQLAlchemy Model:
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, comment='用户名')
    email = db.Column(db.String(120), nullable=False, comment='邮箱')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

示例 2 - SQL DDL:
CREATE TABLE user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(80) NOT NULL COMMENT '用户名',
    email VARCHAR(120) NOT NULL COMMENT '邮箱',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

示例 3 - JSON Schema:
{
  &quot;title&quot;: &quot;User&quot;,
  &quot;properties&quot;: {
    &quot;username&quot;: {&quot;type&quot;: &quot;string&quot;, &quot;title&quot;: &quot;用户名&quot;},
    &quot;email&quot;: {&quot;type&quot;: &quot;string&quot;, &quot;title&quot;: &quot;邮箱&quot;}
  }
}"></textarea>
                </div>
            </div>
            
            <!-- 文件夹批量导入 -->
            <div id="folder-import" style="display: block;">
                <!-- 仓库管理 -->
                <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                    <h4 style="margin: 0 0 12px 0; color: #374151; font-size: 14px; font-weight: 600;">📦 已保存的仓库</h4>
                    <div id="repository-list" style="margin-bottom: 12px;">
                        <!-- 仓库列表将动态加载 -->
                    </div>
                    <button type="button" class="btn btn-secondary" onclick="loadRepositories()" style="font-size: 13px; padding: 6px 12px;">
                        🔄 刷新列表
                    </button>
                </div>
                
                <div class="form-group">
                    <label class="form-label">文件夹路径</label>
                    <input type="text" class="form-input" id="folder-path" placeholder="/path/to/your/schemas" 
                           style="font-family: monospace;">
                    <small style="display: block; color: #6b7280; font-size: 12px; margin-top: 4px;">
                        输入包含 schema .py 文件的文件夹绝对路径，系统将自动扫描所有 .py 文件并解析
                    </small>
                </div>
                
                <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 6px; padding: 12px; margin-top: 12px;">
                    <h5 style="margin: 0 0 6px 0; color: #92400e; font-size: 13px;">⚠️ 注意事项</h5>
                    <ul style="margin: 0; padding-left: 20px; color: #92400e; font-size: 12px; line-height: 1.6;">
                        <li>文件夹中的所有 .py 文件必须包含 <code>schema = {...}</code> 格式的配置</li>
                        <li>系统会自动识别 schema 中的 <code>parent</code> 字段并创建父菜单</li>
                        <li>相同 parent name 的模型会自动归类到同一父菜单下</li>
                        <li>导入成功后，路径将自动保存到仓库列表</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
            <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
            <button type="button" class="btn btn-primary" id="import-btn" onclick="importModel()">
                <span>🚀</span>
                <span id="import-btn-text">导入并解析</span>
            </button>
        </div>
    `;
    
    modal.style.display = 'flex';
    
    // 加载仓库列表
    loadRepositories();
    
    // 文件选择事件
    const fileInput = document.getElementById('import-file-input');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                document.getElementById('import-content').value = event.target.result;
            };
            reader.readAsText(file);
        }
    });
    }
}

// 加载快速导入的仓库列表
async function loadQuickRepositories() {
    try {
        const response = await fetch('/api/repositories');
        if (!response.ok) throw new Error('加载仓库列表失败');
        
        const data = await response.json();
        const repositories = data.repositories || [];
        const select = document.getElementById('quick-repo-select');
        
        if (!select) return;
        
        // 清空现有选项（保留第一个默认选项）
        select.innerHTML = '<option value="">-- 选择仓库 --</option>';
        
        // 添加仓库选项
        repositories.forEach(repo => {
            const option = document.createElement('option');
            option.value = repo.path;
            option.textContent = `${repo.name} (${repo.path})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载快速导入仓库列表失败:', error);
    }
}

// 快速导入仓库改变事件
async function onQuickRepoChange() {
    const select = document.getElementById('quick-repo-select');
    const folderPath = select.value;
    
    if (!folderPath) return;
    
    try {
        showToast('正在导入仓库...', 'info', 2000);
        
        // 调用后端批量导入接口
        const response = await fetch('/api/import_folder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                folder_path: folderPath
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 导入所有父菜单
            if (result.parent_menus && result.parent_menus.length > 0) {
                result.parent_menus.forEach(parent => {
                    const exists = adminSystem.parentMenus.some(p => p.name === parent.name);
                    if (!exists) {
                        adminSystem.parentMenus.push(parent);
                    }
                });
            }
            
            // 导入所有模型
            let importCount = 0;
            if (result.schemas && result.schemas.length > 0) {
                result.schemas.forEach(schema => {
                    // 为每个字段添加唯一 ID
                    schema.fields = schema.fields.map(f => ({
                        ...f,
                        id: Date.now() + Math.random()
                    }));
                    
                    // 创建新模型
                    const newModel = {
                        id: Date.now() + Math.random(),
                        ...schema,
                        createdAt: new Date().toISOString().split('T')[0],
                        source_file: schema.source_file || null,
                        source_folder: folderPath,
                        repo_name: schema.repo_name || result.repo_name || null
                    };
                    
                    adminSystem.models.push(newModel);
                    importCount++;
                });
            }
            
            // 刷新UI
            adminSystem.renderLeftModelMenu();
            
            // 构建成功消息
            let quickMsg = `快速导入成功！`;
            if (result.repo_name) {
                quickMsg = `📦 ${result.repo_name}: ` + quickMsg;
            }
            quickMsg += `\n导入了 ${result.parent_menus.length} 个父菜单和 ${importCount} 个模型`;
            
            showToast(quickMsg, 'success', 3000);
        } else {
            showToast('导入失败: ' + (result.error || '未知错误'), 'error');
        }
        
        // 重置选择框
        select.value = '';
        
    } catch (error) {
        console.error('快速导入失败:', error);
        showToast('快速导入失败: ' + error.message, 'error');
        select.value = '';
    }
}

// 加载仓库列表
async function loadRepositories() {
    try {
        const response = await fetch('/api/repositories');
        if (!response.ok) throw new Error('加载仓库列表失败');
        
        const data = await response.json();
        const repositories = data.repositories || [];
        const listContainer = document.getElementById('repository-list');
        
        if (!listContainer) return;
        
        if (repositories.length === 0) {
            listContainer.innerHTML = '<p style="color: #9ca3af; font-size: 13px; margin: 0;">暂无保存的仓库</p>';
            return;
        }
        
        listContainer.innerHTML = repositories.map(repo => `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px; background: white; border: 1px solid #e5e7eb; border-radius: 6px; margin-bottom: 8px;">
                <div style="flex: 1; cursor: pointer;" onclick="selectRepository('${repo.path}')">
                    <div style="font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 2px;">
                        ${repo.name}
                    </div>
                    <div style="font-size: 12px; color: #6b7280; font-family: monospace;">
                        ${repo.path}
                    </div>
                </div>
                <button type="button" class="btn btn-secondary" onclick="event.stopPropagation(); deleteRepository(${repo.id}, '${repo.name}')" 
                        style="font-size: 12px; padding: 4px 10px; background: #ef4444; color: white;">
                    🗑️ 删除
                </button>
            </div>
        `).join('');
    } catch (error) {
        console.error('加载仓库列表失败:', error);
        showToast('加载仓库列表失败: ' + error.message, 'error');
    }
}

// 选择仓库并填充路径
function selectRepository(path) {
    const folderPathInput = document.getElementById('folder-path');
    if (folderPathInput) {
        folderPathInput.value = path;
        showToast('已选择仓库: ' + path, 'success', 2000);
    }
}

// 删除仓库
async function deleteRepository(repoId, repoName) {
    if (!confirm(`确定要删除仓库 "${repoName}" 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/repositories/${repoId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '删除失败');
        }
        
        showToast(`仓库 "${repoName}" 已删除`, 'success', 2000);
        loadRepositories(); // 重新加载列表
        
        // 同时更新快速导入下拉框
        loadQuickRepositories();
    } catch (error) {
        console.error('删除仓库失败:', error);
        showToast('删除仓库失败: ' + error.message, 'error');
    }
}

// 保存仓库
async function saveRepository(path, repoName = null) {
    // 优先使用传入的仓库名，否则尝试从路径中提取 cg- 开头的文件夹名
    let name = repoName;
    
    if (!name) {
        const pathParts = path.split('/');
        for (const part of pathParts) {
            if (part.startsWith('cg-')) {
                name = part;
                break;
            }
        }
    }
    
    // 如果还是没有找到，使用最后一个文件夹名
    if (!name) {
        name = path.split('/').pop();
    }
    
    try {
        const response = await fetch('/api/repositories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, path })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '保存失败');
        }
        
        showToast(`仓库 "${name}" 已保存`, 'success', 2000);
        
        // 重新加载仓库列表
        if (document.getElementById('repository-list')) {
            loadRepositories();
        }
        
        // 同时更新快速导入下拉框
        loadQuickRepositories();
    } catch (error) {
        console.error('保存仓库失败:', error);
        // 不显示错误，因为可能是重复添加
    }
}

function toggleImportMode() {
    const mode = document.getElementById('import-mode').value;
    const singleImport = document.getElementById('single-file-import');
    const folderImport = document.getElementById('folder-import');
    const btnText = document.getElementById('import-btn-text');
    
    if (mode === 'folder') {
        singleImport.style.display = 'none';
        folderImport.style.display = 'block';
        btnText.textContent = '批量导入';
    } else {
        singleImport.style.display = 'block';
        folderImport.style.display = 'none';
        btnText.textContent = '导入并解析';
    }
}

async function importModel() {
    const mode = document.getElementById('import-mode').value;
    
    // 文件夹批量导入模式
    if (mode === 'folder') {
        const folderPath = document.getElementById('folder-path').value.trim();
        
        if (!folderPath) {
            alert('请输入文件夹路径！');
            return;
        }
        
        try {
            // 显示加载状态
            const importBtn = document.getElementById('import-btn');
            const originalText = importBtn.innerHTML;
            importBtn.innerHTML = '<span>⏳</span><span>批量导入中...</span>';
            importBtn.disabled = true;
            
            // 调用后端批量导入接口
            const response = await fetch('/api/import_folder', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    folder_path: folderPath
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 关闭模态框
                closeModal();
                
                // 导入所有父菜单
                if (result.parent_menus && result.parent_menus.length > 0) {
                    result.parent_menus.forEach(parent => {
                        const exists = adminSystem.parentMenus.some(p => p.name === parent.name);
                        if (!exists) {
                            adminSystem.parentMenus.push(parent);
                        }
                    });
                }
                
                // 导入所有模型
                let importCount = 0;
                if (result.schemas && result.schemas.length > 0) {
                    result.schemas.forEach(schema => {
                        // 为每个字段添加唯一 ID
                        schema.fields = schema.fields.map(f => ({
                            ...f,
                            id: Date.now() + Math.random()
                        }));
                        
                        // 创建新模型，保存源文件路径用于自动同步
                        const newModel = {
                            id: Date.now() + Math.random(),
                            ...schema,
                            createdAt: new Date().toISOString().split('T')[0],
                            source_file: schema.source_file || null,  // 保存源文件路径
                            source_folder: folderPath,  // 保存源文件夹路径
                            repo_name: schema.repo_name || result.repo_name || null  // 保存仓库名
                        };
                        
                        adminSystem.models.push(newModel);
                        importCount++;
                    });
                }
                
                // 刷新UI
                adminSystem.renderLeftModelMenu();
                
                // 构建成功消息
                let successMsg = `批量导入成功！`;
                if (result.repo_name) {
                    successMsg = `📦 ${result.repo_name}: ` + successMsg;
                }
                successMsg += `导入了 ${result.parent_menus.length} 个父菜单和 ${importCount} 个模型`;
                
                showToast(successMsg, 'success', 3000);
                
                // 保存仓库，传入仓库名
                await saveRepository(folderPath, result.repo_name);
            } else {
                showToast('导入失败: ' + (result.error || '未知错误'), 'error');
            }
            
            importBtn.innerHTML = originalText;
            importBtn.disabled = false;
            
        } catch (error) {
            console.error('批量导入失败:', error);
            alert('批量导入失败: ' + error.message);
            
            const importBtn = document.getElementById('import-btn');
            importBtn.innerHTML = '<span>🚀</span><span>批量导入</span>';
            importBtn.disabled = false;
        }
        
        return;
    }
    
    // 单文件导入模式（原有逻辑）
    const content = document.getElementById('import-content').value.trim();
    const fileType = document.getElementById('import-file-type').value;
    
    if (!content) {
        showToast('请上传文件或粘贴模型定义！', 'warning');
        return;
    }
    
    try {
        // 显示加载状态
        const importBtn = event.target.closest('button');
        const originalText = importBtn.innerHTML;
        importBtn.innerHTML = '<span>⏳</span><span>解析中...</span>';
        importBtn.disabled = true;
        
        // 调用后端解析接口
        const response = await fetch('/api/parse_model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: content,
                file_type: fileType
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 关闭模态框
            closeModal();
            
            let importedModels = [];
            
            // 处理多个模型或单个模型
            if (result.is_multiple && result.schemas) {
                // 多个模型
                for (const schema of result.schemas) {
                    // 为每个字段添加唯一 ID
                    schema.fields = schema.fields.map(f => ({
                        ...f,
                        id: Date.now() + Math.random()
                    }));
                    
                    // 创建新模型
                    const newModel = {
                        id: Date.now() + Math.random(),
                        ...schema,
                        createdAt: new Date().toISOString().split('T')[0],
                        status: 'active'
                    };
                    
                    // 添加到模型列表
                    adminSystem.models.push(newModel);
                    importedModels.push(newModel);
                }
                
                // 设置最后一个为当前模型
                if (importedModels.length > 0) {
                    adminSystem.currentModel = importedModels[importedModels.length - 1];
                }
                
                // 更新父菜单列表
                adminSystem.loadParentMenus();
                adminSystem.renderLeftModelMenu();
                
                // 更新界面
                adminSystem.renderLeftModelMenu();
                adminSystem.showFieldManager();
                adminSystem.updateBreadcrumb();
                
                // 显示成功消息
                adminSystem.showSuccessMessage(
                    `🎉 成功导入 ${importedModels.length} 个模型！`
                );
                
                // 显示详细信息
                setTimeout(() => {
                    const modelList = importedModels.map((m, i) => 
                        `${i + 1}. ${m.label} - ${m.fields.length} 个字段`
                    ).join('\n');
                    
                    alert(`成功导入 ${importedModels.length} 个模型！\n\n${modelList}\n\n您可以在左侧菜单中切换查看和编辑每个模型。`);
                }, 500);
                
            } else if (result.schema) {
                // 单个模型
                const schema = result.schema;
                
                // 为每个字段添加唯一 ID
                schema.fields = schema.fields.map(f => ({
                    ...f,
                    id: Date.now() + Math.random()
                }));
                
                // 创建新模型
                const newModel = {
                    id: Date.now(),
                    ...schema,
                    createdAt: new Date().toISOString().split('T')[0],
                    status: 'active'
                };
                
                // 添加到模型列表
                adminSystem.models.push(newModel);
                
                // 设置为当前模型
                adminSystem.currentModel = newModel;
                
                // 更新父菜单列表
                adminSystem.loadParentMenus();
                adminSystem.renderLeftModelMenu();
                
                // 更新界面
                adminSystem.renderLeftModelMenu();
                adminSystem.showFieldManager();
                adminSystem.updateBreadcrumb();
                
                // 显示成功消息
                adminSystem.showSuccessMessage(`成功导入模型 "${schema.label}"，包含 ${schema.fields.length} 个字段！`);
                
                // 提示用户可以进行修改
                setTimeout(() => {
                    if (confirm('模型已成功导入！\n\n您可以在当前页面查看和修改字段配置、动作配置等。\n\n是否现在查看基础配置？')) {
                        adminSystem.openBasicConfig();
                    }
                }, 500);
            } else {
                throw new Error('解析结果为空');
            }
        } else {
            throw new Error(result.error || '解析失败');
        }
    } catch (error) {
        console.error('导入失败:', error);
        alert('导入失败：' + error.message + '\n\n请检查文件格式是否正确。');
        
        // 恢复按钮状态
        const importBtn = event.target.closest('button');
        if (importBtn) {
            importBtn.innerHTML = '<span>🚀</span><span>导入并解析</span>';
            importBtn.disabled = false;
        }
    }
}

function openFieldConfig() {
    adminSystem.openFieldConfig();
}

function openActionConfig() {
    adminSystem.openActionConfig();
}

function openBasePropsConfig() {
    adminSystem.openBasePropsConfig();
}

function openCustomActionsConfig() {
    adminSystem.openCustomActionsConfig();
}

function generateAndCopy() {
    adminSystem.generateAndCopy();
}

function closeModal() {
    adminSystem.closeModal();
}

function onParentSelectChange() {
    const parentSelect = document.getElementById('parent-select');
    const customInputs = document.getElementById('custom-parent-inputs');
    
    if (parentSelect.value === '__custom__') {
        customInputs.style.display = 'block';
    } else {
        customInputs.style.display = 'none';
    }
}

function saveBasicConfig() {
    adminSystem.saveBasicConfig();
}

function saveFieldConfig() {
    adminSystem.saveFieldConfig();
}

function saveActionConfig() {
    adminSystem.saveActionConfig();
}

function saveBasePropsConfig() {
    const helper = (id) => document.getElementById(id)?.value.trim();
    const helperNum = (id) => {
        const val = document.getElementById(id)?.value;
        return val ? parseInt(val) : undefined;
    };
    const helperJSON = (id) => {
        const val = helper(id);
        if (!val) return undefined;
        try { return JSON.parse(val); } catch(e) { return undefined; }
    };
    
    // 辅助函数：从多选框获取选中的字段
    const getSelectedFields = (selectId) => {
        const checkboxes = document.querySelectorAll(`input.field-checkbox[data-select-id="${selectId}"]:checked`);
        return Array.from(checkboxes).map(cb => cb.value);
    };
    
    // 辅助函数：获取过滤器配置
    const getFilterConfig = (filterType) => {
        const result = {};
        const fieldCheckboxes = document.querySelectorAll(`input.filter-field-checkbox[data-filter-type="${filterType}"]:checked`);
        
        fieldCheckboxes.forEach(fieldCb => {
            const fieldName = fieldCb.value;
            const operatorCheckboxes = document.querySelectorAll(`input.filter-operator-checkbox[data-field="${fieldName}"][data-filter-type="${filterType}"]:checked`);
            const operators = Array.from(operatorCheckboxes).map(cb => cb.value);
            
            if (operators.length > 0) {
                result[fieldName] = operators;
            }
        });
        
        return result;
    };
    
    const baseProps = {};
    
    // 字段列表配置 - 从多选框读取
    const columnList = getSelectedFields('bp-column-list');
    if (columnList.length > 0) baseProps.column_list = columnList;
    
    const formColumns = getSelectedFields('bp-form-columns');
    if (formColumns.length > 0) baseProps.form_columns = formColumns;
    
    const editFormColumns = getSelectedFields('bp-edit-form-columns');
    if (editFormColumns.length > 0) baseProps.edit_form_columns = editFormColumns;
    
    const ajaxFormColumns = getSelectedFields('bp-ajax-form-columns');
    if (ajaxFormColumns.length > 0) baseProps.ajax_form_columns = ajaxFormColumns;
    
    const filterFormColumns = getSelectedFields('bp-filter-form-columns');
    if (filterFormColumns.length > 0) baseProps.filter_form_columns = filterFormColumns;
    
    const columnDetails = getSelectedFields('bp-column-details');
    if (columnDetails.length > 0) baseProps.column_details_list = columnDetails;
    
    const columnEditable = getSelectedFields('bp-column-editable');
    if (columnEditable.length > 0) baseProps.column_editable_list = columnEditable;
    
    const columnSortable = getSelectedFields('bp-column-sortable');
    if (columnSortable.length > 0) baseProps.column_sortable_list = columnSortable;
    
    const exportList = getSelectedFields('bp-export-list');
    if (exportList.length > 0) baseProps.export_list = exportList;
    
    // 搜索过滤配置 - 从多选框读取
    const columnFilters = getFilterConfig('column');
    if (Object.keys(columnFilters).length > 0) baseProps.column_filters = columnFilters;
    
    const formFilters = getFilterConfig('form');
    if (Object.keys(formFilters).length > 0) baseProps.form_filters = formFilters;
    
    // 页面配置
    const pageSize = helperNum('bp-page-size');
    if (pageSize) baseProps.page_size = pageSize;
    
    const importSize = helperNum('bp-import-size');
    if (importSize) baseProps.import_size = importSize;
    
    const explain = helper('bp-explain');
    if (explain) baseProps.explain = explain;
    
    const submitJumpEdit = helper('bp-submit-jump-edit');
    if (submitJumpEdit) baseProps.submit_jump_edit = submitJumpEdit;
    
    const timeout = helperJSON('bp-timeout');
    if (timeout && typeof timeout === 'object' && Object.keys(timeout).length > 0) {
        // 验证每个超时值不超过120秒
        const validatedTimeout = {};
        let hasInvalid = false;
        
        Object.keys(timeout).forEach(key => {
            const value = parseInt(timeout[key]);
            if (value > 120) {
                validatedTimeout[key] = 120;
                hasInvalid = true;
            } else if (value < 1) {
                validatedTimeout[key] = 1;
                hasInvalid = true;
            } else {
                validatedTimeout[key] = value;
            }
        });
        
        if (hasInvalid) {
            alert('超时配置值必须在1-120秒之间，已自动调整超出范围的值');
        }
        
        baseProps.timeout = validatedTimeout;
    }
    
    // 样式配置
    const customStyle = {};
    
    const detailStyle = helper('bp-detail-style');
    if (detailStyle && detailStyle !== 'none') customStyle.detail_style = detailStyle;
    
    const formSubmitStyle = helper('bp-form-submit-style');
    if (formSubmitStyle) customStyle.form_submit_style = formSubmitStyle;
    
    const fieldStyle = helper('bp-field-style');
    if (fieldStyle) customStyle.field_style = fieldStyle;
    
    const editableListStyle = helper('bp-editable-list-style');
    if (editableListStyle) customStyle.editable_list_style = editableListStyle;
    
    const submitJump = helper('bp-submit-jump');
    if (submitJump) customStyle.submit_jump = submitJump;
    
    const submitAlert = document.getElementById('bp-submit-alert')?.checked;
    if (submitAlert) customStyle.submit_alert = true;
    
    const detailLabelWidth = helperNum('bp-detail-label-width');
    if (detailLabelWidth) customStyle.detail_label_width = detailLabelWidth;
    
    const formLabelWidth = helperNum('bp-form-label-width');
    if (formLabelWidth) customStyle.form_label_width = formLabelWidth;
    
    const operationWidth = helperNum('bp-operation-width');
    if (operationWidth) customStyle.operation_width = operationWidth;
    
    const tableHeight = helperNum('bp-table-height');
    if (tableHeight) customStyle.table_height = tableHeight;
    
    const tableColumnFixed = helperNum('bp-table-column-fixed');
    if (tableColumnFixed) customStyle.table_column_fixed = tableColumnFixed;
    
    if (Object.keys(customStyle).length > 0) {
        baseProps.custom_style = customStyle;
    }
    
    // 前端搜索配置 (filter_style)
    const filterType = helper('bp-filter-type');
    const filterAll = document.getElementById('bp-filter-all')?.checked;
    if (filterType || filterAll) {
        baseProps.filter_style = {};
        if (filterType) baseProps.filter_style.filter_type = filterType;
        if (filterAll) baseProps.filter_style.filter_all = true;
    }
    
    // 编辑提交设置 (submit_style)
    const submitType = helper('bp-submit-type');
    const alertContent = helper('bp-alert-content');
    if (submitType || alertContent) {
        baseProps.submit_style = {};
        if (submitType) baseProps.submit_style.type = submitType;
        if (alertContent) baseProps.submit_style.alert_content = alertContent;
    }
    
    adminSystem.currentModel.base_props = baseProps;
    adminSystem.updateConfigSections();
    adminSystem.closeModal();
    adminSystem.showSuccessMessage('Base Props 配置已保存！');
}

function saveCustomActionsConfig() {
    // custom_actions 在 addCustomAction 中已经动态更新
    adminSystem.closeModal();
    adminSystem.showSuccessMessage('Custom Actions 配置已保存！');
}

function addCustomAction() {
    showCustomActionDialog();
}

function editCustomAction(index) {
    const action = adminSystem.currentModel.custom_actions[index];
    showCustomActionDialog(action, index);
}

// 显示自定义动作配置对话框
function showCustomActionDialog(existingAction = null, editIndex = null) {
    const modal = document.getElementById('config-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    
    modalTitle.textContent = existingAction ? '编辑自定义动作' : '添加自定义动作';
    
    // 功能模板定义
    const templates = {
        copy: {
            name: '复制',
            icon: '📋',
            action: {
                action_name: 'copy',
                label: '复制',
                action: 'ajax',
                params: [],
                location: 'list'
            }
        },
        download_ajax: {
            name: '下载 (AJAX)',
            icon: '⬇️',
            action: {
                action_name: 'download',
                label: '下载',
                action: 'ajax',
                params: ['id'],
                location: 'list',
                config: {
                    type: 'download',
                    return_key: 'url'
                }
            }
        },
        download_jump: {
            name: '下载 (直接)',
            icon: '💾',
            action: {
                action_name: 'download',
                label: 'Download',
                action: 'jump',
                params: [],
                jump: {
                    type: 'download',
                    href: ''
                },
                location: 'list'
            }
        },
        qr_code: {
            name: '二维码',
            icon: '📱',
            action: {
                action_name: 'qr_code',
                label: 'QR Code',
                action: 'qcr_code',
                params: ['id'],
                location: 'list',
                config: {
                    type: 'url',
                    href: 'https://example.com'
                }
            }
        },
        inner_jump: {
            name: '内部跳转',
            icon: '🔗',
            action: {
                action_name: 'inner_jump',
                label: '跳转',
                action: 'jump',
                params: [],
                jump: {
                    type: 'inner',
                    href: ''
                },
                location: 'list'
            }
        },
        outer_jump: {
            name: '外部跳转',
            icon: '🌐',
            action: {
                action_name: 'outer_jump',
                label: '预览',
                action: 'jump',
                params: [],
                jump: {
                    type: 'outer',
                    href: 'http://'
                },
                location: 'list'
            }
        },
        alert: {
            name: '弹框确认',
            icon: '⚠️',
            action: {
                action_name: 'alert',
                label: '确认',
                action: 'alert',
                params: [],
                alert: {
                    content: '确定要执行该操作吗？',
                    content_field: []
                },
                location: 'outer_list',
                icon: 'el-icon-warning'
            }
        },
        form: {
            name: '二次弹窗',
            icon: '📝',
            action: {
                action_name: 'form',
                label: '编辑',
                action: 'form',
                params: [],
                form_fields: [],
                location: 'outer_list',
                icon: 'el-icon-edit',
                default_value: []
            }
        }
    };
    
    modalBody.innerHTML = `
        <div style="margin-bottom: 20px;">
            <!-- 第一步：选择模板或类型 -->
            <div id="step-1">
                <h4 style="margin: 0 0 16px 0; color: #374151; font-size: 15px;">📋 选择配置方式</h4>
                
                <!-- 功能模板 -->
                <div style="margin-bottom: 24px;">
                    <label style="display: block; margin-bottom: 12px; font-weight: 500; color: #374151;">常用功能模板</label>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
                        ${Object.entries(templates).map(([key, tmpl]) => `
                            <div onclick="selectTemplate('${key}')" style="cursor: pointer; padding: 16px; border: 2px solid #e5e7eb; border-radius: 8px; text-align: center; transition: all 0.2s; background: white;">
                                <div style="font-size: 32px; margin-bottom: 8px;">${tmpl.icon}</div>
                                <div style="font-size: 13px; color: #374151; font-weight: 500;">${tmpl.name}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <!-- 分隔线 -->
                <div style="text-align: center; margin: 24px 0; position: relative;">
                    <div style="position: absolute; top: 50%; left: 0; right: 0; height: 1px; background: #e5e7eb;"></div>
                    <span style="position: relative; background: white; padding: 0 16px; color: #9ca3af; font-size: 13px;">或</span>
                </div>
                
                <!-- 按类型自定义 -->
                <div>
                    <label style="display: block; margin-bottom: 12px; font-weight: 500; color: #374151;">按类型自定义</label>
                    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px;">
                        <div onclick="selectType('ajax')" style="cursor: pointer; padding: 12px; border: 2px solid #3b82f6; border-radius: 8px; text-align: center; background: #eff6ff; color: #3b82f6; font-weight: 500; font-size: 13px;">
                            AJAX
                        </div>
                        <div onclick="selectType('jump')" style="cursor: pointer; padding: 12px; border: 2px solid #10b981; border-radius: 8px; text-align: center; background: #d1fae5; color: #10b981; font-weight: 500; font-size: 13px;">
                            JUMP
                        </div>
                        <div onclick="selectType('alert')" style="cursor: pointer; padding: 12px; border: 2px solid #f59e0b; border-radius: 8px; text-align: center; background: #fef3c7; color: #f59e0b; font-weight: 500; font-size: 13px;">
                            ALERT
                        </div>
                        <div onclick="selectType('form')" style="cursor: pointer; padding: 12px; border: 2px solid #8b5cf6; border-radius: 8px; text-align: center; background: #ede9fe; color: #8b5cf6; font-weight: 500; font-size: 13px;">
                            FORM
                        </div>
                        <div onclick="selectType('qcr_code')" style="cursor: pointer; padding: 12px; border: 2px solid #ec4899; border-radius: 8px; text-align: center; background: #fce7f3; color: #ec4899; font-weight: 500; font-size: 13px;">
                            QRC_CODE
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 第二步：配置详情 -->
            <div id="step-2" style="display: none;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                    <button type="button" onclick="backToStep1()" style="padding: 6px 12px; background: #f3f4f6; border: none; border-radius: 4px; cursor: pointer;">← 返回</button>
                    <h4 style="margin: 0; color: #374151; font-size: 15px;" id="config-title">配置详情</h4>
                </div>
                
                <form id="custom-action-form">
                    <!-- 基础配置 -->
                    <div style="background: #f9fafb; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                        <h5 style="margin: 0 0 12px 0; color: #374151; font-size: 14px;">基础配置</h5>
                        
                        <div class="form-group">
                            <label class="form-label">Action Name *</label>
                            <input type="text" class="form-input" id="action_name" required placeholder="例如: copy, download">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Label (显示文本) *</label>
                            <input type="text" class="form-input" id="label" required placeholder="例如: 复制, 下载">
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Action Type *</label>
                            <input type="text" class="form-input" id="action" readonly>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Params (参数字段)</label>
                            <input type="text" class="form-input" id="params" placeholder='例如: id, name (逗号分隔)'>
                            <small style="color: #6b7280; font-size: 12px;">从当前行中选取的参数字段，多个用逗号分隔</small>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">Location (位置) *</label>
                            <select class="form-input" id="location">
                                <option value="list">list - 列表右侧收缩位置</option>
                                <option value="outer_list">outer_list - 与编辑删除同级</option>
                                <option value="batch_list">batch_list - 批量选中时</option>
                            </select>
                        </div>
                        
                        <div class="form-group" id="icon-group" style="display: none;">
                            <label class="form-label">Icon (图标)</label>
                            <input type="text" class="form-input" id="icon" placeholder="例如: el-icon-document-copy">
                            <small style="color: #6b7280; font-size: 12px;">搭配 outer_list 使用</small>
                        </div>
                    </div>
                    
                    <!-- 类型特定配置 -->
                    <div id="type-specific-config"></div>
                    
                </form>
            </div>
        </div>
        
        <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
            <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
            <button type="button" class="btn btn-primary" id="save-action-btn" onclick="saveCustomActionFromDialog()" style="display: none;">
                <span>💾</span>
                <span>保存动作</span>
            </button>
        </div>
    `;
    
    // 如果是编辑模式，自动填充
    if (existingAction) {
        window.currentEditIndex = editIndex;
        // 根据类型自动选择
        const type = existingAction.action;
        setTimeout(() => {
            selectType(type, existingAction);
        }, 100);
    } else {
        window.currentEditIndex = null;
    }
    
    // 监听 location 变化，显示/隐藏 icon
    setTimeout(() => {
        const locationSelect = document.getElementById('location');
        if (locationSelect) {
            locationSelect.addEventListener('change', function() {
                document.getElementById('icon-group').style.display = 
                    this.value === 'outer_list' ? 'block' : 'none';
            });
        }
    }, 100);
    
    // 存储模板数据
    window.customActionTemplates = templates;
    
    modal.style.display = 'flex';
}

// 选择模板
function selectTemplate(templateKey) {
    const template = window.customActionTemplates[templateKey];
    const action = JSON.parse(JSON.stringify(template.action)); // 深拷贝
    selectType(action.action, action);
}

// 选择类型
function selectType(type, existingData = null) {
    document.getElementById('step-1').style.display = 'none';
    document.getElementById('step-2').style.display = 'block';
    document.getElementById('save-action-btn').style.display = 'inline-flex';
    
    // 填充基础信息
    document.getElementById('action').value = type;
    
    if (existingData) {
        document.getElementById('action_name').value = existingData.action_name || '';
        document.getElementById('label').value = existingData.label || '';
        document.getElementById('params').value = Array.isArray(existingData.params) ? existingData.params.join(', ') : '';
        document.getElementById('location').value = existingData.location || 'list';
        if (existingData.icon) {
            document.getElementById('icon').value = existingData.icon;
            document.getElementById('icon-group').style.display = 'block';
        }
    }
    
    // 根据类型渲染特定配置
    renderTypeSpecificConfig(type, existingData);
}

// 渲染类型特定配置
function renderTypeSpecificConfig(type, data = null) {
    const container = document.getElementById('type-specific-config');
    
    switch(type) {
        case 'ajax':
            container.innerHTML = `
                <div style="background: #eff6ff; padding: 16px; border-radius: 8px; border: 1px solid #3b82f6;">
                    <h5 style="margin: 0 0 12px 0; color: #3b82f6; font-size: 14px;">📡 AJAX 配置</h5>
                    
                    <div class="form-group">
                        <label class="form-label">Config (可选)</label>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                            <div>
                                <label style="font-size: 12px; color: #6b7280;">Type</label>
                                <input type="text" class="form-input" id="config_type" placeholder="例如: download" value="${data?.config?.type || ''}">
                            </div>
                            <div>
                                <label style="font-size: 12px; color: #6b7280;">Return Key</label>
                                <input type="text" class="form-input" id="config_return_key" placeholder="例如: url" value="${data?.config?.return_key || ''}">
                            </div>
                        </div>
                        <small style="color: #6b7280; font-size: 12px;">下载类 AJAX 需要配置 type=download 和 return_key</small>
                    </div>
                </div>
            `;
            break;
            
        case 'jump':
            container.innerHTML = `
                <div style="background: #d1fae5; padding: 16px; border-radius: 8px; border: 1px solid #10b981;">
                    <h5 style="margin: 0 0 12px 0; color: #10b981; font-size: 14px;">🔗 JUMP 配置</h5>
                    
                    <div class="form-group">
                        <label class="form-label">Jump Type *</label>
                        <select class="form-input" id="jump_type" onchange="updateJumpTypeFields()">
                            <option value="inner" ${data?.jump?.type === 'inner' ? 'selected' : ''}>inner - 内部跳转</option>
                            <option value="outer" ${data?.jump?.type === 'outer' ? 'selected' : ''}>outer - 外部跳转</option>
                            <option value="download" ${data?.jump?.type === 'download' ? 'selected' : ''}>download - 下载</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label" id="jump_href_label">Href</label>
                        <input type="text" class="form-input" id="jump_href" placeholder="模型名称 或 URL" value="${data?.jump?.href || ''}">
                        <small style="color: #6b7280; font-size: 12px;" id="jump_href_hint">inner: 模型名称，outer: URL，download: params 中的字段</small>
                    </div>
                </div>
            `;
            break;
            
        case 'alert':
            container.innerHTML = `
                <div style="background: #fef3c7; padding: 16px; border-radius: 8px; border: 1px solid #f59e0b;">
                    <h5 style="margin: 0 0 12px 0; color: #f59e0b; font-size: 14px;">⚠️ ALERT 配置</h5>
                    
                    <div class="form-group">
                        <label class="form-label">Content (确认内容) *</label>
                        <input type="text" class="form-input" id="alert_content" placeholder="例如: 确定要复制吗？" value="${data?.alert?.content || ''}">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Content Field (展示字段)</label>
                        <input type="text" class="form-input" id="alert_content_field" placeholder="例如: id, uid, uuid (逗号分隔)" 
                               value="${data?.alert?.content_field ? data.alert.content_field.join(', ') : ''}">
                        <small style="color: #6b7280; font-size: 12px;">弹框时展示的字段，选填</small>
                    </div>
                </div>
            `;
            break;
            
        case 'qcr_code':
            container.innerHTML = `
                <div style="background: #fce7f3; padding: 16px; border-radius: 8px; border: 1px solid #ec4899;">
                    <h5 style="margin: 0 0 12px 0; color: #ec4899; font-size: 14px;">📱 QRC_CODE 配置</h5>
                    
                    <div class="form-group">
                        <label class="form-label">Config Type *</label>
                        <input type="text" class="form-input" id="qrc_config_type" placeholder="例如: url" value="${data?.config?.type || 'url'}">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Href (URL 地址) *</label>
                        <input type="text" class="form-input" id="qrc_config_href" placeholder="例如: https://example.com" value="${data?.config?.href || ''}">
                        <small style="color: #6b7280; font-size: 12px;">二维码扫描后访问的 URL</small>
                    </div>
                </div>
            `;
            break;
            
        case 'form':
            container.innerHTML = `
                <div style="background: #ede9fe; padding: 16px; border-radius: 8px; border: 1px solid #8b5cf6;">
                    <h5 style="margin: 0 0 12px 0; color: #8b5cf6; font-size: 14px;">📝 FORM 配置</h5>
                    
                    <div class="form-group">
                        <label class="form-label">Form Fields (可编辑字段) *</label>
                        <input type="text" class="form-input" id="form_fields" placeholder="例如: apple_auth_key (逗号分隔)" 
                               value="${data?.form_fields ? data.form_fields.join(', ') : ''}">
                        <small style="color: #6b7280; font-size: 12px;">二次弹窗中可编辑的字段</small>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Default Value (默认值配置)</label>
                        <textarea class="form-input" id="form_default_value" rows="4" placeholder='例如: [{"name": "apple_auth_key", "disable": false}]'>${data?.default_value ? JSON.stringify(data.default_value, null, 2) : ''}</textarea>
                        <small style="color: #6b7280; font-size: 12px;">JSON 格式，配置字段的默认值和是否可编辑</small>
                    </div>
                </div>
            `;
            break;
    }
}

// 返回第一步
function backToStep1() {
    document.getElementById('step-1').style.display = 'block';
    document.getElementById('step-2').style.display = 'none';
    document.getElementById('save-action-btn').style.display = 'none';
}

// 保存自定义动作
function saveCustomActionFromDialog() {
    const action = {
        action_name: document.getElementById('action_name').value.trim(),
        label: document.getElementById('label').value.trim(),
        action: document.getElementById('action').value,
        params: document.getElementById('params').value.split(',').map(p => p.trim()).filter(p => p),
        location: document.getElementById('location').value
    };
    
    // 验证必填项
    if (!action.action_name || !action.label) {
        alert('请填写必填项：Action Name 和 Label');
        return;
    }
    
    // Icon（可选）
    const iconInput = document.getElementById('icon');
    if (iconInput && iconInput.value.trim()) {
        action.icon = iconInput.value.trim();
    }
    
    // 根据类型添加特定配置
    const type = action.action;
    
    switch(type) {
        case 'ajax':
            const configType = document.getElementById('config_type')?.value.trim();
            const configReturnKey = document.getElementById('config_return_key')?.value.trim();
            if (configType || configReturnKey) {
                action.config = {};
                if (configType) action.config.type = configType;
                if (configReturnKey) action.config.return_key = configReturnKey;
            }
            break;
            
        case 'jump':
            const jumpType = document.getElementById('jump_type').value;
            const jumpHref = document.getElementById('jump_href').value.trim();
            action.jump = {
                type: jumpType,
                href: jumpHref
            };
            break;
            
        case 'alert':
            const alertContent = document.getElementById('alert_content').value.trim();
            const alertContentField = document.getElementById('alert_content_field').value.split(',').map(f => f.trim()).filter(f => f);
            if (!alertContent) {
                alert('Alert 类型必须填写 Content');
                return;
            }
            action.alert = {
                content: alertContent,
                content_field: alertContentField
            };
            break;
            
        case 'qcr_code':
            const qrcType = document.getElementById('qrc_config_type').value.trim();
            const qrcHref = document.getElementById('qrc_config_href').value.trim();
            if (!qrcHref) {
                alert('QRC_CODE 类型必须填写 Href');
                return;
            }
            action.config = {
                type: qrcType || 'url',
                href: qrcHref
            };
            break;
            
        case 'form':
            const formFields = document.getElementById('form_fields').value.split(',').map(f => f.trim()).filter(f => f);
            const formDefaultValue = document.getElementById('form_default_value').value.trim();
            if (formFields.length === 0) {
                alert('Form 类型必须填写 Form Fields');
                return;
            }
            action.form_fields = formFields;
            if (formDefaultValue) {
                try {
                    action.default_value = JSON.parse(formDefaultValue);
                } catch(e) {
                    alert('Default Value 格式错误，请输入有效的 JSON');
                    return;
                }
            }
            break;
    }
    
    // 添加或更新
    if (!adminSystem.currentModel.custom_actions) {
        adminSystem.currentModel.custom_actions = [];
    }
    
    if (window.currentEditIndex !== null && window.currentEditIndex !== undefined) {
        adminSystem.currentModel.custom_actions[window.currentEditIndex] = action;
        showToast('自定义动作已更新', 'success', 2000);
    } else {
        adminSystem.currentModel.custom_actions.push(action);
        showToast('自定义动作已添加', 'success', 2000);
    }
    
    // 关闭对话框并刷新列表
    closeModal();
    adminSystem.openCustomActionsConfig();
}

// Jump 类型字段更新
function updateJumpTypeFields() {
    const jumpType = document.getElementById('jump_type').value;
    const hrefLabel = document.getElementById('jump_href_label');
    const hrefHint = document.getElementById('jump_href_hint');
    
    switch(jumpType) {
        case 'inner':
            hrefLabel.textContent = 'Href (模型名称) *';
            hrefHint.textContent = '要跳转的模型名称';
            break;
        case 'outer':
            hrefLabel.textContent = 'Href (URL) *';
            hrefHint.textContent = '外部链接 URL';
            break;
        case 'download':
            hrefLabel.textContent = 'Href (字段名)';
            hrefHint.textContent = 'params 中配置的字段名，值为下载 URL';
            break;
    }
}

function removeCustomAction(index) {
    if (!confirm('确认删除该自定义动作？')) return;
    adminSystem.currentModel.custom_actions.splice(index, 1);
    adminSystem.openCustomActionsConfig();
}

// 字段管理相关函数
function addField() {
    if (!adminSystem.currentModel) {
        alert('请先选择或创建一个模型');
        return;
    }
    
    const modal = document.getElementById('config-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    
    modalTitle.textContent = '添加字段';
    
    // 使用 adminSystem 而不是 this
    const currentFields = adminSystem.currentModel.fields || [];
    const fieldOptions = currentFields.map(f => `<option value="${f.name}">${f.label} (${f.name})</option>`).join('');
    
    modalBody.innerHTML = `
        <form id="add-field-form">
            <div class="form-grid">
                <div class="form-group">
                    <label class="form-label">字段名称 (name) *</label>
                    <input type="text" class="form-input" id="field-name" placeholder="例如: user_id">
                </div>
                <div class="form-group">
                    <label class="form-label">显示标签 (label) *</label>
                    <input type="text" class="form-input" id="field-label" placeholder="例如: 用户ID">
                </div>
            </div>
            
            <div class="form-group">
                <label class="form-label">字段类型 (type) *</label>
                <select class="form-input" id="field-type" onchange="onFieldTypeChange(this.value)">
                    <optgroup label="基础类型">
                        <option value="String">String - 字符串</option>
                        <option value="Integer">Integer - 整数</option>
                        <option value="Float">Float - 浮点数</option>
                        <option value="Boolean">Boolean - 布尔值</option>
                        <option value="DateTime">DateTime - 日期时间</option>
                    </optgroup>
                    <optgroup label="文本类型">
                        <option value="TextArea">TextArea - 多行文本</option>
                        <option value="Editor">Editor - 富文本编辑器</option>
                    </optgroup>
                    <optgroup label="选择类型">
                        <option value="Select">Select - 单选下拉</option>
                        <option value="SelectMulti">SelectMulti - 多选下拉</option>
                        <option value="Radio">Radio - 单选按钮</option>
                    </optgroup>
                    <optgroup label="文件类型">
                        <option value="File">File - 单文件上传</option>
                        <option value="FileMulti">FileMulti - 多文件上传</option>
                        <option value="Image">Image - 单图片上传</option>
                        <option value="ImageMulti">ImageMulti - 多图片上传</option>
                    </optgroup>
                    <optgroup label="关联类型">
                        <option value="LinkString">LinkString - 链接跳转</option>
                        <option value="LinkForm">LinkForm - 关联表单</option>
                        <option value="InlineModel">InlineModel - 内联模型</option>
                    </optgroup>
                    <optgroup label="高级类型">
                        <option value="Json">Json - JSON数据</option>
                        <option value="JsonEditor">JsonEditor - JSON编辑器</option>
                        <option value="Calculation">Calculation - 计算字段</option>
                        <option value="SourceForm">SourceForm - 动态表单</option>
                    </optgroup>
                </select>
            </div>
            
            <!-- 字段类型特定配置 -->
            <div id="field-type-specific" style="display: none;"></div>
            
            <button type="button" class="toggle-advanced" onclick="toggleAdvancedOptions()">
                显示高级选项
            </button>
            
            <div id="advanced-options" class="advanced-options" style="padding-top: 8px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 12px;">
                    <div>
                        <label style="font-size: 12px; color: #374151; font-weight: 500; display: block; margin-bottom: 4px;">说明 (explain)</label>
                        <input type="text" class="form-input" id="field-explain" placeholder="字段说明" style="font-size: 13px; padding: 6px 10px;">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #374151; font-weight: 500; display: block; margin-bottom: 4px;">占位符 (placeholder)</label>
                        <input type="text" class="form-input" id="field-placeholder" placeholder="占位符" style="font-size: 13px; padding: 6px 10px;">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #374151; font-weight: 500; display: block; margin-bottom: 4px;">默认值 (default)</label>
                        <input type="text" class="form-input" id="field-default" placeholder="默认值" style="font-size: 13px; padding: 6px 10px;">
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 10px; margin-bottom: 12px;">
                    <div>
                        <label style="font-size: 12px; color: #374151; font-weight: 500; display: block; margin-bottom: 4px;">宽度px (width)</label>
                        <input type="number" class="form-input" id="field-width" placeholder="120" style="font-size: 13px; padding: 6px 10px;">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #374151; font-weight: 500; display: block; margin-bottom: 4px;">数据来源 (source)</label>
                        <input type="text" class="form-input" id="field-source" placeholder="动态数据URL" style="font-size: 13px; padding: 6px 10px;">
                    </div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <label style="font-size: 12px; color: #374151; font-weight: 500; display: block; margin-bottom: 6px;">渲染选项 (render_kw)</label>
                    <div style="display: flex; gap: 16px;">
                        <label style="display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer;">
                            <input type="checkbox" id="field-readonly">
                            只读 (readonly)
                        </label>
                        <label style="display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer;">
                            <input type="checkbox" id="field-createonly">
                            仅创建时可见 (createonly)
                        </label>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">显示规则 (show_rule)</label>
                    <div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #f9fafb;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 4px;">关联字段</label>
                                <select class="form-input" id="show-rule-field" style="font-size: 13px;">
                                    <option value="">不设置</option>
                                    ${fieldOptions}
                                </select>
                            </div>
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 4px;">匹配方式</label>
                                <select class="form-input" id="show-rule-match" style="font-size: 13px;">
                                    <option value="value">等于 (value)</option>
                                    <option value="contain">包含 (contain)</option>
                                </select>
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 4px;">匹配值</label>
                                <input type="text" class="form-input" id="show-rule-value" placeholder="输入值" style="font-size: 13px;">
                            </div>
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 4px;">执行动作</label>
                                <select class="form-input" id="show-rule-action" style="font-size: 13px;">
                                    <option value="true">隐藏字段 (hideis: true)</option>
                                    <option value="false">显示字段 (hideis: false)</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <small style="color: #6b7280; font-size: 12px; display: block; margin-top: 4px;">控制字段根据其他字段值的显示/隐藏</small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">复制规则 (copy_rule)</label>
                    <div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #f9fafb;">
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                <input type="radio" name="copy-rule" value="开启" checked>
                                <span style="font-size: 13px;">可复制无按钮 (默认)</span>
                            </label>
                            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                <input type="radio" name="copy-rule" value="with-button">
                                <span style="font-size: 13px;">可复制有按钮 (显示复制按钮 🔗)</span>
                            </label>
                            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                <input type="radio" name="copy-rule" value="关闭">
                                <span style="font-size: 13px;">不可复制 (字体变灰)</span>
                            </label>
                        </div>
                    </div>
                    <small style="color: #6b7280; font-size: 11px; display: block; margin-top: 3px;">配置字段的复制链接功能，默认可复制无按钮</small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">提示折叠 (tooltip)</label>
                    <div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px; background: #f9fafb;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 3px;">弹窗宽度 (width)</label>
                                <input type="number" class="form-input" id="tooltip-width" placeholder="900" style="font-size: 13px; padding: 6px;">
                            </div>
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 3px;">触发方式 (trigger)</label>
                                <select class="form-input" id="tooltip-trigger" style="font-size: 13px; padding: 6px;">
                                    <option value="hover">hover - 鼠标移入</option>
                                    <option value="click">click - 点击</option>
                                    <option value="focus">focus - 持续点击</option>
                                </select>
                            </div>
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 3px;">字符数 (length)</label>
                                <input type="number" class="form-input" id="tooltip-length" placeholder="100" style="font-size: 13px; padding: 6px;">
                            </div>
                        </div>
                        <div>
                            <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 3px;">展示行数 (row)</label>
                            <input type="number" class="form-input" id="tooltip-row" placeholder="不限制" style="font-size: 13px; padding: 6px;">
                        </div>
                    </div>
                    <small style="color: #6b7280; font-size: 11px; display: block; margin-top: 3px;">列表页字段折叠展示配置，length和row至少填一个</small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">验证器 (validators)</label>
                    <div id="validators-list" style="margin-bottom: 8px;">
                        <!-- 验证器列表将在这里动态生成 -->
                    </div>
                    <button type="button" class="btn btn-secondary btn-small" onclick="addValidator()">
                        + 添加验证器
                    </button>
                    <small style="color: #6b7280; font-size: 12px; display: block; margin-top: 8px;">
                        常用验证器：data_required (必填)、length (长度限制)、regex (正则)
                    </small>
                </div>
            </div>
            
            <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                <button type="button" class="btn btn-secondary" onclick="closeFieldModal()">取消</button>
                <button type="button" class="btn btn-primary" onclick="saveField()">添加字段</button>
            </div>
        </form>
    `;
    
    modal.style.display = 'flex';
}

function toggleAdvancedOptions() {
    const advancedOptions = document.getElementById('advanced-options');
    const toggleBtn = document.querySelector('.toggle-advanced');
    
    if (advancedOptions.classList.contains('show')) {
        advancedOptions.classList.remove('show');
        toggleBtn.textContent = '显示高级选项';
    } else {
        advancedOptions.classList.add('show');
        toggleBtn.textContent = '隐藏高级选项';
    }
}

function addValidator() {
    const validatorsList = document.getElementById('validators-list');
    const validatorItem = document.createElement('div');
    validatorItem.className = 'validator-item';
    validatorItem.innerHTML = `
        <input type="text" class="validator-name" placeholder="验证器名称" value="data_required">
        <input type="text" class="validator-kws" placeholder='参数JSON，如: {"min":3,"max":12}' value="">
        <button type="button" class="btn btn-danger btn-small" onclick="removeValidator(this)">删除</button>
    `;
    validatorsList.appendChild(validatorItem);
}

function removeValidator(button) {
    button.closest('.validator-item').remove();
}

function saveField() {
    const name = document.getElementById('field-name').value.trim();
    const label = document.getElementById('field-label').value.trim();
    const type = document.getElementById('field-type').value;
    
    if (!name || !label || !type) {
        alert('请填写必填项（字段名、显示标签、类型）');
        return;
    }

    const field = {
        id: Date.now() + Math.random(),
        name: name,
        label: label,
        type: type
    };
    
    // 基础高级选项
    const explain = document.getElementById('field-explain')?.value.trim();
    const placeholder = document.getElementById('field-placeholder')?.value.trim();
    const defaultValue = document.getElementById('field-default')?.value.trim();
    const width = document.getElementById('field-width')?.value;
    const source = document.getElementById('field-source')?.value.trim();
    
    if (explain) field.explain = explain;
    if (placeholder) field.placeholder = placeholder;
    if (defaultValue) field.default = defaultValue;
    if (width) field.width = parseInt(width);
    if (source) field.source = source;
    
    // 显示规则 (show_rule)
    const showRuleField = document.getElementById('show-rule-field')?.value;
    const showRuleMatch = document.getElementById('show-rule-match')?.value;
    const showRuleValue = document.getElementById('show-rule-value')?.value.trim();
    const showRuleAction = document.getElementById('show-rule-action')?.value;
    
    if (showRuleField && showRuleValue) {
        field.show_rule = {
            name: showRuleField,
            hideis: showRuleAction === 'true'
        };
        // 根据匹配方式添加对应的key
        if (showRuleMatch === 'value') {
            field.show_rule.value = showRuleValue;
        } else {
            field.show_rule.contain = showRuleValue;
        }
    }
    
    // 复制规则 (copy_rule)
    const copyRuleRadio = document.querySelector('input[name="copy-rule"]:checked')?.value;
    if (copyRuleRadio === 'with-button') {
        field.copy_rule = {}; // 可复制有按钮
    } else if (copyRuleRadio === '关闭') {
        field.copy_rule = '关闭'; // 不可复制
    }
    // 如果是"开启"（默认），不设置copy_rule字段
    
    // 提示折叠 (tooltip)
    const tooltipWidth = document.getElementById('tooltip-width')?.value;
    const tooltipTrigger = document.getElementById('tooltip-trigger')?.value;
    const tooltipLength = document.getElementById('tooltip-length')?.value;
    const tooltipRow = document.getElementById('tooltip-row')?.value;
    
    if (tooltipWidth || tooltipTrigger || tooltipLength || tooltipRow) {
        field.tooltip = {};
        if (tooltipWidth) field.tooltip.width = parseInt(tooltipWidth);
        if (tooltipTrigger) field.tooltip.trigger = tooltipTrigger;
        if (tooltipLength) field.tooltip.length = parseInt(tooltipLength);
        if (tooltipRow) field.tooltip.row = parseInt(tooltipRow);
    }
    
    // 渲染选项
    const readonly = document.getElementById('field-readonly')?.checked;
    const createonly = document.getElementById('field-createonly')?.checked;
    if (readonly || createonly) {
        field.render_kw = {};
        if (readonly) field.render_kw.readonly = true;
        if (createonly) field.render_kw.createonly = true;
    }
    
    // 字段类型特定配置
    switch(type) {
        case 'Select':
        case 'SelectMulti':
        case 'Radio':
            const choices = document.getElementById('field-choices')?.value.trim();
            const coerce = document.getElementById('field-coerce')?.value;
            const fieldChains = document.getElementById('field-chains')?.value.trim();
            const allowCreate = document.getElementById('field-allow-create')?.checked;
            
            if (choices) {
                try {
                    field.choices = JSON.parse(choices);
                } catch(e) {
                    // 如果不是JSON，当作URL
                    field.choices = choices;
                }
            }
            if (coerce) field.coerce = coerce;
            if (fieldChains) {
                try { field.field_chains = JSON.parse(fieldChains); } catch(e) {}
            }
            if (allowCreate) field.allow_create = true;
            break;
            
        case 'Image':
        case 'File':
        case 'ImageMulti':
        case 'FileMulti':
            const style = document.getElementById('field-style')?.value;
            const config = document.getElementById('field-config')?.value.trim();
            if (style) field.style = style;
            if (config) field.config = config;
            break;
            
        case 'LinkString':
            const params = document.getElementById('field-params')?.value.trim();
            const model = document.getElementById('field-model')?.value.trim();
            if (params) {
                try { field.params = JSON.parse(params); } catch(e) {}
            }
            if (model) field.model = model;
            break;
            
        case 'LinkForm':
            const formName = document.getElementById('field-form-name')?.value.trim();
            if (formName) field.form_name = formName;
            const actions = [];
            document.querySelectorAll('.linkform-action:checked').forEach(cb => {
                actions.push(cb.value);
            });
            if (actions.length > 0) field.actions = actions;
            break;
            
        case 'InlineModel':
            const inlineFormName = document.getElementById('field-form-name')?.value.trim();
            if (inlineFormName) field.form_name = inlineFormName;
            break;
            
        case 'Calculation':
            const formula = document.getElementById('field-formula')?.value.trim();
            const conversion = document.getElementById('field-conversion')?.value.trim();
            if (formula || conversion) {
                field.method = {};
                if (formula) field.method.formula = formula;
                if (conversion) {
                    try { field.method.field_conversion = JSON.parse(conversion); } catch(e) {}
                }
            }
            break;
            
        case 'JsonEditor':
            const outSelected = document.getElementById('field-out-selected')?.checked;
            const expandAll = document.getElementById('field-expand-all')?.checked;
            const showDiff = document.getElementById('field-show-diff')?.checked;
            const remoteExplain = document.getElementById('field-remote-explain')?.value.trim();
            if (outSelected) field.out_selected = true;
            if (expandAll) field.expand_all = true;
            if (showDiff) field.show_diff = true;
            if (remoteExplain) field.remote_explain = remoteExplain;
            break;
            
        case 'DateTime':
            const filterRules = document.getElementById('field-filter-rules')?.value.trim();
            if (filterRules) {
                try { field.filter_rules = JSON.parse(filterRules); } catch(e) {}
            }
            break;
    }
    
    // 验证器
    const validatorItems = document.querySelectorAll('.validator-item');
    if (validatorItems.length > 0) {
        const validators = [];
        validatorItems.forEach(item => {
            const validatorName = item.querySelector('.validator-name').value.trim();
            const kwsStr = item.querySelector('.validator-kws').value.trim();
            if (validatorName) {
                const validator = { name: validatorName };
                if (kwsStr) {
                    try {
                        validator.kws = JSON.parse(kwsStr);
                    } catch (e) {
                        validator.kws = { raw: kwsStr };
                    }
                }
                validators.push(validator);
            }
        });
        if (validators.length > 0) {
            field.validators = validators;
        }
    }
    
    adminSystem.currentModel.fields.push(field);
    
    // 关闭模态框并更新预览
    adminSystem.closeModal();
    adminSystem.updatePreview();
    adminSystem.showSuccessMessage('字段添加成功！');
}

function closeFieldModal() {
    adminSystem.closeModal();
}

function editField(fieldId) {
    const field = adminSystem.currentModel.fields.find(f => f.id == fieldId);
    if (!field) return;
    
    const modal = document.getElementById('config-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    
    modalTitle.textContent = '编辑字段';
    modalBody.innerHTML = `
        <form id="edit-field-form">
            <div class="form-grid">
                <div class="form-group">
                    <label class="form-label">字段名称 (name) *</label>
                    <input type="text" class="form-input" id="field-name" value="${field.name}" placeholder="例如: user_id">
                </div>
                <div class="form-group">
                    <label class="form-label">显示标签 (label) *</label>
                    <input type="text" class="form-input" id="field-label" value="${field.label}" placeholder="例如: 用户ID">
                </div>
            </div>
            
            <div class="form-group">
                <label class="form-label">字段类型 (type) *</label>
                <select class="form-input" id="field-type">
                    <option value="String" ${field.type === 'String' ? 'selected' : ''}>String</option>
                    <option value="Integer" ${field.type === 'Integer' ? 'selected' : ''}>Integer</option>
                    <option value="Float" ${field.type === 'Float' ? 'selected' : ''}>Float</option>
                    <option value="Boolean" ${field.type === 'Boolean' ? 'selected' : ''}>Boolean</option>
                    <option value="Datetime" ${field.type === 'Datetime' ? 'selected' : ''}>Datetime</option>
                    <option value="TextArea" ${field.type === 'TextArea' ? 'selected' : ''}>TextArea</option>
                    <option value="Editor" ${field.type === 'Editor' ? 'selected' : ''}>Editor</option>
                    <option value="Select" ${field.type === 'Select' ? 'selected' : ''}>Select</option>
                    <option value="SelectMulti" ${field.type === 'SelectMulti' ? 'selected' : ''}>SelectMulti</option>
                    <option value="Radio" ${field.type === 'Radio' ? 'selected' : ''}>Radio</option>
                    <option value="File" ${field.type === 'File' ? 'selected' : ''}>File</option>
                    <option value="Image" ${field.type === 'Image' ? 'selected' : ''}>Image</option>
                    <option value="ImageMulti" ${field.type === 'ImageMulti' ? 'selected' : ''}>ImageMulti</option>
                    <option value="FileMulti" ${field.type === 'FileMulti' ? 'selected' : ''}>FileMulti</option>
                    <option value="Json" ${field.type === 'Json' ? 'selected' : ''}>Json</option>
                    <option value="JsonEditor" ${field.type === 'JsonEditor' ? 'selected' : ''}>JsonEditor</option>
                    <option value="LinkString" ${field.type === 'LinkString' ? 'selected' : ''}>LinkString</option>
                    <option value="InlineModel" ${field.type === 'InlineModel' ? 'selected' : ''}>InlineModel</option>
                    <option value="LinkForm" ${field.type === 'LinkForm' ? 'selected' : ''}>LinkForm</option>
                    <option value="Calculation" ${field.type === 'Calculation' ? 'selected' : ''}>Calculation</option>
                    <option value="SourceForm" ${field.type === 'SourceForm' ? 'selected' : ''}>SourceForm</option>
                </select>
            </div>
            
            <button type="button" class="toggle-advanced" onclick="toggleAdvancedOptions()" style="background: #f3f4f6; border: 1px solid #d1d5db; padding: 8px 16px; border-radius: 6px; cursor: pointer; width: 100%; margin-bottom: 12px;">
                显示高级选项
            </button>
            
            <div id="advanced-options" class="advanced-options" style="padding-top: 8px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 12px;">
                    <div>
                        <label style="font-size: 12px; color: #374151; font-weight: 500; display: block; margin-bottom: 4px;">说明 (explain)</label>
                        <input type="text" class="form-input" id="field-explain" value="${field.explain || ''}" placeholder="字段说明" style="font-size: 13px; padding: 6px 10px;">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #374151; font-weight: 500; display: block; margin-bottom: 4px;">占位符 (placeholder)</label>
                        <input type="text" class="form-input" id="field-placeholder" value="${field.placeholder || ''}" placeholder="占位符" style="font-size: 13px; padding: 6px 10px;">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #374151; font-weight: 500; display: block; margin-bottom: 4px;">默认值 (default)</label>
                        <input type="text" class="form-input" id="field-default" value="${field.default || ''}" placeholder="默认值" style="font-size: 13px; padding: 6px 10px;">
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 10px; margin-bottom: 12px;">
                    <div>
                        <label style="font-size: 12px; color: #374151; font-weight: 500; display: block; margin-bottom: 4px;">宽度px (width)</label>
                        <input type="number" class="form-input" id="field-width" value="${field.width || ''}" placeholder="120" style="font-size: 13px; padding: 6px 10px;">
                    </div>
                    <div>
                        <label style="font-size: 12px; color: #374151; font-weight: 500; display: block; margin-bottom: 4px;">数据来源 (source)</label>
                        <input type="text" class="form-input" id="field-source" value="${field.source || ''}" placeholder="动态数据URL" style="font-size: 13px; padding: 6px 10px;">
                    </div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <label style="font-size: 12px; color: #374151; font-weight: 500; display: block; margin-bottom: 6px;">渲染选项 (render_kw)</label>
                    <div style="display: flex; gap: 16px;">
                        <label style="display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer;">
                            <input type="checkbox" id="field-readonly" ${field.render_kw?.readonly ? 'checked' : ''}>
                            只读 (readonly)
                        </label>
                        <label style="display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer;">
                            <input type="checkbox" id="field-createonly" ${field.render_kw?.createonly ? 'checked' : ''}>
                            仅创建时可见 (createonly)
                        </label>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">显示规则 (show_rule)</label>
                    <div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #f9fafb;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 4px;">关联字段</label>
                                <select class="form-input" id="show-rule-field" style="font-size: 13px;">
                                    <option value="">不设置</option>
                                    ${adminSystem.currentModel.fields.filter(f => f.id !== field.id).map(f => `<option value="${f.name}" ${field.show_rule?.name === f.name ? 'selected' : ''}>${f.label} (${f.name})</option>`).join('')}
                                </select>
                            </div>
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 4px;">匹配方式</label>
                                <select class="form-input" id="show-rule-match" style="font-size: 13px;">
                                    <option value="value" ${field.show_rule?.value !== undefined ? 'selected' : ''}>等于 (value)</option>
                                    <option value="contain" ${field.show_rule?.contain !== undefined ? 'selected' : ''}>包含 (contain)</option>
                                </select>
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 4px;">匹配值</label>
                                <input type="text" class="form-input" id="show-rule-value" placeholder="输入值" value="${field.show_rule?.value || field.show_rule?.contain || ''}" style="font-size: 13px;">
                            </div>
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 4px;">执行动作</label>
                                <select class="form-input" id="show-rule-action" style="font-size: 13px;">
                                    <option value="true" ${field.show_rule?.hideis === true ? 'selected' : ''}>隐藏字段 (hideis: true)</option>
                                    <option value="false" ${field.show_rule?.hideis === false ? 'selected' : ''}>显示字段 (hideis: false)</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <small style="color: #6b7280; font-size: 12px; display: block; margin-top: 4px;">控制字段根据其他字段值的显示/隐藏</small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">复制规则 (copy_rule)</label>
                    <div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #f9fafb;">
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                <input type="radio" name="copy-rule" value="开启" ${!field.copy_rule || (typeof field.copy_rule === 'object' && field.copy_rule.status === '开启') ? 'checked' : ''}>
                                <span style="font-size: 13px;">可复制无按钮 (默认)</span>
                        </label>
                            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                <input type="radio" name="copy-rule" value="with-button" ${typeof field.copy_rule === 'object' && field.copy_rule !== null && Object.keys(field.copy_rule).length === 0 ? 'checked' : ''}>
                                <span style="font-size: 13px;">可复制有按钮 (显示复制按钮 🔗)</span>
                            </label>
                            <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                <input type="radio" name="copy-rule" value="关闭" ${field.copy_rule === '关闭' ? 'checked' : ''}>
                                <span style="font-size: 13px;">不可复制 (字体变灰)</span>
                        </label>
                    </div>
                    </div>
                    <small style="color: #6b7280; font-size: 11px; display: block; margin-top: 3px;">配置字段的复制链接功能，默认可复制无按钮</small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">提示折叠 (tooltip)</label>
                    <div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px; background: #f9fafb;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 3px;">弹窗宽度 (width)</label>
                                <input type="number" class="form-input" id="tooltip-width" placeholder="900" value="${field.tooltip?.width || ''}" style="font-size: 13px; padding: 6px;">
                            </div>
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 3px;">触发方式 (trigger)</label>
                                <select class="form-input" id="tooltip-trigger" style="font-size: 13px; padding: 6px;">
                                    <option value="hover" ${field.tooltip?.trigger === 'hover' ? 'selected' : ''}>hover - 鼠标移入</option>
                                    <option value="click" ${field.tooltip?.trigger === 'click' ? 'selected' : ''}>click - 点击</option>
                                    <option value="focus" ${field.tooltip?.trigger === 'focus' ? 'selected' : ''}>focus - 持续点击</option>
                                </select>
                            </div>
                            <div>
                                <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 3px;">字符数 (length)</label>
                                <input type="number" class="form-input" id="tooltip-length" placeholder="100" value="${field.tooltip?.length || ''}" style="font-size: 13px; padding: 6px;">
                            </div>
                        </div>
                        <div>
                            <label style="font-size: 12px; color: #6b7280; display: block; margin-bottom: 3px;">展示行数 (row)</label>
                            <input type="number" class="form-input" id="tooltip-row" placeholder="不限制" value="${field.tooltip?.row || ''}" style="font-size: 13px; padding: 6px;">
                        </div>
                    </div>
                    <small style="color: #6b7280; font-size: 11px; display: block; margin-top: 3px;">列表页字段折叠展示配置，length和row至少填一个</small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">验证器 (validators)</label>
                    <div id="validators-list" style="margin-bottom: 8px;">
                        ${(field.validators || []).map(v => `
                            <div class="validator-item" style="display: flex; gap: 8px; margin-bottom: 8px;">
                                <input type="text" class="validator-name" placeholder="验证器名称" value="${v.name}" style="flex: 1; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
                                <input type="text" class="validator-kws" placeholder='参数JSON' value='${JSON.stringify(v.kws || {})}' style="flex: 2; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
                                <button type="button" class="btn btn-danger btn-small" onclick="removeValidator(this)">删除</button>
                            </div>
                        `).join('')}
                    </div>
                    <button type="button" class="btn btn-secondary btn-small" onclick="addValidator()">
                        + 添加验证器
                    </button>
                    <small style="color: #6b7280; font-size: 12px; display: block; margin-top: 8px;">
                        常用验证器：data_required (必填)、length (长度限制)、regex (正则)
                    </small>
                </div>
            </div>
            
            <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                <button type="button" class="btn btn-secondary" onclick="closeFieldModal()">取消</button>
                <button type="button" class="btn btn-primary" onclick="updateField('${fieldId}')">保存修改</button>
            </div>
        </form>
    `;
    
    modal.style.display = 'flex';
    
    // 初始化字段类型特定配置
    onFieldTypeChange(field.type);
    
    // 填充字段类型特定配置的数据
    setTimeout(() => {
        fillFieldTypeSpecificData(field);
    }, 100);
}

function fillFieldTypeSpecificData(field) {
    // 根据字段类型填充特定配置数据
    switch(field.type) {
        case 'Select':
        case 'SelectMulti':
        case 'Radio':
            const choicesElement = document.getElementById('field-choices');
            const coerceElement = document.getElementById('field-coerce');
            const chainsElement = document.getElementById('field-chains');
            const allowCreateElement = document.getElementById('field-allow-create');
            
            if (choicesElement && field.choices !== undefined) {
                if (Array.isArray(field.choices)) {
                    choicesElement.value = JSON.stringify(field.choices, null, 2);
                } else {
                    choicesElement.value = field.choices;
                }
                
                // 如果有常量引用标记，显示特殊提示
                if (field._has_constants) {
                    const container = choicesElement.parentElement;
                    const existingNote = container.querySelector('.constant-note');
                    if (!existingNote) {
                        const note = document.createElement('div');
                        note.className = 'constant-note';
                        note.style.cssText = `
                            background: #fef3c7; 
                            border: 1px solid #f59e0b; 
                            border-radius: 4px; 
                            padding: 8px; 
                            margin-top: 8px; 
                            font-size: 12px; 
                            color: #92400e;
                        `;
                        note.innerHTML = `
                            <strong>⚠️ 常量引用检测</strong><br>
                            此字段包含常量引用: ${field._constant_refs?.join(', ') || '未知'}<br>
                            原始配置: ${field.choices}
                        `;
                        container.appendChild(note);
                    }
                }
            }
            
            if (coerceElement && field.coerce) {
                coerceElement.value = field.coerce;
            }
            
            if (chainsElement && field.field_chains) {
                if (Array.isArray(field.field_chains)) {
                    chainsElement.value = JSON.stringify(field.field_chains, null, 2);
                } else {
                    chainsElement.value = field.field_chains;
                }
            }
            
            if (allowCreateElement && field.allow_create) {
                allowCreateElement.checked = field.allow_create;
            }
            break;
            
        case 'Image':
        case 'File':
        case 'ImageMulti':
        case 'FileMulti':
            const styleElement = document.getElementById('field-style');
            if (styleElement && field.style) {
                styleElement.value = field.style;
            }
            break;
            
        case 'DateTime':
            const filterRulesElement = document.getElementById('field-filter-rules');
            if (filterRulesElement && field.filter_rules) {
                if (typeof field.filter_rules === 'object') {
                    filterRulesElement.value = JSON.stringify(field.filter_rules, null, 2);
                } else {
                    filterRulesElement.value = field.filter_rules;
                }
            }
            break;
    }
}

function updateField(fieldId) {
    const field = adminSystem.currentModel.fields.find(f => f.id == fieldId);
    if (!field) return;
    
    const name = document.getElementById('field-name').value.trim();
    const label = document.getElementById('field-label').value.trim();
    const type = document.getElementById('field-type').value;
    
    if (!name || !label || !type) {
        alert('请填写必填项（字段名、显示标签、类型）');
        return;
    }
    
    // 更新字段基本信息
    field.name = name;
    field.label = label;
    field.type = type;
    
    // 高级选项
    const explain = document.getElementById('field-explain').value.trim();
    const placeholder = document.getElementById('field-placeholder').value.trim();
    const defaultValue = document.getElementById('field-default').value.trim();
    const width = document.getElementById('field-width').value;
    const source = document.getElementById('field-source').value.trim();
    
    if (explain) field.explain = explain; else delete field.explain;
    if (placeholder) field.placeholder = placeholder; else delete field.placeholder;
    if (defaultValue) field.default = defaultValue; else delete field.default;
    if (width) field.width = parseInt(width); else delete field.width;
    if (source) field.source = source; else delete field.source;
    
    // 渲染选项
    const readonly = document.getElementById('field-readonly').checked;
    const createonly = document.getElementById('field-createonly').checked;
    if (readonly || createonly) {
        field.render_kw = {};
        if (readonly) field.render_kw.readonly = true;
        if (createonly) field.render_kw.createonly = true;
    } else {
        delete field.render_kw;
    }
    
    // 显示规则 (show_rule)
    const showRuleField = document.getElementById('show-rule-field')?.value;
    const showRuleMatch = document.getElementById('show-rule-match')?.value;
    const showRuleValue = document.getElementById('show-rule-value')?.value.trim();
    const showRuleAction = document.getElementById('show-rule-action')?.value;
    
    if (showRuleField && showRuleValue) {
        field.show_rule = {
            name: showRuleField,
            hideis: showRuleAction === 'true'
        };
        // 根据匹配方式添加对应的key
        if (showRuleMatch === 'value') {
            field.show_rule.value = showRuleValue;
        } else {
            field.show_rule.contain = showRuleValue;
        }
    } else {
        delete field.show_rule;
    }
    
    // 复制规则 (copy_rule)
    const copyRuleRadio = document.querySelector('input[name="copy-rule"]:checked')?.value;
    if (copyRuleRadio === 'with-button') {
        field.copy_rule = {}; // 可复制有按钮
    } else if (copyRuleRadio === '关闭') {
        field.copy_rule = '关闭'; // 不可复制
    } else {
        delete field.copy_rule; // 如果是"开启"（默认），不设置copy_rule字段
    }
    
    // 提示折叠 (tooltip)
    const tooltipWidth = document.getElementById('tooltip-width')?.value;
    const tooltipTrigger = document.getElementById('tooltip-trigger')?.value;
    const tooltipLength = document.getElementById('tooltip-length')?.value;
    const tooltipRow = document.getElementById('tooltip-row')?.value;
    
    if (tooltipWidth || tooltipTrigger || tooltipLength || tooltipRow) {
        field.tooltip = {};
        if (tooltipWidth) field.tooltip.width = parseInt(tooltipWidth);
        if (tooltipTrigger) field.tooltip.trigger = tooltipTrigger;
        if (tooltipLength) field.tooltip.length = parseInt(tooltipLength);
        if (tooltipRow) field.tooltip.row = parseInt(tooltipRow);
    } else {
        delete field.tooltip;
    }
    
    // 验证器
    const validatorItems = document.querySelectorAll('.validator-item');
    if (validatorItems.length > 0) {
        const validators = [];
        validatorItems.forEach(item => {
            const validatorName = item.querySelector('.validator-name').value.trim();
            const kwsStr = item.querySelector('.validator-kws').value.trim();
            if (validatorName) {
                const validator = { name: validatorName };
                if (kwsStr) {
                    try {
                        validator.kws = JSON.parse(kwsStr);
                    } catch (e) {
                        validator.kws = { raw: kwsStr };
                    }
                }
                validators.push(validator);
            }
        });
        if (validators.length > 0) {
            field.validators = validators;
        } else {
            delete field.validators;
        }
    } else {
        delete field.validators;
    }
    
    adminSystem.closeModal();
    adminSystem.updatePreview();
    adminSystem.showSuccessMessage('字段已更新！');
}

function removeField(fieldId) {
    if (!confirm('确认删除该字段？')) return;
    
    adminSystem.currentModel.fields = adminSystem.currentModel.fields.filter(f => f.id != fieldId);
    
    // 刷新字段配置模态框中的字段列表
    const fieldsList = document.getElementById('fields-list');
    if (fieldsList) {
        if (adminSystem.currentModel.fields.length === 0) {
            fieldsList.innerHTML = '<div style="text-align: center; padding: 40px; color: #9ca3af;">暂无字段，点击"添加字段"开始配置</div>';
        } else {
            fieldsList.innerHTML = adminSystem.currentModel.fields.map(field => adminSystem.renderFieldItem(field)).join('');
        }
    }
    
    // 更新预览
    adminSystem.updatePreview();
    adminSystem.showSuccessMessage('字段已删除！');
}

// deleteField 是 removeField 的别名，用于在表格中调用
function deleteField(fieldId) {
    removeField(fieldId);
}

// 切换预览标签
function switchPreviewTab(tab) {
    // 切换标签激活状态
    document.querySelectorAll('.preview-tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    // 隐藏所有内容
    document.getElementById('preview-list').style.display = 'none';
    document.getElementById('preview-form').style.display = 'none';
    document.getElementById('preview-edit').style.display = 'none';
    document.getElementById('preview-detail').style.display = 'none';
    
    // 显示选中的内容
    if (tab === 'list') {
        document.getElementById('preview-list').style.display = 'block';
    } else if (tab === 'form') {
        document.getElementById('preview-form').style.display = 'block';
    } else if (tab === 'edit') {
        document.getElementById('preview-edit').style.display = 'block';
    } else if (tab === 'detail') {
        document.getElementById('preview-detail').style.display = 'block';
    }
}

// 字段类型改变时的处理函数
function onFieldTypeChange(fieldType) {
    const specificDiv = document.getElementById('field-type-specific');
    if (!specificDiv) return;
    
    specificDiv.innerHTML = '';
    specificDiv.style.display = 'none';
    
    // 根据字段类型显示特定配置
    switch(fieldType) {
        case 'Select':
        case 'SelectMulti':
        case 'Radio':
            specificDiv.innerHTML = `
                <div class="form-group">
                    <label class="form-label">选项配置 (choices)</label>
                    <textarea class="form-input" id="field-choices" rows="4" placeholder='格式: [["key1", "label1"], ["key2", "label2"]] 或 URL地址'></textarea>
                    <small style="color: #6b7280; font-size: 12px;">支持常量数组或动态URL</small>
                </div>
                <div class="form-group">
                    <label class="form-label">值类型 (coerce)</label>
                    <select class="form-input" id="field-coerce">
                        <option value="string">string - 字符串</option>
                        <option value="int">int - 整数</option>
                        <option value="text_image">text_image - 图文</option>
                    </select>
                </div>
                ${fieldType !== 'SelectMulti' ? `
                <div class="form-group">
                    <label class="form-label">级联配置 (field_chains)</label>
                    <textarea class="form-input" id="field-chains" rows="3" placeholder='[{"child": "field_name", "params": ["param1"]}]'></textarea>
                </div>
                ` : ''}
                <div class="form-group">
                    <label style="display: flex; align-items: center; gap: 6px;">
                        <input type="checkbox" id="field-allow-create">
                        <span>允许输入自定义选项 (allow_create)</span>
                    </label>
                </div>
            `;
            specificDiv.style.display = 'block';
            break;
            
        case 'Image':
        case 'File':
        case 'ImageMulti':
        case 'FileMulti':
            specificDiv.innerHTML = `
                <div class="form-group">
                    <label class="form-label">上传方式 (style)</label>
                    <select class="form-input" id="field-style">
                        <option value="url">url - URL方式(S3)</option>
                        <option value="stream">stream - 二进制流</option>
                        <option value="large">large - 大文件(>10MB)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">配置名称 (config)</label>
                    <input type="text" class="form-input" id="field-config" placeholder="config_name">
                    <small style="color: #6b7280; font-size: 12px;">仅 url/large 方式需要</small>
                </div>
            `;
            specificDiv.style.display = 'block';
            break;
            
        case 'LinkString':
            specificDiv.innerHTML = `
                <div class="form-group">
                    <label class="form-label">跳转参数 (params)</label>
                    <input type="text" class="form-input" id="field-params" placeholder='["field1", "field2"]'>
                </div>
                <div class="form-group">
                    <label class="form-label">跳转模型 (model)</label>
                    <input type="text" class="form-input" id="field-model" placeholder="model_name 或 external-links">
                    <small style="color: #6b7280; font-size: 12px;">内部跳转填写模型名，外部跳转填 external-links</small>
                </div>
            `;
            specificDiv.style.display = 'block';
            break;
            
        case 'LinkForm':
        case 'InlineModel':
            specificDiv.innerHTML = `
                <div class="form-group">
                    <label class="form-label">表单名称 (form_name)</label>
                    <input type="text" class="form-input" id="field-form-name" placeholder="lf_form_name">
                </div>
                ${fieldType === 'LinkForm' ? `
                <div class="form-group">
                    <label class="form-label">可用动作 (actions)</label>
                    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                        <label><input type="checkbox" class="linkform-action" value="add"> add</label>
                        <label><input type="checkbox" class="linkform-action" value="delete"> delete</label>
                        <label><input type="checkbox" class="linkform-action" value="edit"> edit</label>
                        <label><input type="checkbox" class="linkform-action" value="import"> import</label>
                    </div>
                </div>
                ` : ''}
            `;
            specificDiv.style.display = 'block';
            break;
            
        case 'Calculation':
            specificDiv.innerHTML = `
                <div class="form-group">
                    <label class="form-label">计算公式 (formula)</label>
                    <input type="text" class="form-input" id="field-formula" placeholder="field1 * field2">
                </div>
                <div class="form-group">
                    <label class="form-label">字段映射 (field_conversion)</label>
                    <textarea class="form-input" id="field-conversion" rows="3" placeholder='{"field1": "real_field1", "field2": "real_field2"}'></textarea>
                </div>
            `;
            specificDiv.style.display = 'block';
            break;
            
        case 'JsonEditor':
            specificDiv.innerHTML = `
                <div class="form-group">
                    <label style="display: flex; align-items: center; gap: 6px;">
                        <input type="checkbox" id="field-out-selected">
                        <span>显示外部选择控件 (out_selected)</span>
                    </label>
                </div>
                <div class="form-group">
                    <label style="display: flex; align-items: center; gap: 6px;">
                        <input type="checkbox" id="field-expand-all">
                        <span>展开所有字段 (expand_all)</span>
                    </label>
                </div>
                <div class="form-group">
                    <label style="display: flex; align-items: center; gap: 6px;">
                        <input type="checkbox" id="field-show-diff">
                        <span>显示修改对比 (show_diff)</span>
                    </label>
                </div>
                <div class="form-group">
                    <label class="form-label">字段说明URL (remote_explain)</label>
                    <input type="text" class="form-input" id="field-remote-explain" placeholder="https://api.example.com/explains">
                </div>
            `;
            specificDiv.style.display = 'block';
            break;
            
        case 'DateTime':
            specificDiv.innerHTML = `
                <div class="form-group">
                    <label class="form-label">筛选规则 (filter_rules)</label>
                    <textarea class="form-input" id="field-filter-rules" rows="4" placeholder='{"value": "now", "range": 4, "left_interval": 3, "right_interval": 4}'></textarea>
                    <small style="color: #6b7280; font-size: 12px;">用于限制时间查询范围</small>
                </div>
            `;
            specificDiv.style.display = 'block';
            break;
    }
}

// 辅助函数：切换字段选择器的展开/收起
function toggleFieldSelector(id) {
    const selector = document.getElementById(`${id}-selector`);
    const header = selector.previousElementSibling.tagName === 'SMALL' 
        ? selector.previousElementSibling.previousElementSibling 
        : selector.previousElementSibling;
    const icon = header.querySelector('.toggle-icon');
    
    if (selector.style.display === 'none') {
        selector.style.display = 'block';
        icon.style.transform = 'rotate(180deg)';
        header.style.backgroundColor = '#e0f2f1';
    } else {
        selector.style.display = 'none';
        icon.style.transform = 'rotate(0deg)';
        header.style.backgroundColor = '#f8fafc';
    }
}

function toggleOtherFieldsSection() {
    const section = document.getElementById('other-fields-section');
    const icon = document.getElementById('other-fields-toggle');
    
    if (section.style.display === 'none') {
        section.style.display = 'block';
        icon.textContent = '▲';
    } else {
        section.style.display = 'none';
        icon.textContent = '▼';
    }
}

function toggleBasePropSection(sectionName) {
    const content = document.getElementById(`bp-${sectionName}-content`);
    const toggle = document.getElementById(`bp-${sectionName}-toggle`);
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.textContent = '▲';
        toggle.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        toggle.textContent = '▼';
        toggle.style.transform = 'rotate(0deg)';
    }
}

// 辅助函数：更新字段计数显示
function updateFieldCount(id) {
    const checkboxes = document.querySelectorAll(`input.field-checkbox[data-select-id="${id}"]:checked`);
    const count = checkboxes.length;
    const header = document.getElementById(`${id}-selector`).previousElementSibling;
    const countSpan = header.querySelector('span[style*="color: #14b8a6"]') || header.querySelector('span:last-child');
    
    if (header.tagName === 'SMALL') {
        const actualHeader = header.previousElementSibling;
        const actualCountSpan = actualHeader.querySelector('span[style*="color: #14b8a6"]') || actualHeader.querySelector('span:last-child');
        if (actualCountSpan) {
            actualCountSpan.textContent = count > 0 ? ` (已选 ${count} 个)` : ' (未选择)';
        }
    } else if (countSpan) {
        countSpan.textContent = count > 0 ? ` (已选 ${count} 个)` : ' (未选择)';
    }
}

// 辅助函数：全选/全不选字段
function toggleAllFields(selectId, checked) {
    const checkboxes = document.querySelectorAll(`input.field-checkbox[data-select-id="${selectId}"]`);
    checkboxes.forEach(cb => {
        cb.checked = checked;
    });
    // 更新计数
    updateFieldCount(selectId);
}

// 辅助函数：切换过滤字段的操作符显示
function toggleFilterField(checkbox) {
    const parent = checkbox.closest('div').parentElement;
    const operatorsDiv = parent.querySelector('.filter-operators');
    
    if (checkbox.checked) {
        operatorsDiv.style.display = 'flex';
        // 默认选中第一个操作符
        const firstOperator = operatorsDiv.querySelector('input[type="checkbox"]');
        if (firstOperator && !operatorsDiv.querySelector('input[type="checkbox"]:checked')) {
            firstOperator.checked = true;
        }
    } else {
        operatorsDiv.style.display = 'none';
        // 取消所有操作符的选中
        const operatorCheckboxes = operatorsDiv.querySelectorAll('input[type="checkbox"]');
        operatorCheckboxes.forEach(cb => cb.checked = false);
    }
}

// 打开配置对话框
async function openConfigDialog() {
    const modal = document.getElementById('config-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    
    modalTitle.textContent = '⚙️ 系统配置';
    
    try {
        // 从后端获取配置
        const response = await fetch('/api/config');
        const config = await response.json();
        
        modalBody.innerHTML = `
            <div style="margin-bottom: 20px;">
                <div style="background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 6px; padding: 16px; margin-bottom: 20px;">
                    <h4 style="margin: 0 0 8px 0; color: #0369a1; font-size: 14px;">📋 远程同步配置</h4>
                    <p style="margin: 0; color: #0c4a6e; font-size: 13px;">配置自动同步和远程项目的相关参数</p>
                </div>
                
                <div class="form-group">
                    <label class="form-label">项目路径</label>
                    <input type="text" class="form-input" id="config-project-path" value="${config.project_path?.value || ''}" 
                           placeholder="/path/to/your/project" style="font-family: monospace;">
                    <small style="display: block; color: #6b7280; font-size: 12px; margin-top: 4px;">
                        ${config.project_path?.description || ''}
                    </small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">项目启动文件</label>
                    <input type="text" class="form-input" id="config-project-app" value="${config.project_app?.value || ''}" 
                           placeholder="app.py" style="font-family: monospace;">
                    <small style="display: block; color: #6b7280; font-size: 12px; margin-top: 4px;">
                        ${config.project_app?.description || ''}
                    </small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">API 地址</label>
                    <input type="text" class="form-input" id="config-api-url" value="${config.api_url?.value || ''}" 
                           placeholder="http://..." style="font-family: monospace;">
                    <small style="display: block; color: #6b7280; font-size: 12px; margin-top: 4px;">
                        ${config.api_url?.description || ''}
                    </small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">同步地址</label>
                    <input type="text" class="form-input" id="config-sync-url" value="${config.sync_url?.value || ''}" 
                           placeholder="http://..." style="font-family: monospace;">
                    <small style="display: block; color: #6b7280; font-size: 12px; margin-top: 4px;">
                        ${config.sync_url?.description || ''}
                    </small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">首页地址</label>
                    <input type="text" class="form-input" id="config-home-url" value="${config.home_url?.value || ''}" 
                           placeholder="http://localhost:8000/home/" style="font-family: monospace;">
                    <small style="display: block; color: #6b7280; font-size: 12px; margin-top: 4px;">
                        ${config.home_url?.description || ''}
                    </small>
                </div>
                
                <div class="form-group">
                    <label class="form-label">认证 Token</label>
                    <textarea class="form-input" id="config-token" rows="4" 
                              placeholder="eyJhbGciOi..." style="font-family: monospace; font-size: 12px;">${config.token?.value || ''}</textarea>
                    <small style="display: block; color: #6b7280; font-size: 12px; margin-top: 4px;">
                        ${config.token?.description || ''}
                    </small>
                </div>
            </div>
            
            <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
                <button type="button" class="btn btn-primary" onclick="saveConfig()">
                    <span>💾</span>
                    <span>保存配置</span>
                </button>
            </div>
        `;
        
        modal.style.display = 'flex';
    } catch (error) {
        console.error('加载配置失败:', error);
        showToast('加载配置失败: ' + error.message, 'error');
    }
}

// 保存配置
async function saveConfig() {
    const configs = {
        project_path: document.getElementById('config-project-path').value,
        project_app: document.getElementById('config-project-app').value,
        api_url: document.getElementById('config-api-url').value,
        sync_url: document.getElementById('config-sync-url').value,
        home_url: document.getElementById('config-home-url').value,
        token: document.getElementById('config-token').value
    };
    
    try {
        const response = await fetch('/api/config/batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(configs)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('配置已保存！', 'success', 2000);
            closeModal();
        } else {
            showToast('保存失败: ' + (result.error || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('保存配置失败:', error);
        showToast('保存配置失败: ' + error.message, 'error');
    }
}

// Toast 通知函数 - 已禁用
function showToast(message, type = 'info', duration = 3000) {
    // 通知功能已完全禁用
}

// 添加进度条动画样式
if (!document.getElementById('progress-animations')) {
    const style = document.createElement('style');
    style.id = 'progress-animations';
    style.textContent = `
        @keyframes slideInUp {
            from {
                transform: translateY(100px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
}

// 初始化系统
let adminSystem;
document.addEventListener('DOMContentLoaded', () => {
    adminSystem = new AdminSystem();
    // 加载快速导入的仓库列表
    loadQuickRepositories();
});