// Fix PDF tabs display
document.addEventListener('DOMContentLoaded', function() {
    // Add this script to the page to fix tab display issues
    const style = document.createElement('style');
    style.textContent = `
        .pdf-tabs-header {
            display: flex !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            width: 100% !important;
            justify-content: flex-start !important;
        }
        
        .pdf-tab-button {
            flex: 0 0 auto !important;
            min-width: 120px !important;
        }
        
        .pdf-tabs-container {
            width: 100% !important;
            margin-top: 20px !important;
        }
        
        .pdf-tab-pane.active {
            display: block !important;
            width: 100% !important;
        }
    `;
    document.head.appendChild(style);
    
    // Function to fix tab display
    function fixTabDisplay() {
        const tabsContainer = document.getElementById('pdf-tabs-container');
        if (tabsContainer) {
            tabsContainer.style.width = '100%';
            
            const tabHeader = tabsContainer.querySelector('.pdf-tabs-header');
            if (tabHeader) {
                tabHeader.style.display = 'flex';
                tabHeader.style.flexWrap = 'nowrap';
                tabHeader.style.overflowX = 'auto';
                tabHeader.style.width = '100%';
                tabHeader.style.justifyContent = 'flex-start';
                
                const tabButtons = tabHeader.querySelectorAll('.pdf-tab-button');
                tabButtons.forEach(button => {
                    button.style.flex = '0 0 auto';
                    button.style.minWidth = '120px';
                });
            }
            
            const tabContent = tabsContainer.querySelector('.pdf-tabs-content');
            if (tabContent) {
                tabContent.style.width = '100%';
                
                const activePane = tabContent.querySelector('.pdf-tab-pane.active');
                if (activePane) {
                    activePane.style.display = 'block';
                    activePane.style.width = '100%';
                }
            }
        }
    }
    
    // Run the fix immediately and periodically
    fixTabDisplay();
    setInterval(fixTabDisplay, 1000);
    
    // Also run when tabs are created or activated
    const originalCreatePdfTab = window.createPdfTab;
    if (originalCreatePdfTab) {
        window.createPdfTab = function() {
            originalCreatePdfTab.apply(this, arguments);
            setTimeout(fixTabDisplay, 100);
        };
    }
    
    const originalSetActivePdfTab = window.setActivePdfTab;
    if (originalSetActivePdfTab) {
        window.setActivePdfTab = function() {
            originalSetActivePdfTab.apply(this, arguments);
            setTimeout(fixTabDisplay, 100);
        };
    }
});