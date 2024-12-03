document.addEventListener('DOMContentLoaded', () => {
    const cartIcon = document.getElementById('cart-icon');
    const cartSidebar = document.getElementById('cart_sidebar');
    const closeCartSidebar = document.getElementById('close-cart-sidebar');
    const overlay = document.getElementById('overlay');

    const toggleSidebar = (isVisible) => {
        if (isVisible) {
            cartSidebar.classList.add('open');
            overlay.classList.add('show');
        } else {
            cartSidebar.classList.remove('open');
            overlay.classList.remove('show');
        }
    };

    cartIcon.addEventListener('click', (event) => {
        event.preventDefault();
        toggleSidebar(true);
    });

    [closeCartSidebar, overlay].forEach((element) =>
        element.addEventListener('click', () => toggleSidebar(false))
    );

    const qtyInputs = document.querySelectorAll('.quantity-input');
    const qtyMinusButtons = document.querySelectorAll('.qty-btn-minus');
    const qtyPlusButtons = document.querySelectorAll('.qty-btn-plus');

    qtyMinusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentElement.querySelector('.quantity-input');
            const currentValue = parseInt(input.value);
            if (currentValue > 1) {
                input.value = currentValue - 1;
                updateCartItem(input);
            }
        });
    });

    qtyPlusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const currentValue = parseInt(input.value);
            input.value = currentValue + 1;
            updateCartItem(input);
        });
    });

    qtyInputs.forEach(input => {
        input.addEventListener('change', function() {
            updateCartItem(this);
        });
    });

    const updateCartItem = (input) => {
        const productSlug = input.getAttribute('data-product-slug');
        const quantity = parseInt(input.value);
        const url = `/products/cart/update-cart-item/${productSlug}/?quantity=${quantity}`;

        fetch(url, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then((response) => response.json())
        .then((data) => {
            if (typeof data.item_total === 'number' && typeof data.total_price === 'number') {
                const itemTotalElements = document.querySelectorAll(`.total-price-${productSlug}`);
                itemTotalElements.forEach(element => {
                    element.textContent = `$${data.item_total.toFixed(2)}`;
                });
                document.querySelectorAll('.subtotal').forEach(element => {
                    element.textContent = `$${data.total_price.toFixed(2)}`;
                });
                document.querySelectorAll('.total').forEach(element => {
                    element.textContent = `$${data.total_price.toFixed(2)}`;
                });
                document.getElementById('cart-count').textContent = data.cart_count;
                showNotification('success', 'Product quantity updated successfully.');
            }
        })
        .catch((error) => console.error('Error updating cart:', error));
    };

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

    const addToCartButtons = document.querySelectorAll('.add-cart');
    const cartUrl = cartIcon.getAttribute('data-cart-url');

    addToCartButtons.forEach((button) =>
        button.addEventListener('click', (event) => {
            event.preventDefault();
            const url = button.getAttribute('data-url');
            const quantity = document.getElementById('quantity-input').value;

            fetch(`${url}?quantity=${quantity}`, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
                .then((response) => response.json())
                .then((data) => {
                    document.getElementById('cart-count').textContent = data.cart_count;
                    showNotification('success', `Product added successfully. <a href="${cartUrl}">View Cart</a>`);
                })
                .catch((error) => {
                    console.error('Error adding product to cart:', error);
                    showNotification('error', 'There was a problem adding the product to the cart.');
                });
        })
    );
});
