document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const body = document.body;
    
    // Check localStorage for saved state
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true') {
        sidebar.classList.add('collapsed');
    }
    
    // Toggle sidebar on button click
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        
        // Save state to localStorage
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
    
    // Create overlay element for mobile view
    const overlay = document.createElement('div');
    overlay.classList.add('overlay');
    body.appendChild(overlay);
    
    // Handle overlay click - close sidebar on mobile
    overlay.addEventListener('click', function() {
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('mobile-expanded');
            overlay.classList.remove('active');
        }
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth <= 768) {
            // Mobile view
            sidebar.classList.remove('collapsed');
            if (sidebar.classList.contains('mobile-expanded')) {
                overlay.classList.add('active');
            }
        } else {
            // Desktop view
            overlay.classList.remove('active');
            if (savedState === 'true') {
                sidebar.classList.add('collapsed');
            }
        }
    });
    
    // Add mobile toggle button if not exists
    if (!document.getElementById('mobileSidebarToggle')) {
        const mobileToggle = document.createElement('button');
        mobileToggle.id = 'mobileSidebarToggle';
        mobileToggle.classList.add('mobile-sidebar-toggle');
        mobileToggle.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-menu"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>
        `;
        
        // Add mobile toggle button to main content
        if (mainContent) {
            mainContent.prepend(mobileToggle);
            
            // Mobile toggle event handler
            mobileToggle.addEventListener('click', function() {
                sidebar.classList.toggle('mobile-expanded');
                overlay.classList.toggle('active');
            });
        }
    }
}); 