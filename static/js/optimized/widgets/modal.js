/**
 * Modal Dialog Widget
 * Reusable modal component with various types and configurations
 */
class Modal extends BaseComponent{constructor(containerId,options ={}){super(containerId,options);this.eventBus = options.eventBus || window.App.eventBus;this.isOpen = false;this.closeTimeout = null;this.focusTrap = null;}get defaultOptions(){return{...super.defaultOptions,title: '',content: '',type: 'default',size: 'medium',closable: true,backdrop: true,keyboard: true,animation: 'fade',position: 'center',persistent: false,showHeader: true,showFooter: true,actions: [],formData: null,onOpen: null,onClose: null,onConfirm: null,onCancel: null};}getInitialState(){return{...super.getInitialState(),isOpen: false,isAnimating: false,formData: this.options.formData ||{},validationErrors:{}};}render(){const{title,type,size,closable,showHeader,showFooter,position,animation}= this.options;const sizeClass = `modal--${size}`;const typeClass = `modal--${type}`;const positionClass = `modal--${position}`;const animationClass = `modal--${animation}`;this.container.innerHTML = `
 <div class="modal-overlay ${this.state.isOpen ? 'modal-overlay--open' : ''}" 
 id="modal-overlay">
 <div class="modal ${sizeClass}${typeClass}${positionClass}${animationClass}${this.state.isOpen ? 'modal--open' : ''}" 
 id="modal-dialog"
 role="dialog" 
 aria-modal="true"
 aria-labelledby="modal-title">
 ${showHeader ? this.renderHeader() : ''}<div class="modal-body" id="modal-body">
 ${this.renderContent()}</div>
 ${showFooter ? this.renderFooter() : ''}</div>
 </div>
 `;this.setupFocusTrap();if(!document.body.contains(this.container)){document.body.appendChild(this.container);}}renderHeader(){const{title,closable,type}= this.options;const typeIcon = this.getTypeIcon(type);return `
 <div class="modal-header">
 <div class="modal-header__content">
 ${typeIcon ? `<div class="modal-header__icon">${typeIcon}</div>` : ''}<h3 class="modal-title" id="modal-title">${title}</h3>
 </div>
 ${closable ? `
 <button class="modal-close" id="modal-close" aria-label="Close modal">
 <i class="icon-x"></i>
 </button>
 ` : ''}</div>
 `;}renderContent(){const{content,type}= this.options;switch (type){case 'confirm':
 return this.renderConfirmContent();case 'alert':
 return this.renderAlertContent();case 'form':
 return this.renderFormContent();default:
 return typeof content === 'string' ? content : '';}}renderConfirmContent(){const{content}= this.options;return `
 <div class="modal-confirm">
 <div class="modal-confirm__icon">
 <i class="icon-alert-triangle text-warning"></i>
 </div>
 <div class="modal-confirm__content">
 ${content}</div>
 </div>
 `;}renderAlertContent(){const{content}= this.options;return `
 <div class="modal-alert">
 <div class="modal-alert__content">
 ${content}</div>
 </div>
 `;}renderFormContent(){const{formData}= this.options;if(!formData || !formData.fields){return '<p>No form configuration provided</p>';}return `
 <form class="modal-form" id="modal-form">
 ${formData.fields.map(field => this.renderFormField(field)).join('')}</form>
 `;}renderFormField(field){const{type,name,label,placeholder,required,options,value}= field;const errorMessage = this.state.validationErrors[name];const hasError = !!errorMessage;switch (type){case 'text':
 case 'email':
 case 'password':
 case 'number':
 return `
 <div class="form-field ${hasError ? 'form-field--error' : ''}">
 <label class="form-label" for="${name}">
 ${label}${required ? '<span class="text-red-500">*</span>' : ''}</label>
 <input type="${type}" 
 id="${name}" 
 name="${name}"
 class="form-input"
 placeholder="${placeholder || ''}"
 value="${value || ''}"
 ${required ? 'required' : ''}>
 ${hasError ? `<div class="form-error">${errorMessage}</div>` : ''}</div>
 `;case 'textarea':
 return `
 <div class="form-field ${hasError ? 'form-field--error' : ''}">
 <label class="form-label" for="${name}">
 ${label}${required ? '<span class="text-red-500">*</span>' : ''}</label>
 <textarea id="${name}" 
 name="${name}"
 class="form-textarea"
 placeholder="${placeholder || ''}"
 ${required ? 'required' : ''}>${value || ''}</textarea>
 ${hasError ? `<div class="form-error">${errorMessage}</div>` : ''}</div>
 `;case 'select':
 return `
 <div class="form-field ${hasError ? 'form-field--error' : ''}">
 <label class="form-label" for="${name}">
 ${label}${required ? '<span class="text-red-500">*</span>' : ''}</label>
 <select id="${name}" 
 name="${name}"
 class="form-select"
 ${required ? 'required' : ''}>
 ${options.map(option => `
 <option value="${option.value}" ${option.value === value ? 'selected' : ''}>
 ${option.label}</option>
 `).join('')}</select>
 ${hasError ? `<div class="form-error">${errorMessage}</div>` : ''}</div>
 `;case 'checkbox':
 return `
 <div class="form-field ${hasError ? 'form-field--error' : ''}">
 <label class="form-checkbox">
 <input type="checkbox" 
 id="${name}" 
 name="${name}"
 value="true"
 ${value ? 'checked' : ''}${required ? 'required' : ''}>
 <span class="form-checkbox__checkmark"></span>
 <span class="form-checkbox__label">
 ${label}${required ? '<span class="text-red-500">*</span>' : ''}</span>
 </label>
 ${hasError ? `<div class="form-error">${errorMessage}</div>` : ''}</div>
 `;default:
 return `<div class="form-field">Unknown field type: ${type}</div>`;}}renderFooter(){const{type,actions}= this.options;let defaultActions = [];switch (type){case 'confirm':
 defaultActions = [{label: 'Cancel',action: 'cancel',variant: 'secondary'},{label: 'Confirm',action: 'confirm',variant: 'primary'}];break;case 'alert':
 defaultActions = [{label: 'OK',action: 'ok',variant: 'primary'}];break;case 'form':
 defaultActions = [{label: 'Cancel',action: 'cancel',variant: 'secondary'},{label: 'Submit',action: 'submit',variant: 'primary',type: 'submit'}];break;default:
 defaultActions = [{label: 'Close',action: 'close',variant: 'secondary'}];}const finalActions = actions.length > 0 ? actions : defaultActions;return `
 <div class="modal-footer">
 <div class="modal-actions">
 ${finalActions.map(action => `
 <button class="btn btn--${action.variant || 'secondary'}${action.loading ? 'btn--loading' : ''}"
 data-action="${action.action}"
 ${action.type ? `type="${action.type}"` : 'type="button"'}${action.disabled ? 'disabled' : ''}>
 ${action.icon ? `<i class="${action.icon}"></i>` : ''}${action.label}</button>
 `).join('')}</div>
 </div>
 `;}bindEvents(){const closeBtn = this.container.querySelector('#modal-close');if(closeBtn){this.addEventListener(closeBtn,'click',() => this.close());}if(this.options.backdrop){const overlay = this.container.querySelector('#modal-overlay');this.addEventListener(overlay,'click',(e) =>{if(e.target === overlay){this.close();}});}if(this.options.keyboard){this.addEventListener(document,'keydown',(e) =>{if(this.state.isOpen && e.key === 'Escape'){this.close();}});}const actionButtons = this.container.querySelectorAll('[data-action]');actionButtons.forEach(button =>{this.addEventListener(button,'click',(e) =>{this.handleAction(button.dataset.action,e);});});const form = this.container.querySelector('#modal-form');if(form){this.addEventListener(form,'submit',(e) =>{e.preventDefault();this.handleFormSubmit();});const inputs = form.querySelectorAll('input,textarea,select');inputs.forEach(input =>{this.addEventListener(input,'blur',() => this.validateField(input.name));this.addEventListener(input,'input',() => this.clearFieldError(input.name));});}}async open(){if(this.state.isOpen) return;this.setState({isOpen: true,isAnimating: true});this.render();this.bindEvents();if(this.options.onOpen){await this.options.onOpen(this);}document.body.classList.add('modal-open');this.manageFocus();setTimeout(() =>{this.setState({isAnimating: false});},300);this.isOpen = true;}async close(){if(!this.state.isOpen || this.options.persistent) return;this.setState({isAnimating: true});if(this.options.onClose){const shouldClose = await this.options.onClose(this);if(shouldClose === false){this.setState({isAnimating: false});return;}}document.body.classList.remove('modal-open');this.restoreFocus();setTimeout(() =>{this.setState({isOpen: false,isAnimating: false});this.container.innerHTML = '';this.isOpen = false;},300);}async handleAction(action,event){const button = event.target.closest('button');button.classList.add('btn--loading');button.disabled = true;try{switch (action){case 'close':
 case 'cancel':
 if(this.options.onCancel){await this.options.onCancel(this);}this.close();break;case 'confirm':
 case 'ok':
 if(this.options.onConfirm){const result = await this.options.onConfirm(this);if(result !== false){this.close();}}else{this.close();}break;case 'submit':
 this.handleFormSubmit();break;default:
 if(this.options.onAction){await this.options.onAction(action,this);}}}catch (error){console.error('Modal action error:',error);}finally{button.classList.remove('btn--loading');button.disabled = false;}}async handleFormSubmit(){const form = this.container.querySelector('#modal-form');if(!form) return;const formData = new FormData(form);const data ={};for(const [key,value] of formData.entries()){data[key] = value;}const errors = this.validateForm(data);if(Object.keys(errors).length > 0){this.setState({validationErrors: errors});this.render();return;}if(this.options.onSubmit){try{const result = await this.options.onSubmit(data,this);if(result !== false){this.close();}}catch (error){console.error('Form submission error:',error);}}else{this.close();}}validateForm(data){const errors ={};const{formData}= this.options;if(!formData || !formData.fields) return errors;formData.fields.forEach(field =>{if(field.required && !data[field.name]){errors[field.name] = `${field.label}is required`;}if(field.validation && data[field.name]){const validationResult = field.validation(data[field.name]);if(validationResult !== true){errors[field.name] = validationResult;}}});return errors;}validateField(fieldName){const form = this.container.querySelector('#modal-form');const input = form.querySelector(`[name="${fieldName}"]`);const field = this.options.formData.fields.find(f => f.name === fieldName);if(!input || !field) return;const errors ={...this.state.validationErrors};if(field.required && !input.value){errors[fieldName] = `${field.label}is required`;}else if(field.validation && input.value){const validationResult = field.validation(input.value);if(validationResult !== true){errors[fieldName] = validationResult;}else{delete errors[fieldName];}}else{delete errors[fieldName];}this.setState({validationErrors: errors});}clearFieldError(fieldName){const errors ={...this.state.validationErrors};delete errors[fieldName];this.setState({validationErrors: errors});}setupFocusTrap(){this.focusTrap ={firstFocusable: null,lastFocusable: null,previouslyFocused: document.activeElement};}manageFocus(){const modal = this.container.querySelector('#modal-dialog');if(!modal) return;const focusableElements = modal.querySelectorAll(
 'button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])'
 );if(focusableElements.length > 0){this.focusTrap.firstFocusable = focusableElements[0];this.focusTrap.lastFocusable = focusableElements[focusableElements.length - 1];this.focusTrap.firstFocusable.focus();this.addEventListener(modal,'keydown',(e) =>{if(e.key === 'Tab'){if(e.shiftKey){if(document.activeElement === this.focusTrap.firstFocusable){e.preventDefault();this.focusTrap.lastFocusable.focus();}}else{if(document.activeElement === this.focusTrap.lastFocusable){e.preventDefault();this.focusTrap.firstFocusable.focus();}}}});}}restoreFocus(){if(this.focusTrap && this.focusTrap.previouslyFocused){this.focusTrap.previouslyFocused.focus();}}getTypeIcon(type){const icons ={confirm: '<i class="icon-alert-triangle"></i>',alert: '<i class="icon-info"></i>',form: '<i class="icon-edit"></i>',error: '<i class="icon-alert-circle"></i>',success: '<i class="icon-check-circle"></i>',warning: '<i class="icon-alert-triangle"></i>'};return icons[type] || null;}static confirm(title,message,options ={}){return new Promise((resolve) =>{const modal = new Modal('modal-container',{title,content: message,type: 'confirm',onConfirm: () => resolve(true),onCancel: () => resolve(false),onClose: () => resolve(false),...options});modal.open();});}static alert(title,message,options ={}){return new Promise((resolve) =>{const modal = new Modal('modal-container',{title,content: message,type: 'alert',onConfirm: () => resolve(true),onClose: () => resolve(true),...options});modal.open();});}static form(title,formConfig,options ={}){return new Promise((resolve,reject) =>{const modal = new Modal('modal-container',{title,type: 'form',formData: formConfig,onSubmit: (data) => resolve(data),onCancel: () => reject(new Error('Form cancelled')),onClose: () => reject(new Error('Form cancelled')),...options});modal.open();});}static custom(title,content,options ={}){const modal = new Modal('modal-container',{title,content,type: 'custom',...options});modal.open();return modal;}onDestroy(){if(this.isOpen){this.close();}if(this.closeTimeout){clearTimeout(this.closeTimeout);}if(document.body.contains(this.container)){document.body.removeChild(this.container);}document.body.classList.remove('modal-open');}}