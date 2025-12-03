var idCounter = 1;

function isElementVisible(el) {
    var rect = el.getBoundingClientRect();
    var style = window.getComputedStyle(el);
    
    // 1. Check dimensions
    if (rect.width <= 0 || rect.height <= 0) return false;
    
    // 2. Check CSS visibility
    if (style.visibility === 'hidden' || style.display === 'none' || style.opacity === '0') return false;
    
    return true;
}

var allElements = document.querySelectorAll('*');

allElements.forEach(function(el) {
    // 1. Assign a Unique ID to everything
    el.setAttribute('data-m2w-id', idCounter++);
    
    // 2. Mark Visibility
    if (isElementVisible(el)) {
        el.setAttribute('data-m2w-visible', 'true');
    } else {
        el.setAttribute('data-m2w-visible', 'false');
    }
});

return idCounter;