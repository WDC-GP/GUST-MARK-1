/**
 * GUST Bot Enhanced - Form Component Class
 * =======================================
 * Specialized base class for form handling components.
 * Provides validation, submission, field management, and error handling.
 */

class FormComponent extends BaseComponent {
    /**
     * Initialize form component
     * @param {string} containerId - Container element ID
     * @param {Object} options - Form configuration options
     */
    constructor(containerId, options = {}) {
        super(containerId, options);
        
        this.formElement = null;
        this.fields = new Map();
        this.validators = new Map();
        this.isSubmitting = false;
        this.validationErrors = new Map();
        
        // Form-specific state
        this.setState({
            isValid: false,
            isDirty: false,
            submissionCount: 0,
            lastSubmission: null
        });
    }
    
    /**
     * Default options for form components
     */
    get defaultOptions() {
        return {
            ...super.defaultOptions,
            formSelector: 'form',
            validateOnChange: true,
            validateOnBlur: true,
            showValidationErrors: true,
            resetAfterSubmit: true,
            confirmBeforeReset: false,
            submitButtonText: 'Submit',
            resetButtonText: 'Reset',
            loadingButtonText: 'Submitting...',
            autoFocus: true,
            preventDoubleSubmit: true
        };
    }
    
    /**
     * Get initial form state
     */
    getInitialState() {
        return {
            ...super.getInitialState(),
            isValid: false,
            isDirty: false,
            submissionCount: 0,
            lastSubmission: null,
            formData: {}
        };
    }
    
    /**
     * Define form fields configuration
     * Override in subclasses to define field structure
     * @returns {Object} Field definitions
     */
    getFormFields() {
        return {
            // Example field definition:
            // fieldName: {
            //     type: 'text|email|password|number|select|checkbox|textarea',
            //     label: 'Field Label',
            //     placeholder: 'Placeholder text',
            //     required: true,
            //     validation: {
            //         rules: ['required', 'email', 'minLength:3'],
            //         custom: (value) => value.length > 0 || 'Custom error message'
            //     },
            //     options: [], // For select fields
            //     attributes: {} // Additional HTML attributes
            // }
        };
    }
    
    /**
     * Setup form after rendering
     */
    async onReady() {
        await super.onReady();
        
        this.formElement = this.container.querySelector(this.options.formSelector);
        if (!this.formElement) {
            throw new Error(`Form element not found with selector: ${this.options.formSelector}`);
        }
        
        this.setupFormFields();
        this.setupValidation();
        this.setupFormEvents();
        
        // Auto-focus first field if enabled
        if (this.options.autoFocus) {
            this.focusFirstField();
        }
        
        this.log('Form component ready');
    }
    
    /**
     * Render form HTML
     * Can be overridden for custom form layouts
     */
    render() {
        const fields = this.getFormFields();
        const formHTML = this.generateFormHTML(fields);
        
        this.container.innerHTML = `
            <div class="form-component">
                <form class="form" novalidate>
                    ${formHTML}
                    <div class="form-actions">
                        ${this.renderFormActions()}
                    </div>
                </form>
                <div class="form-errors hidden"></div>
            </div>
        `;
    }
    
    /**
     * Generate HTML for all form fields
     * @param {Object} fields - Field definitions
     * @returns {string} Generated HTML
     */
    generateFormHTML(fields) {
        return Object.entries(fields)
            .map(([fieldName, config]) => this.renderField(fieldName, config))
            .join('');
    }
    
    /**
     * Render individual form field
     * @param {string} fieldName - Field name
     * @param {Object} config - Field configuration
     * @returns {string} Field HTML
     */
    renderField(fieldName, config) {
        const {
            type = 'text',
            label = '',
            placeholder = '',
            required = false,
            options = [],
            attributes = {},
            helpText = ''
        } = config;
        
        const fieldId = `${fieldName}_${this.containerId}`;
        const requiredAttr = required ? 'required' : '';
        const requiredMark = required ? '<span class="text-red-400">*</span>' : '';
        
        let fieldHTML = '';
        
        switch (type) {
            case 'select':
                fieldHTML = `
                    <select id="${fieldId}" name="${fieldName}" 
                            class="form-select w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500" 
                            ${requiredAttr} ${this.attributesToString(attributes)}>
                        <option value="">Choose...</option>
                        ${options.map(option => 
                            `<option value="${option.value || option}">${option.label || option}</option>`
                        ).join('')}
                    </select>
                `;
                break;
                
            case 'textarea':
                fieldHTML = `
                    <textarea id="${fieldId}" name="${fieldName}" 
                              placeholder="${this.escapeHtml(placeholder)}"
                              class="form-textarea w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500 h-24" 
                              ${requiredAttr} ${this.attributesToString(attributes)}></textarea>
                `;
                break;
                
            case 'checkbox':
                fieldHTML = `
                    <div class="flex items-center">
                        <input type="checkbox" id="${fieldId}" name="${fieldName}" 
                               class="form-checkbox mr-2" 
                               ${requiredAttr} ${this.attributesToString(attributes)}>
                        <label for="${fieldId}" class="text-sm">${this.escapeHtml(label)}</label>
                    </div>
                `;
                return `
                    <div class="form-field mb-4">
                        ${fieldHTML}
                        ${helpText ? `<div class="form-help text-xs text-gray-400 mt-1">${this.escapeHtml(helpText)}</div>` : ''}
                        <div class="field-error text-red-400 text-sm mt-1 hidden"></div>
                    </div>
                `;
                
            default:
                fieldHTML = `
                    <input type="${type}" id="${fieldId}" name="${fieldName}" 
                           placeholder="${this.escapeHtml(placeholder)}"
                           class="form-input w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500" 
                           ${requiredAttr} ${this.attributesToString(attributes)}>
                `;
        }
        
        return `
            <div class="form-field mb-4">
                ${label && type !== 'checkbox' ? `<label for="${fieldId}" class="block text-sm font-medium mb-2">${this.escapeHtml(label)} ${requiredMark}</label>` : ''}
                ${fieldHTML}
                ${helpText ? `<div class="form-help text-xs text-gray-400 mt-1">${this.escapeHtml(helpText)}</div>` : ''}
                <div class="field-error text-red-400 text-sm mt-1 hidden"></div>
            </div>
        `;
    }
    
    /**
     * Render form action buttons
     * @returns {string} Action buttons HTML
     */
    renderFormActions() {
        return `
            <button type="submit" class="btn btn-primary btn-submit mr-2">
                <span class="btn-text">${this.options.submitButtonText}</span>
                <span class="btn-loading hidden">
                    <span class="spinner inline-block w-4 h-4 mr-2"></span>
                    ${this.options.loadingButtonText}
                </span>
            </button>
            <button type="button" class="btn btn-secondary btn-reset">
                ${this.options.resetButtonText}
            </button>
        `;
    }
    
    /**
     * Setup form field tracking
     */
    setupFormFields() {
        const fieldConfigs = this.getFormFields();
        
        Object.entries(fieldConfigs).forEach(([fieldName, config]) => {
            const fieldElement = this.formElement.querySelector(`[name="${fieldName}"]`);
            if (fieldElement) {
                this.fields.set(fieldName, {
                    element: fieldElement,
                    config: config,
                    isValid: !config.required, // Non-required fields start as valid
                    value: this.getFieldValue(fieldElement),
                    isDirty: false
                });
                
                // Setup validation rules
                if (config.validation) {
                    this.setupFieldValidation(fieldName, config.validation);
                }
            }
        });
    }
    
    /**
     * Setup validation rules for a field
     * @param {string} fieldName - Field name
     * @param {Object} validation - Validation configuration
     */
    setupFieldValidation(fieldName, validation) {
        const validators = [];
        
        if (validation.rules) {
            validation.rules.forEach(rule => {
                if (typeof rule === 'string') {
                    validators.push(this.getBuiltInValidator(rule));
                } else if (typeof rule === 'function') {
                    validators.push(rule);
                }
            });
        }
        
        if (validation.custom && typeof validation.custom === 'function') {
            validators.push(validation.custom);
        }
        
        this.validators.set(fieldName, validators);
    }
    
    /**
     * Get built-in validator function
     * @param {string} rule - Validation rule
     * @returns {Function} Validator function
     */
    getBuiltInValidator(rule) {
        const [ruleName, ...params] = rule.split(':');
        
        switch (ruleName) {
            case 'required':
                return (value) => {
                    return value && value.toString().trim().length > 0 || 'This field is required';
                };
                
            case 'email':
                return (value) => {
                    if (!value) return true; // Let required handle empty values
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    return emailRegex.test(value) || 'Please enter a valid email address';
                };
                
            case 'minLength':
                const minLength = parseInt(params[0]) || 0;
                return (value) => {
                    if (!value) return true;
                    return value.length >= minLength || `Minimum length is ${minLength} characters`;
                };
                
            case 'maxLength':
                const maxLength = parseInt(params[0]) || Infinity;
                return (value) => {
                    if (!value) return true;
                    return value.length <= maxLength || `Maximum length is ${maxLength} characters`;
                };
                
            case 'numeric':
                return (value) => {
                    if (!value) return true;
                    return !isNaN(value) || 'Please enter a valid number';
                };
                
            case 'serverId':
                return (value) => {
                    if (!value) return true;
                    return /^\d+$/.test(value) || 'Server ID must contain only numbers';
                };
                
            case 'serverName':
                return (value) => {
                    if (!value) return true;
                    return /^[a-zA-Z0-9\s\-_]{3,50}$/.test(value) || 'Server name must be 3-50 characters (letters, numbers, spaces, hyphens, underscores only)';
                };
                
            default:
                return () => true; // Unknown rule, pass validation
        }
    }
    
    /**
     * Setup form event listeners
     */
    setupFormEvents() {
        // Form submission
        this.addEventListener(this.formElement, 'submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });
        
        // Reset button
        const resetBtn = this.formElement.querySelector('.btn-reset');
        if (resetBtn) {
            this.addEventListener(resetBtn, 'click', () => {
                this.handleReset();
            });
        }
        
        // Field change events
        this.fields.forEach((fieldData, fieldName) => {
            const { element } = fieldData;
            
            if (this.options.validateOnChange) {
                this.addEventListener(element, 'input', () => {
                    this.handleFieldChange(fieldName);
                });
                
                this.addEventListener(element, 'change', () => {
                    this.handleFieldChange(fieldName);
                });
            }
            
            if (this.options.validateOnBlur) {
                this.addEventListener(element, 'blur', () => {
                    this.handleFieldBlur(fieldName);
                });
            }
        });
    }
    
    /**
     * Handle field value change
     * @param {string} fieldName - Field name that changed
     */
    handleFieldChange(fieldName) {
        const fieldData = this.fields.get(fieldName);
        if (!fieldData) return;
        
        const newValue = this.getFieldValue(fieldData.element);
        const oldValue = fieldData.value;
        
        // Update field data
        fieldData.value = newValue;
        fieldData.isDirty = true;
        
        // Update form dirty state
        this.setState({ isDirty: true });
        
        // Validate field if it's dirty or was previously invalid
        if (fieldData.isDirty || !fieldData.isValid) {
            this.validateField(fieldName);
        }
        
        // Update form validation state
        this.updateFormValidation();
        
        // Emit field change event
        this.eventBus.emit('form:field:change', {
            fieldName,
            oldValue,
            newValue,
            form: this
        });
    }
    
    /**
     * Handle field blur event
     * @param {string} fieldName - Field name
     */
    handleFieldBlur(fieldName) {
        this.validateField(fieldName);
        this.updateFormValidation();
    }
    
    /**
     * Validate single field
     * @param {string} fieldName - Field name to validate
     * @returns {boolean} Is field valid
     */
    validateField(fieldName) {
        const fieldData = this.fields.get(fieldName);
        const validators = this.validators.get(fieldName);
        
        if (!fieldData || !validators) {
            return true;
        }
        
        const value = fieldData.value;
        let isValid = true;
        let errorMessage = '';
        
        // Run all validators
        for (const validator of validators) {
            const result = validator(value);
            if (result !== true) {
                isValid = false;
                errorMessage = result;
                break;
            }
        }
        
        // Update field validity
        fieldData.isValid = isValid;
        
        // Update validation errors
        if (isValid) {
            this.validationErrors.delete(fieldName);
        } else {
            this.validationErrors.set(fieldName, errorMessage);
        }
        
        // Show/hide field error
        if (this.options.showValidationErrors) {
            this.showFieldError(fieldName, isValid ? null : errorMessage);
        }
        
        return isValid;
    }
    
    /**
     * Validate entire form
     * @returns {boolean} Is form valid
     */
    validateForm() {
        let isFormValid = true;
        
        // Validate all fields
        this.fields.forEach((fieldData, fieldName) => {
            const isFieldValid = this.validateField(fieldName);
            if (!isFieldValid) {
                isFormValid = false;
            }
        });
        
        return isFormValid;
    }
    
    /**
     * Update form validation state
     */
    updateFormValidation() {
        const isValid = Array.from(this.fields.values()).every(field => field.isValid);
        this.setState({ isValid });
        
        // Update submit button state
        const submitBtn = this.formElement.querySelector('.btn-submit');
        if (submitBtn) {
            submitBtn.disabled = !isValid || this.isSubmitting;
        }
    }
    
    /**
     * Show field validation error
     * @param {string} fieldName - Field name
     * @param {string|null} errorMessage - Error message or null to hide
     */
    showFieldError(fieldName, errorMessage) {
        const fieldData = this.fields.get(fieldName);
        if (!fieldData) return;
        
        const errorElement = fieldData.element.closest('.form-field')?.querySelector('.field-error');
        if (!errorElement) return;
        
        if (errorMessage) {
            errorElement.textContent = errorMessage;
            errorElement.classList.remove('hidden');
            fieldData.element.classList.add('border-red-500');
        } else {
            errorElement.classList.add('hidden');
            fieldData.element.classList.remove('border-red-500');
        }
    }
    
    /**
     * Get current form data
     * @returns {Object} Form data
     */
    getFormData() {
        const data = {};
        this.fields.forEach((fieldData, fieldName) => {
            data[fieldName] = fieldData.value;
        });
        return data;
    }
    
    /**
     * Set form data
     * @param {Object} data - Data to set
     */
    setFormData(data) {
        Object.entries(data).forEach(([fieldName, value]) => {
            this.setFieldValue(fieldName, value);
        });
    }
    
    /**
     * Set field value
     * @param {string} fieldName - Field name
     * @param {any} value - Value to set
     */
    setFieldValue(fieldName, value) {
        const fieldData = this.fields.get(fieldName);
        if (!fieldData) return;
        
        const { element } = fieldData;
        
        if (element.type === 'checkbox') {
            element.checked = Boolean(value);
        } else {
            element.value = value || '';
        }
        
        // Update field data
        fieldData.value = this.getFieldValue(element);
        
        // Validate field
        this.validateField(fieldName);
        this.updateFormValidation();
    }
    
    /**
     * Get field value from element
     * @param {Element} element - Field element
     * @returns {any} Field value
     */
    getFieldValue(element) {
        if (element.type === 'checkbox') {
            return element.checked;
        }
        if (element.type === 'number') {
            return element.value ? parseFloat(element.value) : '';
        }
        return element.value;
    }
    
    /**
     * Handle form submission
     */
    async handleSubmit() {
        if (this.isSubmitting && this.options.preventDoubleSubmit) {
            this.log('Form submission already in progress');
            return;
        }
        
        // Validate form
        const isValid = this.validateForm();
        if (!isValid) {
            this.showNotification('Please fix the errors in the form', 'error');
            this.focusFirstErrorField();
            return;
        }
        
        try {
            this.isSubmitting = true;
            this.setState({ loading: true });
            this.updateSubmitButton(true);
            
            const formData = this.getFormData();
            
            // Call submission hook
            await this.onSubmit(formData);
            
            // Update submission state
            this.setState({
                submissionCount: this.state.submissionCount + 1,
                lastSubmission: new Date().toISOString()
            });
            
            // Reset form if configured
            if (this.options.resetAfterSubmit) {
                this.resetForm();
            }
            
            this.showNotification('Form submitted successfully', 'success');
            
        } catch (error) {
            this.handleError(error, 'form submission');
        } finally {
            this.isSubmitting = false;
            this.setState({ loading: false });
            this.updateSubmitButton(false);
        }
    }
    
    /**
     * Form submission hook - override in subclasses
     * @param {Object} formData - Form data to submit
     */
    async onSubmit(formData) {
        this.log('Form submitted with data:', formData);
        // Override in subclasses
    }
    
    /**
     * Handle form reset
     */
    handleReset() {
        if (this.options.confirmBeforeReset && this.state.isDirty) {
            if (!confirm('Are you sure you want to reset the form? All changes will be lost.')) {
                return;
            }
        }
        
        this.resetForm();
    }
    
    /**
     * Reset form to initial state
     */
    resetForm() {
        // Reset form element
        this.formElement.reset();
        
        // Reset field data
        this.fields.forEach((fieldData, fieldName) => {
            fieldData.value = this.getFieldValue(fieldData.element);
            fieldData.isDirty = false;
            fieldData.isValid = !fieldData.config.required;
            this.showFieldError(fieldName, null);
        });
        
        // Reset validation errors
        this.validationErrors.clear();
        
        // Reset state
        this.setState({
            isDirty: false,
            isValid: this.validateForm()
        });
        
        this.updateFormValidation();
        
        this.log('Form reset');
    }
    
    /**
     * Focus first field in form
     */
    focusFirstField() {
        const firstField = this.formElement.querySelector('input, select, textarea');
        if (firstField) {
            firstField.focus();
        }
    }
    
    /**
     * Focus first field with validation error
     */
    focusFirstErrorField() {
        for (const [fieldName, fieldData] of this.fields) {
            if (!fieldData.isValid) {
                fieldData.element.focus();
                break;
            }
        }
    }
    
    /**
     * Update submit button state
     * @param {boolean} isLoading - Is form submitting
     */
    updateSubmitButton(isLoading) {
        const submitBtn = this.formElement.querySelector('.btn-submit');
        const btnText = submitBtn?.querySelector('.btn-text');
        const btnLoading = submitBtn?.querySelector('.btn-loading');
        
        if (submitBtn) {
            submitBtn.disabled = isLoading || !this.state.isValid;
            
            if (btnText && btnLoading) {
                if (isLoading) {
                    btnText.classList.add('hidden');
                    btnLoading.classList.remove('hidden');
                } else {
                    btnText.classList.remove('hidden');
                    btnLoading.classList.add('hidden');
                }
            }
        }
    }
    
    /**
     * Convert attributes object to string
     * @param {Object} attributes - HTML attributes
     * @returns {string} Attribute string
     */
    attributesToString(attributes) {
        return Object.entries(attributes)
            .map(([key, value]) => `${key}="${this.escapeHtml(value)}"`)
            .join(' ');
    }
    
    /**
     * Get form validation summary
     * @returns {Object} Validation summary
     */
    getValidationSummary() {
        return {
            isValid: this.state.isValid,
            isDirty: this.state.isDirty,
            errorCount: this.validationErrors.size,
            errors: Object.fromEntries(this.validationErrors),
            fieldStates: Object.fromEntries(
                Array.from(this.fields.entries()).map(([name, data]) => [
                    name,
                    {
                        isValid: data.isValid,
                        isDirty: data.isDirty,
                        value: data.value
                    }
                ])
            )
        };
    }
}

// Export for module systems or global usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FormComponent;
} else {
    window.FormComponent = FormComponent;
}