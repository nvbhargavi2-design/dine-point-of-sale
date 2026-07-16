// Main JavaScript for Dine POS

document.addEventListener('DOMContentLoaded', () => {
    console.log('Dine POS initialized');
    
    // Add to cart functionality placeholder
    const addToCartBtns = document.querySelectorAll('.add-to-cart');
    addToCartBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const dishId = e.target.dataset.id;
            console.log(`Adding dish ${dishId} to cart`);
            // To do: AJAX request to add to cart
        });
    });
});
