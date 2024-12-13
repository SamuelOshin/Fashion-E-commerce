document.addEventListener('DOMContentLoaded', function() {
    const cartIcon = document.querySelectorAll('.cart-icon');
    const cartSidebar = document.getElementById('cart_sidebar');
    const closeCartSidebar = document.getElementById('close-cart-sidebar');
    const overlay = document.getElementById('overlay');
    const cartUrl = cartIcon.length > 0 ? cartIcon[0].getAttribute('data-cart-url') : '';

    const toggleSidebar = (isVisible) => {
        if (isVisible) {
            cartSidebar.classList.add('open');
            overlay.classList.add('show');
        } else {
            cartSidebar.classList.remove('open');
            overlay.classList.remove('show');
        }
    };

    cartIcon.forEach(icon => {
        icon.addEventListener('click', (event) => {
            event.preventDefault();
            toggleSidebar(true);
        });
    });

    [closeCartSidebar, overlay].forEach((element) =>
        element.addEventListener('click', () => toggleSidebar(false))
    );

    // Initialize quantity buttons for product details page
    initializeQuantityButtons();

    // Function to get the CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Function to show notifications
    function showNotification(type, message) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.transform = 'translateY(-20px)';
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${capitalizeFirstLetter(type)}</div>
                <div class="notification-description">${message}</div>
                <div class="close-button">\xD7</div>
            </div>
        `;

        document.body.appendChild(notification);

        // Automatically remove the notification after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);

        // Remove the notification when the close button is clicked
        notification.querySelector('.close-button').addEventListener('click', () => {
            notification.remove();
        });
    }

    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    // Add to cart functionality
    const addToCartButtons = document.querySelectorAll('.add-cart');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();

            const url = this.getAttribute('data-url');
            const quantity = document.getElementById('quantity-input')?.value || 1;
            const selectedSizes = Array.from(document.querySelectorAll('input[name="size"]:checked')).map(input => input.value);
            const selectedColors = Array.from(document.querySelectorAll('input[name="color"]:checked')).map(input => input.value);

            if (selectedSizes.length === 0 || selectedColors.length === 0) {
                showNotification('error', 'Please select at least one size and one color.');
                return;
            }

            // Handle adding to cart logic here
            console.log('Selected Sizes:', selectedSizes);
            console.log('Selected Colors:', selectedColors);
            console.log('Quantity:', quantity);

            // Example: Send data to server
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    sizes: selectedSizes,
                    colors: selectedColors,
                    quantity: quantity
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Response:', data); // Log the response from the server
                if (data.success) {
                    showNotification('success', `Product added successfully. <a href="${cartUrl}">View Cart</a>`);
                    updateCartCount(data.cart_count); // Update cart count
                    updateCartSidebar();
                } else {
                    showNotification('error', 'Failed to add product to cart.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('error', 'An error occurred while adding the product to the cart.');
            });
        });
    });

    // Function to update cart count
    function updateCartCount(count) {
        document.querySelectorAll('.cart-count').forEach(element => {
            element.textContent = count;
        });
    }

    // Close cart sidebar functionality
    const closeCartSidebarButton = document.getElementById('close-cart-sidebar');
    if (closeCartSidebarButton) {
        closeCartSidebarButton.addEventListener('click', function() {
            const cartSidebar = document.querySelector('.cart-sidebar');
            if (cartSidebar) {
                cartSidebar.classList.remove('open');
            }
        });
    }

    // Header Scroll
    const header = document.querySelector('.header');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 0) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });

    // Color selection functionality
    const colorLabels = document.querySelectorAll('.product__details__option__color label');

    if (colorLabels) {
        colorLabels.forEach(label => {
            label.addEventListener('click', function() {
                // Remove the selected class from all labels
                colorLabels.forEach(lbl => lbl.classList.remove('selected'));
                // Add the selected class to the clicked label
                this.classList.add('selected');
            });
        });
    }
});

function initializeQuantityButtons() {
    const qtyInputs = document.querySelectorAll('.quantity-input');
    const qtyMinusButtons = document.querySelectorAll('.qty-btn-minus');
    const qtyPlusButtons = document.querySelectorAll('.qty-btn-plus');

    qtyMinusButtons.forEach(button => {
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        newButton.addEventListener('click', function() {
            const input = this.nextElementSibling;
            if (!input) return;
            
            const currentValue = parseInt(input.value);
            if (currentValue > 1) {
                input.value = currentValue - 1;
                updateCartItem(input);
            }
        });
    });

    qtyPlusButtons.forEach(button => {
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        newButton.addEventListener('click', function() {
            const input = this.previousElementSibling;
            if (!input) return;
            
            const currentValue = parseInt(input.value);
            input.value = currentValue + 1;
            updateCartItem(input);
        });
    });

    qtyInputs.forEach(input => {
        const newInput = input.cloneNode(true);
        input.parentNode.replaceChild(newInput, input);
        newInput.addEventListener('change', function() {
            if (parseInt(this.value) < 1) {
                this.value = 1;
            }
            updateCartItem(this);
        });
    });
}

function updateCartItem(input) {
    const productSlug = input.getAttribute('data-product-slug');
    const quantity = parseInt(input.value);
    const url = `/products/cart/update-cart-item/${productSlug}/?quantity=${quantity}`;

    fetch(url, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then((response) => response.json())
    .then((data) => {
        document.querySelectorAll('.cart-count').forEach(element => {
            element.textContent = data.cart_count;
        });
        updateCartSidebar();
    })
    .catch((error) => console.error('Error updating cart:', error));
}

function updateCartSidebar() {
    fetch('/products/cart-sidebar-content/')
        .then(response => response.text())
        .then(html => {
            document.getElementById('cart_sidebar').innerHTML = html;
            initializeQuantityButtons();  // Reinitialize quantity buttons
        });
}

function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.transform = 'translateY(-20px)';
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-title">${capitalizeFirstLetter(type)}</div>
            <div class="notification-description">${message}</div>
            <div class="close-button">\xD7</div>
        </div>
    `;

    document.body.appendChild(notification);

    // Automatically remove the notification after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);

    // Remove the notification when the close button is clicked
    notification.querySelector('.close-button').addEventListener('click', () => {
        notification.remove();
    });
}

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

const productItems = document.querySelectorAll('.product__item');
productItems.forEach((item) =>
    item.addEventListener('click', () => {
        const url = item.getAttribute('data-url');
        window.location.href = url;
    })
);

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
