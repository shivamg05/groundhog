var idCounter = 1;

function isElementInViewport(el) {
    var rect = el.getBoundingClientRect();
    var windowHeight = (window.innerHeight || document.documentElement.clientHeight);
    var windowWidth = (window.innerWidth || document.documentElement.clientWidth);

    // 1. Check strict dimensions (is it collapsed?)
    if (rect.width <= 0 || rect.height <= 0) return false;

    // 2. Check CSS visibility (is it hidden via style?)
    var style = window.getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none' || style.opacity === '0') return false;

    // 3. Check Geometric Visibility (Is it in the current scroll view?)
    // We add a 'buffer' of 200px so elements slightly off-screen are still included
    // just in case the model wants to scroll slightly.
    var buffer = 200; 

    var vertInView = (rect.top <= windowHeight + buffer) && ((rect.top + rect.height) >= -buffer);
    var horInView = (rect.left <= windowWidth + buffer) && ((rect.left + rect.width) >= -buffer);

    return (vertInView && horInView);
}

var allElements = document.querySelectorAll('*');

allElements.forEach(function(el) {
    // 1. Assign a Unique ID to everything
    // We assign IDs to everything so the structure remains consistent
    el.setAttribute('data-m2w-id', idCounter++);
    
    // 2. Mark Visibility based on Viewport
    if (isElementInViewport(el)) {
        el.setAttribute('data-m2w-visible', 'true');
    } else {
        el.setAttribute('data-m2w-visible', 'false');
    }
});

return idCounter;