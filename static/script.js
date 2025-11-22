class LostFoundApp {
    constructor() {
        this.currentPage = 1;
        this.loading = false;
        this.hasMore = true;
        this.currentType = 'all';
        this.currentCategory = '';
        this.init();
    }

    init() {
        if (document.getElementById('itemsGrid')) {
            this.loadCategories();
            this.loadItems();
            this.setupEventListeners();
        }
    }

    setupEventListeners() {
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.currentType = e.target.dataset.type;
                this.currentPage = 1;
                this.hasMore = true;
                this.loadItems(true);
            });
        });

        // Infinite scroll
        window.addEventListener('scroll', () => {
            if (this.loading || !this.hasMore) return;

            const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
            if (scrollTop + clientHeight >= scrollHeight - 500) {
                this.currentPage++;
                this.loadItems(false);
            }
        });
    }

    async loadCategories() {
        try {
            const response = await fetch('/api/categories');
            const categories = await response.json();
            this.renderCategories(categories);
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    renderCategories(categories) {
        const grid = document.getElementById('categoriesGrid');
        grid.innerHTML = categories.map(cat => `
            <div class="category-card" data-category="${cat.name}">
                <span class="category-icon">${cat.icon}</span>
                <span class="category-name">${cat.name}</span>
            </div>
        `).join('');

        // Add category click listeners
        grid.querySelectorAll('.category-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const category = e.currentTarget.dataset.category;
                
                if (this.currentCategory === category) {
                    this.currentCategory = '';
                    e.currentTarget.classList.remove('active');
                } else {
                    this.currentCategory = category;
                    grid.querySelectorAll('.category-card').forEach(c => c.classList.remove('active'));
                    e.currentTarget.classList.add('active');
                }

                this.currentPage = 1;
                this.hasMore = true;
                this.loadItems(true);
            });
        });
    }

    async loadItems(reset = false) {
        if (this.loading) return;

        this.loading = true;
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.style.display = 'block';

        try {
            let url = `/api/items?page=${this.currentPage}&limit=10`;
            if (this.currentType !== 'all') {
                url += `&type=${this.currentType}`;
            }
            if (this.currentCategory) {
                url += `&category=${encodeURIComponent(this.currentCategory)}`;
            }

            const response = await fetch(url);
            const data = await response.json();

            this.hasMore = data.has_next;

            if (reset) {
                document.getElementById('itemsGrid').innerHTML = this.renderItems(data.items);
            } else {
                document.getElementById('itemsGrid').innerHTML += this.renderItems(data.items);
            }
        } catch (error) {
            console.error('Error loading items:', error);
            document.getElementById('itemsGrid').innerHTML = '<p class="error">Failed to load items</p>';
        } finally {
            this.loading = false;
            if (loadingEl) loadingEl.style.display = 'none';
        }
    }

    renderItems(items) {
        if (items.length === 0) {
            return '<p class="no-items">No items found</p>';
        }

        return items.map(item => `
            <div class="item-card">
                <img src="${item.image_url}" alt="${item.title}" onerror="this.src='/static/placeholder.png'">
                <div class="item-card-content">
                    <h4>${this.escapeHtml(item.title)}</h4>
                    <p>${this.escapeHtml(item.description.substring(0, 100))}...</p>
                    <p><strong>Category:</strong> ${this.escapeHtml(item.category)}</p>
                    <p><strong>Location:</strong> ${this.escapeHtml(item.location)}</p>
                    <p><strong>Type:</strong> ${this.escapeHtml(item.type)}</p>
                </div>
            </div>
        `).join('');
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LostFoundApp();
});

// Phone number formatting
document.addEventListener('DOMContentLoaded', function() {
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.startsWith('0')) {
                value = '256' + value.substring(1);
            } else if (value.startsWith('7') || value.startsWith('7')) {
                value = '256' + value;
            }
            
            if (value.length > 0 && !value.startsWith('+')) {
                value = '+' + value;
            }
            
            e.target.value = value;
        });
    });
});