document.addEventListener('DOMContentLoaded', function() {
    // Set a flag to track if we should scroll
    let shouldScroll = false;
    
    function scrollToTransactions() {
        const targetElement = document.getElementById('transactions');
        if (targetElement && shouldScroll) {
            setTimeout(function() {
                const offset = targetElement.getBoundingClientRect().top + window.pageYOffset - 80;
                window.scrollTo({
                    top: offset,
                    behavior: 'smooth'
                });
            }, 500);
        }
    }
    
    // Only scroll if coming from a stock box click or if URL has #transactions
    if (window.location.hash === '#transactions') {
        shouldScroll = true;
        scrollToTransactions();
    }
    
    // Add click event listeners to stock boxes
    const stockBoxes = document.querySelectorAll('.stock-box');
    stockBoxes.forEach(box => {
        box.addEventListener('click', function(e) {
            shouldScroll = true;
            // Add #transactions to URL only for stock box clicks
            if (!box.href.includes('#transactions')) {
                box.href = box.href + '#transactions';
            }
        });
    });
    
    // Prevent scrolling for filter buttons
    const filterButtons = document.querySelectorAll('.btn-group .btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Remove any existing hash from the URL without scrolling
            if (window.location.hash) {
                history.pushState('', document.title, window.location.pathname + window.location.search);
            }
        });
    });
    
    // For stock detail pages, only scroll if coming from a stock box
    if (document.getElementById('stockChartApex') && shouldScroll) {
        scrollToTransactions();
    }
}); 