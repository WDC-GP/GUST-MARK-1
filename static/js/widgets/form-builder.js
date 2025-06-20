/**
 * GUST Bot Enhanced - Form Builder Widget
 * =====================================
 * Dynamic form generation with validation and submission handling
 */

class FormBuilder {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = { ...this.defaultOptions, ...options };
        this.formData = {};
        this.validators = {};
        this.eventListeners = [];
        
        if (!this.container) {
            throw new Error(`Container element '${containerId}' not found`);
        }
        
        this.validationService = window.App?.services?.validation || new ValidationService();
        this.eventBus = window.App?.eventBus || window.EventBus;
        
        this.init();
    }
    
    get defaultOptions() {
        return {
            submitOnEnter: true,
            validateOnChange: true,
            showRequiredIndicators: true,
            resetAfterSubmit: false,
            submitButtonText: 'Submit',
            submitButtonClass: 'btn btn-primary',
            formClass: 'dynamic-form',
            fieldContainerClass: 'form-field',
            labelClass: 'form-label',
            inputClass: 'form-input',
            errorClass: 'form-error',
            requiredClass: 'required'
        };
    }
    
    init() {
        this.render();
        this.bindEvents();
    }
    
    render() {
        this.container.innerHTML = `
            <form class="${this.options.formClass}" id="${this.containerId}-form">
                <div class="form-fields"></div>
                <div class="form-actions">
                    <button type="submit" class="${this.options.submitButtonClass}">
                        ${this.options.submitButtonText}
                    </button>
                    ${this.options.showClearButton ? `
                        <button type="button" class="btn btn-secondary clear-btn">
                            Clear
                        </button>
                    ` : ''}
                </div>
                <div class="form-messages"></div>
            </form>
        `;
    }
    
    bindEvents() {
        const form = this.container.querySelector('form');
        const clearBtn = this.container.querySelector('.clear-btn');
        
        this.addEventListener(form, 'submit', (e) => this.handleSubmit(e));
        
        if (clearBtn) {
            this.addEventListener(clearBtn, 'click', () => this.clear());
        }
        
        if (this.options.submitOnEnter) {
            this.addEventListener(form, 'keypress', (e) => {
                if (e.key === 'Enter' && e.target.type !== 'textarea') {
                    e.preventDefault();
                    this.handleSubmit(e);
                }
            });
        }
    }
    
    /**
     * Add field to form
     * @param {Object} fieldConfig - Field configuration
     * @param {string} fieldConfig.name - Field name/ID
     * @param {string} fieldConfig.type - Input type (text, select, textarea, etc.)
     * @param {string} fieldConfig.label - Field label
     * @param {boolean} fieldConfig.required - Whether field is required
     * @param {string} fieldConfig.placeholder - Placeholder text
     * @param {Array} fieldConfig.options - Options for select fields
     * @param {Object} fieldConfig.validation - Validation rules
     * @param {string} fieldConfig.defaultValue - Default value
     */
    addField(fieldConfig) {
        const fieldsContainer = this.container.querySelector('.form-fields');
        const fieldElement = this.createField(fieldConfig);
        
        fieldsContainer.appendChild(fieldElement);
        
        // Store validation rules
        if (fieldConfig.validation) {
            this.validators[fieldConfig.name] = fieldConfig.validation;
        }
        
        // Bind field-specific events
        this.bindFieldEvents(fieldElement, fieldConfig);
        
        return this;
    }
    
    createField(config) {
        const fieldContainer = document.createElement('div');
        fieldContainer.className = this.options.fieldContainerClass;
        fieldContainer.dataset.fieldName = config.name;
        
        // Create label
        if (config.label) {
            const label = document.createElement('label');
            label.className = this.options.labelClass;
            label.setAttribute('for', config.name);
            label.textContent = config.label;
            
            if (config.required && this.options.showRequiredIndicators) {
                label.classList.add(this.options.requiredClass);
                label.innerHTML += ' <span class="required-indicator">*</span>';
            }
            
            fieldContainer.appendChild(label);
        }
        
        // Create input element
        const inputElement = this.createInputElement(config);
        fieldContainer.appendChild(inputElement);
        
        // Create error container
        const errorContainer = document.createElement('div');
        errorContainer.className = this.options.errorClass;
        errorContainer.style.display = 'none';
        fieldContainer.appendChild(errorContainer);
        
        return fieldContainer;
    }
    
    createInputElement(config) {
        let element;
        
        switch (config.type) {
            case 'select':
                element = this.createSelectElement(config);
                break;
            case 'textarea':
                element = this.createTextareaElement(config);
                break;
            case 'checkbox':
                element = this.createCheckboxElement(config);
                break;
            case 'radio':
                element = this.createRadioGroupElement(config);
                break;
            default:
                element = this.createInputField(config);
        }
        
        // Set common attributes
        element.id = config.name;
        element.name = config.name;
        
        if (config.defaultValue !== undefined) {
            if (config.type === 'checkbox') {
                element.checked = config.defaultValue;
            } else {
                element.value = config.defaultValue;
            }
            this.formData[config.name] = config.defaultValue;
        }
        
        if (config.required) {
            element.required = true;
        }
        
        return element;
    }
    
    createInputField(config) {
        const input = document.createElement('input');
        input.type = config.type || 'text';
        input.className = this.options.inputClass;
        
        if (config.placeholder) {
            input.placeholder = config.placeholder;
        }
        
        if (config.min !== undefined) input.min = config.min;
        if (config.max !== undefined) input.max = config.max;
        if (config.step !== undefined) input.step = config.step;
        if (config.pattern) input.pattern = config.pattern;
        
        return input;
    }
    
    createSelectElement(config) {
        const select = document.createElement('select');
        select.className = this.options.inputClass;
        
        // Add placeholder option
        if (config.placeholder) {
            const placeholderOption = document.createElement('option');
            placeholderOption.value = '';
            placeholderOption.textContent = config.placeholder;
            placeholderOption.disabled = true;
            placeholderOption.selected = true;
            select.appendChild(placeholderOption);
        }
        
        // Add options
        if (config.options) {
            config.options.forEach(option => {
                const optionElement = document.createElement('option');
                
                if (typeof option === 'string') {
                    optionElement.value = option;
                    optionElement.textContent = option;
                } else {
                    optionElement.value = option.value;
                    optionElement.textContent = option.label || option.value;
                    if (option.disabled) optionElement.disabled = true;
                }
                
                select.appendChild(optionElement);
            });
        }
        
        return select;
    }
    
    createTextareaElement(config) {
        const textarea = document.createElement('textarea');
        textarea.className = this.options.inputClass;
        
        if (config.placeholder) textarea.placeholder = config.placeholder;
        if (config.rows) textarea.rows = config.rows;
        if (config.cols) textarea.cols = config.cols;
        
        return textarea;
    }
    
    createCheckboxElement(config) {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-checkbox';
        
        return checkbox;
    }
    
    createRadioGroupElement(config) {
        const container = document.createElement('div');
        container.className = 'radio-group';
        
        if (config.options) {
            config.options.forEach(option => {
                const radioContainer = document.createElement('div');
                radioContainer.className = 'radio-item';
                
                const radio = document.createElement('input');
                radio.type = 'radio';
                radio.name = config.name;
                radio.value = typeof option === 'string' ? option : option.value;
                radio.id = `${config.name}_${radio.value}`;
                
                const label = document.createElement('label');
                label.setAttribute('for', radio.id);
                label.textContent = typeof option === 'string' ? option : option.label;
                
                radioContainer.appendChild(radio);
                radioContainer.appendChild(label);
                container.appendChild(radioContainer);
            });
        }
        
        return container;
    }
    
    bindFieldEvents(fieldElement, config) {
        const input = fieldElement.querySelector('input, select, textarea');
        
        if (!input) return;
        
        // Change event for form data tracking
        this.addEventListener(input, 'change', (e) => {
            this.updateFormData(config.name, e.target.value, e.target.type);
        });
        
        // Input event for real-time validation
        if (this.options.validateOnChange && config.validation) {
            this.addEventListener(input, 'input', (e) => {
                this.validateField(config.name, e.target.value);
            });
        }
        
        // Blur event for validation
        this.addEventListener(input, 'blur', (e) => {
            if (config.validation) {
                this.validateField(config.name, e.target.value);
            }
        });
    }
    
    updateFormData(fieldName, value, type) {
        if (type === 'checkbox') {
            this.formData[fieldName] = document.getElementById(fieldName).checked;
        } else if (type === 'radio') {
            const checkedRadio = this.container.querySelector(`input[name="${fieldName}"]:checked`);
            this.formData[fieldName] = checkedRadio ? checkedRadio.value : null;
        } else {
            this.formData[fieldName] = value;
        }
        
        // Emit data change event
        if (this.eventBus) {
            this.eventBus.emit('form:data-changed', {
                formId: this.containerId,
                fieldName,
                value: this.formData[fieldName],
                allData: { ...this.formData }
            });
        }
    }
    
    validateField(fieldName, value) {
        const validation = this.validators[fieldName];
        if (!validation) return true;
        
        const result = this.validationService.validateField(value, validation);
        this.displayFieldError(fieldName, result.isValid ? null : result.errors[0]);
        
        return result.isValid;
    }
    
    validateForm() {
        let isValid = true;
        const errors = {};
        
        // Validate all fields with validation rules
        Object.keys(this.validators).forEach(fieldName => {
            const value = this.formData[fieldName];
            const validation = this.validators[fieldName];
            
            const result = this.validationService.validateField(value, validation);
            if (!result.isValid) {
                isValid = false;
                errors[fieldName] = result.errors;
                this.displayFieldError(fieldName, result.errors[0]);
            } else {
                this.displayFieldError(fieldName, null);
            }
        });
        
        return { isValid, errors };
    }
    
    displayFieldError(fieldName, error) {
        const fieldContainer = this.container.querySelector(`[data-field-name="${fieldName}"]`);
        if (!fieldContainer) return;
        
        const errorContainer = fieldContainer.querySelector(`.${this.options.errorClass}`);
        const inputElement = fieldContainer.querySelector('input, select, textarea');
        
        if (error) {
            errorContainer.textContent = error;
            errorContainer.style.display = 'block';
            inputElement.classList.add('error');
            fieldContainer.classList.add('has-error');
        } else {
            errorContainer.style.display = 'none';
            inputElement.classList.remove('error');
            fieldContainer.classList.remove('has-error');
        }
    }
    
    displayFormMessage(message, type = 'info') {
        const messagesContainer = this.container.querySelector('.form-messages');
        messagesContainer.innerHTML = `
            <div class="form-message form-message--${type}">
                ${message}
            </div>
        `;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            messagesContainer.innerHTML = '';
        }, 5000);
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        // Collect current form data
        this.collectFormData();
        
        // Validate form
        const validation = this.validateForm();
        if (!validation.isValid) {
            this.displayFormMessage('Please fix the errors above', 'error');
            return;
        }
        
        // Emit submit event
        if (this.eventBus) {
            this.eventBus.emit('form:submit', {
                formId: this.containerId,
                data: { ...this.formData },
                originalEvent: e
            });
        }
        
        // Call submit handler if provided
        if (this.options.onSubmit) {
            try {
                await this.options.onSubmit(this.formData, this);
                
                if (this.options.resetAfterSubmit) {
                    this.clear();
                }
            } catch (error) {
                this.displayFormMessage(error.message || 'Submission failed', 'error');
            }
        }
    }
    
    collectFormData() {
        const form = this.container.querySelector('form');
        const formData = new FormData(form);
        
        // Update internal form data
        for (const [key, value] of formData.entries()) {
            this.formData[key] = value;
        }
        
        // Handle checkboxes (they won't appear in FormData if unchecked)
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            this.formData[checkbox.name] = checkbox.checked;
        });
    }
    
    setFieldValue(fieldName, value) {
        const element = this.container.querySelector(`#${fieldName}`);
        if (!element) return;
        
        if (element.type === 'checkbox') {
            element.checked = value;
        } else {
            element.value = value;
        }
        
        this.updateFormData(fieldName, value, element.type);
    }
    
    getFieldValue(fieldName) {
        return this.formData[fieldName];
    }
    
    getData() {
        this.collectFormData();
        return { ...this.formData };
    }
    
    setData(data) {
        Object.keys(data).forEach(fieldName => {
            this.setFieldValue(fieldName, data[fieldName]);
        });
    }
    
    clear() {
        const form = this.container.querySelector('form');
        form.reset();
        this.formData = {};
        
        // Clear all error messages
        const errorContainers = this.container.querySelectorAll(`.${this.options.errorClass}`);
        errorContainers.forEach(container => {
            container.style.display = 'none';
        });
        
        // Remove error classes
        const errorFields = this.container.querySelectorAll('.error, .has-error');
        errorFields.forEach(field => {
            field.classList.remove('error', 'has-error');
        });
        
        // Clear form messages
        const messagesContainer = this.container.querySelector('.form-messages');
        messagesContainer.innerHTML = '';
        
        if (this.eventBus) {
            this.eventBus.emit('form:cleared', { formId: this.containerId });
        }
    }
    
    disable() {
        const inputs = this.container.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => input.disabled = true);
    }
    
    enable() {
        const inputs = this.container.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => input.disabled = false);
    }
    
    addEventListener(element, event, handler) {
        element.addEventListener(event, handler);
        this.eventListeners.push({ element, event, handler });
    }
    
    destroy() {
        // Cleanup event listeners
        this.eventListeners.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this.eventListeners = [];
        
        // Clear container
        if (this.container) {
            this.container.innerHTML = '';
        }
        
        // Clear form data
        this.formData = {};
        this.validators = {};
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormBuilder;
} else {
    window.FormBuilder = FormBuilder;
}