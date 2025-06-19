/**
 * GUST Bot Enhanced - Validation Service
 * ====================================
 * Comprehensive validation rules and form validation logic
 */
class ValidationService{constructor(options ={}){this.options ={...this.defaultOptions,...options};this.customValidators = new Map();this.customMessages = new Map();this.eventBus = options.eventBus || window.App?.eventBus || window.EventBus;this.init();}get defaultOptions(){return{locale: 'en',stopOnFirstError: false,trimValues: true,allowEmpty: false,dateFormat: 'YYYY-MM-DD',timeFormat: 'HH:mm',datetimeFormat: 'YYYY-MM-DD HH:mm',enableDebug: false};}init(){this.registerBuiltInValidators();this.registerBuiltInMessages();this.log('Validation service initialized');}/**
 * Validate a single field
 * @param{*}value - Value to validate
 * @param{Object}rules - Validation rules
 * @param{string}fieldName - Field name for error messages
 * @returns{Object}Validation result{isValid,errors,value}*/
 validateField(value,rules,fieldName = 'field'){const result ={isValid: true,errors: [],value: value,fieldName};if(this.options.trimValues && typeof value === 'string'){result.value = value.trim();value = result.value;}if(rules.required && this.isEmpty(value)){const error = this.getMessage('required',fieldName,rules.required);result.errors.push(error);result.isValid = false;if(this.options.stopOnFirstError){return result;}}if(this.isEmpty(value) && !rules.required){if(!this.options.allowEmpty && Object.keys(rules).length > 1){return result;}}Object.entries(rules).forEach(([ruleName,ruleValue]) =>{if(ruleName === 'required') return;const validator = this.getValidator(ruleName);if(!validator){this.log(`Unknown validator: ${ruleName}`,null,'warn');return;}try{const isValid = validator.call(this,value,ruleValue,fieldName);if(!isValid){const error = this.getMessage(ruleName,fieldName,ruleValue,value);result.errors.push(error);result.isValid = false;if(this.options.stopOnFirstError){return;}}}catch (error){this.log(`Validator error for '${ruleName}':`,error,'error');result.errors.push(`Validation error: ${error.message}`);result.isValid = false;}});return result;}/**
 * Validate multiple fields
 * @param{Object}data - Object with field values
 * @param{Object}schema - Validation schema
 * @returns{Object}Validation result
 */
 validateForm(data,schema){const result ={isValid: true,errors:{},data:{...data},summary: []};Object.entries(schema).forEach(([fieldName,rules]) =>{const value = data[fieldName];const fieldResult = this.validateField(value,rules,fieldName);result.data[fieldName] = fieldResult.value;if(!fieldResult.isValid){result.isValid = false;result.errors[fieldName] = fieldResult.errors;result.summary.push(...fieldResult.errors);}});return result;}/**
 * Register custom validator
 * @param{string}name - Validator name
 * @param{Function}validator - Validator function
 * @param{string}message - Error message template
 */
 registerValidator(name,validator,message){this.customValidators.set(name,validator);if(message){this.customMessages.set(name,message);}this.log(`Registered custom validator: ${name}`);}/**
 * Register custom error message
 * @param{string}rule - Rule name
 * @param{string}message - Message template
 */
 registerMessage(rule,message){this.customMessages.set(rule,message);}/**
 * Get validator function
 */
 getValidator(name){return this.customValidators.get(name) || this.builtInValidators[name];}/**
 * Get error message
 */
 getMessage(rule,fieldName,ruleValue,value){let template = this.customMessages.get(rule) || this.builtInMessages[rule] || 'Invalid value';template = template
 .replace(/{field}/g,fieldName)
 .replace(/{value}/g,String(value || ''))
 .replace(/{rule}/g,String(ruleValue || ''));return template;}/**
 * Check if value is empty
 */
 isEmpty(value){if(value === null || value === undefined) return true;if(typeof value === 'string') return value.trim().length === 0;if(Array.isArray(value)) return value.length === 0;if(typeof value === 'object') return Object.keys(value).length === 0;return false;}/**
 * Built-in validators
 */
 get builtInValidators(){return{string: (value) => typeof value === 'string',number: (value) => !isNaN(Number(value)) && isFinite(Number(value)),integer: (value) => Number.isInteger(Number(value)),boolean: (value) => typeof value === 'boolean' || value === 'true' || value === 'false',array: (value) => Array.isArray(value),object: (value) => typeof value === 'object' && value !== null && !Array.isArray(value),minLength: (value,min) => String(value).length >= min,maxLength: (value,max) => String(value).length <= max,length: (value,exact) => String(value).length === exact,min: (value,min) => Number(value) >= min,max: (value,max) => Number(value) <= max,range: (value,range) =>{const num = Number(value);return num >= range.min && num <= range.max;},positive: (value) => Number(value) > 0,negative: (value) => Number(value) < 0,regex: (value,pattern) =>{const regex = pattern instanceof RegExp ? pattern : new RegExp(pattern);return regex.test(String(value));},email: (value) =>{const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;return emailRegex.test(String(value));},url: (value) =>{try{new URL(String(value));return true;}catch{return false;}},alphanumeric: (value) => /^[a-zA-Z0-9]+$/.test(String(value)),alpha: (value) => /^[a-zA-Z]+$/.test(String(value)),numeric: (value) => /^[0-9]+$/.test(String(value)),date: (value) => !isNaN(Date.parse(String(value))),dateAfter: (value,afterDate) =>{const date = new Date(value);const after = new Date(afterDate);return date > after;},dateBefore: (value,beforeDate) =>{const date = new Date(value);const before = new Date(beforeDate);return date < before;},dateRange: (value,range) =>{const date = new Date(value);const start = new Date(range.start);const end = new Date(range.end);return date >= start && date <= end;},equals: (value,expected) => value === expected,notEquals: (value,notExpected) => value !== notExpected,in: (value,array) => array.includes(value),notIn: (value,array) => !array.includes(value),contains: (value,substring) => String(value).includes(substring),startsWith: (value,prefix) => String(value).startsWith(prefix),endsWith: (value,suffix) => String(value).endsWith(suffix),uppercase: (value) => String(value) === String(value).toUpperCase(),lowercase: (value) => String(value) === String(value).toLowerCase(),serverId: (value) =>{const serverIdRegex = /^\d{7,}$/;return serverIdRegex.test(String(value));},serverName: (value) =>{const nameRegex = /^[a-zA-Z0-9\s\-_]{3,50}$/;return nameRegex.test(String(value));},userId: (value) =>{const userIdRegex = /^[a-zA-Z0-9_]{3,20}$/;return userIdRegex.test(String(value));},region: (value) =>{const validRegions = ['US','EU','AS'];return validRegions.includes(String(value).toUpperCase());},itemName: (value) =>{const itemRegex = /^[a-zA-Z0-9_.]{2,50}$/;return itemRegex.test(String(value));},duration: (value) =>{const num = Number(value);return num > 0 && num <= 1440;},amount: (value) =>{const num = Number(value);return num > 0 && num <= 1000000;},password: (value) =>{const password = String(value);return password.length >= 8 &&
 /[a-z]/.test(password) &&
 /[A-Z]/.test(password) &&
 /[0-9]/.test(password);},strongPassword: (value) =>{const password = String(value);return password.length >= 12 &&
 /[a-z]/.test(password) &&
 /[A-Z]/.test(password) &&
 /[0-9]/.test(password) &&
 /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);},fileSize: (file,maxSize) =>{if(!file || !file.size) return false;return file.size <= maxSize;},fileType: (file,allowedTypes) =>{if(!file || !file.type) return false;return allowedTypes.includes(file.type);},fileExtension: (file,allowedExtensions) =>{if(!file || !file.name) return false;const extension = file.name.split('.').pop().toLowerCase();return allowedExtensions.includes(extension);},unique: async (value,options) =>{if(options.checkFunction){return await options.checkFunction(value);}return true;},conditionalRequired: (value,condition) =>{if(typeof condition === 'function'){return !condition() || !this.isEmpty(value);}return !condition || !this.isEmpty(value);}};}/**
 * Built-in error messages
 */
 get builtInMessages(){return{required: '{field}is required',string: '{field}must be a string',number: '{field}must be a valid number',integer: '{field}must be an integer',boolean: '{field}must be true or false',array: '{field}must be an array',object: '{field}must be an object',minLength: '{field}must be at least{rule}characters long',maxLength: '{field}must not exceed{rule}characters',length: '{field}must be exactly{rule}characters long',min: '{field}must be at least{rule}',max: '{field}must not exceed{rule}',range: '{field}must be between{rule.min}and{rule.max}',positive: '{field}must be a positive number',negative: '{field}must be a negative number',regex: '{field}format is invalid',email: '{field}must be a valid email address',url: '{field}must be a valid URL',alphanumeric: '{field}must contain only letters and numbers',alpha: '{field}must contain only letters',numeric: '{field}must contain only numbers',date: '{field}must be a valid date',dateAfter: '{field}must be after{rule}',dateBefore: '{field}must be before{rule}',dateRange: '{field}must be between{rule.start}and{rule.end}',equals: '{field}must equal{rule}',notEquals: '{field}must not equal{rule}',in: '{field}must be one of:{rule}',notIn: '{field}must not be one of:{rule}',contains: '{field}must contain "{rule}"',startsWith: '{field}must start with "{rule}"',endsWith: '{field}must end with "{rule}"',uppercase: '{field}must be uppercase',lowercase: '{field}must be lowercase',serverId: '{field}must be a valid server ID (7+ digits)',serverName: '{field}must be 3-50 characters,letters,numbers,spaces,hyphens,underscores only',userId: '{field}must be 3-20 characters,letters,numbers,underscores only',region: '{field}must be a valid region (US,EU,AS)',itemName: '{field}must be a valid item name (2-50 characters,letters,numbers,dots,underscores)',duration: '{field}must be between 1 and 1440 minutes',amount: '{field}must be between 1 and 1,000,000',password: '{field}must be at least 8 characters with uppercase,lowercase,and number',strongPassword: '{field}must be at least 12 characters with uppercase,lowercase,number,and special character',fileSize: '{field}file size must not exceed{rule}bytes',fileType: '{field}must be one of these file types:{rule}',fileExtension: '{field}must have one of these extensions:{rule}',unique: '{field}must be unique',conditionalRequired: '{field}is required when condition is met'};}registerBuiltInValidators(){Object.entries(this.builtInValidators).forEach(([name,validator]) =>{this.customValidators.set(name,validator);});}registerBuiltInMessages(){Object.entries(this.builtInMessages).forEach(([rule,message]) =>{this.customMessages.set(rule,message);});}/**
 * Validation schema builders
 */
 /**
 * Create server validation schema
 */
 serverSchema(){return{serverId:{required: true,serverId: true},serverName:{required: true,serverName: true},serverRegion:{required: true,region: true},serverType:{in: ['Standard','Modded','PvP','PvE','RP','Vanilla+']},description:{maxLength: 200}};}/**
 * Create user ban validation schema
 */
 banSchema(){return{userId:{required: true,userId: true},serverId:{required: true,serverId: true},duration:{required: true,duration: true},reason:{required: true,minLength: 5,maxLength: 200}};}/**
 * Create KOTH event validation schema
 */
 kothEventSchema(){return{serverId:{required: true,serverId: true},duration:{required: true,duration: true},reward_item:{required: true,itemName: true},reward_amount:{required: true,amount: true},arena_location:{required: true,minLength: 3,maxLength: 50}};}/**
 * Create clan validation schema
 */
 clanSchema(){return{name:{required: true,minLength: 3,maxLength: 30,alphanumeric: true},leader:{required: true,userId: true},serverId:{required: true,serverId: true},description:{maxLength: 500}};}/**
 * Create economy transfer validation schema
 */
 transferSchema(){return{fromUserId:{required: true,userId: true},toUserId:{required: true,userId: true},amount:{required: true,positive: true,max: 1000000}};}/**
 * Create gambling validation schema
 */
 gamblingSchema(){return{userId:{required: true,userId: true},amount:{required: true,positive: true,max: 100000}};}/**
 * Utility methods
 */
 /**
 * Sanitize input value
 */
 sanitize(value,options ={}){if(typeof value !== 'string') return value;let sanitized = value;if(options.trim !== false){sanitized = sanitized.trim();}if(options.removeHTML){sanitized = sanitized.replace(/<[^>]*>/g,'');}if(options.removeScripts){sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,'');}if(options.toLowerCase){sanitized = sanitized.toLowerCase();}if(options.toUpperCase){sanitized = sanitized.toUpperCase();}return sanitized;}/**
 * Quick validation methods
 */
 isEmail(value){return this.validateField(value,{email: true}).isValid;}isURL(value){return this.validateField(value,{url: true}).isValid;}isServerId(value){return this.validateField(value,{serverId: true}).isValid;}isUserId(value){return this.validateField(value,{userId: true}).isValid;}isValidRegion(value){return this.validateField(value,{region: true}).isValid;}/**
 * Async validation support
 */
 async validateFieldAsync(value,rules,fieldName = 'field'){const asyncValidators = Object.entries(rules).filter(([name]) => 
 name === 'unique' || (this.getValidator(name) && this.getValidator(name).constructor.name === 'AsyncFunction')
 );if(asyncValidators.length === 0){return this.validateField(value,rules,fieldName);}const syncRules = Object.fromEntries(
 Object.entries(rules).filter(([name]) => !asyncValidators.some(([asyncName]) => asyncName === name))
 );const syncResult = this.validateField(value,syncRules,fieldName);if(!syncResult.isValid && this.options.stopOnFirstError){return syncResult;}for(const [ruleName,ruleValue] of asyncValidators){const validator = this.getValidator(ruleName);try{const isValid = await validator.call(this,value,ruleValue,fieldName);if(!isValid){const error = this.getMessage(ruleName,fieldName,ruleValue,value);syncResult.errors.push(error);syncResult.isValid = false;if(this.options.stopOnFirstError){break;}}}catch (error){this.log(`Async validator error for '${ruleName}':`,error,'error');syncResult.errors.push(`Validation error: ${error.message}`);syncResult.isValid = false;}}return syncResult;}/**
 * Get validation summary
 */
 getValidationSummary(errors){if(Array.isArray(errors)){return errors.join(',');}if(typeof errors === 'object'){const allErrors = Object.values(errors).flat();return allErrors.join(',');}return String(errors);}/**
 * Log message
 */
 log(message,data = null,level = 'info'){if(!this.options.enableDebug && level === 'debug') return;const prefix = '[ValidationService]';switch (level){case 'error':
 console.error(prefix,message,data);break;case 'warn':
 console.warn(prefix,message,data);break;default:}}}if(typeof module !== 'undefined' && module.exports){module.exports = ValidationService;}else{window.ValidationService = ValidationService;}