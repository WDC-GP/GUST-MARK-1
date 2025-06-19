/**
 * Data Table Widget
 * Reusable data table with sorting,filtering,pagination,and selection
 */
class DataTable extends BaseComponent{constructor(containerId,options ={}){super(containerId,options);this.eventBus = options.eventBus || window.App.eventBus;this.sortedData = [];this.filteredData = [];this.paginatedData = [];this.selectedRows = new Set();}get defaultOptions(){return{...super.defaultOptions,columns: [],data: [],sortable: true,filterable: true,searchable: true,selectable: false,multiSelect: true,pagination: true,pageSize: 20,pageSizeOptions: [10,20,50,100],showHeader: true,showFooter: true,responsive: true,striped: true,hover: true,bordered: false,compact: false,loading: false,emptyMessage: 'No data available',loadingMessage: 'Loading...',rowActions: [],bulkActions: [],exportable: false,virtualScrolling: false,stickyHeader: false,onRowClick: null,onRowSelect: null,onSort: null,onFilter: null,onPageChange: null};}getInitialState(){return{...super.getInitialState(),data: this.options.data || [],sortColumn: null,sortDirection: 'asc',filters:{},searchText: '',currentPage: 1,totalPages: 1,selectedRows: new Set(),loading: this.options.loading};}render(){const{responsive,striped,hover,bordered,compact,stickyHeader,showHeader,showFooter,pagination,selectable,searchable}= this.options;const tableClasses = [
 'data-table',responsive ? 'data-table--responsive' : '',striped ? 'data-table--striped' : '',hover ? 'data-table--hover' : '',bordered ? 'data-table--bordered' : '',compact ? 'data-table--compact' : '',stickyHeader ? 'data-table--sticky-header' : '',selectable ? 'data-table--selectable' : ''
 ].filter(Boolean).join(' ');this.container.innerHTML = `
 <div class="data-table-container">
 <!-- Table Controls -->
 <div class="data-table-controls">
 <div class="data-table-controls__left">
 ${this.renderBulkActions()}${searchable ? this.renderSearchBox() : ''}</div>
 <div class="data-table-controls__right">
 ${this.renderExportButton()}${this.renderRefreshButton()}</div>
 </div>
 <!-- Table Wrapper -->
 <div class="data-table-wrapper">
 <table class="${tableClasses}" id="data-table">
 ${showHeader ? this.renderHeader() : ''}<tbody id="table-body">
 ${this.renderBody()}</tbody>
 </table>
 <!-- Loading Overlay -->
 <div class="data-table-loading ${this.state.loading ? 'active' : ''}" id="table-loading">
 <div class="loading-spinner"></div>
 <span class="loading-text">${this.options.loadingMessage}</span>
 </div>
 <!-- Empty State -->
 <div class="data-table-empty ${this.paginatedData.length === 0 && !this.state.loading ? 'active' : ''}" id="table-empty">
 <div class="empty-icon">
 <i class="icon-inbox"></i>
 </div>
 <div class="empty-message">${this.options.emptyMessage}</div>
 </div>
 </div>
 <!-- Table Footer -->
 ${showFooter ? this.renderFooter() : ''}</div>
 `;this.processData();}bindEvents(){const searchInput = this.container.querySelector('#table-search');if(searchInput){this.addEventListener(searchInput,'input',this.debounce((e) => this.handleSearch(e.target.value),300)
 );}const selectAll = this.container.querySelector('#select-all');if(selectAll){this.addEventListener(selectAll,'change',(e) =>{this.handleSelectAll(e.target.checked);});}const rowCheckboxes = this.container.querySelectorAll('.row-checkbox');rowCheckboxes.forEach(checkbox =>{this.addEventListener(checkbox,'change',(e) =>{this.handleRowSelection(e.target.dataset.rowId,e.target.checked);});});const sortableHeaders = this.container.querySelectorAll('.sortable-header');sortableHeaders.forEach(header =>{this.addEventListener(header,'click',() =>{this.handleSort(header.dataset.column);});});const rows = this.container.querySelectorAll('.table-row');rows.forEach(row =>{this.addEventListener(row,'click',(e) =>{if(!e.target.closest('.row-actions') && !e.target.closest('.row-checkbox')){this.handleRowClick(row.dataset.rowId,e);}});});const actionButtons = this.container.querySelectorAll('.row-action-btn');actionButtons.forEach(button =>{this.addEventListener(button,'click',(e) =>{e.stopPropagation();this.handleRowAction(button.dataset.action,button.dataset.rowId);});});const bulkActionButtons = this.container.querySelectorAll('.bulk-action-btn');bulkActionButtons.forEach(button =>{this.addEventListener(button,'click',() =>{this.handleBulkAction(button.dataset.action);});});const pageButtons = this.container.querySelectorAll('.page-btn');pageButtons.forEach(button =>{this.addEventListener(button,'click',() =>{const page = parseInt(button.dataset.page);this.goToPage(page);});});const pageSizeSelect = this.container.querySelector('#page-size-select');if(pageSizeSelect){this.addEventListener(pageSizeSelect,'change',(e) =>{this.changePageSize(parseInt(e.target.value));});}const exportBtn = this.container.querySelector('#export-btn');if(exportBtn){this.addEventListener(exportBtn,'click',() => this.exportData());}const refreshBtn = this.container.querySelector('#refresh-btn');if(refreshBtn){this.addEventListener(refreshBtn,'click',() => this.refresh());}}renderHeader(){const{columns,selectable,multiSelect}= this.options;return `
 <thead class="data-table-head">
 <tr class="table-row table-row--header">
 ${selectable && multiSelect ? `
 <th class="table-cell table-cell--select">
 <label class="checkbox-label">
 <input type="checkbox" id="select-all" class="checkbox">
 <span class="checkbox-mark"></span>
 </label>
 </th>
 ` : selectable ? `
 <th class="table-cell table-cell--select"></th>
 ` : ''}${columns.map(column => `
 <th class="table-cell ${column.sortable !== false ? 'table-cell--sortable sortable-header' : ''}${column.align ? `table-cell--${column.align}` : ''}"
 data-column="${column.key}"
 ${column.width ? `style="width: ${column.width}"` : ''}>
 <div class="table-cell-content">
 <span class="column-label">${column.label}</span>
 ${column.sortable !== false ? `
 <span class="sort-indicator ${this.getSortIndicatorClass(column.key)}">
 <i class="icon-chevron-up sort-asc"></i>
 <i class="icon-chevron-down sort-desc"></i>
 </span>
 ` : ''}</div>
 </th>
 `).join('')}${this.options.rowActions.length > 0 ? `
 <th class="table-cell table-cell--actions">Actions</th>
 ` : ''}</tr>
 </thead>
 `;}renderBody(){if(this.state.loading){return '';}if(this.paginatedData.length === 0){return '';}return this.paginatedData.map((row,index) => this.renderRow(row,index)).join('');}renderRow(row,index){const{columns,selectable,rowActions}= this.options;const rowId = this.getRowId(row,index);const isSelected = this.selectedRows.has(rowId);return `
 <tr class="table-row ${isSelected ? 'table-row--selected' : ''}${index % 2 === 0 ? 'table-row--even' : 'table-row--odd'}"
 data-row-id="${rowId}">
 ${selectable ? `
 <td class="table-cell table-cell--select">
 <label class="checkbox-label">
 <input type="checkbox" 
 class="checkbox row-checkbox" 
 data-row-id="${rowId}"
 ${isSelected ? 'checked' : ''}>
 <span class="checkbox-mark"></span>
 </label>
 </td>
 ` : ''}${columns.map(column => `
 <td class="table-cell ${column.align ? `table-cell--${column.align}` : ''}"
 data-column="${column.key}">
 <div class="table-cell-content">
 ${this.formatCellValue(row,column)}</div>
 </td>
 `).join('')}${rowActions.length > 0 ? `
 <td class="table-cell table-cell--actions">
 <div class="row-actions">
 ${rowActions.map(action => `
 <button class="row-action-btn ${action.variant ? `btn--${action.variant}` : 'btn--ghost'}"
 data-action="${action.key}"
 data-row-id="${rowId}"
 title="${action.label}"
 ${action.disabled && action.disabled(row) ? 'disabled' : ''}>
 ${action.icon ? `<i class="${action.icon}"></i>` : action.label}</button>
 `).join('')}</div>
 </td>
 ` : ''}</tr>
 `;}renderFooter(){const{pagination}= this.options;return `
 <div class="data-table-footer">
 <div class="data-table-info">
 <span class="data-count">
 Showing ${this.getDisplayRange()}of ${this.filteredData.length}entries
 ${this.filteredData.length !== this.state.data.length ? 
 `(filtered from ${this.state.data.length}total)` : ''}</span>
 ${this.selectedRows.size > 0 ? `
 <span class="selection-count">
 ${this.selectedRows.size}selected
 </span>
 ` : ''}</div>
 ${pagination ? this.renderPagination() : ''}</div>
 `;}renderPagination(){const{pageSize,pageSizeOptions}= this.options;const{currentPage,totalPages}= this.state;const pages = this.getPaginationPages();return `
 <div class="data-table-pagination">
 <div class="page-size-selector">
 <label class="page-size-label">Show:</label>
 <select id="page-size-select" class="page-size-select">
 ${pageSizeOptions.map(size => `
 <option value="${size}" ${size === pageSize ? 'selected' : ''}>
 ${size}</option>
 `).join('')}</select>
 </div>
 <div class="pagination-controls">
 <button class="page-btn page-btn--prev" 
 data-page="${currentPage - 1}"
 ${currentPage <= 1 ? 'disabled' : ''}>
 <i class="icon-chevron-left"></i>
 Previous
 </button>
 <div class="page-numbers">
 ${pages.map(page =>{if(page === '...'){return '<span class="page-ellipsis">...</span>';}return `
 <button class="page-btn ${page === currentPage ? 'page-btn--active' : ''}"
 data-page="${page}">
 ${page}</button>
 `;}).join('')}</div>
 <button class="page-btn page-btn--next" 
 data-page="${currentPage + 1}"
 ${currentPage >= totalPages ? 'disabled' : ''}>
 Next
 <i class="icon-chevron-right"></i>
 </button>
 </div>
 </div>
 `;}renderSearchBox(){return `
 <div class="search-box">
 <div class="search-input-group">
 <input type="text" 
 id="table-search" 
 class="search-input"
 placeholder="Search table..."
 value="${this.state.searchText}">
 <i class="icon-search search-icon"></i>
 </div>
 </div>
 `;}renderBulkActions(){const{bulkActions,selectable}= this.options;if(!selectable || bulkActions.length === 0){return '';}return `
 <div class="bulk-actions ${this.selectedRows.size > 0 ? 'bulk-actions--visible' : ''}">
 <span class="bulk-actions-label">
 ${this.selectedRows.size}selected
 </span>
 <div class="bulk-actions-buttons">
 ${bulkActions.map(action => `
 <button class="bulk-action-btn btn btn--${action.variant || 'secondary'}"
 data-action="${action.key}">
 ${action.icon ? `<i class="${action.icon}"></i>` : ''}${action.label}</button>
 `).join('')}</div>
 </div>
 `;}renderExportButton(){if(!this.options.exportable) return '';return `
 <button id="export-btn" class="btn btn--secondary" title="Export data">
 <i class="icon-download"></i>
 Export
 </button>
 `;}renderRefreshButton(){return `
 <button id="refresh-btn" class="btn btn--secondary" title="Refresh data">
 <i class="icon-refresh"></i>
 Refresh
 </button>
 `;}formatCellValue(row,column){const value = this.getNestedValue(row,column.key);if(column.formatter){return column.formatter(value,row,column);}if(value === null || value === undefined){return '<span class="text-muted">—</span>';}if(typeof value === 'boolean'){return value ? '<i class="icon-check text-success"></i>' : '<i class="icon-x text-error"></i>';}if(column.type === 'date' && value){return new Date(value).toLocaleDateString();}if(column.type === 'datetime' && value){return new Date(value).toLocaleString();}if(column.type === 'currency' && typeof value === 'number'){return new Intl.NumberFormat('en-US',{style: 'currency',currency: 'USD'}).format(value);}if(column.type === 'number' && typeof value === 'number'){return value.toLocaleString();}return this.escapeHtml(String(value));}processData(){let data = [...this.state.data];if(this.state.searchText){data = this.filterDataBySearch(data,this.state.searchText);}data = this.filterDataByColumns(data,this.state.filters);this.filteredData = data;if(this.state.sortColumn){data = this.sortData(data,this.state.sortColumn,this.state.sortDirection);}this.sortedData = data;this.calculatePagination();this.paginatedData = this.paginateData(data);this.updateDisplay();}filterDataBySearch(data,searchText){const search = searchText.toLowerCase();const{columns}= this.options;return data.filter(row =>{return columns.some(column =>{if(column.searchable === false) return false;const value = this.getNestedValue(row,column.key);if(value === null || value === undefined) return false;return String(value).toLowerCase().includes(search);});});}filterDataByColumns(data,filters){return data.filter(row =>{return Object.entries(filters).every(([column,filterValue]) =>{const value = this.getNestedValue(row,column);return String(value).toLowerCase().includes(String(filterValue).toLowerCase());});});}sortData(data,column,direction){return [...data].sort((a,b) =>{const aValue = this.getNestedValue(a,column);const bValue = this.getNestedValue(b,column);if(aValue === null || aValue === undefined) return 1;if(bValue === null || bValue === undefined) return -1;let result = 0;if(typeof aValue === 'number' && typeof bValue === 'number'){result = aValue - bValue;}else if(aValue instanceof Date && bValue instanceof Date){result = aValue.getTime() - bValue.getTime();}else{result = String(aValue).localeCompare(String(bValue));}return direction === 'desc' ? -result : result;});}calculatePagination(){const{pageSize}= this.options;const totalItems = this.filteredData.length;const totalPages = Math.ceil(totalItems / pageSize);this.setState({totalPages});if(this.state.currentPage > totalPages){this.setState({currentPage: Math.max(1,totalPages)});}}paginateData(data){if(!this.options.pagination) return data;const{pageSize}= this.options;const{currentPage}= this.state;const startIndex = (currentPage - 1) * pageSize;const endIndex = startIndex + pageSize;return data.slice(startIndex,endIndex);}updateDisplay(){const tbody = this.container.querySelector('#table-body');if(tbody){tbody.innerHTML = this.renderBody();}if(this.options.showFooter){const footer = this.container.querySelector('.data-table-footer');if(footer){footer.innerHTML = this.renderFooter().replace(/<\/?div[^>]*>/g,'');}}this.updateBulkActions();this.updateEmptyState();this.bindEvents();}updateBulkActions(){const bulkActions = this.container.querySelector('.bulk-actions');if(bulkActions){bulkActions.classList.toggle('bulk-actions--visible',this.selectedRows.size > 0);const label = bulkActions.querySelector('.bulk-actions-label');if(label){label.textContent = `${this.selectedRows.size}selected`;}}}updateEmptyState(){const emptyState = this.container.querySelector('#table-empty');if(emptyState){const showEmpty = this.paginatedData.length === 0 && !this.state.loading;emptyState.classList.toggle('active',showEmpty);}}handleSearch(searchText){this.setState({searchText,currentPage: 1});this.processData();if(this.options.onFilter){this.options.onFilter({search: searchText});}}handleSort(column){let direction = 'asc';if(this.state.sortColumn === column){direction = this.state.sortDirection === 'asc' ? 'desc' : 'asc';}this.setState({sortColumn: column,sortDirection: direction});this.processData();if(this.options.onSort){this.options.onSort({column,direction});}}handleRowClick(rowId,event){if(this.options.onRowClick){const row = this.findRowById(rowId);this.options.onRowClick(row,rowId,event);}}handleRowSelection(rowId,selected){if(selected){this.selectedRows.add(rowId);}else{this.selectedRows.delete(rowId);}this.setState({selectedRows: this.selectedRows});this.updateBulkActions();if(this.options.onRowSelect){const selectedData = Array.from(this.selectedRows).map(id => this.findRowById(id));this.options.onRowSelect(selectedData,this.selectedRows);}}handleSelectAll(selected){if(selected){this.paginatedData.forEach((row,index) =>{const rowId = this.getRowId(row,index);this.selectedRows.add(rowId);});}else{this.paginatedData.forEach((row,index) =>{const rowId = this.getRowId(row,index);this.selectedRows.delete(rowId);});}this.setState({selectedRows: this.selectedRows});this.updateDisplay();}handleRowAction(action,rowId){const row = this.findRowById(rowId);const actionConfig = this.options.rowActions.find(a => a.key === action);if(actionConfig && actionConfig.handler){actionConfig.handler(row,rowId);}}handleBulkAction(action){const actionConfig = this.options.bulkActions.find(a => a.key === action);const selectedData = Array.from(this.selectedRows).map(id => this.findRowById(id));if(actionConfig && actionConfig.handler){actionConfig.handler(selectedData,this.selectedRows);}}updateData(newData){this.setState({data: newData});this.selectedRows.clear();this.processData();}addRow(row){const newData = [...this.state.data,row];this.updateData(newData);}removeRow(rowId){const newData = this.state.data.filter((row,index) =>{return this.getRowId(row,index) !== rowId;});this.updateData(newData);}updateRow(rowId,newData){const data = this.state.data.map((row,index) =>{return this.getRowId(row,index) === rowId ?{...row,...newData}: row;});this.updateData(data);}goToPage(page){if(page >= 1 && page <= this.state.totalPages){this.setState({currentPage: page});this.processData();if(this.options.onPageChange){this.options.onPageChange(page);}}}changePageSize(newSize){this.options.pageSize = newSize;this.setState({currentPage: 1});this.processData();}clearSelection(){this.selectedRows.clear();this.setState({selectedRows: this.selectedRows});this.updateDisplay();}setLoading(loading){this.setState({loading});const loadingOverlay = this.container.querySelector('#table-loading');if(loadingOverlay){loadingOverlay.classList.toggle('active',loading);}this.updateEmptyState();}refresh(){if(this.options.onRefresh){this.options.onRefresh();}else{this.processData();}}exportData(){const data = this.filteredData;const{columns}= this.options;const headers = columns.map(col => col.label);const rows = data.map(row => 
 columns.map(col =>{const value = this.getNestedValue(row,col.key);return this.escapeCSV(value);})
 );const csvContent = [headers,...rows]
 .map(row => row.join(','))
 .join('\n');const blob = new Blob([csvContent],{type: 'text/csv'});const url = URL.createObjectURL(blob);const a = document.createElement('a');a.href = url;a.download = `table-export-${new Date().toISOString().split('T')[0]}.csv`;document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);}getRowId(row,index){return row.id || row._id || index;}findRowById(rowId){return this.state.data.find((row,index) =>{return this.getRowId(row,index) == rowId;});}getNestedValue(obj,path){return path.split('.').reduce((current,key) =>{return current && current[key] !== undefined ? current[key] : null;},obj);}getSortIndicatorClass(column){if(this.state.sortColumn === column){return `sort-indicator--${this.state.sortDirection}`;}return '';}getDisplayRange(){const{pageSize}= this.options;const{currentPage}= this.state;const start = (currentPage - 1) * pageSize + 1;const end = Math.min(currentPage * pageSize,this.filteredData.length);return `${start}-${end}`;}getPaginationPages(){const{currentPage,totalPages}= this.state;const delta = 2;const pages = [];pages.push(1);if(currentPage - delta > 2){pages.push('...');}for(let i = Math.max(2,currentPage - delta);i <= Math.min(totalPages - 1,currentPage + delta);i++){pages.push(i);}if(currentPage + delta < totalPages - 1){pages.push('...');}if(totalPages > 1){pages.push(totalPages);}return pages;}escapeHtml(text){const div = document.createElement('div');div.textContent = text;return div.innerHTML;}escapeCSV(value){if(value === null || value === undefined) return '';const str = String(value);if(str.includes(',') || str.includes('"') || str.includes('\n')){return `"${str.replace(/"/g,'""')}"`;}return str;}debounce(func,wait){let timeout;return function executedFunction(...args){const later = () =>{clearTimeout(timeout);func(...args);};clearTimeout(timeout);timeout = setTimeout(later,wait);};}onDestroy(){this.selectedRows.clear();this.sortedData = [];this.filteredData = [];this.paginatedData = [];}}