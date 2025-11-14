// Primer Workflow 文件管理器核心逻辑
class WorkflowExplorer {
    constructor() {
        this.workflowData = null;
        this.folderStructure = null;
        this.currentPath = [];
        this.selectedNode = null;
        this.searchTerm = '';
        
        this.initializeEventListeners();
        this.loadSampleData();
    }

    initializeEventListeners() {
        // 文件上传
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // 搜索功能
        document.getElementById('searchBox').addEventListener('input', this.handleSearch.bind(this));

        // 键盘快捷键
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
    }

    loadSampleData() {
        // 加载示例数据用于演示
        const sampleWorkflow = {
            "export_status": "SUCCESS",
            "id": "sample-workflow",
            "version": 1,
            "workflow_source": {
                "name": "示例 Workflow",
                "description": "这是一个示例工作流",
                "status": "PUBLISHED",
                "workflow": {
                    "start": "trigger-1",
                    "blocks": [
                        {
                            "id": "trigger-1",
                            "type": "TRIGGER",
                            "name": "支付创建触发器",
                            "outcomes": {
                                "conditional": [{
                                    "next": "condition-1",
                                    "name": "支付方式判断"
                                }]
                            }
                        },
                        {
                            "id": "condition-1", 
                            "type": "CONDITION",
                            "name": "支付方式判断",
                            "condition_type": "MULTI_IF",
                            "outcomes": {
                                "conditional": [
                                    {
                                        "next": "condition-2",
                                        "name": "银行卡支付",
                                        "condition": {
                                            "expression": {"path": "paymentMethodType"},
                                            "operator": "=",
                                            "operand": {"value": "PAYMENT_CARD"}
                                        }
                                    },
                                    {
                                        "next": "app-3", 
                                        "name": "Apple Pay",
                                        "condition": {
                                            "expression": {"path": "paymentMethodType"},
                                            "operator": "=",
                                            "operand": {"value": "APPLE_PAY"}
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            "id": "condition-2",
                            "type": "CONDITION",
                            "name": "货币类型判断",
                            "condition_type": "MULTI_IF",
                            "outcomes": {
                                "conditional": [
                                    {
                                        "next": "app-1",
                                        "name": "USD货币",
                                        "condition": {
                                            "expression": {"path": "payment.currencyCode"},
                                            "operator": "=",
                                            "operand": {"value": "USD"}
                                        }
                                    },
                                    {
                                        "next": "app-2",
                                        "name": "EUR货币",
                                        "condition": {
                                            "expression": {"path": "payment.currencyCode"},
                                            "operator": "=",
                                            "operand": {"value": "EUR"}
                                        }
                                    }
                                ]
                            }
                        },
                        {
                            "id": "app-1",
                            "type": "APPLICATION",
                            "name": "Airwallex处理器",
                            "action_name": "Authorize payment",
                            "input_configuration": [
                                {
                                    "target": {"path": "processor"},
                                    "source": {
                                        "properties": [{
                                            "target": {"path": "processor_id"},
                                            "source": {"value": "AIRWALLEX"}
                                        }]
                                    }
                                },
                                {
                                    "target": {"path": "threeDs"},
                                    "source": {
                                        "properties": [{
                                            "target": {"path": "option"},
                                            "source": {"value": "FORCE_3DS"}
                                        }]
                                    }
                                }
                            ]
                        },
                        {
                            "id": "app-2",
                            "type": "APPLICATION",
                            "name": "Adyen处理器",
                            "action_name": "Authorize payment",
                            "input_configuration": [
                                {
                                    "target": {"path": "processor"},
                                    "source": {
                                        "properties": [{
                                            "target": {"path": "processor_id"},
                                            "source": {"value": "ADYEN"}
                                        }]
                                    }
                                },
                                {
                                    "target": {"path": "threeDs"},
                                    "source": {
                                        "properties": [{
                                            "target": {"path": "option"},
                                            "source": {"value": "ADAPTIVE_3DS"}
                                        }]
                                    }
                                }
                            ]
                        },
                        {
                            "id": "app-3",
                            "type": "APPLICATION", 
                            "name": "Stripe处理器",
                            "action_name": "Authorize payment",
                            "input_configuration": [
                                {
                                    "target": {"path": "processor"},
                                    "source": {
                                        "properties": [{
                                            "target": {"path": "processor_id"},
                                            "source": {"value": "STRIPE"}
                                        }]
                                    }
                                },
                                {
                                    "target": {"path": "threeDs"},
                                    "source": {
                                        "properties": [{
                                            "target": {"path": "option"},
                                            "source": {"value": "DO_NOT_PERFORM"}
                                        }]
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        };
        
        this.loadWorkflow(sampleWorkflow);
    }

    handleDragOver(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.add('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        document.getElementById('uploadArea').classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.loadFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.loadFile(files[0]);
        }
    }

    loadFile(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                this.loadWorkflow(data[0]); // Primer导出的是数组格式
            } catch (error) {
                this.showMessage('文件格式错误，请选择有效的JSON文件', 'error');
            }
        };
        reader.readAsText(file);
    }

    loadWorkflow(workflowData) {
        this.workflowData = workflowData;
        this.buildFolderStructure();
        this.renderFolderTree();
        this.updateWorkflowInfo();
        this.showMessage('Workflow 加载成功！', 'success');
    }

    buildFolderStructure() {
        const workflow = this.workflowData.workflow_source.workflow;
        
        // 创建基于流程的文件夹结构
        this.folderStructure = {
            name: 'Workflow Flow',
            type: 'folder',
            children: {}
        };

        // 创建block映射
        const blockMap = new Map();
        workflow.blocks.forEach(block => {
            blockMap.set(block.id, block);
        });

        // 从start开始构建流程树
        const startBlockId = workflow.start;
        const startBlock = blockMap.get(startBlockId);
        
        if (startBlock) {
            const rootFolder = this.buildFlowFolder(startBlock, blockMap, new Set());
            this.folderStructure.children['🚀 Workflow Start'] = rootFolder;
        }
    }

    // 递归构建流程文件夹
    buildFlowFolder(block, blockMap, visited) {
        if (visited.has(block.id)) {
            return {
                name: `⚠️ Circular Reference: ${this.getBlockDisplayName(block)}`,
                type: 'file',
                originalBlock: block,
                description: '检测到循环引用'
            };
        }

        visited.add(block.id);

        const blockData = this.createNodeFromBlock(block);
        blockData.type = 'folder';
        blockData.children = {};

        // 处理TRIGGER类型的outcomes - 直接显示所有条件分支
        if (block.type === 'TRIGGER' && block.outcomes) {
            // 处理conditional outcomes
            if (block.outcomes.conditional) {
                block.outcomes.conditional.forEach((outcome, index) => {
                    // 对于Trigger，我们需要展开条件的内容，而不是显示条件名称
                    if (outcome.next) {
                        const nextBlock = blockMap.get(outcome.next);
                        if (nextBlock && nextBlock.type === 'CONDITION') {
                            // 如果下一个是条件块，展开其条件
                            this.expandConditionBlock(nextBlock, blockData, blockMap, visited);
                        } else {
                            // 如果下一个是应用，直接显示
                            const conditionName = this.getOutcomeDisplayName(outcome, index);
                            const conditionFile = {
                                name: conditionName,
                                type: 'file',
                                originalOutcome: outcome,
                                description: this.getConditionDescription(outcome),
                                nextBlockId: outcome.next
                            };
                            blockData.children[conditionFile.name] = conditionFile;
                        }
                    }
                });
            }

            // 处理default outcome
            if (block.outcomes.default) {
                const defaultName = block.outcomes.default.name || 'All other conditions';
                const defaultFile = {
                    name: defaultName,
                    type: 'file',
                    originalOutcome: block.outcomes.default,
                    description: '默认路径',
                    nextBlockId: block.outcomes.default.next
                };
                blockData.children[defaultFile.name] = defaultFile;
            }
        }
        // 处理CONDITION类型的outcomes - 直接显示所有条件分支
        else if (block.type === 'CONDITION' && block.outcomes) {
            // 处理conditional outcomes
            if (block.outcomes.conditional) {
                block.outcomes.conditional.forEach((outcome, index) => {
                    const conditionName = this.getOutcomeDisplayName(outcome, index);
                    const conditionFile = {
                        name: conditionName,
                        type: 'file',
                        originalOutcome: outcome,
                        description: this.getConditionDescription(outcome),
                        nextBlockId: outcome.next
                    };
                    blockData.children[conditionFile.name] = conditionFile;
                });
            }

            // 处理default outcome
            if (block.outcomes.default) {
                const defaultName = block.outcomes.default.name || 'All other conditions';
                const defaultFile = {
                    name: defaultName,
                    type: 'file',
                    originalOutcome: block.outcomes.default,
                    description: '默认路径',
                    nextBlockId: block.outcomes.default.next
                };
                blockData.children[defaultFile.name] = defaultFile;
            }
        }
        // 处理APPLICATION类型 - 直接显示下一步
        else if (block.type === 'APPLICATION' && block.outcome && block.outcome.next) {
            const nextBlock = blockMap.get(block.outcome.next);
            if (nextBlock) {
                const nextFolder = this.buildFlowFolder(nextBlock, blockMap, new Set(visited));
                blockData.children['📁 Next Step'] = nextFolder;
            }
        }

        return blockData;
    }

    // 展开条件块，将其条件直接添加到父文件夹中
    expandConditionBlock(conditionBlock, parentFolder, blockMap, visited) {
        if (visited.has(conditionBlock.id)) return;
        
        // 处理conditional outcomes
        if (conditionBlock.outcomes && conditionBlock.outcomes.conditional) {
            conditionBlock.outcomes.conditional.forEach((outcome, index) => {
                const conditionName = this.getOutcomeDisplayName(outcome, index);
                const conditionFile = {
                    name: conditionName,
                    type: 'file',
                    originalOutcome: outcome,
                    description: this.getConditionDescription(outcome),
                    nextBlockId: outcome.next
                };
                parentFolder.children[conditionFile.name] = conditionFile;
            });
        }

        // 处理default outcome
        if (conditionBlock.outcomes && conditionBlock.outcomes.default) {
            const defaultName = conditionBlock.outcomes.default.name || 'All other conditions';
            const defaultFile = {
                name: defaultName,
                type: 'file',
                originalOutcome: conditionBlock.outcomes.default,
                description: '默认路径',
                nextBlockId: conditionBlock.outcomes.default.next
            };
            parentFolder.children[defaultFile.name] = defaultFile;
        }
    }

    // 获取outcome的显示名称
    getOutcomeDisplayName(outcome, index) {
        if (outcome.name) {
            return outcome.name;
        }
        
        // 根据条件内容生成名称
        if (outcome.condition) {
            const condition = outcome.condition;
            const operand = condition.operand;
            
            if (Array.isArray(operand)) {
                // 对于数组，显示所有选项
                const labels = operand.map(op => op.label || op.value);
                return labels.join('/');
            } else if (operand && operand.label) {
                return operand.label;
            } else if (operand && operand.value) {
                return operand.value;
            }
        }
        
        return `Condition ${index + 1}`;
    }

    // 获取条件描述
    getConditionDescription(outcome) {
        if (!outcome.condition) return '无条件分支';
        
        const condition = outcome.condition;
        const expression = condition.expression;
        
        if (expression && expression.type === 'BLOCK_OUTPUT_REFERENCE') {
            const path = expression.path;
            const operator = condition.operator;
            const operand = condition.operand;
            
            let operandText = '';
            if (Array.isArray(operand)) {
                operandText = operand.map(op => op.label || op.value).join(', ');
            } else {
                operandText = operand.label || operand.value || operand;
            }
            
            return `${path} ${operator} ${operandText}`;
        }
        
        return '自定义条件';
    }

    // 获取block显示名称
    getBlockDisplayName(block) {
        if (block.name) return block.name;
        
        switch (block.type) {
            case 'TRIGGER':
                return '触发器';
            case 'CONDITION':
                return '条件判断';
            case 'APPLICATION':
                return '支付处理';
            default:
                return '未知节点';
        }
    }

    createNodeFromBlock(block) {
        const node = {
            id: block.id,
            name: block.name || this.getDefaultName(block.type),
            type: block.type.toLowerCase(),
            originalBlock: block,
            description: this.getNodeDescription(block),
            properties: this.extractProperties(block)
        };
        
        return node;
    }

    getDefaultName(type) {
        const names = {
            'TRIGGER': '触发器',
            'CONDITION': '条件判断',
            'APPLICATION': '支付处理'
        };
        return names[type] || '未知节点';
    }

    getNodeDescription(block) {
        switch (block.type) {
            case 'TRIGGER':
                return block.trigger?.description || '支付创建触发器';
            case 'CONDITION':
                return `条件类型: ${block.condition_type || 'MULTI_IF'}`;
            case 'APPLICATION':
                return `动作: ${block.action_name || 'Authorize payment'}`;
            default:
                return '节点描述';
        }
    }

    extractProperties(block) {
        const properties = {};
        
        switch (block.type) {
            case 'TRIGGER':
                properties.description = block.trigger?.description || '支付创建触发器';
                properties.application_name = block.trigger?.application_name || 'Payment created';
                break;
                
            case 'CONDITION':
                properties.condition_type = block.condition_type || 'MULTI_IF';
                if (block.outcomes?.conditional) {
                    properties.conditions = block.outcomes.conditional.map(condition => ({
                        name: condition.name,
                        expression: condition.condition?.expression?.path,
                        operator: condition.condition?.operator,
                        operand: condition.condition?.operand?.value
                    }));
                }
                break;
                
            case 'APPLICATION':
                properties.action_name = block.action_name || 'Authorize payment';
                properties.application_name = block.application_instance_name || 'Primer Payments';
                properties.processor = this.extractProcessor(block);
                properties.three_ds = this.extract3DS(block);
                properties.fraud_checks = this.extractFraudChecks(block);
                properties.auto_actions = this.extractAutoActions(block);
                properties.preview_fields = this.extractPreviewFields(block);
                break;
        }
        
        return properties;
    }

    extractProcessor(block) {
        const processorConfig = block.input_configuration?.find(config => 
            config.target?.path === 'processor'
        );
        
        if (processorConfig?.source?.properties) {
            const processorId = processorConfig.source.properties.find(p => 
                p.target?.path === 'processor_id'
            )?.source;
            const mid = processorConfig.source.properties.find(p => 
                p.target?.path === 'mid'
            )?.source;
            const processorConfigId = processorConfig.source.properties.find(p => 
                p.target?.path === 'processor_config_id'
            )?.source;
            const merchantAccountId = processorConfig.source.properties.find(p => 
                p.target?.path === 'merchant_account_id'
            )?.source;
            
            return {
                processorId: processorId?.value || 'Unknown',
                processorLabel: processorId?.label || 'Unknown',
                mid: mid?.value || 'Unknown',
                processorConfigId: processorConfigId?.value || 'Unknown',
                processorConfigLabel: processorConfigId?.label || 'Unknown',
                merchantAccountId: merchantAccountId?.value || 'Unknown',
                merchantAccountLabel: merchantAccountId?.label || 'Unknown'
            };
        }
        
        return {
            processorId: 'Unknown',
            processorLabel: 'Unknown',
            mid: 'Unknown',
            processorConfigId: 'Unknown',
            processorConfigLabel: 'Unknown',
            merchantAccountId: 'Unknown',
            merchantAccountLabel: 'Unknown'
        };
    }

    extract3DS(block) {
        const threeDSConfig = block.input_configuration?.find(config => 
            config.target?.path === 'threeDs'
        );
        
        if (threeDSConfig?.source?.properties) {
            const option = threeDSConfig.source.properties.find(p => 
                p.target?.path === 'option'
            )?.source;
            const challengePreference = threeDSConfig.source.properties.find(p => 
                p.target?.path === 'challengePreference'
            )?.source;
            const exemption = threeDSConfig.source.properties.find(p => 
                p.target?.path === 'exemption'
            )?.source;
            
            return {
                option: option?.value || 'Unknown',
                optionLabel: option?.label || 'Unknown',
                challengePreference: challengePreference?.value || 'Unknown',
                challengePreferenceLabel: challengePreference?.label || 'Unknown',
                exemption: exemption?.value || 'Unknown',
                exemptionLabel: exemption?.label || 'Unknown'
            };
        }
        
        return {
            option: 'Unknown',
            optionLabel: 'Unknown',
            challengePreference: 'Unknown',
            challengePreferenceLabel: 'Unknown',
            exemption: 'Unknown',
            exemptionLabel: 'Unknown'
        };
    }

    extractFraudChecks(block) {
        const fraudConfig = block.input_configuration?.find(config => 
            config.target?.path === 'fraudChecks'
        );
        
        if (fraudConfig?.source?.properties) {
            const preAuth = fraudConfig.source.properties.find(p => 
                p.target?.path === 'preAuth'
            );
            const postAuth = fraudConfig.source.properties.find(p => 
                p.target?.path === 'postAuth'
            );
            const failRequestCancelPayment = fraudConfig.source.properties.find(p => 
                p.target?.path === 'failRequestCancelPayment'
            );
            const rejectResultCancelPayment = fraudConfig.source.properties.find(p => 
                p.target?.path === 'rejectResultCancelPayment'
            );
            
            return {
                preAuth: preAuth?.source?.properties?.find(p => 
                    p.target?.path === 'applyPreAuthFraudCheck'
                )?.source?.value || false,
                postAuth: postAuth?.source?.properties?.find(p => 
                    p.target?.path === 'applyPostAuthFraudCheck'
                )?.source?.value || false,
                failRequestCancelPayment: failRequestCancelPayment?.source?.value || false,
                rejectResultCancelPayment: rejectResultCancelPayment?.source?.value || false
            };
        }
        
        return { 
            preAuth: false, 
            postAuth: false, 
            failRequestCancelPayment: false, 
            rejectResultCancelPayment: false 
        };
    }

    extractAutoActions(block) {
        const autoActionsConfig = block.input_configuration?.find(config => 
            config.target?.path === 'autoActions'
        );
        
        if (autoActionsConfig?.source?.properties) {
            const autoNextStep = autoActionsConfig.source.properties.find(p => 
                p.target?.path === 'autoNextStep'
            )?.source;
            const status = autoActionsConfig.source.properties.find(p => 
                p.target?.path === 'status'
            )?.source;
            const captureAmount = autoActionsConfig.source.properties.find(p => 
                p.target?.path === 'captureAmount'
            )?.source;
            
            return {
                autoNextStep: autoNextStep?.value || 'CONTINUE_THEN_CAPTURE_PAYMENT',
                autoNextStepLabel: autoNextStep?.label || 'CONTINUE_THEN_CAPTURE_PAYMENT',
                status: status?.value || true,
                captureAmount: captureAmount?.value || 'Unknown',
                captureAmountLabel: captureAmount?.label || 'Unknown'
            };
        }
        
        return { 
            autoNextStep: 'CONTINUE_THEN_CAPTURE_PAYMENT', 
            autoNextStepLabel: 'CONTINUE_THEN_CAPTURE_PAYMENT',
            status: true,
            captureAmount: 'Unknown',
            captureAmountLabel: 'Unknown'
        };
    }

    extractPreviewFields(block) {
        // Extract preview fields which contain rich configuration information
        if (block.preview_fields && Array.isArray(block.preview_fields)) {
            return block.preview_fields.map(field => ({
                icon: field.icon || null,
                label: field.label || 'Unknown',
                value: field.value || 'Unknown'
            }));
        }
        return [];
    }

    renderFolderTree() {
        const treeContainer = document.getElementById('folderTree');
        const emptyState = document.getElementById('emptyState');
        
        if (!this.folderStructure) {
            emptyState.style.display = 'block';
            treeContainer.style.display = 'none';
            return;
        }
        
        emptyState.style.display = 'none';
        treeContainer.style.display = 'block';
        
        treeContainer.innerHTML = '';
        this.renderTreeItem(this.folderStructure, treeContainer, 0);
        
        // 显示搜索框
        document.getElementById('searchBox').style.display = 'block';
    }

    renderTreeItem(item, container, depth = 0) {
        const li = document.createElement('li');
        li.className = 'tree-item';
        
        const isFolder = item.children !== undefined;
        const hasChildren = isFolder && Object.keys(item.children).length > 0;
        
        li.innerHTML = `
            <div class="${isFolder ? 'tree-folder' : 'tree-file'}" data-path="${item.id || item.name}" data-type="${item.type}">
                ${hasChildren ? `<span class="tree-toggle" onclick="toggleFolder('${item.id || item.name}')">▶</span>` : '<span class="tree-toggle"></span>'}
                <span class="tree-icon ${item.type}">${this.getTypeIcon(item.type)}</span>
                <div class="tree-content">
                    <div class="tree-name">${item.name}</div>
                    <div class="tree-description">${item.description || ''}</div>
                </div>
            </div>
            ${hasChildren ? `<ul class="tree-children collapsed" id="children-${item.id || item.name}"></ul>` : ''}
        `;
        
        container.appendChild(li);
        
        // 添加点击事件
        const clickableElement = li.querySelector('.tree-folder, .tree-file');
        clickableElement.addEventListener('click', (e) => {
            e.stopPropagation();
            if (isFolder) {
                this.navigateToFolder(item);
            } else {
                this.selectNode(item);
            }
        });
        
        // 如果有子项，递归渲染
        if (hasChildren) {
            const childrenContainer = li.querySelector('.tree-children');
            Object.values(item.children).forEach(child => {
                this.renderTreeItem(child, childrenContainer, depth + 1);
            });
        }
    }

    getTypeIcon(type) {
        const icons = {
            'folder': '📁',
            'trigger': '🎯',
            'condition': '🔀',
            'application': '⚙️'
        };
        return icons[type] || '📄';
    }

    getIconForField(iconName) {
        const iconMap = {
            'AIRWALLEX': '🏦',
            'ADYEN': '💳',
            'STRIPE': '💎',
            'PAYPAL': '🅿️',
            'SQUARE': '⬜',
            'BRAINTREE': '🌳',
            'WORLDPAY': '🌍',
            'CYBERSOURCE': '🔒',
            'AMAZON_PAY': '📦',
            'GOOGLE_PAY': '🔍',
            'APPLE_PAY': '🍎'
        };
        return iconMap[iconName] || '⚙️';
    }

    navigateToFolder(folder) {
        this.currentPath.push(folder);
        this.updateBreadcrumb();
        this.renderCurrentFolder();
    }

    updateBreadcrumb() {
        const breadcrumb = document.getElementById('breadcrumb');
        breadcrumb.innerHTML = '';
        
        // 添加根目录
        const rootItem = document.createElement('span');
        rootItem.className = 'breadcrumb-item';
        rootItem.textContent = '🏠 根目录';
        rootItem.addEventListener('click', () => this.navigateToRoot());
        breadcrumb.appendChild(rootItem);
        
        // 添加路径项
        this.currentPath.forEach((folder, index) => {
            const separator = document.createElement('span');
            separator.textContent = ' / ';
            separator.style.color = '#a0aec0';
            breadcrumb.appendChild(separator);
            
            const item = document.createElement('span');
            item.className = index === this.currentPath.length - 1 ? 'breadcrumb-item active' : 'breadcrumb-item';
            item.textContent = `${this.getTypeIcon(folder.type)} ${folder.name}`;
            
            if (index !== this.currentPath.length - 1) {
                item.addEventListener('click', () => this.navigateToIndex(index));
            }
            
            breadcrumb.appendChild(item);
        });
    }

    navigateToRoot() {
        this.currentPath = [];
        this.renderFolderTree();
        this.updateBreadcrumb();
    }

    navigateToIndex(index) {
        this.currentPath = this.currentPath.slice(0, index + 1);
        this.updateBreadcrumb();
        this.renderCurrentFolder();
    }

    renderCurrentFolder() {
        const treeContainer = document.getElementById('folderTree');
        treeContainer.innerHTML = '';
        
        const currentFolder = this.currentPath.length === 0 ? 
            this.folderStructure : 
            this.currentPath[this.currentPath.length - 1];
        
        if (currentFolder.children) {
            Object.values(currentFolder.children).forEach(child => {
                this.renderTreeItem(child, treeContainer);
            });
        }
    }

    selectNode(node) {
        // 如果是条件文件且有下一个block，创建文件夹并导航进去
        if (node.originalOutcome && node.nextBlockId) {
            this.navigateToConditionFolder(node);
            return;
        }
        
        // 移除之前的选中状态
        document.querySelectorAll('.tree-file.selected, .tree-folder.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        // 添加选中状态
        const selectedElement = document.querySelector(`[data-path="${node.id}"]`);
        if (selectedElement) {
            selectedElement.classList.add('selected');
        }
        
        this.selectedNode = node;
        this.showNodeDetail(node);
    }

    // 导航到条件文件夹
    navigateToConditionFolder(conditionNode) {
        const workflow = this.workflowData.workflow_source.workflow;
        const blockMap = new Map();
        workflow.blocks.forEach(block => {
            blockMap.set(block.id, block);
        });
        
        const nextBlock = blockMap.get(conditionNode.nextBlockId);
        if (!nextBlock) return;

        // 创建条件文件夹
        const conditionFolder = {
            name: conditionNode.name,
            type: 'folder',
            children: {},
            description: `条件: ${conditionNode.description}`
        };

        // 根据下一个block的类型添加内容
        if (nextBlock.type === 'APPLICATION') {
            // 如果下一个是Application，添加Application文件
            const applicationFile = this.createNodeFromBlock(nextBlock);
            applicationFile.type = 'application'; // 保持为application类型以显示详细配置
            applicationFile.name = nextBlock.name || 'Primer Payments';
            conditionFolder.children[applicationFile.name] = applicationFile;
        } else if (nextBlock.type === 'CONDITION') {
            // 如果下一个是Condition，展开其条件
            this.expandConditionBlock(nextBlock, conditionFolder, blockMap, new Set());
        }

        // 添加到当前路径并导航
        this.currentPath.push(conditionFolder);
        this.renderCurrentFolder();
        this.updateBreadcrumb();
    }


    // 导航到下一个block
    navigateToNextBlock(nextBlockId) {
        const workflow = this.workflowData.workflow_source.workflow;
        const blockMap = new Map();
        workflow.blocks.forEach(block => {
            blockMap.set(block.id, block);
        });
        
        const nextBlock = blockMap.get(nextBlockId);
        if (nextBlock) {
            // 创建新的文件夹结构
            const nextFolder = this.buildFlowFolder(nextBlock, blockMap, new Set());
            
            // 添加到当前路径
            this.currentPath.push(nextFolder);
            this.renderCurrentFolder();
            this.updateBreadcrumb();
        }
    }

    showNodeDetail(node) {
        const detailEmptyState = document.getElementById('detailEmptyState');
        const detailContent = document.getElementById('detailContent');
        
        detailEmptyState.style.display = 'none';
        detailContent.style.display = 'block';
        
        // 更新标题
        document.getElementById('detailTitle').textContent = node.name;
        document.getElementById('detailIcon').textContent = this.getTypeIcon(node.type);
        
        // 更新详情内容
        const detailBody = document.getElementById('detailBody');
        detailBody.innerHTML = this.generateDetailContent(node);
    }

    generateDetailContent(node) {
        // 如果是条件文件，显示条件详情
        if (node.originalOutcome) {
            return this.generateOutcomeDetail(node);
        }
        
        // 如果有originalBlock且是APPLICATION类型，显示详细配置
        if (node.originalBlock && node.originalBlock.type === 'APPLICATION') {
            return this.generateApplicationDetail(node);
        }
        
        switch (node.type) {
            case 'trigger':
            case 'folder':
                return this.generateTriggerDetail(node);
            case 'condition':
                return this.generateConditionDetail(node);
            case 'application':
                return this.generateApplicationDetail(node);
            case 'file':
                return this.generateFileDetail(node);
            default:
                return '<div class="empty-state"><div class="empty-title">未知节点类型</div></div>';
        }
    }

    generateTriggerDetail(node) {
        const props = node.properties;
        return `
            <div class="detail-section">
                <div class="section-title">
                    <span>🎯</span>
                    基本信息
                </div>
                <div class="property-grid">
                    <div class="property-card">
                        <div class="property-name">描述</div>
                        <div class="property-value">${props.description || '无描述'}</div>
                    </div>
                    <div class="property-card">
                        <div class="property-name">应用名称</div>
                        <div class="property-value">${props.application_name || '未知'}</div>
                    </div>
                    <div class="property-card">
                        <div class="property-name">节点ID</div>
                        <div class="property-value highlight">${node.id}</div>
                    </div>
                </div>
            </div>
        `;
    }

    generateConditionDetail(node) {
        const props = node.properties;
        return `
            <div class="detail-section">
                <div class="section-title">
                    <span>🔀</span>
                    条件配置
                </div>
                <div class="property-grid">
                    <div class="property-card">
                        <div class="property-name">条件类型</div>
                        <div class="property-value highlight">${props.condition_type || 'MULTI_IF'}</div>
                    </div>
                    <div class="property-card">
                        <div class="property-name">节点ID</div>
                        <div class="property-value highlight">${node.id}</div>
                    </div>
                </div>
            </div>
            ${props.conditions && props.conditions.length > 0 ? `
                <div class="detail-section">
                    <div class="section-title">
                        <span>📋</span>
                        条件列表
                    </div>
                    <ul class="condition-list">
                        ${props.conditions.map(condition => `
                            <li class="condition-item">
                                <div class="condition-name">${condition.name}</div>
                                <div class="condition-expression">
                                    ${condition.expression} ${condition.operator} ${condition.operand}
                                </div>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
    }

    generateApplicationDetail(node) {
        const props = node.properties;
        return `
            <div class="detail-section">
                <div class="section-title">
                    <span>⚙️</span>
                    应用配置
                </div>
                <div class="property-grid">
                    <div class="property-card">
                        <div class="property-name">动作名称</div>
                        <div class="property-value highlight">${props.action_name || '未知'}</div>
                    </div>
                    <div class="property-card">
                        <div class="property-name">应用实例</div>
                        <div class="property-value">${props.application_name || '未知'}</div>
                    </div>
                    <div class="property-card">
                        <div class="property-name">节点ID</div>
                        <div class="property-value highlight">${node.id}</div>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <div class="section-title">
                    <span>💳</span>
                    处理器配置
                </div>
                <div class="property-grid">
                    <div class="property-card processor">
                        <div class="property-name">处理器类型</div>
                        <div class="property-value highlight">${props.processor?.processorLabel || '未知'}</div>
                    </div>
                    <div class="property-card processor">
                        <div class="property-name">处理器ID</div>
                        <div class="property-value">${props.processor?.processorId || '未知'}</div>
                    </div>
                    <div class="property-card processor">
                        <div class="property-name">商户ID (MID)</div>
                        <div class="property-value">${props.processor?.mid || '未知'}</div>
                    </div>
                    <div class="property-card processor">
                        <div class="property-name">处理器配置ID</div>
                        <div class="property-value">${props.processor?.processorConfigId || '未知'}</div>
                    </div>
                    <div class="property-card processor">
                        <div class="property-name">商户账户ID</div>
                        <div class="property-value">${props.processor?.merchantAccountId || '未知'}</div>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <div class="section-title">
                    <span>🔐</span>
                    3D Secure 配置
                </div>
                <div class="property-grid">
                    <div class="property-card three-ds">
                        <div class="property-name">3DS选项</div>
                        <div class="property-value highlight">${props.three_ds?.option || '未知'}</div>
                    </div>
                    <div class="property-card three-ds">
                        <div class="property-name">挑战偏好</div>
                        <div class="property-value">${props.three_ds?.challengePreference || '未知'}</div>
                    </div>
                    <div class="property-card three-ds">
                        <div class="property-name">豁免设置</div>
                        <div class="property-value">${props.three_ds?.exemption || '未知'}</div>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <div class="section-title">
                    <span>🛡️</span>
                    欺诈检测
                </div>
                <div class="property-grid">
                    <div class="property-card fraud">
                        <div class="property-name">预授权检测</div>
                        <div class="property-value">${props.fraud_checks?.preAuth ? '启用' : '禁用'}</div>
                    </div>
                    <div class="property-card fraud">
                        <div class="property-name">后授权检测</div>
                        <div class="property-value">${props.fraud_checks?.postAuth ? '启用' : '禁用'}</div>
                    </div>
                    <div class="property-card fraud">
                        <div class="property-name">失败请求取消支付</div>
                        <div class="property-value">${props.fraud_checks?.failRequestCancelPayment ? '启用' : '禁用'}</div>
                    </div>
                    <div class="property-card fraud">
                        <div class="property-name">拒绝结果取消支付</div>
                        <div class="property-value">${props.fraud_checks?.rejectResultCancelPayment ? '启用' : '禁用'}</div>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <div class="section-title">
                    <span>🔄</span>
                    自动操作
                </div>
                <div class="property-grid">
                    <div class="property-card auto">
                        <div class="property-name">自动下一步</div>
                        <div class="property-value highlight">${props.auto_actions?.autoNextStepLabel || props.auto_actions?.autoNextStep || 'CONTINUE_THEN_CAPTURE_PAYMENT'}</div>
                    </div>
                    <div class="property-card auto">
                        <div class="property-name">自动捕获状态</div>
                        <div class="property-value">${props.auto_actions?.status ? '启用' : '禁用'}</div>
                    </div>
                    <div class="property-card auto">
                        <div class="property-name">捕获金额</div>
                        <div class="property-value">${props.auto_actions?.captureAmountLabel || props.auto_actions?.captureAmount || '未知'}</div>
                    </div>
                </div>
            </div>
            
            ${props.preview_fields && props.preview_fields.length > 0 ? `
            <div class="detail-section">
                <div class="section-title">
                    <span>📋</span>
                    配置预览
                </div>
                <div class="property-grid">
                    ${props.preview_fields.map(field => `
                        <div class="property-card">
                            <div class="property-name">
                                ${field.icon ? `<span style="margin-right: 0.5rem;">${this.getIconForField(field.icon)}</span>` : ''}
                                ${field.label}
                            </div>
                            <div class="property-value ${field.value.includes('(') ? 'highlight' : ''}">${field.value}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
            ` : ''}
        `;
    }

    // 生成条件详情
    generateOutcomeDetail(node) {
        const outcome = node.originalOutcome;
        const condition = outcome.condition;
        
        return `
            <div class="detail-section">
                <div class="section-title">
                    <span>🔀</span>
                    条件详情
                </div>
                <div class="property-grid">
                    <div class="property-card">
                        <div class="property-name">条件名称</div>
                        <div class="property-value highlight">${node.name}</div>
                    </div>
                    <div class="property-card">
                        <div class="property-name">条件ID</div>
                        <div class="property-value">${outcome.id}</div>
                    </div>
                    <div class="property-card">
                        <div class="property-name">描述</div>
                        <div class="property-value">${node.description || '无条件描述'}</div>
                    </div>
                    ${outcome.next ? `
                    <div class="property-card">
                        <div class="property-name">下一个节点</div>
                        <div class="property-value highlight">${outcome.next}</div>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            ${condition ? `
            <div class="detail-section">
                <div class="section-title">
                    <span>🔍</span>
                    条件表达式
                </div>
                <div class="property-grid">
                    <div class="property-card">
                        <div class="property-name">表达式类型</div>
                        <div class="property-value">${condition.expression?.type || '未知'}</div>
                    </div>
                    ${condition.expression?.path ? `
                    <div class="property-card">
                        <div class="property-name">路径</div>
                        <div class="property-value highlight">${condition.expression.path}</div>
                    </div>
                    ` : ''}
                    <div class="property-card">
                        <div class="property-name">操作符</div>
                        <div class="property-value highlight">${condition.operator}</div>
                    </div>
                    <div class="property-card">
                        <div class="property-name">操作数</div>
                        <div class="property-value">${this.formatOperand(condition.operand)}</div>
                    </div>
                </div>
            </div>
            ` : ''}
        `;
    }

    // 生成文件详情
    generateFileDetail(node) {
        return `
            <div class="detail-section">
                <div class="section-title">
                    <span>📄</span>
                    文件信息
                </div>
                <div class="property-grid">
                    <div class="property-card">
                        <div class="property-name">文件名</div>
                        <div class="property-value highlight">${node.name}</div>
                    </div>
                    <div class="property-card">
                        <div class="property-name">描述</div>
                        <div class="property-value">${node.description || '无描述'}</div>
                    </div>
                    ${node.id ? `
                    <div class="property-card">
                        <div class="property-name">节点ID</div>
                        <div class="property-value">${node.id}</div>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // 格式化操作数
    formatOperand(operand) {
        if (Array.isArray(operand)) {
            return operand.map(op => op.label || op.value).join(', ');
        } else if (operand && typeof operand === 'object') {
            return operand.label || operand.value || JSON.stringify(operand);
        } else {
            return operand || '无';
        }
    }

    handleSearch(e) {
        this.searchTerm = e.target.value.toLowerCase();
        this.renderFolderTree();
        
        if (this.searchTerm) {
            this.filterTreeItems();
        }
    }

    filterTreeItems() {
        const items = document.querySelectorAll('.tree-file, .tree-folder');
        items.forEach(item => {
            const name = item.querySelector('.tree-name').textContent.toLowerCase();
            const description = item.querySelector('.tree-description').textContent.toLowerCase();
            
            if (name.includes(this.searchTerm) || description.includes(this.searchTerm)) {
                item.style.display = 'flex';
                item.parentElement.style.display = 'block';
            } else {
                item.style.display = 'none';
                item.parentElement.style.display = 'none';
            }
        });
    }

    handleKeyDown(e) {
        if (e.key === 'Escape') {
            this.searchTerm = '';
            document.getElementById('searchBox').value = '';
            this.renderFolderTree();
        }
    }

    updateWorkflowInfo() {
        const info = document.getElementById('workflowInfo');
        if (!this.workflowData) {
            info.style.display = 'none';
            return;
        }
        
        info.style.display = 'block';
        
        // 统计节点数量
        const stats = this.countNodes();
        document.getElementById('triggerCount').textContent = stats.triggers;
        document.getElementById('conditionCount').textContent = stats.conditions;
        document.getElementById('applicationCount').textContent = stats.applications;
        
        document.getElementById('workflowName').textContent = this.workflowData.workflow_source.name || 'Unknown';
        document.getElementById('workflowVersion').textContent = this.workflowData.version || 'Unknown';
        
        const status = this.workflowData.workflow_source.status || 'Unknown';
        const statusElement = document.getElementById('workflowStatus');
        statusElement.textContent = status;
        statusElement.className = `info-value status-badge status-${status.toLowerCase()}`;
    }

    countNodes() {
        const stats = { triggers: 0, conditions: 0, applications: 0 };
        
        if (this.folderStructure?.children) {
            Object.values(this.folderStructure.children).forEach(folder => {
                Object.values(folder.children).forEach(node => {
                    switch (node.type) {
                        case 'trigger':
                            stats.triggers++;
                            break;
                        case 'condition':
                            stats.conditions++;
                            break;
                        case 'application':
                            stats.applications++;
                            break;
                    }
                });
            });
        }
        
        return stats;
    }

    showMessage(message, type) {
        // 创建消息元素
        const messageEl = document.createElement('div');
        messageEl.className = `status-message status-${type}`;
        messageEl.textContent = message;
        messageEl.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 2000;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            font-weight: 500;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        `;
        
        if (type === 'success') {
            messageEl.style.background = 'rgba(72, 187, 120, 0.9)';
            messageEl.style.color = 'white';
        } else {
            messageEl.style.background = 'rgba(245, 101, 101, 0.9)';
            messageEl.style.color = 'white';
        }
        
        document.body.appendChild(messageEl);
        
        // 3秒后自动移除
        setTimeout(() => {
            messageEl.remove();
        }, 3000);
    }

    // 导出功能
    exportWorkflow() {
        if (!this.workflowData) {
            this.showMessage('没有可导出的workflow数据', 'error');
            return;
        }
        
        // 构建导出数据
        const exportData = this.buildExportData();
        
        // 创建下载链接
        const dataStr = JSON.stringify([exportData], null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = `workflow-${this.workflowData.id || 'export'}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
        this.showMessage('Workflow 导出成功！', 'success');
    }

    buildExportData() {
        // 这里需要根据可视化数据重建Primer格式的JSON
        // 这是一个简化的实现，实际应用中需要更完整的转换逻辑
        
        const blocks = [];
        
        // 从文件夹结构中提取所有节点
        if (this.folderStructure?.children) {
            Object.values(this.folderStructure.children).forEach(folder => {
                Object.values(folder.children).forEach(node => {
                    blocks.push(node.originalBlock);
                });
            });
        }
        
        return {
            export_status: "SUCCESS",
            id: this.workflowData.id,
            version: this.workflowData.version,
            workflow_source: {
                ...this.workflowData.workflow_source,
                workflow: {
                    start: blocks[0]?.id,
                    blocks: blocks
                }
            }
        };
    }

    saveWorkflow() {
        // 保存到本地存储
        if (!this.workflowData) {
            this.showMessage('没有可保存的workflow数据', 'error');
            return;
        }
        
        const workflowData = {
            workflowData: this.workflowData,
            folderStructure: this.folderStructure,
            currentPath: this.currentPath,
            timestamp: new Date().toISOString()
        };
        
        localStorage.setItem('savedWorkflowExplorer', JSON.stringify(workflowData));
        this.showMessage('Workflow 已保存到本地存储！', 'success');
    }
}

// 全局函数
let explorer;

window.addEventListener('DOMContentLoaded', () => {
    explorer = new WorkflowExplorer();
});

// 全局函数定义
function toggleFolder(folderId) {
    const toggle = document.querySelector(`[onclick="toggleFolder('${folderId}')"]`);
    const children = document.getElementById(`children-${folderId}`);
    
    if (children) {
        if (children.classList.contains('collapsed')) {
            children.classList.remove('collapsed');
            toggle.classList.add('expanded');
        } else {
            children.classList.add('collapsed');
            toggle.classList.remove('expanded');
        }
    }
}

function exportWorkflow() {
    explorer.exportWorkflow();
}

function saveWorkflow() {
    explorer.saveWorkflow();
}

function editNode() {
    if (explorer.selectedNode) {
        // 这里可以实现编辑功能
        explorer.showMessage('编辑功能开发中...', 'success');
    }
}
