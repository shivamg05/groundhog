//stamps elements in DOM with element ids
(function() {
    let idCounter = 1;

    function isElementVisible(el) {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        
        // 1. Check dimensions
        if (rect.width <= 0 || rect.height <= 0) return false;
        
        // 2. Check CSS visibility
        if (style.visibility === 'hidden' || style.display === 'none' || style.opacity === '0') return false;
        
        return true;
    }

    const allElements = document.querySelectorAll('*');
    
    allElements.forEach(el => {
        // 1. Assign a Unique ID to everything
        // This is the ID the model will predict.
        el.setAttribute('data-m2w-id', idCounter++);
        
        // 2. Mark Visibility
        // This helps Phase 2 (Preprocessing) know what to include in the prompt.
        if (isElementVisible(el)) {
            el.setAttribute('data-m2w-visible', 'true');
        } else {
            el.setAttribute('data-m2w-visible', 'false');
        }
    });
    
    return idCounter;
})();