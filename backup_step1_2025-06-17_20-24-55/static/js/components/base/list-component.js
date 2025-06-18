/**
 * GUST Bot Enhanced - List Component Class
 * =======================================
 * Specialized base class for list/table components.
 * Provides sorting, filtering, pagination, selection, and bulk operations.
 */

class ListComponent extends BaseComponent {
    /**
     * Initialize list component
     * @param {string} containerId - Container element ID
     * @param {Object} options - List configuration options
     */
    constructor(containerId, options = {}) {
        super(containerId, options);
        
        this.items = [];
        this.filteredItems = [];
        this.selectedItems = new Set();
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.currentPage = 1;
        this.searchQuery = '';
        this.activeFilters = new Map();
        
        // List-specific state
        this.setState({
            totalItems: 0,
            totalPages: 0,
            hasSelection: false,
            allSelected: false,
            isFiltered: false,
            isEmpty: true
        });
    }
    
    /**
     * Default options for list components
     */
    get defaultOptions() {
        return {
            ...super.defaultOptions,
            // Display options
            itemsPerPage: 20,
            showPagination: true,
            showSearch: true,
            showFilters: true,
            showBulkActions: true,
            showItemCount: true,
            showEmptyState: true,
            
            // Interaction options
            selectable: true,
            multiSelect: true,
            sortable: true,
            clickToSelect: false,
            
            // Layout options
            layout: 'list', // 'list', 'grid', 'table'
            itemTemplate: null,
            emptyStateTemplate: null,
            
            // Search and filter options
            searchPlaceholder: 'Search...',
            searchFields: [], // Fields to search in
            filterableFields: [], // Fields that can be filtered
            
            // Pagination options
            showFirstLast: true,
            showPrevNext: true,
            showPageNumbers: true,
            maxPageNumbers: 5,
            
            // Performance options
            virtualScrolling: false,
            lazyLoading: false,
            debounceSearch: 300
        };
    }
    
    /**
     * Get initial list state
     */
    getInitialState() {
        return {
            ...super.getInitialState(),
            totalItems: 0,
            totalPages: 0,
            hasSelection: false,
            allSelected: false,
            isFiltered: false,
            isEmpty: true,
            currentPage: 1
        };
    }
    
    /**
     * Define list columns/fields configuration
     * Override in subclasses to define column structure
     * @returns {Object} Column definitions
     */
    getColumns() {
        return {
            // Example column definition:
            // id: {
            //     header: 'ID',
            //     sortable: true,
            //     filterable: false,
            //     searchable: true,
            //     width: '100px',
            //     render: (value, item) => value,
            //     className: 'text-center'
            // }
        };
    }
    
    /**
     * Define bulk actions available for selected items
     * Override in subclasses to define available actions
     * @returns {Array} Bulk action definitions
     */
    getBulkActions() {
        return [
            // Example action:
            // {
            //     id: 'delete',
            //     label: 'Delete Selected',
            //     icon: '🗑️',
            //     confirmMessage: 'Are you sure you want to delete the selected items?',
            //     action: (selectedItems) => this.handleBulkDelete(selectedItems)
            // }
        ];
    }
    
    /**
     * Render list component
     */
    render() {
        this.container.innerHTML = `
            <div class="list-component">
                ${this.renderHeader()}
                ${this.renderControls()}
                ${this.renderContent()}
                ${this.renderFooter()}
            </div>
        `;
    }
    
    /**
     * Render list header with title and summary
     * @returns {string} Header HTML
     */
    renderHeader() {
        return `
            <div class="list-header mb-4">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="text-lg font-semibold">${this.getTitle()}</h3>
                        ${this.options.showItemCount ? this.renderItemCount() : ''}
                    </div>
                    <div class="list-header-actions">
                        ${this.renderHeaderActions()}
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Get list title - override in subclasses
     * @returns {string} List title
     */
    getTitle() {
        return 'Items';
    }
    
    /**
     * Render item count summary
     * @returns {string} Item count HTML
     */
    renderItemCount() {
        const { totalItems, isFiltered } = this.state;
        const showing = this.filteredItems.length;
        
        if (isFiltered && showing !== totalItems) {
            return `<div class="text-sm text-gray-400">Showing ${showing} of ${totalItems} items</div>`;
        }
        return `<div class="text-sm text-gray-400">${totalItems} items</div>`;
    }
    
    /**
     * Render header actions (add button, etc.)
     * Override in subclasses to add custom actions
     * @returns {string} Header actions HTML
     */
    renderHeaderActions() {
        return '';
    }
    
    /**
     * Render list controls (search, filters, bulk actions)
     * @returns {string} Controls HTML
     */
    renderControls() {
        return `
            <div class="list-controls mb-4">
                <div class="flex flex-wrap items-center gap-4">
                    ${this.options.showSearch ? this.renderSearch() : ''}
                    ${this.options.showFilters ? this.renderFilters() : ''}
                    ${this.options.showBulkActions ? this.renderBulkActions() : ''}
                </div>
            </div>
        `;
    }
    
    /**
     * Render search input
     * @returns {string} Search HTML
     */
    renderSearch() {
        return `
            <div class="list-search">
                <input type="text" 
                       class="search-input form-input bg-gray-700 border-gray-600 focus:border-purple-500 rounded px-3 py-2" 
                       placeholder="${this.options.searchPlaceholder}"
                       value="${this.escapeHtml(this.searchQuery)}">
            </div>
        `;
    }
    
    /**
     * Render filter controls
     * @returns {string} Filters HTML
     */
    renderFilters() {
        const filterableFields = this.options.filterableFields;
        if (!filterableFields.length) return '';
        
        return `
            <div class="list-filters flex gap-2">
                ${filterableFields.map(field => this.renderFilter(field)).join('')}
                ${this.activeFilters.size > 0 ? this.renderClearFilters() : ''}
            </div>
        `;
    }
    
    /**
     * Render individual filter control
     * @param {string} field - Field name to filter
     * @returns {string} Filter HTML
     */
    renderFilter(field) {
        const columns = this.getColumns();
        const column = columns[field];
        if (!column) return '';
        
        const values = this.getUniqueValues(field);
        const currentValue = this.activeFilters.get(field) || '';
        
        return `
            <select class="filter-select form-select bg-gray-700 border-gray-600 text-sm rounded px-2 py-1" 
                    data-field="${field}">
                <option value="">All ${column.header || field}</option>
                ${values.map(value => 
                    `<option value="${this.escapeHtml(value)}" ${value === currentValue ? 'selected' : ''}>
                        ${this.escapeHtml(value)}
                    </option>`
                ).join('')}
            </select>
        `;
    }
    
    /**
     * Render clear filters button
     * @returns {string} Clear filters HTML
     */
    renderClearFilters() {
        return `
            <button class="btn btn-sm btn-secondary clear-filters">
                Clear Filters
            </button>
        `;
    }
    
    /**
     * Render bulk actions dropdown
     * @returns {string} Bulk actions HTML
     */
    renderBulkActions() {
        const bulkActions = this.getBulkActions();
        if (!bulkActions.length || !this.options.selectable) return '';
        
        return `
            <div class="bulk-actions ${this.state.hasSelection ? '' : 'opacity-50'}">
                <select class="bulk-action-select form-select bg-gray-700 border-gray-600 text-sm rounded px-2 py-1" 
                        ${!this.state.hasSelection ? 'disabled' : ''}>
                    <option value="">Bulk Actions (${this.selectedItems.size})</option>
                    ${bulkActions.map(action => 
                        `<option value="${action.id}">${action.icon || ''} ${action.label}</option>`
                    ).join('')}
                </select>
                <button class="btn btn-sm btn-secondary execute-bulk ml-2" 
                        ${!this.state.hasSelection ? 'disabled' : ''}>
                    Execute
                </button>
            </div>
        `;
    }
    
    /**
     * Render main content area
     * @returns {string} Content HTML
     */
    renderContent() {
        return `
            <div class="list-content">
                ${this.state.isEmpty ? this.renderEmptyState() : this.renderItems()}
            </div>
        `;
    }
    
    /**
     * Render empty state
     * @returns {string} Empty state HTML
     */
    renderEmptyState() {
        if (this.options.emptyStateTemplate) {
            return this.options.emptyStateTemplate;
        }
        
        const isFiltered = this.state.isFiltered;
        
        return `
            <div class="empty-state text-center py-12">
                <div class="text-6xl mb-4">${isFiltered ? '🔍' : '📋'}</div>
                <h3 class="text-lg font-semibold mb-2">
                    ${isFiltered ? 'No items match your filters' : 'No items found'}
                </h3>
                <p class="text-gray-400 mb-4">
                    ${isFiltered ? 'Try adjusting your search or filter criteria' : 'Get started by adding your first item'}
                </p>
                ${isFiltered ? this.renderClearFiltersButton() : this.renderAddItemButton()}
            </div>
        `;
    }
    
    /**
     * Render clear filters button for empty state
     * @returns {string} Clear filters button HTML
     */
    renderClearFiltersButton() {
        return `
            <button class="btn btn-secondary clear-all-filters">
                Clear Filters
            </button>
        `;
    }
    
    /**
     * Render add item button for empty state
     * Override in subclasses to provide specific action
     * @returns {string} Add item button HTML
     */
    renderAddItemButton() {
        return `
            <button class="btn btn-primary add-first-item">
                Add First Item
            </button>
        `;
    }
    
    /**
     * Render items based on layout
     * @returns {string} Items HTML
     */
    renderItems() {
        const paginatedItems = this.getPaginatedItems();
        
        switch (this.options.layout) {
            case 'table':
                return this.renderTable(paginatedItems);
            case 'grid':
                return this.renderGrid(paginatedItems);
            default:
                return this.renderList(paginatedItems);
        }
    }
    
    /**
     * Render items as a table
     * @param {Array} items - Items to render
     * @returns {string} Table HTML
     */
    renderTable(items) {
        const columns = this.getColumns();
        
        return `
            <div class="table-container overflow-x-auto">
                <table class="table w-full">
                    <thead>
                        <tr class="bg-gray-800">
                            ${this.options.selectable ? this.renderSelectAllHeader() : ''}
                            ${Object.entries(columns).map(([key, column]) => 
                                this.renderColumnHeader(key, column)
                            ).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${items.map(item => this.renderTableRow(item)).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    /**
     * Render select all checkbox header
     * @returns {string} Select all header HTML
     */
    renderSelectAllHeader() {
        return `
            <th class="p-3 w-12">
                <input type="checkbox" 
                       class="select-all-checkbox" 
                       ${this.state.allSelected ? 'checked' : ''}>
            </th>
        `;
    }
    
    /**
     * Render table column header
     * @param {string} key - Column key
     * @param {Object} column - Column configuration
     * @returns {string} Column header HTML
     */
    renderColumnHeader(key, column) {
        const isSortable = column.sortable && this.options.sortable;
        const isSorted = this.sortColumn === key;
        const sortDirection = isSorted ? this.sortDirection : '';
        
        return `
            <th class="p-3 text-left ${column.className || ''} ${isSortable ? 'cursor-pointer hover:bg-gray-700' : ''}" 
                ${isSortable ? `data-sort="${key}"` : ''}>
                <div class="flex items-center">
                    <span>${column.header || key}</span>
                    ${isSortable ? `
                        <span class="sort-indicator ml-1">
                            ${isSorted ? (sortDirection === 'asc' ? '↑' : '↓') : '↕'}
                        </span>
                    ` : ''}
                </div>
            </th>
        `;
    }
    
    /**
     * Render table row
     * @param {Object} item - Item data
     * @returns {string} Row HTML
     */
    renderTableRow(item) {
        const columns = this.getColumns();
        const itemId = this.getItemId(item);
        const isSelected = this.selectedItems.has(itemId);
        
        return `
            <tr class="border-t border-gray-700 hover:bg-gray-800 ${isSelected ? 'bg-gray-750' : ''}" 
                data-item-id="${itemId}">
                ${this.options.selectable ? `
                    <td class="p-3">
                        <input type="checkbox" 
                               class="item-checkbox" 
                               value="${itemId}"
                               ${isSelected ? 'checked' : ''}>
                    </td>
                ` : ''}
                ${Object.entries(columns).map(([key, column]) => 
                    this.renderTableCell(item, key, column)
                ).join('')}
            </tr>
        `;
    }
    
    /**
     * Render table cell
     * @param {Object} item - Item data
     * @param {string} key - Column key
     * @param {Object} column - Column configuration
     * @returns {string} Cell HTML
     */
    renderTableCell(item, key, column) {
        const value = this.getNestedValue(item, key);
        const displayValue = column.render ? column.render(value, item) : this.escapeHtml(value);
        
        return `
            <td class="p-3 ${column.className || ''}" 
                ${column.width ? `style="width: ${column.width}"` : ''}>
                ${displayValue}
            </td>
        `;
    }
    
    /**
     * Render items as a list
     * @param {Array} items - Items to render
     * @returns {string} List HTML
     */
    renderList(items) {
        return `
            <div class="list-items space-y-2">
                ${items.map(item => this.renderListItem(item)).join('')}
            </div>
        `;
    }
    
    /**
     * Render individual list item
     * Override in subclasses for custom item rendering
     * @param {Object} item - Item data
     * @returns {string} List item HTML
     */
    renderListItem(item) {
        const itemId = this.getItemId(item);
        const isSelected = this.selectedItems.has(itemId);
        
        if (this.options.itemTemplate) {
            return this.options.itemTemplate(item, isSelected);
        }
        
        // Default list item rendering
        return `
            <div class="list-item bg-gray-800 p-4 rounded border ${isSelected ? 'border-purple-500' : 'border-gray-700'} 
                        ${this.options.clickToSelect ? 'cursor-pointer hover:bg-gray-750' : ''}" 
                 data-item-id="${itemId}">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        ${this.renderItemContent(item)}
                    </div>
                    <div class="flex items-center space-x-2">
                        ${this.options.selectable ? `
                            <input type="checkbox" 
                                   class="item-checkbox" 
                                   value="${itemId}"
                                   ${isSelected ? 'checked' : ''}>
                        ` : ''}
                        ${this.renderItemActions(item)}
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Render item content - override in subclasses
     * @param {Object} item - Item data
     * @returns {string} Item content HTML
     */
    renderItemContent(item) {
        return `<div>${this.escapeHtml(JSON.stringify(item))}</div>`;
    }
    
    /**
     * Render item actions - override in subclasses
     * @param {Object} item - Item data
     * @returns {string} Item actions HTML
     */
    renderItemActions(item) {
        return '';
    }
    
    /**
     * Render items as a grid
     * @param {Array} items - Items to render
     * @returns {string} Grid HTML
     */
    renderGrid(items) {
        return `
            <div class="grid-items grid gap-4" style="grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));">
                ${items.map(item => this.renderGridItem(item)).join('')}
            </div>
        `;
    }
    
    /**
     * Render individual grid item
     * Override in subclasses for custom grid item rendering
     * @param {Object} item - Item data
     * @returns {string} Grid item HTML
     */
    renderGridItem(item) {
        const itemId = this.getItemId(item);
        const isSelected = this.selectedItems.has(itemId);
        
        return `
            <div class="grid-item bg-gray-800 p-4 rounded border ${isSelected ? 'border-purple-500' : 'border-gray-700'}" 
                 data-item-id="${itemId}">
                ${this.renderItemContent(item)}
                <div class="mt-3 flex justify-between items-center">
                    ${this.options.selectable ? `
                        <input type="checkbox" 
                               class="item-checkbox" 
                               value="${itemId}"
                               ${isSelected ? 'checked' : ''}>
                    ` : '<div></div>'}
                    <div class="flex space-x-2">
                        ${this.renderItemActions(item)}
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Render footer with pagination
     * @returns {string} Footer HTML
     */
    renderFooter() {
        return `
            <div class="list-footer mt-4">
                ${this.options.showPagination && this.state.totalPages > 1 ? this.renderPagination() : ''}
            </div>
        `;
    }
    
    /**
     * Render pagination controls
     * @returns {string} Pagination HTML
     */
    renderPagination() {
        const { currentPage, totalPages } = this.state;
        const { showFirstLast, showPrevNext, showPageNumbers, maxPageNumbers } = this.options;
        
        const startPage = Math.max(1, currentPage - Math.floor(maxPageNumbers / 2));
        const endPage = Math.min(totalPages, startPage + maxPageNumbers - 1);
        
        return `
            <div class="pagination flex items-center justify-center space-x-1">
                ${showFirstLast && currentPage > 1 ? `
                    <button class="page-btn btn btn-sm btn-secondary" data-page="1">First</button>
                ` : ''}
                
                ${showPrevNext && currentPage > 1 ? `
                    <button class="page-btn btn btn-sm btn-secondary" data-page="${currentPage - 1}">Prev</button>
                ` : ''}
                
                ${showPageNumbers ? Array.from({ length: endPage - startPage + 1 }, (_, i) => {
                    const page = startPage + i;
                    return `
                        <button class="page-btn btn btn-sm ${page === currentPage ? 'btn-primary' : 'btn-secondary'}" 
                                data-page="${page}">${page}</button>
                    `;
                }).join('') : ''}
                
                ${showPrevNext && currentPage < totalPages ? `
                    <button class="page-btn btn btn-sm btn-secondary" data-page="${currentPage + 1}">Next</button>
                ` : ''}
                
                ${showFirstLast && currentPage < totalPages ? `
                    <button class="page-btn btn btn-sm btn-secondary" data-page="${totalPages}">Last</button>
                ` : ''}
            </div>
        `;
    }
    
    /**
     * Setup list event listeners
     */
    bindEvents() {
        super.bindEvents();
        
        // Search input
        const searchInput = this.$('.search-input');
        if (searchInput) {
            this.addEventListener(searchInput, 'input', 
                this.debounce((e) => this.handleSearch(e.target.value), this.options.debounceSearch)
            );
        }
        
        // Filter selects
        this.$$('.filter-select').forEach(select => {
            this.addEventListener(select, 'change', (e) => {
                this.handleFilter(e.target.dataset.field, e.target.value);
            });
        });
        
        // Clear filters
        const clearFilters = this.$('.clear-filters, .clear-all-filters');
        if (clearFilters) {
            this.addEventListener(clearFilters, 'click', () => this.clearFilters());
        }
        
        // Sorting (for table headers)
        this.$$('[data-sort]').forEach(header => {
            this.addEventListener(header, 'click', (e) => {
                this.handleSort(e.currentTarget.dataset.sort);
            });
        });
        
        // Selection
        if (this.options.selectable) {
            this.setupSelectionEvents();
        }
        
        // Bulk actions
        const executeBtn = this.$('.execute-bulk');
        if (executeBtn) {
            this.addEventListener(executeBtn, 'click', () => this.executeBulkAction());
        }
        
        // Pagination
        this.$$('.page-btn').forEach(btn => {
            this.addEventListener(btn, 'click', (e) => {
                this.goToPage(parseInt(e.target.dataset.page));
            });
        });
        
        // Click to select
        if (this.options.clickToSelect && this.options.selectable) {
            this.$$('.list-item, .grid-item').forEach(item => {
                this.addEventListener(item, 'click', (e) => {
                    if (!e.target.closest('input, button, a')) {
                        this.toggleItemSelection(item.dataset.itemId);
                    }
                });
            });
        }
    }
    
    /**
     * Setup selection event listeners
     */
    setupSelectionEvents() {
        // Select all checkbox
        const selectAllCheckbox = this.$('.select-all-checkbox');
        if (selectAllCheckbox) {
            this.addEventListener(selectAllCheckbox, 'change', (e) => {
                if (e.target.checked) {
                    this.selectAll();
                } else {
                    this.deselectAll();
                }
            });
        }
        
        // Individual item checkboxes
        this.$$('.item-checkbox').forEach(checkbox => {
            this.addEventListener(checkbox, 'change', (e) => {
                if (e.target.checked) {
                    this.selectItem(e.target.value);
                } else {
                    this.deselectItem(e.target.value);
                }
            });
        });
    }
    
    /**
     * Load list data
     * Override in subclasses to implement data loading
     */
    async loadData() {
        try {
            this.setState({ loading: true, error: null });
            
            // Override in subclasses
            const data = await this.fetchData();
            this.setItems(data);
            
            this.setState({ loading: false });
            
        } catch (error) {
            this.handleError(error, 'data loading');
        }
    }
    
    /**
     * Fetch data from API
     * Override in subclasses to implement actual data fetching
     * @returns {Promise<Array>} Promise resolving to items array
     */
    async fetchData() {
        // Override in subclasses
        return [];
    }
    
    /**
     * Set list items and update state
     * @param {Array} items - Items to set
     */
    setItems(items) {
        this.items = Array.isArray(items) ? items : [];
        this.applyFiltersAndSort();
        this.updateState();
        this.renderUpdate();
    }
    
    /**
     * Apply filters and sorting to items
     */
    applyFiltersAndSort() {
        let filtered = [...this.items];
        
        // Apply search
        if (this.searchQuery) {
            filtered = this.filterBySearch(filtered, this.searchQuery);
        }
        
        // Apply filters
        this.activeFilters.forEach((value, field) => {
            filtered = this.filterByField(filtered, field, value);
        });
        
        // Apply sorting
        if (this.sortColumn) {
            filtered = this.sortItems(filtered, this.sortColumn, this.sortDirection);
        }
        
        this.filteredItems = filtered;
    }
    
    /**
     * Filter items by search query
     * @param {Array} items - Items to filter
     * @param {string} query - Search query
     * @returns {Array} Filtered items
     */
    filterBySearch(items, query) {
        if (!query) return items;
        
        const searchFields = this.options.searchFields;
        const lowercaseQuery = query.toLowerCase();
        
        return items.filter(item => {
            if (searchFields.length > 0) {
                // Search in specific fields
                return searchFields.some(field => {
                    const value = this.getNestedValue(item, field);
                    return value && value.toString().toLowerCase().includes(lowercaseQuery);
                });
            } else {
                // Search in all string values
                return JSON.stringify(item).toLowerCase().includes(lowercaseQuery);
            }
        });
    }
    
    /**
     * Filter items by field value
     * @param {Array} items - Items to filter
     * @param {string} field - Field to filter by
     * @param {string} value - Filter value
     * @returns {Array} Filtered items
     */
    filterByField(items, field, value) {
        if (!value) return items;
        
        return items.filter(item => {
            const itemValue = this.getNestedValue(item, field);
            return itemValue && itemValue.toString() === value;
        });
    }
    
    /**
     * Sort items by column
     * @param {Array} items - Items to sort
     * @param {string} column - Column to sort by
     * @param {string} direction - Sort direction ('asc' or 'desc')
     * @returns {Array} Sorted items
     */
    sortItems(items, column, direction) {
        return [...items].sort((a, b) => {
            const aVal = this.getNestedValue(a, column);
            const bVal = this.getNestedValue(b, column);
            
            let result = 0;
            if (aVal < bVal) result = -1;
            else if (aVal > bVal) result = 1;
            
            return direction === 'desc' ? -result : result;
        });
    }
    
    /**
     * Get paginated items for current page
     * @returns {Array} Items for current page
     */
    getPaginatedItems() {
        const { itemsPerPage } = this.options;
        const startIndex = (this.currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        
        return this.filteredItems.slice(startIndex, endIndex);
    }
    
    /**
     * Update component state based on current data
     */
    updateState() {
        const totalItems = this.items.length;
        const filteredCount = this.filteredItems.length;
        const totalPages = Math.ceil(filteredCount / this.options.itemsPerPage);
        
        this.setState({
            totalItems,
            totalPages,
            isEmpty: filteredCount === 0,
            isFiltered: this.searchQuery || this.activeFilters.size > 0,
            hasSelection: this.selectedItems.size > 0,
            allSelected: this.selectedItems.size === filteredCount && filteredCount > 0,
            currentPage: Math.min(this.currentPage, Math.max(1, totalPages))
        });
    }
    
    /**
     * Handle search input
     * @param {string} query - Search query
     */
    handleSearch(query) {
        this.searchQuery = query;
        this.currentPage = 1;
        this.applyFiltersAndSort();
        this.updateState();
        this.renderUpdate();
        
        this.eventBus.emit('list:search', { query, list: this });
    }
    
    /**
     * Handle filter change
     * @param {string} field - Field to filter
     * @param {string} value - Filter value
     */
    handleFilter(field, value) {
        if (value) {
            this.activeFilters.set(field, value);
        } else {
            this.activeFilters.delete(field);
        }
        
        this.currentPage = 1;
        this.applyFiltersAndSort();
        this.updateState();
        this.renderUpdate();
        
        this.eventBus.emit('list:filter', { field, value, list: this });
    }
    
    /**
     * Clear all filters
     */
    clearFilters() {
        this.searchQuery = '';
        this.activeFilters.clear();
        this.currentPage = 1;
        this.applyFiltersAndSort();
        this.updateState();
        this.renderUpdate();
        
        this.eventBus.emit('list:filters-cleared', { list: this });
    }
    
    /**
     * Handle column sorting
     * @param {string} column - Column to sort by
     */
    handleSort(column) {
        if (this.sortColumn === column) {
            // Toggle direction
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            // New column
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }
        
        this.applyFiltersAndSort();
        this.updateState();
        this.renderUpdate();
        
        this.eventBus.emit('list:sort', { column, direction: this.sortDirection, list: this });
    }
    
    /**
     * Go to specific page
     * @param {number} page - Page number
     */
    goToPage(page) {
        if (page >= 1 && page <= this.state.totalPages) {
            this.currentPage = page;
            this.setState({ currentPage: page });
            this.renderUpdate();
            
            this.eventBus.emit('list:page-change', { page, list: this });
        }
    }
    
    /**
     * Select item
     * @param {string} itemId - Item ID to select
     */
    selectItem(itemId) {
        this.selectedItems.add(itemId);
        this.updateSelectionState();
        this.updateSelectionUI();
        
        this.eventBus.emit('list:item-selected', { itemId, list: this });
    }
    
    /**
     * Deselect item
     * @param {string} itemId - Item ID to deselect
     */
    deselectItem(itemId) {
        this.selectedItems.delete(itemId);
        this.updateSelectionState();
        this.updateSelectionUI();
        
        this.eventBus.emit('list:item-deselected', { itemId, list: this });
    }
    
    /**
     * Toggle item selection
     * @param {string} itemId - Item ID to toggle
     */
    toggleItemSelection(itemId) {
        if (this.selectedItems.has(itemId)) {
            this.deselectItem(itemId);
        } else {
            this.selectItem(itemId);
        }
    }
    
    /**
     * Select all items
     */
    selectAll() {
        this.filteredItems.forEach(item => {
            this.selectedItems.add(this.getItemId(item));
        });
        this.updateSelectionState();
        this.updateSelectionUI();
        
        this.eventBus.emit('list:all-selected', { list: this });
    }
    
    /**
     * Deselect all items
     */
    deselectAll() {
        this.selectedItems.clear();
        this.updateSelectionState();
        this.updateSelectionUI();
        
        this.eventBus.emit('list:all-deselected', { list: this });
    }
    
    /**
     * Update selection state
     */
    updateSelectionState() {
        const hasSelection = this.selectedItems.size > 0;
        const allSelected = this.selectedItems.size === this.filteredItems.length && this.filteredItems.length > 0;
        
        this.setState({ hasSelection, allSelected });
    }
    
    /**
     * Update selection UI elements
     */
    updateSelectionUI() {
        // Update bulk actions
        const bulkActionSelect = this.$('.bulk-action-select');
        const executeBtn = this.$('.execute-bulk');
        const bulkActions = this.$('.bulk-actions');
        
        if (bulkActionSelect) {
            bulkActionSelect.disabled = !this.state.hasSelection;
            bulkActionSelect.querySelector('option').textContent = `Bulk Actions (${this.selectedItems.size})`;
        }
        
        if (executeBtn) {
            executeBtn.disabled = !this.state.hasSelection;
        }
        
        if (bulkActions) {
            bulkActions.classList.toggle('opacity-50', !this.state.hasSelection);
        }
        
        // Update select all checkbox
        const selectAllCheckbox = this.$('.select-all-checkbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = this.state.allSelected;
            selectAllCheckbox.indeterminate = this.state.hasSelection && !this.state.allSelected;
        }
    }
    
    /**
     * Execute bulk action
     */
    async executeBulkAction() {
        const bulkActionSelect = this.$('.bulk-action-select');
        if (!bulkActionSelect || !bulkActionSelect.value) return;
        
        const actionId = bulkActionSelect.value;
        const bulkActions = this.getBulkActions();
        const action = bulkActions.find(a => a.id === actionId);
        
        if (!action) return;
        
        // Confirm action if needed
        if (action.confirmMessage) {
            if (!confirm(action.confirmMessage)) {
                return;
            }
        }
        
        try {
            const selectedItemData = this.getSelectedItems();
            await action.action(selectedItemData);
            
            // Reset selection and bulk action dropdown
            this.deselectAll();
            bulkActionSelect.value = '';
            
            this.showNotification(`Bulk action "${action.label}" completed successfully`, 'success');
            
        } catch (error) {
            this.handleError(error, 'bulk action');
        }
    }
    
    /**
     * Get selected item data
     * @returns {Array} Array of selected item objects
     */
    getSelectedItems() {
        return this.items.filter(item => this.selectedItems.has(this.getItemId(item)));
    }
    
    /**
     * Get item ID for tracking
     * Override in subclasses to define how to identify items
     * @param {Object} item - Item object
     * @returns {string} Item ID
     */
    getItemId(item) {
        return item.id || item._id || JSON.stringify(item);
    }
    
    /**
     * Get nested object value by path
     * @param {Object} obj - Object to get value from
     * @param {string} path - Property path (e.g., 'user.name')
     * @returns {any} Property value
     */
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => current?.[key], obj);
    }
    
    /**
     * Get unique values for a field (for filter options)
     * @param {string} field - Field name
     * @returns {Array} Unique values
     */
    getUniqueValues(field) {
        const values = this.items.map(item => this.getNestedValue(item, field))
            .filter(value => value != null && value !== '');
        return [...new Set(values)].sort();
    }
    
    /**
     * Debounce function calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Get list statistics
     * @returns {Object} List statistics
     */
    getStatistics() {
        return {
            totalItems: this.items.length,
            filteredItems: this.filteredItems.length,
            selectedItems: this.selectedItems.size,
            currentPage: this.currentPage,
            totalPages: this.state.totalPages,
            isFiltered: this.state.isFiltered,
            hasSelection: this.state.hasSelection
        };
    }
}

// Export for module systems or global usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ListComponent;
} else {
    window.ListComponent = ListComponent;
}