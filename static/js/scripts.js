document.addEventListener('DOMContentLoaded', function() {
    initializeUIComponents();
    initializeCartEventListeners();
    initializeAddToCartButtons();
    initializeQuantityButtons();
    initializeMagnificPopup();
    initializeProductItemRedirects();
    initializeHeaderScroll();
    initializeColorSelection();
    initializeCartQuantityHandlers();
    initializeCartCount();
    
    // Example for multiple notifications
    const notifications = document.querySelectorAll('.notification');
    notifications.forEach(notification => {
        const timeoutDuration = 5000; // 5 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            notification.addEventListener('transitionend', () => {
                notification.remove();
            });
        }, timeoutDuration);
    });
//FOR CURRENY UPDATE
    const currencyItems = document.querySelectorAll('.currency-item');
    let currentCurrency = 'NGN'; // Default currency
    let exchangeRates = {};

    /**
     * Fetch exchange rates from Open Exchange Rates API
     * @param {string} baseCurrency - The base currency code (e.g., 'NGN')
     */
    async function fetchExchangeRates(baseCurrency = 'NGN') {
        try {
            const response = await fetch(`https://open.er-api.com/v6/latest/${baseCurrency}`);
            const data = await response.json();
            if (!data || !data.rates) {
                console.error('Invalid data received from exchange rate API.');
                return;
            }
            exchangeRates = data.rates;
            console.log('Exchange rates fetched:', exchangeRates);
        } catch (error) {
            console.error('Error fetching exchange rates:', error);
        }
    }

    /**
     * Update all product prices based on the selected currency
     * @param {string} currency - The selected currency code (e.g., 'EUR')
     */
    function updatePrices(currency) {
        const priceElements = document.querySelectorAll('.product-price');
        const rate = exchangeRates[currency];

        if (!rate) {
            console.error(`Exchange rate for ${currency} not found.`);
            return;
        }

        priceElements.forEach(el => {
            const basePriceStr = el.getAttribute('data-base-price');
            const basePrice = parseFloat(basePriceStr);
            if (isNaN(basePrice)) {
                console.error('Invalid base price:', basePriceStr);
                return;
            }
            const convertedPrice = (basePrice * rate).toFixed(2);
            el.textContent = `${currency} ${convertedPrice}`;
        });
        console.log(`Prices updated to ${currency}`);
    }

    /**
     * Set the active class on the selected currency item
     * @param {Element} selectedItem - The clicked currency item element
     */
    function setActiveCurrency(selectedItem) {
        currencyItems.forEach(item => item.classList.remove('active'));
        selectedItem.classList.add('active');
    }

    /**
     * Event listener for currency item clicks
     */
    currencyItems.forEach(item => {
        item.addEventListener('click', async () => {
            const selectedCurrency = item.getAttribute('data-currency');
            if (selectedCurrency === currentCurrency) return; // No change needed

            currentCurrency = selectedCurrency;
            setActiveCurrency(item); // Update active class

            await fetchExchangeRates('NGN'); // Fetch new rates based on NGN
            updatePrices(currentCurrency); // Update displayed prices

            // Store selected currency in localStorage for persistence
            localStorage.setItem('selectedCurrency', currentCurrency);
            console.log(`Currency selected: ${currentCurrency}`);
        });
    });

    /**
     * Initialize currency selection on page load
     */
    (async function initializeCurrency() {
        const storedCurrency = localStorage.getItem('selectedCurrency');
        currentCurrency = storedCurrency ? storedCurrency : 'NGN';

        const activeItem = Array.from(currencyItems).find(
            item => item.getAttribute('data-currency') === currentCurrency
        );
        if (activeItem) setActiveCurrency(activeItem);

        await fetchExchangeRates('NGN'); // Fetch rates based on initialized currency
        updatePrices(currentCurrency); // Update displayed prices
    })();

    // Additional event listener to handle active class and update selected currency display
    currencyItems.forEach(item => {
        item.addEventListener('click', function () {
            currencyItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            const selectedCurrencyElement = document.querySelector('#selected-currency');
            if (selectedCurrencyElement) {
                selectedCurrencyElement.innerHTML = this.getAttribute('data-currency') + ' <i class="arrow_carrot-down"></i>';
            }
        });
    });
});

// Define cartUrl globally
const cartIcon = document.querySelector('.cart-icon');
const cartUrl = cartIcon ? cartIcon.getAttribute('data-cart-url') : '';


// -------------------- Initialization Functions --------------------

// Placeholder for additional UI components
function initializeUIComponents() {
    // Initialize other UI components if needed
}

function initializeCartCount() {
    fetch('/products/cart-count/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount(data.cart_quantity);
        } else {
            console.error('Failed to fetch cart count.');
        }
    })
    .catch(error => {
        console.error('Error fetching cart count:', error);
    });
}

// -------------------- Cart Event Listeners --------------------

function initializeCartEventListeners() {
    const cartIcons = document.querySelectorAll('.cart-icon');
    const overlay = document.getElementById('overlay');
    const cartSidebar = document.getElementById('cart_sidebar');
    const closeCartSidebar = document.getElementById('close-cart-sidebar');

    const toggleSidebar = (isVisible) => {
        if (isVisible) {
            cartSidebar.classList.add('open');
            overlay.classList.add('show');
        } else {
            cartSidebar.classList.remove('open');
            overlay.classList.remove('show');
        }
    };

    cartIcons.forEach(icon => {
        icon.addEventListener('click', (event) => {
            event.preventDefault();
            toggleSidebar(true);
        });
    });

    [closeCartSidebar, overlay].forEach(element => {
        if (element) {
            element.addEventListener('click', () => toggleSidebar(false));
        }
    });

    // Remove Item Links
    const removeItemLinks = document.querySelectorAll('.remove-item');
    removeItemLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const productSlug = link.getAttribute('data-product-slug');
            const size = link.getAttribute('data-size');
            const color = link.getAttribute('data-color');
            removeFromCart(productSlug, size, color);
        });
    });
}

// -------------------- Add to Cart Functionality --------------------

function initializeAddToCartButtons() {
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();

            const form = button.closest('form');
            if (!form) {
                console.error('Add to Cart button is not inside a form.');
                showNotification('error', 'Internal error: Unable to add to cart.');
                return;
            }

            const productSlug = form.getAttribute('data-product-slug');
            if (!productSlug) {
                console.error('data-product-slug attribute is missing on the form.');
                showNotification('error', 'Internal error: Product information is missing.');
                return;
            }

            const sizeInput = form.querySelector('input[name="size"]:checked') || form.querySelector('input[name="size"]');
            const colorInput = form.querySelector('input[name="color"]:checked') || form.querySelector('input[name="color"]');
            const quantityInput = form.querySelector('input[name="quantity"]');

            const formData = {
                size: sizeInput ? sizeInput.value : '',
                color: colorInput ? colorInput.value : '',
                quantity: parseInt(quantityInput.value, 10) || 1
            };

            fetch(`/products/cart/add/${productSlug}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('success', data.message || 'Product added to cart successfully.', cartUrl);
                    updateCartCount(data.cart_count);
                    updateCartSidebar();
                } else {
                    showNotification('error', data.message || 'Failed to add product to cart.');
                }
            })
            .catch(error => {
                console.error('Error adding to cart:', error);
                showNotification('error', 'An error occurred while adding to the cart.');
            });
        });
    });
}

// // -------------------- Quantity Buttons Initialization --------------------

function initializeQuantityButtons() {
    const qtyMinusButtons = document.querySelectorAll('.add-qty-btn-minus');
    const qtyPlusButtons = document.querySelectorAll('.add-qty-btn-plus');
    const qtyInputs = document.querySelectorAll('.quantity-input');

    qtyMinusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.nextElementSibling;
            if (!input) return;
            let currentValue = parseInt(input.value, 10);
            if (currentValue > 1) {
                input.value = currentValue - 1;
            }
        });
    });

    qtyPlusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.previousElementSibling;
            if (!input) return;
            let currentValue = parseInt(input.value, 10);
            input.value = currentValue + 1;
            
        });
    });

    qtyInputs.forEach(input => {
        input.addEventListener('change', function() {
            let value = parseInt(this.value, 10);
            if (isNaN(value) || value < 1) {
                value = 1;
                this.value = value;
            }
            
        });
    });
}

// -------------------- Update Cart Sidebar --------------------

function updateCartSidebar() {
    fetch('/products/cart-sidebar-content/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.html) {
            document.getElementById('cart_sidebar').innerHTML = data.html;
        }
        if (typeof data.cart_count !== 'undefined') {
            updateCartCount(data.cart_count);
        }
    })
    .catch(error => {
        console.error('Error updating cart sidebar:', error);
    });
}

// -------------------- Update Cart Count --------------------

function updateCartCount(count) {
    const cartCountElements = document.querySelectorAll('.cart-count');
    cartCountElements.forEach(element => {
        element.innerText = count;
    });
}

// -------------------- Remove from Cart Functionality --------------------

// Function to dynamically remove a specific item from the cart
function removeFromCart(productSlug, size, color) {
    fetch(`/products/cart/remove/${productSlug}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            size: size,
            color: color
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('success', data.message || 'Item removed from cart.');
            updateCartCount(data.cart_count);
            updateCartSidebar();

            // Optionally, remove the item's row from the table
            const rowSelector = `tr[data-product-slug="${productSlug}"][data-size="${size}"][data-color="${color}"]`;
            const row = document.querySelector(rowSelector);
            if (row) {
                row.remove();
            }
        } else {
            showNotification('error', data.message || 'Failed to remove item from cart.');
        }
    })
    .catch(error => {
        console.error('Error removing from cart:', error);
        showNotification('error', 'An error occurred while removing the item.');
    });
}

// -------------------- Update Cart Item Functionality --------------------


// Function to update cart item
function updateCartItem(productSlug, quantity, size, color) {
    if (!productSlug || !size || !color) {
        console.error('Missing required attributes:', { productSlug, size, color });
        showNotification('error', 'Unable to update cart item due to missing information.');
        return;
    }

    fetch(`/products/cart/update-cart-item/${productSlug}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            quantity: quantity,
            size: size, 
            color: color
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update individual item's total price
            const row = document.querySelector(`tr[data-product-slug="${productSlug}"][data-size="${size}"][data-color="${color}"]`);
            if (row) {
                const totalPriceCell = row.querySelector('.cart__price');
                if (totalPriceCell) {
                    totalPriceCell.textContent = `$${data.item_total.toFixed(2)}`;
                }
            }

            // Update overall cart subtotal and total
            const cartSubtotal = document.getElementById('cart-subtotal');
            const cartTotal = document.getElementById('cart-total');
            if (cartSubtotal) {
                cartSubtotal.textContent = `$${data.total_price.toFixed(2)}`;
            }
            if (cartTotal) {
                cartTotal.textContent = `$${data.total_price.toFixed(2)}`;
            }

            // Update cart count
            updateCartCount(data.cart_count);
            // Assuming updateCartSidebar is defined elsewhere
            updateCartSidebar();
            
            showNotification('success', data.message || 'Cart updated successfully.', cartUrl);
        } else {
            showNotification('error', data.message || 'Failed to update cart.');
        }
    })
    .catch(error => {
        console.error('Error updating cart:', error);
        showNotification('error', 'An error occurred while updating the cart.');
    });
}

// -------------------- Helper Functions --------------------

// Function to get the CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Function to show notifications
function showNotification(type, message, cartUrl = '') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.transform = 'translateY(-20px)';
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-title">${capitalizeFirstLetter(type)}</div>
            <div class="notification-description">${message}</div>
            ${type === 'success' && cartUrl ? `<a href="${cartUrl}">View Cart</a>` : ''}
            <div class="close-button">&times;</div>
        </div>
    `;

    document.body.appendChild(notification);

    // Automatically remove the notification after 3 seconds
    const timeoutDuration = 5000; // 5 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        notification.addEventListener('transitionend', () => {
            notification.remove();
        });
    }, timeoutDuration);

    // Remove the notification when the close button is clicked
    notification.querySelector('.close-button').addEventListener('click', () => {
        notification.remove();
    });
}

// Function to capitalize the first letter
function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

// -------------------- Additional Functionalities --------------------

// Initialize Magnific Popup
function initializeMagnificPopup() {
    $('.video-link, .video-popup').magnificPopup({
        type: 'iframe',
        iframe: {
            patterns: {
                youtube: {
                    index: 'youtube.com/',
                    id: 'v=',
                    src: 'https://www.youtube.com/embed/%id%?autoplay=1',
                },
                vimeo: {
                    index: 'vimeo.com/',
                    id: '/',
                    src: 'https://player.vimeo.com/video/%id%?autoplay=1',
                },
                gmaps: {
                    index: 'https://maps.google.',
                    src: '%id%&output=embed',
                },
                mp4: {
                    index: '.mp4',
                    src: '%id%',
                },
            },
        },
    });
}

// Product Item Redirect
function initializeProductItemRedirects() {
    const productItems = document.querySelectorAll('.product__item');
    productItems.forEach(item => {
        item.addEventListener('click', () => {
            const url = item.getAttribute('data-url');
            if (url) {
                window.location.href = url;
            }
        });
    });
}

// Initialize Header Scroll
function initializeHeaderScroll() {
    const header = document.querySelector('.header');
    window.addEventListener('scroll', function() {
        if (window.scrollY > 0) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });
}

// Initialize Color Selection
function initializeColorSelection() {
    const colorLabels = document.querySelectorAll('.product__details__option__color label');
    colorLabels.forEach(label => {
        label.addEventListener('click', function() {
            colorLabels.forEach(lbl => lbl.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
}

// Initialize cart event listeners for quantity changes
function initializeCartQuantityHandlers() {
    // Selectors should match your HTML structure
    const qtyInputs = document.querySelectorAll('.quantity-input');
    const qtyMinusButtons = document.querySelectorAll('.qty-btn-minus'); 
    const qtyPlusButtons = document.querySelectorAll('.qty-btn-plus');

    // Handle manual input changes
    qtyInputs.forEach(input => {
        input.addEventListener('change', function() {
            const quantity = parseInt(this.value, 10) || 1;
            const productSlug = this.getAttribute('data-product-slug');
            const size = this.getAttribute('data-size');
            const color = this.getAttribute('data-color');

            if (!productSlug || !size || !color) {
                console.error('Missing attributes for cart item:', { productSlug, size, color });
                showNotification('error', 'Unable to update cart item due to missing information.');
                return;
            }

            updateCartItem(productSlug, quantity, size, color);
        });
    });

    // Handle minus button clicks  
    qtyMinusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.nextElementSibling;
            if (!input) return;
            
            let currentValue = parseInt(input.value, 10) || 1;
            if (currentValue > 1) {
                currentValue--;
                input.value = currentValue;
                
                const productSlug = input.getAttribute('data-product-slug');
                const size = input.getAttribute('data-size'); 
                const color = input.getAttribute('data-color');
                
                if (!productSlug || !size || !color) {
                    console.error('Missing attributes for cart item:', { productSlug, size, color });
                    showNotification('error', 'Unable to update cart item due to missing information.');
                    return;
                }

                updateCartItem(productSlug, currentValue, size, color);
            }
        });
    });

    // Handle plus button clicks
    qtyPlusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.previousElementSibling;
            if (!input) return;
            
            let currentValue = parseInt(input.value, 10) || 1;
            currentValue++;
            input.value = currentValue;
            
            const productSlug = input.getAttribute('data-product-slug');
            const size = input.getAttribute('data-size');
            const color = input.getAttribute('data-color');
            
            if (!productSlug || !size || !color) {
                console.error('Missing attributes for cart item:', { productSlug, size, color });
                showNotification('error', 'Unable to update cart item due to missing information.');
                return;
            }

            updateCartItem(productSlug, currentValue, size, color);
        });
    });

    
}



// Close sidebar when clicking outside
document.addEventListener('click', function(event) {
    const sidebar = document.querySelector('.shop__sidebar');
    const toggleButton = document.querySelector('.sidebar-toggle');
    if (document.body.classList.contains('sidebar-active') &&
        !sidebar.contains(event.target) &&
        !toggleButton.contains(event.target)) {
        document.body.classList.remove('sidebar-active');
    }
});
